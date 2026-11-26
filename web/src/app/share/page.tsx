import { ExportPanel } from '@/components/ExportPanel';
export const metadata = { title: 'Share & export — StreakForge' };
export default function Share() {
  return (
    <div className="view"><section><div className="wrap">
      <div className="sec-head"><span className="mono">Take it with you</span><h2>Share &amp; export</h2><p>Three ways out work today, all built from the same data you are looking at; email is under development. Your current as-of date is carried in.</p></div>
      <ExportPanel />
    </div></section></div>
  );
}
