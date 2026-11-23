export interface Kpi { id: string; name: string; cat: string; value: number; display: string; unit: string; defn: string; note: string; pair: string | null }
export interface Insight { id: string; title: string; aud: string; conf: string; confN: number; story: string; evidence: string; impact: string; action: string; route: string; anchor: string }
export interface Branch { gym_branch_id: string; members: number; churn_rate: number; activation_rate: number; avg_sessions_per_week: number; is_churn_outlier: boolean }
export interface Cohort { join_month: string; members: number; activation_rate: number }
export interface Segment { segment_col: string; segment_level: string; members: number; activation_rate: number; cramers_v: number; p_value: number }
export interface Risk { id: string; branch: string; recency: number; events: number; slope: number | null; ratio: number; sig: number[]; sample: boolean }
export interface FunnelStep { stage: string; members: number }
export type Rfm = [string, number, string];
export interface SiteData { kpis: Kpi[]; insights: Insight[]; branches: Branch[]; cohorts: Cohort[]; segments: Segment[]; risk: Risk[]; funnel: FunnelStep[]; rfm: Rfm[] }
export type AsOf = 'pipeline' | 'data';
export type Sim = '' | 'loading' | 'empty' | 'error';
