'use client';
import { useApp } from '@/lib/app';
import { pc } from '@/lib/format';

const D0 = new Date('2021-01-01').getTime(), D1 = new Date('2026-08-14').getTime();
const x = (d: string) => 40 + ((new Date(d).getTime() - D0) / (D1 - D0)) * 680;

export function ClockSvg() {
  const { asof, m } = useApp();
  const e = x('2025-10-05'), a = x('2026-08-14'), c1 = x('2025-09-05'), c2 = x('2026-07-15');
  const dm = asof === 'data';
  return (
    <svg className="clock-svg" id="clockSvg" viewBox="0 0 760 240" role="img" aria-label="Timeline from January 2021 to August 2026 with a 313-day gap between the last event and the pipeline date">
      <defs><pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="7" stroke="var(--faint)" strokeWidth="1.2" /></pattern></defs>
      <rect x="40" y="96" width={e - 40} height="26" fill="var(--ink)" /><rect x={e} y="96" width={a - e} height="26" fill="url(#hatch)" stroke="var(--faint)" />
      <text x="40" y="84">2021-01 · first event</text>
      <text x={e - 6} y="84" textAnchor="end" className="strong">last real event 2025-10-05</text>
      <text x={(e + a) / 2} y="146" textAnchor="middle" fill="var(--ember-ink)" style={{ fill: 'var(--ember-ink)' }}>313 days with no data</text>
      <line x1={c1} x2={c1} y1="68" y2="132" stroke={dm ? 'var(--ember)' : 'var(--faint)'} strokeWidth={dm ? 3 : 1.5} strokeDasharray={dm ? 0 : '3 3'} />
      <line x1={c2} x2={c2} y1="68" y2="132" stroke={dm ? 'var(--faint)' : 'var(--ember)'} strokeWidth={dm ? 1.5 : 3} strokeDasharray={dm ? '3 3' : 0} />
      <text x={c1} y="172" textAnchor="middle" className={dm ? 'strong' : ''}>cutoff 2025-09-05</text><text x={c1} y="188" textAnchor="middle" className={dm ? 'strong' : ''}>churn {pc(m.churnData)}</text>
      <text x={c2} y="206" textAnchor="middle" className={dm ? '' : 'strong'}>cutoff 2026-07-15</text><text x={c2} y="222" textAnchor="middle" className={dm ? '' : 'strong'}>churn {pc(m.churnPipeline)}</text>
      <text x={a} y="60" textAnchor="end" className="strong">pipeline as-of 2026-08-14</text>
      <text x="40" y="22" style={{ fill: 'var(--muted)' }}>A member is churned if their last billing cycle ended before the cutoff (as-of minus 30 days).</text>
    </svg>
  );
}

export function TwoClocks() {
  const { asof, setAsof, m } = useApp();
  return (
    <div className="clocks reveal">
      <ClockSvg />
      <div className="cc" role="radiogroup" aria-label="Choose as-of date">
        <button className="radio" role="radio" data-asof="pipeline" aria-checked={asof === 'pipeline'} onClick={() => setAsof('pipeline')}><span className="num">{pc(m.churnPipeline)}</span><div><b>Pipeline date</b><span>2026-08-14. Reproducible, but anchored 313 days past the data.</span></div></button>
        <button className="radio" role="radio" data-asof="data" aria-checked={asof === 'data'} onClick={() => setAsof('data')}><span className="num">{pc(m.churnData)}</span><div><b>Data-realistic date</b><span>2025-10-05. The number to act on.</span></div></button>
      </div>
    </div>
  );
}
