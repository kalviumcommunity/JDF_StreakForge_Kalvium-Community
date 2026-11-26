import type { SiteData } from './types';

/** Every headline figure, derived from the exported JSON (no hard-coded numbers). */
export function metrics(d: SiteData) {
  const kpi = (id: string) => d.kpis.find((k) => k.id === id)!;
  const N = d.funnel[0].members;
  const churnPipeline = kpi('kpi_01').value;
  const churnData = kpi('kpi_15').value;
  const cohortMean = d.cohorts.reduce((a, c) => a + c.activation_rate, 0) / d.cohorts.length;
  return {
    N,
    nAct: d.funnel[1].members,
    nAP: kpi('kpi_03').value,
    nAD: Math.round(N * (1 - churnData)),
    churnPipeline,
    churnData,
    act: kpi('kpi_04').value,
    streak: kpi('kpi_13').value,
    spend: kpi('kpi_06').value,
    cohortMean,
    segCounts: ['Champions', 'Loyal / Engaged', 'At Risk', 'Dormant / Lapsed'].map(
      (n) => d.rfm.find((r) => r[0] === n)![1]
    ),
  };
}
export type Metrics = ReturnType<typeof metrics>;
