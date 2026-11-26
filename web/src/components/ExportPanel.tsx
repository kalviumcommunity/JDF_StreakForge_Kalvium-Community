'use client';
import { useMemo } from 'react';
import { useApp } from '@/lib/app';
import { copy, files, mdBrief, printReport, save, zip } from '@/lib/exports';
import { slug } from '@/lib/format';

const d = (n: number) => ({ '--d': `${n}ms` } as React.CSSProperties);

export function ExportPanel() {
  const { data, m, asof, toast } = useApp();
  const md = useMemo(() => mdBrief(data, m, asof), [data, m, asof]);
  return (
    <>
      <div className="share-grid">
        <div className="sc reveal"><span className="mono">01 · Brief</span><h3>Markdown brief</h3><p>Headline numbers, five findings and the twelve names, as one readable file.</p><div className="row"><button className="btn solid" id="xMd" onClick={() => save(`streakforge-brief-${slug()}.md`, new Blob([mdBrief(data, m, asof)], { type: 'text/markdown' }), toast)}>Download .md</button><button className="btn" id="cMd" onClick={() => copy(mdBrief(data, m, asof), toast, 'Brief copied')}>Copy text</button></div></div>
        <div className="sc reveal" style={d(80)}><span className="mono">02 · Data</span><h3>CSV bundle</h3><p>Five CSVs and a README in one .zip: KPIs, branches, segments, cohorts and the at-risk list.</p><div className="row"><button className="btn solid" id="xZip" onClick={() => save(`streakforge-data-${slug()}.zip`, zip(files(data)), toast)}>Download .zip</button><button className="btn" id="cCsv" onClick={() => copy(files(data)['kpi_summary.csv'], toast, 'KPI CSV copied')}>Copy KPI CSV</button></div></div>
        <div className="sc reveal" style={d(160)}><span className="mono">03 · Print</span><h3>One-page PDF</h3><p>Opens your browser&apos;s print dialog on a clean executive one-pager. Choose “Save as PDF”.</p><div className="row"><button className="btn solid" id="xPdf" onClick={() => printReport(data, m, asof, toast)}>Print or save PDF</button></div></div>
        <div className="sc reveal" style={d(240)}><span className="mono">04 · Email</span><h3>Send a summary</h3><p>Emailing a summary straight from this page is under development. Until it ships, use the Markdown brief or the CSV bundle.</p><div className="row"><span className="flag warn">Under development</span><button className="btn" disabled aria-disabled="true" style={{ opacity: 0.45, cursor: 'not-allowed' }}>Send by email</button></div></div>
      </div>
      <div className="preview" id="pv" tabIndex={0} aria-label="Brief preview">{md}</div>
    </>
  );
}
