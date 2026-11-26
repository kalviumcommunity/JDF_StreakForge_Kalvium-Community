'use client';
import { useState } from 'react';
import { useApp } from '@/lib/app';
import { nf, pc } from '@/lib/format';
import { useWidth } from '@/lib/useWidth';
import type { Branch } from '@/lib/types';

export function BranchExplorer() {
  const { data, m } = useApp();
  const [sel, setSel] = useState<string | null>(null);
  const [tip, setTip] = useState<{ t: string; x: number; y: number } | null>(null);
  const [ref, cw] = useWidth<HTMLDivElement>();
  const W = Math.max(320, cw), Hh = Math.min(460, W * 0.62), mg = { l: 48, r: 14, t: 12, b: 40 };
  const xmin = 0.9, xmax = 0.985, ymin = 0.08, ymax = 0.26;
  const X = (v: number) => mg.l + ((v - xmin) / (xmax - xmin)) * (W - mg.l - mg.r);
  const Y = (v: number) => Hh - mg.b - ((v - ymin) / (ymax - ymin)) * (Hh - mg.t - mg.b);
  const R = (n: number) => 3 + Math.sqrt(n) * 0.62;
  const xt: number[] = [], yt: number[] = [];
  for (let v = 0.9; v <= 0.985; v += 0.02) xt.push(v);
  for (let v = 0.1; v <= 0.26; v += 0.04) yt.push(v);
  const b = data.branches.find((x) => x.gym_branch_id === sel);
  const pick = (id: string) => setSel(id);
  const low = () => setSel(data.branches.reduce((a, c) => (c.activation_rate < a.activation_rate ? c : a)).gym_branch_id);
  const high = () => setSel(data.branches.reduce((a, c) => (c.churn_rate > a.churn_rate ? c : a)).gym_branch_id);
  return (
    <div className="rk">
      <div>
        <div className="filters"><button className="chip" id="bLow" onClick={low}>Show lowest activation</button><button className="chip" id="bHigh" onClick={high}>Show highest churn</button><button className="chip" id="bClear" onClick={() => setSel(null)}>Clear selection</button></div>
        <div className="chart" id="bchart" ref={ref}>
          <svg className="bubble-svg" viewBox={`0 0 ${W} ${Hh}`} role="group" aria-label="Branch bubble chart">
            {xt.map((v) => <g key={'x' + v}><line x1={X(v)} x2={X(v)} y1={mg.t} y2={Hh - mg.b} stroke="var(--line2)" /><text x={X(v)} y={Hh - mg.b + 18} textAnchor="middle">{(v * 100).toFixed(0)}%</text></g>)}
            {yt.map((v) => <g key={'y' + v}><line y1={Y(v)} y2={Y(v)} x1={mg.l} x2={W - mg.r} stroke="var(--line2)" /><text x={mg.l - 8} y={Y(v) + 4} textAnchor="end">{(v * 100).toFixed(0)}%</text></g>)}
            <line x1={X(m.churnPipeline)} x2={X(m.churnPipeline)} y1={mg.t} y2={Hh - mg.b} stroke="var(--ember)" strokeDasharray="4 4" />
            <line y1={Y(m.act)} y2={Y(m.act)} x1={mg.l} x2={W - mg.r} stroke="var(--ember)" strokeDasharray="4 4" />
            {data.branches.slice().sort((a, c) => c.members - a.members).map((br) => (
              <circle key={br.gym_branch_id} className={'bub ' + (sel === br.gym_branch_id ? 'sel' : sel ? 'dim' : '')} cx={X(br.churn_rate)} cy={Y(br.activation_rate)} r={R(br.members)} tabIndex={0} role="button"
                aria-label={`${br.gym_branch_id}: ${br.members} members, churn ${pc(br.churn_rate)}, activation ${pc(br.activation_rate)}`} data-b={br.gym_branch_id}
                onClick={() => pick(br.gym_branch_id)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(br.gym_branch_id); } }}
                onMouseEnter={() => setTip({ t: `${br.gym_branch_id} · ${br.members} members`, x: X(br.churn_rate), y: Y(br.activation_rate) - 18 })} onMouseLeave={() => setTip(null)} />
            ))}
            <text x={(W + mg.l) / 2} y={Hh - 4} textAnchor="middle">Churn rate</text>
            <text transform={`translate(12 ${Hh / 2}) rotate(-90)`} textAnchor="middle">7-day activation</text>
          </svg>
          <div className={'ctip' + (tip ? ' on' : '')} id="btip" style={tip ? { left: tip.x, top: tip.y, transform: 'translate(-50%,-100%)' } : undefined}>{tip?.t}</div>
        </div>
        <p className="mono" style={{ marginTop: 10 }}>X: churn rate at pipeline date · Y: 7-day activation · size: members · lines: platform average</p>
      </div>
      <aside className="bcard" id="bcard" aria-live="polite"><BranchCard b={b} /></aside>
    </div>
  );
}

function BranchCard({ b }: { b?: Branch }) {
  const { data, m } = useApp();
  if (!b) {
    return (<><span className="mono">Branch detail</span><h3>Pick a bubble</h3><p style={{ color: 'var(--muted)', margin: 0 }}>Click any branch, or use the shortcuts above. The detail shows how it compares with the platform.</p>
      <dl className="kv" style={{ marginTop: 18 }}><dt>Platform churn</dt><dd>{pc(m.churnPipeline)}</dd><dt>Platform activation</dt><dd>{pc(m.act)}</dd><dt>Branches flagged as outliers</dt><dd>{data.branches.filter((x) => x.is_churn_outlier).length} of {data.branches.length}</dd></dl></>);
  }
  const dc = b.churn_rate - m.churnPipeline, da = b.activation_rate - m.act;
  return (<><span className="mono">Branch detail</span><h3>{b.gym_branch_id}</h3>
    <dl className="kv"><dt>Members</dt><dd>{nf(b.members)}</dd><dt>Churn rate</dt><dd>{pc(b.churn_rate)} ({dc >= 0 ? '+' : ''}{(dc * 100).toFixed(1)} pts)</dd><dt>7-day activation</dt><dd>{pc(b.activation_rate)} ({da >= 0 ? '+' : ''}{(da * 100).toFixed(1)} pts)</dd><dt>Avg sessions per week</dt><dd>{b.avg_sessions_per_week.toFixed(2)}</dd><dt>Churn outlier?</dt><dd>{b.is_churn_outlier ? 'Yes' : 'No'}</dd></dl>
    <p className="callout" style={{ marginTop: 16 }}>{b.members < 200 ? `Small branch: with ${b.members} members a few points of difference is ordinary sampling noise.` : 'Within the fences. Nothing here calls for a branch-specific fix.'}</p></>);
}
