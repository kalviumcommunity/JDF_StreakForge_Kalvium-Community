import { BranchExplorer } from '@/components/BubbleChart';
import { RiskTable } from '@/components/RiskTable';
export const metadata = { title: 'Risk & branches — StreakForge' };
export default function Risk() {
  return (
    <div className="view">
      <section id="branches"><div className="wrap"><div className="sec-head reveal"><span className="mono">Finding 04</span><h2>Forty branches, no bad apples</h2><p>Each bubble is a branch. Churn runs from 90.7% to 98.0% and no branch sits outside the statistical fences (90.4% to 98.0%). The spread is what sampling noise looks like.</p></div>
        <BranchExplorer /></div></section>
      <section id="at-risk"><div className="wrap"><div className="sec-head reveal"><span className="mono">Finding 05</span><h2>Twelve members worth a call this week</h2><p>Active members who trigger three or more of four risk signals. Mark a row as contacted to see how a team would work the list.</p></div>
        <RiskTable /></div></section>
    </div>
  );
}
