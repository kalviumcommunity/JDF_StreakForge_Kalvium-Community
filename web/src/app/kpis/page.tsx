import { Ledger } from '@/components/Ledger';
export const metadata = { title: 'KPI ledger — StreakForge' };
export default function Kpis() {
  return (
    <div className="view"><section><div className="wrap">
      <div className="sec-head"><span className="mono">15 KPIs · 5 categories</span><h2>The KPI ledger</h2><p>Every number the pipeline produces, with the definition that produced it. Open a row for the reading note.</p></div>
      <Ledger />
    </div></section></div>
  );
}
