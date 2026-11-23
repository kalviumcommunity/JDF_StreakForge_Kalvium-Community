'use client';
import { useEffect, useRef, useState } from 'react';
import { useApp } from '@/lib/app';
import { pc } from '@/lib/format';
import { useWidth } from '@/lib/useWidth';

const RANGES = [['all', '2021 to 2025'], ['y24', '2024 onward'], ['12', 'Last 12 cohorts']] as const;

export function CohortChart() {
  const { data, m, rm } = useApp();
  const [range, setRange] = useState<'all' | 'y24' | '12'>('all');
  const [idx, setIdx] = useState(-1);
  const [ref, cw] = useWidth<HTMLDivElement>();
  const path = useRef<SVGPathElement>(null);
  let list = data.cohorts;
  if (range === 'y24') list = list.filter((d) => d.join_month >= '2024-01');
  if (range === '12') list = list.slice(-12);
  const W = Math.max(320, cw), Hh = Math.min(380, W * 0.45), mg = { l: 48, r: 16, t: 20, b: 34 };
  const X = (i: number) => mg.l + (i / (list.length - 1)) * (W - mg.l - mg.r), Y = (v: number) => Hh - mg.b - (v / 0.4) * (Hh - mg.t - mg.b);
  const pts = list.map((d, i) => [X(i), Y(d.activation_rate)]);
  const step = Math.ceil(list.length / 8);
  const d0 = 'M' + pts.map((p) => p.join(' ')).join('L');
  const mx = list.reduce((a, d, i) => (d.activation_rate > list[a].activation_rate ? i : a), 0);
  const show = (i: number) => setIdx(Math.max(0, Math.min(list.length - 1, i)));
  const hide = () => setIdx(-1);
  useEffect(() => {
    const L = path.current; if (rm || !L) return;
    const len = L.getTotalLength(); L.style.transition = 'none'; L.style.strokeDasharray = String(len); L.style.strokeDashoffset = String(len);
    L.getBoundingClientRect(); L.style.transition = 'stroke-dashoffset 1.4s cubic-bezier(.2,.7,.2,1)'; L.style.strokeDashoffset = '0';
  }, [range, cw, rm]);
  const cur = idx >= 0 && idx < list.length ? list[idx] : null;
  return (
    <>
      <div className="filters"><span className="mono">Range</span>{RANGES.map((r) => <button key={r[0]} className="chip" data-rng={r[0]} aria-pressed={range === r[0]} onClick={() => { setRange(r[0]); setIdx(-1); }}>{r[1]}</button>)}</div>
      <div className="chart" id="cchart" ref={ref}>
        <svg viewBox={`0 0 ${W} ${Hh}`} tabIndex={0} role="img" aria-label="Activation rate by monthly join cohort. Use left and right arrow keys to read values."
          onMouseMove={(e) => { const r = e.currentTarget.getBoundingClientRect(), px = ((e.clientX - r.left) / r.width) * W; show(Math.round(((px - mg.l) / (W - mg.l - mg.r)) * (list.length - 1))); }}
          onMouseLeave={hide} onBlur={hide}
          onKeyDown={(e) => { if (e.key === 'ArrowRight') { e.preventDefault(); show(idx < 0 ? 0 : idx + 1); } if (e.key === 'ArrowLeft') { e.preventDefault(); show(idx < 0 ? 0 : idx - 1); } }}>
          {[0, 0.1, 0.2, 0.3, 0.4].map((v) => <g key={v}><line x1={mg.l} x2={W - mg.r} y1={Y(v)} y2={Y(v)} stroke="var(--line2)" /><text x={mg.l - 8} y={Y(v) + 4} textAnchor="end">{(v * 100).toFixed(0)}%</text></g>)}
          {list.map((d, i) => i % step === 0 && <text key={d.join_month} x={X(i)} y={Hh - 10} textAnchor="middle">{d.join_month}</text>)}
          <line x1={mg.l} x2={W - mg.r} y1={Y(m.cohortMean)} y2={Y(m.cohortMean)} stroke="var(--ember)" strokeDasharray="4 4" />
          <path d={`${d0}L${X(list.length - 1)} ${Y(0)}L${X(0)} ${Y(0)}Z`} fill="var(--loyal)" fillOpacity=".1" />
          <path id="cpath" ref={path} d={d0} fill="none" stroke="var(--ink)" strokeWidth="2" />
          <circle cx={pts[mx][0]} cy={pts[mx][1]} r="5" fill="var(--ember)" />
          <text x={pts[mx][0]} y={pts[mx][1] - 12} textAnchor={mx > list.length - 4 ? 'end' : 'middle'} style={{ fill: 'var(--ink)' }}>{list[mx].join_month} · {pc(list[mx].activation_rate)}</text>
          <line id="cx" x1={cur ? pts[idx][0] : 0} x2={cur ? pts[idx][0] : 0} y1={mg.t} y2={Hh - mg.b} stroke="var(--ink)" opacity={cur ? 0.35 : 0} />
          <circle id="cd" cx={cur ? pts[idx][0] : 0} cy={cur ? pts[idx][1] : 0} r="5" fill="var(--ink)" opacity={cur ? 1 : 0} />
        </svg>
        <div className={'ctip' + (cur ? ' on' : '')} id="ctip" style={cur ? { left: Math.min(W - 170, Math.max(0, pts[idx][0] - 70)), top: Math.max(0, pts[idx][1] - 48) } : undefined}>{cur && `${cur.join_month} · ${pc(cur.activation_rate)} of ${cur.members} members`}</div>
      </div>
      <p className="mono" style={{ marginTop: 10 }}>Hover or use arrow keys on the chart. Each point is one join-month cohort. Dashed line: all-time mean {pc(m.cohortMean)}.</p>
    </>
  );
}
