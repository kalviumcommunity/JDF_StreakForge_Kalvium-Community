'use client';
import { useState } from 'react';
import { useApp } from '@/lib/app';
import { AnchorLink } from './Shell';

export function Dossiers() {
  const { data } = useApp();
  const [aud, setAud] = useState('All'), [open, setOpen] = useState<string | null>(null);
  const auds = ['All', ...Array.from(new Set(data.insights.flatMap((i) => i.aud.split(' / '))))];
  const list = data.insights.filter((i) => aud === 'All' || i.aud.includes(aud));
  return (
    <>
      <div className="filters" role="group" aria-label="Audience">
        {auds.map((a) => <button key={a} className="chip" aria-pressed={aud === a} data-aud={a} onClick={() => setAud(a)}>{a}</button>)}
      </div>
      <div className="dos" id="dos">
        {!list.length ? <div className="empty"><h3>Nothing for {aud}</h3><p>No insight is tagged for this audience.</p></div> : list.map((i) => {
          const o = open === i.id;
          return (
            <div className={'dossier' + (o ? ' open' : '')} data-i={i.id} key={i.id}>
              <button className="dh" aria-expanded={o} aria-controls={`d-${i.id}`} onClick={() => setOpen(o ? null : i.id)}>
                <span className="big">{i.id.replace('INS-', '')}</span><span className="tt">{i.title}</span><span className="au">{i.aud}<br />Confidence: {i.conf}</span>
                <svg className="chev" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2"><path d="M8 2v12M2 8h12" /></svg>
              </button>
              <div className="db" id={`d-${i.id}`} role="region"><div><div className="dgrid"><span />
                <div><p className="story-t">{i.story}</p><div className="ctl-row" style={{ marginTop: 18 }}><AnchorLink className="btn sm" href={`/${i.route}/`} anchor={i.anchor}>See the evidence</AnchorLink></div></div>
                <div className="facts"><div><h4>Evidence</h4><p>{i.evidence}</p></div><div><h4>Business impact</h4><p>{i.impact}</p></div><div><h4>Recommended action</h4><p>{i.action}</p></div>
                  <div><h4>Confidence · {i.conf}</h4><div className="meter" aria-hidden="true">{[1, 2, 3, 4].map((n) => <i key={n} className={n <= i.confN ? 'on' : ''} />)}</div></div></div></div></div></div>
            </div>
          );
        })}
      </div>
    </>
  );
}
