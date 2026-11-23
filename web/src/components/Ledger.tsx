'use client';
import { useEffect, useRef, useState } from 'react';
import { useApp } from '@/lib/app';
import { copy } from '@/lib/exports';

export function Ledger() {
  const { data, toast, rm } = useApp();
  const [cat, setCat] = useState('All'), [q, setQ] = useState(''), [open, setOpen] = useState<string | null>(null);
  const jump = useRef<string | null>(null);
  const cats = ['All', ...Array.from(new Set(data.kpis.map((k) => k.cat)))];
  const ql = q.toLowerCase();
  const list = data.kpis.filter((k) => (cat === 'All' || k.cat === cat) && (!ql || (k.name + k.id + k.defn).toLowerCase().includes(ql)));
  useEffect(() => {
    if (jump.current) { document.querySelector(`[data-k="${jump.current}"]`)?.scrollIntoView({ behavior: rm ? 'auto' : 'smooth', block: 'center' }); jump.current = null; }
  }, [open, rm]);
  return (
    <>
      <div className="filters" role="group" aria-label="Category">
        {cats.map((c) => <button key={c} className="chip" aria-pressed={cat === c} data-cat={c} onClick={() => setCat(c)}>{c}</button>)}
        <input className="search" id="kq" type="search" placeholder="Search KPIs" aria-label="Search KPIs" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      <div className="ledger" id="ledger">
        {!list.length ? (
          <div className="empty"><h3>No KPI matches</h3><p>Nothing in the ledger matches “{q}” in {cat}.</p><button className="btn" id="kclear" onClick={() => { setQ(''); setCat('All'); }}>Clear search</button></div>
        ) : list.map((k) => {
          const isOpen = open === k.id, pair = k.pair ? data.kpis.find((x) => x.id === k.pair) : null;
          return (
            <div className={'lrow' + (isOpen ? ' open' : '')} data-k={k.id} key={k.id}>
              <button className="lhead" aria-expanded={isOpen} aria-controls={`b-${k.id}`} onClick={() => setOpen(isOpen ? null : k.id)}>
                <span className="id">{k.id.replace('kpi_', 'K')}</span><span><span className="nm">{k.name}</span></span><span className="cat">{k.cat}</span>
                <span className="val">{k.display}<small>{k.unit === '%' ? '' : k.unit}</small></span>
                <svg className="chev" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2"><path d="M8 2v12M2 8h12" /></svg>
              </button>
              <div className="lbody" id={`b-${k.id}`} role="region"><div><div className="lin"><span />
                <div><h4>Definition</h4><p>{k.defn}</p></div>
                <div><h4>How to read it</h4><p>{k.note || 'No caveats beyond the definition.'}</p>
                  {pair && <><div className="pair" aria-hidden="true"><i style={{ height: k.value * 60 }} /><i style={{ height: pair.value * 60 }} /></div><p className="mono" style={{ marginTop: 6 }}>{k.id} vs {pair.id}: {k.display} / {pair.display}</p></>}
                  <div className="ctl-row" style={{ marginTop: 12 }}>
                    <button className="btn sm ghost" data-copy={k.display} onClick={() => copy(k.display, toast, 'Value copied')}>Copy value</button>
                    {pair && <button className="btn sm ghost" data-jump={pair.id} onClick={() => { jump.current = pair.id; setOpen(pair.id); }}>Compare with {pair.id.replace('kpi_', 'K')}</button>}
                  </div></div></div></div></div>
            </div>
          );
        })}
      </div>
    </>
  );
}
