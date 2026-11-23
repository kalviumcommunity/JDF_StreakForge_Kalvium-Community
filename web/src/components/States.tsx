'use client';
import { AnchorLink } from './Shell';
import type { Sim } from '@/lib/types';

export function Loading() {
  return (
    <div className="view"><section><div className="wrap" aria-busy="true">
      <div className="skel" style={{ height: 56, width: '50%', marginBottom: 24 }} />
      <div className="skel" style={{ height: 20, width: '70%', marginBottom: 34 }} />
      {[0, 1, 2, 3, 4].map((i) => <div key={i} className="skel" style={{ height: 64, marginBottom: 10 }} />)}
      <p className="mono" role="status">Loading exported results</p>
    </div></section></div>
  );
}
export function Empty({ onReset }: { onReset: () => void }) {
  return (
    <div className="view"><section><div className="wrap"><div className="empty">
      <h3>Nothing to show here yet</h3>
      <p>No rows came back for this view. Go back to the full data, or try a different page.</p>
      <button className="btn solid" data-sim="" onClick={onReset}>Back to the data</button>
    </div></div></section></div>
  );
}
export function ErrorState({ onReset }: { onReset: () => void }) {
  return (
    <div className="view"><section><div className="wrap"><div className="err" role="alert">
      <h3>Results could not load</h3>
      <p>The exported results file did not respond. Retry, or open the last good snapshot from 2025-10-05.</p>
      <div className="ctl-row" style={{ justifyContent: 'center' }}>
        <button className="btn solid" data-sim="" onClick={onReset}>Retry</button>
        <AnchorLink className="btn" href="/kpis/">Use cached KPIs</AnchorLink>
      </div>
    </div></div></section></div>
  );
}
export function SimView({ sim, onReset }: { sim: Exclude<Sim, ''>; onReset: () => void }) {
  return sim === 'loading' ? <Loading /> : sim === 'empty' ? <Empty onReset={onReset} /> : <ErrorState onReset={onReset} />;
}
