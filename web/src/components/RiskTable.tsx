'use client';
import { useState } from 'react';
import { useApp } from '@/lib/app';
import { copy } from '@/lib/exports';
import { inr } from '@/lib/format';

type SortKey = 'recency' | 'events' | 'ratio';
const SIG = ['R', 'F', 'T', 'P'], SIGT = ['High recency', 'Low frequency', 'Negative trend', 'Paying not showing'];

export function RiskTable() {
  const { data, toast } = useApp();
  const [rq, setRq] = useState('');
  const [sort, setSort] = useState<{ k: SortKey; d: number }>({ k: 'recency', d: -1 });
  const [done, setDone] = useState<Set<string>>(new Set());
  const q = rq.toLowerCase();
  const rows = data.risk.filter((r) => !q || (r.id + r.branch).toLowerCase().includes(q)).slice().sort((a, b) => (a[sort.k] - b[sort.k]) * sort.d);
  const th = (l: string, key: SortKey) => (
    <th aria-sort={sort.k === key ? (sort.d > 0 ? 'ascending' : 'descending') : 'none'}>
      <button data-sort={key} onClick={() => setSort(sort.k === key ? { k: key, d: -sort.d } : { k: key, d: -1 })}>{l}{sort.k === key ? (sort.d > 0 ? ' ↑' : ' ↓') : ''}</button>
    </th>
  );
  const real = data.risk.filter((r) => !r.sample);
  const hasSample = real.length !== data.risk.length;
  return (
    <>
      <div className="filters">
        <input className="search" id="rq" type="search" placeholder="Search by member or branch" aria-label="Search at-risk members" value={rq} onChange={(e) => setRq(e.target.value)} />
        <button className="btn sm" id="copyRisk" onClick={() => copy(real.map((r) => `${r.id}, ${r.branch}, silent ${r.recency} days, ${inr(r.ratio)}/session`).join('\n'), toast, `Outreach list copied (${real.length} real rows${hasSample ? ', samples excluded' : ''})`)}>Copy outreach list</button>
        <span className="mono" id="rcount">{rows.length} of {data.risk.length} shown · {done.size} contacted</span>
      </div>
      <div className="tbl-wrap" id="rtbl">
        {!rows.length ? (
          <div className="empty" style={{ border: 0 }}><h3>No members match</h3><p>No flagged member matches “{rq}”.</p><button className="btn" id="rclear" onClick={() => setRq('')}>Clear search</button></div>
        ) : (
          <table>
            <thead><tr><th>#</th><th>Member</th><th>Branch</th>{th('Days silent', 'recency')}{th('Events', 'events')}{th('₹ per session', 'ratio')}<th>Signals</th><th>Outreach</th></tr></thead>
            <tbody>{rows.map((r) => {
              const isDone = done.has(r.id);
              return (
                <tr key={r.id} className={isDone ? 'done' : ''}>
                  <td className="n">{String(data.risk.indexOf(r) + 1).padStart(2, '0')}</td>
                  <td><span className="mid">{r.sample ? 'Sample member' : r.id}</span> {r.sample && <span className="flag">sample</span>}</td>
                  <td className="n">{r.sample ? '—' : r.branch}</td><td className="n">{r.recency}</td><td className="n">{r.events}</td><td className="n">{inr(r.ratio)}</td>
                  <td><div className="pips" aria-label={`Signals present: ${SIG.filter((_, j) => r.sig[j]).join(', ')}`}>{SIG.map((l, j) => <span key={l} className={'pip' + (r.sig[j] ? ' on' : '')} title={SIGT[j]}>{l}</span>)}</div></td>
                  <td><button className={'btn sm' + (isDone ? ' solid' : '')} data-done={r.id} aria-pressed={isDone} onClick={() => {
                    const n = new Set(done); const was = n.has(r.id); was ? n.delete(r.id) : n.add(r.id); setDone(n);
                    toast(was ? 'Marked as not contacted' : 'Marked as contacted (this session only)');
                  }}>{isDone ? 'Contacted' : 'Mark contacted'}</button></td>
                </tr>
              );
            })}</tbody>
          </table>
        )}
      </div>
      <p className="mono" style={{ marginTop: 14 }}>Signals: R recency above 75th percentile · F fewer events than 25th percentile · T falling trend · P paying but not showing.{hasSample && <> Rows tagged <span className="flag">sample</span> are placeholders.</>}</p>
    </>
  );
}
