'use client';
import { useState } from 'react';
import { useApp } from '@/lib/app';
import { nf, pc } from '@/lib/format';

const DIMS: Record<string, string> = { city_tier: 'City tier', has_personal_trainer: 'Personal trainer', membership_type: 'Membership', preferred_workout_time: 'Workout time', referral_source: 'Referral source', signup_channel: 'Signup channel' };

export function SegmentExplorer() {
  const { data, m } = useApp();
  const [dim, setDim] = useState('membership_type');
  const rs = data.segments.filter((r) => r.segment_col === dim).sort((a, b) => b.activation_rate - a.activation_rate);
  const mx = 0.32, r0 = rs[0], v = r0.cramers_v, p = r0.p_value;
  return (
    <div className="exp">
      <div>
        <div className="filters" role="group" aria-label="Dimension">
          {Object.keys(DIMS).map((d) => <button key={d} className="chip" data-dim={d} aria-pressed={dim === d} onClick={() => setDim(d)}>{DIMS[d]}</button>)}
        </div>
        <div id="segs">
          {rs.map((r) => (
            <div className="srow" key={r.segment_level}>
              <span><b>{r.segment_level}</b><br /><span className="mono">{nf(r.members)} members</span></span>
              <div className="bar"><i style={{ '--w': `${(r.activation_rate / mx) * 100}%` } as React.CSSProperties} /><u style={{ '--ref': `${(m.act / mx) * 100}%` } as React.CSSProperties} title={`Platform average ${pc(m.act)}`} /></div>
              <span className="v">{pc(r.activation_rate)}</span>
            </div>
          ))}
          <p className="mono" style={{ marginTop: 12 }}>Ember tick: platform average {pc(m.act)}</p>
        </div>
      </div>
      <aside className="bcard" id="vcard">
        <span className="mono">Strength of association</span><h3>V = {v.toFixed(3)}</h3>
        <div className="vmeter" aria-hidden="true"><i style={{ left: `${Math.min(98, (v / 1) * 100 * 5)}%` }} /></div>
        <div className="vscale"><span>0</span><span>0.1</span><span>0.3</span><span>0.5</span><span>1</span></div>
        <dl className="kv" style={{ marginTop: 16 }}><dt>Reading</dt><dd>{v < 0.1 ? 'Weak' : 'Moderate'}</dd><dt>p-value</dt><dd>{p === 0 ? '< 0.001' : p.toFixed(3)}</dd><dt>Spread, best to worst</dt><dd>{((rs[0].activation_rate - rs[rs.length - 1].activation_rate) * 100).toFixed(1)} pts</dd></dl>
        <p className="callout" style={{ marginTop: 16 }}>{p < 0.05 ? `The difference is statistically real but small: it cannot account for an ${Math.round((1 - m.nAct / m.N) * 100)}% drop-off.` : 'The differences here are within chance.'}</p>
      </aside>
    </div>
  );
}
