import type { AsOf, SiteData } from './types';
import type { Metrics } from './metrics';
import { esc, inr, nf, pc, slug } from './format';

type Toast = (m: string) => void;

export function mdBrief(d: SiteData, m: Metrics, asof: AsOf) {
  const ch = asof === 'pipeline' ? `${pc(m.churnPipeline)} (pipeline as-of 2026-08-14)` : `${pc(m.churnData)} (data-realistic as-of 2025-10-05)`;
  return `# StreakForge brief\n\n_Synthetic dataset: ${nf(m.N)} members, 40 branches. Events 2021-01 to 2025-10-05. Generated ${slug()}._\n\n## Headline\n- Churn: ${ch}. Report both figures together: ${pc(m.churnPipeline)} vs ${pc(m.churnData)}.\n- 7-day activation: ${pc(m.nAct / m.N)} (${nf(m.nAct)} of ${nf(m.N)}). ${pc(1 - m.nAct / m.N)} never engage in week one.\n- Median spend per member: ${inr(m.spend)}. Average streak: ${m.streak.toFixed(1)} days.\n\n## Five findings\n${d.insights.map((i) => `${i.id}. ${i.title} (${i.aud}; confidence ${i.conf})\n   Action: ${i.action}`).join('\n')}\n\n## Twelve members to call\n${d.risk.map((r, i) => `${i + 1}. ${r.sample ? 'Sample member (placeholder)' : r.id + ' / ' + r.branch} - silent ${r.recency} days, ${r.events} event(s), ${inr(r.ratio)} per session`).join('\n')}\n`;
}

type Row = Record<string, unknown>;
export function csv(rows: Row[], cols: string[]) {
  const q = (v: unknown) => (v == null ? '' : /[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));
  return [cols.join(','), ...rows.map((r) => cols.map((c) => q(r[c])).join(','))].join('\n') + '\n';
}

export function files(d: SiteData): Record<string, string> {
  return {
    'kpi_summary.csv': csv(d.kpis.map((k) => ({ kpi_id: k.id, kpi_name: k.name, category: k.cat, value: k.value, unit: k.unit, definition: k.defn })), ['kpi_id', 'kpi_name', 'category', 'value', 'unit', 'definition']),
    'branch_risk_summary.csv': csv(d.branches as unknown as Row[], ['gym_branch_id', 'members', 'churn_rate', 'activation_rate', 'avg_sessions_per_week', 'is_churn_outlier']),
    'activation_segment_comparison.csv': csv(d.segments as unknown as Row[], ['segment_col', 'segment_level', 'members', 'activation_rate', 'cramers_v', 'p_value']),
    'activation_cohort_trend.csv': csv(d.cohorts as unknown as Row[], ['join_month', 'members', 'activation_rate']),
    'at_risk_members.csv': csv(d.risk.map((r) => ({ member_id: r.sample ? '' : r.id, gym_branch_id: r.sample ? '' : r.branch, recency_days: r.recency, frequency_total_events: r.events, engagement_trend_slope: r.slope, plan_to_engagement_ratio: r.ratio, risk_high_recency: r.sig[0], risk_low_frequency: r.sig[1], risk_negative_trend: r.sig[2], risk_paying_not_showing: r.sig[3], is_sample_row: r.sample })), ['member_id', 'gym_branch_id', 'recency_days', 'frequency_total_events', 'engagement_trend_slope', 'plan_to_engagement_ratio', 'risk_high_recency', 'risk_low_frequency', 'risk_negative_trend', 'risk_paying_not_showing', 'is_sample_row']),
    'README.txt': `StreakForge data bundle, ${slug()}\nSynthetic data. Pipeline as-of 2026-08-14; last event 2025-10-05.\nRows with is_sample_row=true are placeholders.\n`,
  };
}

/* ---- zip (store method, own CRC-32; no library) ---- */
const CRC = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; }
  return (b: Uint8Array) => { let c = ~0; for (let i = 0; i < b.length; i++) c = t[(c ^ b[i]) & 255] ^ (c >>> 8); return ~c >>> 0; };
})();
export function crc32(b: Uint8Array) { return CRC(b); }

export function zip(fs: Record<string, string>): Blob {
  const enc = new TextEncoder(), parts: BlobPart[] = [], cen: { nm: Uint8Array; crc: number; len: number; off: number }[] = [];
  let off = 0;
  const u16 = (v: number) => [v & 255, (v >> 8) & 255], u32 = (v: number) => [v & 255, (v >> 8) & 255, (v >> 16) & 255, (v >>> 24) & 255];
  for (const [n, t] of Object.entries(fs)) {
    const nm = enc.encode(n), b = enc.encode(t), crc = CRC(b);
    const lh = new Uint8Array([0x50, 0x4b, 3, 4, ...u16(20), ...u16(0x0800), ...u16(0), ...u16(0), ...u16(0x21), ...u32(crc), ...u32(b.length), ...u32(b.length), ...u16(nm.length), ...u16(0)]);
    parts.push(lh as BlobPart, nm as BlobPart, b as BlobPart); cen.push({ nm, crc, len: b.length, off }); off += lh.length + nm.length + b.length;
  }
  let cs = 0; const cparts: BlobPart[] = [];
  cen.forEach((c) => {
    const h = new Uint8Array([0x50, 0x4b, 1, 2, ...u16(20), ...u16(20), ...u16(0x0800), ...u16(0), ...u16(0), ...u16(0x21), ...u32(c.crc), ...u32(c.len), ...u32(c.len), ...u16(c.nm.length), ...u16(0), ...u16(0), ...u16(0), ...u16(0), ...u32(0), ...u32(c.off)]);
    cparts.push(h as BlobPart, c.nm as BlobPart); cs += h.length + c.nm.length;
  });
  const end = new Uint8Array([0x50, 0x4b, 5, 6, 0, 0, 0, 0, ...u16(cen.length), ...u16(cen.length), ...u32(cs), ...u32(off), 0, 0]);
  return new Blob([...parts, ...cparts, end as BlobPart], { type: 'application/zip' });
}

export function save(name: string, blob: Blob, toast: Toast) {
  try {
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    toast('Downloading ' + name + '. If nothing happens, your viewer blocks downloads: use Copy instead.');
  } catch { toast('Download blocked here. Use Copy instead.'); }
}
export async function copy(t: string, toast: Toast, msg?: string) {
  try { await navigator.clipboard.writeText(t); toast(msg || 'Copied to clipboard'); }
  catch {
    const ta = document.createElement('textarea'); ta.value = t; document.body.appendChild(ta); ta.select();
    let ok = false; try { ok = document.execCommand('copy'); } catch { /* ignore */ }
    ta.remove(); toast(ok ? msg || 'Copied to clipboard' : 'Copy was blocked. Select the preview text and copy it manually.');
  }
}

export function printReport(d: SiteData, m: Metrics, asof: AsOf, toast: Toast) {
  const host = document.getElementById('printReport'); if (!host) return;
  host.innerHTML = `<p class="mono">StreakForge · executive one-pager · ${slug()}</p><h1>81 in 100 members never show up in week one</h1><p>Synthetic dataset of ${nf(m.N)} members across 40 branches. Events 2021-01 to 2025-10-05.</p><h2>Headline numbers</h2><div class="pk"><div><b>${asof === 'pipeline' ? pc(m.churnPipeline) : pc(m.churnData)}</b><br>Churn (${asof === 'pipeline' ? 'pipeline' : 'data-realistic'} as-of)</div><div><b>${pc(m.act)}</b><br>7-day activation</div><div><b>${m.streak.toFixed(1)}</b><br>Avg streak, days</div><div><b>${inr(m.spend)}</b><br>Median spend</div></div><h2>Five findings</h2>${d.insights.map((i) => `<p><b>${esc(i.id)} · ${esc(i.title)}.</b> ${esc(i.action)} <i>(${esc(i.aud)}; confidence ${esc(i.conf)})</i></p>`).join('')}<h2>Twelve members to call</h2><table><tr><th>#</th><th>Member</th><th>Branch</th><th>Days silent</th><th>₹ per session</th></tr>${d.risk.map((r, i) => `<tr><td>${i + 1}</td><td>${r.sample ? 'Sample (placeholder)' : esc(r.id)}</td><td>${r.sample ? '—' : esc(r.branch)}</td><td>${r.recency}</td><td>${inr(r.ratio)}</td></tr>`).join('')}</table>`;
  try { window.print(); } catch { toast('Printing is blocked in this viewer. Open the standalone file to save a PDF.'); }
}
