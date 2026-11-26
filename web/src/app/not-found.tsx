import { AnchorLink } from '@/components/Shell';
export const metadata = { title: 'Page not found — StreakForge' };
export default function NotFound() {
  return (
    <div className="view"><div className="wrap nf"><div className="num">404</div><div>
      <h2 style={{ fontSize: 56, marginBottom: 14 }}>That page is not on the map</h2>
      <p style={{ color: 'var(--muted)', maxWidth: '44ch' }}>The link may be old, or mistyped. Every dashboard page is one click from the overview.</p>
      <div className="ctl-row" style={{ marginTop: 20 }}><AnchorLink className="btn solid" href="/overview/">Back to overview</AnchorLink><AnchorLink className="btn" href="/kpis/">Open the KPI ledger</AnchorLink></div>
    </div></div></div>
  );
}
