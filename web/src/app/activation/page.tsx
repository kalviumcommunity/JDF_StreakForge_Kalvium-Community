import { Funnel } from '@/components/Funnel';
import { CohortChart } from '@/components/CohortChart';
import { SegmentExplorer } from '@/components/SegmentExplorer';
export const metadata = { title: 'Activation — StreakForge' };
export default function Activation() {
  return (
    <div className="view">
      <section id="funnel"><div className="wrap"><div className="sec-head reveal"><span className="mono">Finding 02</span><h2>The cliff after signup</h2><p>18.8% of members do anything within seven days. Everything downstream is smaller still.</p></div><Funnel /></div></section>
      <section id="cohort"><div className="wrap"><div className="sec-head reveal"><span className="mono">Finding 03</span><h2>It is quietly getting better</h2><p>Monthly cohorts rose from <b>14.6% in October 2024</b> to <b>36.6% in September 2025</b>. Something changed. The data cannot say what.</p></div><CohortChart /></div></section>
      <section id="segments"><div className="wrap"><div className="sec-head reveal"><span className="mono">Finding 02, continued</span><h2>No segment explains it</h2><p>Activation barely moves across plan, city, channel or time of day. Membership type is the largest effect and it is still weak.</p></div><SegmentExplorer /></div></section>
    </div>
  );
}
