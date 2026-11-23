import { Dossiers } from '@/components/Dossiers';
export const metadata = { title: 'Insights — StreakForge' };
export default function Insights() {
  return (
    <div className="view"><section><div className="wrap">
      <div className="sec-head"><span className="mono">5 insights</span><h2>What the data says, and who should act</h2><p>Each finding carries its evidence, the business impact, one recommended action and how confident we are. Filter by who needs to read it.</p></div>
      <Dossiers />
    </div></section></div>
  );
}
