import { FieldStory } from '@/components/FieldStory';
import { OverviewSections } from '@/components/OverviewSections';
export const metadata = { title: 'Overview — StreakForge' };
export default function Overview() {
  return <div className="view"><FieldStory /><OverviewSections /></div>;
}
