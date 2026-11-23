'use client';
import { useApp } from '@/lib/app';
import { inr, pc } from '@/lib/format';
import { CountUp } from './CountUp';
import { Funnel } from './Funnel';
import { TwoClocks } from './TwoClocks';
import { AnchorLink } from './Shell';

const d = (n: number) => ({ '--d': `${n}ms` } as React.CSSProperties);

export function OverviewSections() {
  const { asof, m } = useApp();
  const churn = asof === 'pipeline' ? m.churnPipeline : m.churnData;
  return (
    <>
      <section><div className="wrap"><div className="sec-head reveal"><span className="mono">The numbers that matter</span><h2>Four figures, one honest caveat</h2></div>
        <div className="heads" id="heads">
          <div className="head reveal"><span className="mono">Retention</span><CountUp to={churn * 100} fmt={(v) => v.toFixed(1) + '%'} /><div className="nm">Churn rate</div>
            <div className="df" id="churnNote">{asof === 'pipeline' ? <>At the pipeline date. At the last real event it is <b>{pc(m.churnData)}</b>.</> : <>At the last real event. The pipeline date gives <b>{pc(m.churnPipeline)}</b>.</>}</div></div>
          <div className="head reveal" style={d(80)}><span className="mono">Activation</span><CountUp to={m.act * 100} fmt={(v) => v.toFixed(1) + '%'} /><div className="nm">7-day activation</div><div className="df">Members who do anything within a week of joining.</div></div>
          <div className="head reveal" style={d(160)}><span className="mono">Streaks</span><CountUp to={m.streak} fmt={(v) => v.toFixed(1)} /><div className="nm">Average streak, days</div><div className="df">Mean of each member&apos;s average streak length.</div></div>
          <div className="head reveal" style={d(240)}><span className="mono">Revenue</span><CountUp to={m.spend} fmt={(v) => inr(v)} /><div className="nm">Median spend per member</div><div className="df">Median, because spend is heavily skewed.</div></div>
        </div></div></section>
      <section id="two-clocks"><div className="wrap"><div className="sec-head reveal"><span className="mono">Finding 01</span><h2>Two clocks, two churn rates</h2><p>The pipeline judges every member as of <b>2026-08-14</b>. The data ends on <b>2025-10-05</b>. The 313 days in between are not inactivity, they are missing records.</p></div>
        <TwoClocks /></div></section>
      <section id="funnel-sec"><div className="wrap"><div className="sec-head reveal"><span className="mono">Finding 02</span><h2>Where members actually fall away</h2><p>Each step shows how many of the {m.N.toLocaleString('en-IN')} signups make it through. The first step after signup is the cliff.</p></div><Funnel /></div></section>
      <section><div className="wrap"><div className="sec-head reveal"><span className="mono">Next</span><h2>Go one level down</h2></div>
        <div className="heads" style={{ borderTop: '1px solid var(--ink)' }}>
          {([['kpis', 'KPI ledger', 'All 15 KPIs with plain-English definitions.'], ['insights', 'Insights', 'Five findings, who should act and how sure we are.'], ['risk', 'Risk & branches', '40 branches and the 12 members to call.'], ['activation', 'Activation', 'Cohorts, segments and what does not explain it.']] as const).map((x, i) => (
            <AnchorLink key={x[0]} className="head reveal" style={{ ...d(i * 70), textDecoration: 'none' }} href={`/${x[0]}/`}>
              <span className="mono">0{i + 1}</span><div className="num" style={{ fontSize: 42, margin: '14px 0 8px' }}>{x[1]}</div><div className="df">{x[2]}</div><span className="btn sm" style={{ marginTop: 14 }}>Open</span>
            </AnchorLink>
          ))}
        </div></div></section>
    </>
  );
}
