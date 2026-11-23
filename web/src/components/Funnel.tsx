'use client';
import { useApp } from '@/lib/app';
import { nf, pc } from '@/lib/format';

export function Funnel() {
  const { data } = useApp();
  const t = data.funnel[0].members;
  return (
    <div className="funnel">
      {data.funnel.map((f, i) => {
        const w = Math.max(0.4, (f.members / t) * 100);
        return (
          <div className="fr" key={f.stage}>
            <div><b>{f.stage}</b><br />{i ? <span className="drop">−{pc(1 - f.members / data.funnel[i - 1].members)} vs previous</span> : <span className="drop">Start</span>}</div>
            <div className="bar"><i style={{ '--w': `${w}%` } as React.CSSProperties} /></div>
            <div className="v">{nf(f.members)}<small>{pc(f.members / t)} of signups</small></div>
          </div>
        );
      })}
    </div>
  );
}
