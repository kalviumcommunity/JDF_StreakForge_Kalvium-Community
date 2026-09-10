# StreakForge
 
**Fitness Engagement & Retention Insight Platform**
 
### 🔗 **[Launch the live dashboard →](https://streakforge-fitness-engagement-retention-insight-platform.streamlit.app/)**
 
An end-to-end data analytics pipeline and deployed interactive dashboard that identifies which engagement behaviours actually influence long-term member retention for an Indian gym chain and its companion fitness app.
 
**Stack:** Python 3.11 · pandas · NumPy · SciPy · Plotly · Streamlit
 
> **Not a churn prediction model.** StreakForge is deliberately an *insight-generation* platform — the value is in a defensible, fully documented analytical chain from raw messy CSVs to a stakeholder-ready narrative, not in a model score.
 
---
 
## Table of Contents
 
1. [Live App](#1-live-app)
2. [Problem Statement](#2-problem-statement)
3. [Headline Findings](#3-headline-findings)
4. [What Gets Committed](#4-what-gets-committed)
5. [Repository Structure](#5-repository-structure)
6. [Data Sources](#6-data-sources)
7. [Analytical Pipeline](#7-analytical-pipeline)
8. [Engineering Principles](#8-engineering-principles)
9. [Core KPIs](#9-core-kpis)
10. [Documentation Index](#10-documentation-index)
11. [Known Limitations](#11-known-limitations)
---
 
## 1. Live App
 
**→ https://streakforge-fitness-engagement-retention-insight-platform.streamlit.app/**
 
A six-page read/display dashboard over pre-computed CSVs. **No pipeline runs at request time** — every KPI, segment, and risk score is computed by notebooks 01–06 and persisted before deployment, so the app is fast, deterministic, and cheap to host.
 
| Page | Contents |
|---|---|
| **Overview** | Headline KPIs, data-health panel, RFM segment mix donut, weekly engagement sparkline |
| **KPI Dashboard** | Full 15-KPI card grid with category grouping and `context_note` caveats |
| **Insights & Narrative** | The five insights, filterable by **stakeholder audience** |
| **At-Risk & Branch Risk** | The 12 flagged members, the 40-branch risk summary, signal-mix breakdown |
| **Activation Deep-Dive** | Funnel drop-off, cohort trend, segment comparison |
| **Share & Export** | Markdown report, CSV ZIP bundle, optional PDF, SMTP email delivery |
 
**Runtime behaviour built for hosting:**
 
- **`st.cache_data` loaders with mtime-aware invalidation** — drop in regenerated CSVs and the cache clears itself, no manual "Clear cache"
- **Per-page error boundaries** so one bad page can't take down the app
- **Health checks** validating file presence and row counts against expected processed CSVs, surfaced in the Overview panel
- **Graceful degradation** — the PDF export path is optional (`fpdf2`); Markdown and CSV export never depend on it, and the app runs fine if SMTP secrets are absent
- **Pre-flight page** at `?page=deploy_check`, cross-checking `deliverables_manifest.csv` against what's actually on disk
---
 
## 2. Problem Statement
 
A fitness application stores **workout completion logs, streak history, and subscription renewals**, but product teams cannot identify which engagement behaviours actually influence long-term retention. The data lives in five independently sourced systems with no shared grain, inconsistent formats, and no single analytical table.
 
**Objective:** consolidate those five sources into one validated analytical fact table, enrich it with retention-relevant derived features, and surface the retention story through EDA, KPIs, anomaly detection, root-cause investigation, and a deployed interactive dashboard.
 
**In scope:** profiling, cleaning, merging, feature engineering, EDA, KPI design, anomaly/risk detection, root-cause analysis, visual storytelling, Streamlit dashboard with filters and export.
 
**Out of scope:** predictive/ML churn modelling, real-time pipelines, production authentication or multi-tenancy.
 
---
 
## 3. Headline Findings
 
| # | Insight | Audience | Confidence |
|---|---|---|---|
| **INS-01** | **94% churn is largely a measurement artefact, not a business crisis.** The pipeline's fixed `AS_OF_DATE` (2026-08-14) sits ~10 months past the dataset's last real event (2025-10-05). Re-anchored, churn is **84.0%**. | Leadership / Finance | High |
| **INS-02** | **Activation, not renewal, is where members are lost.** Only **18.8%** of members log any activity within 7 days of joining — an **81.2% drop-off** at a single funnel stage, the largest of any step. No channel or demographic segment explains it (all Cramér's V < 0.1). | Product / Growth | Medium-High |
| **INS-03** | **Activation is quietly improving.** Monthly cohort activation rose from **~14.6%** (late 2024) to **~36.6%** (Sep 2025) — the opposite of what the headline drop-off implies in isolation. | Leadership / Product | Medium |
| **INS-04** | **This is a platform-wide problem, not a branch-operations one.** **0 of 40 branches** are statistical churn outliers, and none compound a churn anomaly with bottom-quartile activation. | Operations | Medium |
| **INS-05** | **A small, well-defined "paid once, never engaged" cohort is ready for outreach.** **12 currently-active members** trigger nearly all composite risk signals — mostly single-event members paying **₹48K–₹102K per logged session**. | Customer Success | High |
 
### The AS_OF_DATE duality — read this before quoting any number
 
The pipeline constant `AS_OF_DATE = 2026-08-14` is held fixed for reproducibility, but the **data-realistic boundary** is `DATA_BOUNDARY_DATE = 2025-10-05`. This inflates headline churn from **84.0% → 94.0%**.
 
Both figures are computed, labelled, and reported **side by side** at every layer — `kpi_summary.csv` (`kpi_01` vs `kpi_15`), the KPI card `context_note` field, the executive one-pager, and every relevant page and export in the live app. **The headline 94.0% should never be quoted to leadership without its 84.0% counterpart.**
 
---
 
## 4. What Gets Committed
 
The app reads **nine files and nothing else**. Everything the notebooks produce upstream of those is reproducible and stays out of the repo.
 
### Required in the repo (the app will not start without these)
 
| Path | Rows | Read by |
|---|---|---|
| `data/processed/member_behaviour_summary.csv` | 16,956 × 33 | Filters, Overview, segment mix |
| `data/processed/kpi_summary.csv` | 15 | KPI Dashboard, Overview |
| `data/processed/at_risk_members.csv` | 12 | At-Risk page |
| `data/processed/branch_risk_summary.csv` | 40 | Branch Risk page |
| `data/processed/activation_segment_comparison.csv` | 23 | Activation Deep-Dive |
| `data/processed/activation_cohort_trend.csv` | 57 | Activation Deep-Dive |
| `data/processed/insight_narrative.csv` | 5 | Insights & Narrative |
| `data/processed/insights_payload.json` | — | Insights (falls back to CSVs if absent) |
| `reports/insight_summary.md` | 75 lines | Insights, Share & Export |
 
Also commit `data/processed/kpi_cards_spec.csv` and `data/processed/deliverables_manifest.csv` — the card spec carries the AS_OF_DATE `context_note`, and the manifest powers the `?page=deploy_check` pre-flight.
 
Total committed data footprint is a **few megabytes**.
 
## 5. Repository Structure
 
```
StreakForge/
├── data/
│   ├── raw/                          # acquired datasets, untouched      (git-ignored)
│   ├── interim/                      # cleaned per-source + validation   (git-ignored)
│   ├── processed/                    # KPI/insight tables                (COMMITTED)
│   └── external/                     # schema references
├── notebooks/
│   ├── 01_data_profiling_and_cleaning.ipynb        # PR1–PR5
│   ├── 02_merging_and_validation.ipynb             # PR6
│   ├── 03_feature_engineering.ipynb                # PR7
│   ├── 04_eda_and_behavioural_analysis.ipynb       # PR8–PR10
│   ├── 05_kpi_and_insight_generation.ipynb         # PR11–PR12
│   └── 06_visualisation_and_storytelling.ipynb     # PR13–PR16
├── src/
│   ├── data_pipeline.py
│   ├── insights.py                   # KPI + insight logic
│   └── utils.py
├── streamlit_app/
│   ├── app.py                        # entry point + router + error boundaries
│   ├── components/
│   │   ├── data_loader.py            # cached, mtime-aware CSV/JSON loaders
│   │   ├── theme.py                  # brand palette + light/dark toggle
│   │   ├── sidebar.py                # navigation + filter/share callbacks
│   │   ├── filters.py                # session-state-backed cascading filters
│   │   ├── sharing.py                # Markdown / CSV-ZIP / PDF / SMTP export
│   │   ├── health.py                 # file-presence + row-count checks
│   │   └── state.py                  # session bootstrapping
│   ├── pages_content/
│   │   ├── overview.py
│   │   ├── kpi_dashboard.py
│   │   ├── insights.py
│   │   ├── risk.py
│   │   ├── activation.py
│   │   ├── share.py
│   │   └── deploy_check.py           # internal pre-flight (?page=deploy_check)
│   └── assets/
├── reports/
│   ├── figures/                      # PR8–PR12 static PNGs
│   │   └── interactive/              # PR13–PR15 standalone Plotly HTML
│   ├── insight_summary.md            # auto-generated                    (COMMITTED)
│   └── root_cause_investigation_log.csv
├── docs/
│   ├── PRD.md
│   ├── data_dictionary.md
│   └── daily_log/                    # one entry per PR day
├── .streamlit/
│   ├── config.toml
│   └── secrets_template.toml         # secrets.toml itself is git-ignored
├── requirements.txt
├── runtime.txt
└── README.md
```
 
---
 
## 6. Data Sources
 
Five synthetic-but-domain-grounded source datasets, generated to reflect **Indian gym-industry realities** (city-tier pricing, festival/monsoon seasonality, corporate tie-ups, PT combos). Data quality messiness is **structural and intentional** — mixed date formats, duplicate city spellings, grace-period negatives, sparse structural nulls — and is deliberately left **unflagged in the raw files**.
 
| Dataset | Rows | Grain |
|---|---|---|
| `members_master.csv` | 17,500 | One row per member |
| `subscription_renewal_records.csv` | ~45,764 | One row per billing/renewal cycle |
| `streak_history_episodes.csv` | ~40,202 | One row per streak **episode** (not per day) |
| `gym_checkin_workout_logs.csv` | 108,744 | One row per physical check-in |
| `app_engagement_events.csv` | 97,988 | One row per digital app event |
 
The two event sources are **unioned** into a single `engagement_events` fact table (**206,732 rows**), then enriched via **static (`m:1`) and as-of range joins** against members, subscriptions, and streaks.
 
**Final analytical tables:**
 
| Table | Shape | Grain | Shipped? |
|---|---|---|---|
| `streakforge_merged.csv` | 206,732 × 60 | Engagement event | No |
| `streakforge_features.csv` | 206,732 × 80 | Event + 20 derived features | No |
| `member_behaviour_summary.csv` | 16,956 × 33 | **Member** (RFM + segment) | **Yes** |
 
---
 
## 7. Analytical Pipeline
 
Delivered as **21 PRs across 25 days**, grouped into five phases. Each notebook opens with its purpose and explicit inputs/outputs, and each has a companion markdown summary generated from **actually executed outputs**.
 
### Phase 1 — Data Preparation (PR1–PR6)
 
| Notebook | What it does |
|---|---|
| `01_data_profiling_and_cleaning` | Profiles all five sources (dtype, nulls, cardinality, samples), runs exact-duplicate and referential-integrity checks, then cleans: **business-meaning-aware imputation** (not blanket fills), dtype enforcement, deduplication, string normalisation (`Bangalore`/`Bengaluru`, `Gurgaon`/`Gurugram` → 81 raw city values collapse to **29 real cities**), multi-format date parsing, statistical outlier detection, and a business-rule validation log. |
| `02_merging_and_validation` | Unions the two event sources onto a common spine — source-specific columns preserved as **nullable extensions** rather than dropped — adds surrogate key `engagement_event_id`, then enriches via `validate="m:1"` static joins and `pd.merge_asof()` range joins. **11 logged join checks**, all row-conserving. Surfaced a real defect PR3 missed: **10 rows with duplicated `source_event_id`**. |
 
### Phase 2 — Feature Engineering & EDA (PR7–PR10)
 
| Notebook | What it does |
|---|---|
| `03_feature_engineering` | **20 derived columns.** Fully vectorised — no per-row `.apply()`. Sequential per-member features (inter-session gaps, trailing-window counts) use **`np.searchsorted` binary search** on sorted int64-nanosecond arrays — O(n log n) instead of nested loops. Member-level truth (churn, spend, streak recovery) is computed off the **un-joined source tables**, since the as-of joined event view skews toward Lapsed/Grace states. |
| `04_eda_and_behavioural_analysis` | Distribution and correlation analysis, GroupBy segment cuts, cross-tabs, time-series/rolling trends, **RFM-style scoring → 4 behavioural segments**, and funnel drop-off analysis. Produces the member-grain `member_behaviour_summary.csv` the app reads. |
 
### Phase 3 — KPI & Insight Generation (PR11–PR12)
 
| Notebook | What it does |
|---|---|
| `05_kpi_and_insight_generation` | **15 KPIs** across 5 categories via a reusable `add_kpi()` helper (shaped for lift-and-shift into `src/insights.py`). Anomaly detection over a **249-week** engagement series and **40 branches**. Composite risk scoring → **12 at-risk members**. A structured **4-row root-cause investigation log** (question → hypothesis → evidence → verdict → confidence → action). |
 
### Phase 4 — Visualisation & Storytelling (PR13–PR16)
 
| Notebook | What it does |
|---|---|
| `06_visualisation_and_storytelling` | Establishes a **semantic brand palette** (green = retention, red/orange = risk) and a reusable `apply_streakforge_theme()` house style where every chart title carries the *business takeaway*, not the axis label. **7 standalone interactive Plotly HTML charts**, a KPI card grid, an executive one-pager, the 5-insight narrative, `insights_payload.json`, a **33-row deliverables manifest**, and a programmatically generated `insight_summary.md`. |
 
### Phase 5 — Streamlit App (PR17–PR21)
 
App structure and navigation (PR17) → cascading session-state filters (PR18) → sharing and email export (PR19) → caching, health checks, error boundaries, theme toggle (PR20) → configuration and pre-flight page (PR21). See [Section 1](#1-live-app).
 
---
 
## 8. Engineering Principles
 
These are **non-negotiable** and enforced consistently from notebook 01 through to the app:
 
- **Flag, don't silently fix.** Data quality issues are documented and annotated, never quietly corrected. A negative `days_before_expiry_renewed` is a *grace-period signal*, not an error; 96,099 null `trainer_id` values mean *self-guided sessions*, not missing data.
- **AS_OF_DATE sensitivity.** The fixed pipeline constant and the data-realistic boundary are always distinguished, and both figures reported — including in the UI.
- **CSV-only persistence.** No parquet, pickle, or binary formats at any stage. PDF/email exports are *artefacts*, never pipeline state.
- **The Streamlit app is a read/display layer only.** All KPI and segment logic is pre-computed by the notebooks; nothing is re-derived at request time.
- **Grain discipline.** Aggregations apply `drop_duplicates(<business_key>)` before any grouping, and **member-grain is preferred over event-grain** so high-activity members aren't over-weighted.
- **Fresh load per PR.** No in-memory state carried between sections; every PR is independently loadable and re-runnable.
- **Documentation matches implementation.** Markdown summaries are written from real executed outputs, never anticipated values from draft code.
- **Corrections flow upstream.** `insight_summary.md` is auto-generated from `kpi_cards_spec.csv` and `insight_narrative.csv` — fix the CSVs and regenerate, never hand-edit the markdown.
---
 
## 9. Core KPIs
 
_Generated by `06_visualisation_and_storytelling.ipynb` — AS_OF_DATE 2026-08-14_
 
| KPI | Category | Value |
|---|---|---|
| Overall Churn Rate | Retention | **94.0%** ⚠️ *see duality note* |
| Churn Rate (data-realistic as-of) | Retention | **84.0%** ✅ *operationally meaningful* |
| Overall Retention Rate | Retention | 6.0% |
| Active Members | Retention | 1,011 |
| **7-Day Activation Rate** | Acquisition & Activation | **18.8%** |
| Renewal Follow-Through Rate | Acquisition & Activation | 42.3% |
| Median Revenue per Member | Revenue | ₹8,970 |
| Mean Revenue per Member | Revenue | ₹18,711 |
| Discount Utilisation Rate | Revenue | 30.3% |
| Corporate Tie-Up Mix | Revenue | 20.6% |
| Median Plan-to-Engagement Ratio | Revenue | ₹2,520/session |
| Avg Weekly Session Rate | Engagement | 0.30/wk |
| Avg Session Consistency Score | Engagement | 0.77 (CV) |
| Avg Streak Length | Product / Streak Health | 36.0 days |
| Streak-Break Recovery Rate | Product / Streak Health | 14.8% |
 
**Medians are preferred over means** for right-skewed spend metrics, per PR8's distribution flags.
 
---
 
## 10. Documentation Index
 
| File | Covers |
|---|---|
| `docs/PRD.md` | Full product requirement document — scope, data spec, 25-day execution plan |
| `docs/data_dictionary.md` | Column-level specification, updated whenever a column is added, renamed, or derived |
| `data_profiling_and_cleaning.md` | PR1–PR5 — profiling findings and cleaning decisions |
| `merging_and_validation.md` | PR6 — union strategy, join validation log |
| `feature_engineering.md` | PR7 — all 20 derived columns and the vectorisation approach |
| `eda_and_behavioural_analysis.md` | PR8–PR10 — distributions, segments, RFM, funnel |
| `kpi_and_insight_generation.md` | PR11–PR12 — KPI definitions, anomalies, root-cause log |
| `visualisation_and_storytelling.md` | PR13–PR16 — chart design system, narrative, exports |
| `reports/insight_summary.md` | Auto-generated KPI + insight summary (the executive read) |
| `streakforge_dataset_specifications.md` | Source dataset generation specification |
 
Every summary document follows the same structure: **inputs/outputs at top → per-PR sections → tables of real results → Key Findings Carried Forward → Open Items Flagged for Downstream Work.**
 
---
 
## 11. Known Limitations
 
- **Synthetic data.** All five sources are generated, not real. Patterns are domain-grounded (Indian city tiers, monsoon/festival seasonality, referential integrity) but the conclusions are illustrative of the *method*, not of any real gym chain.
- **The live app is a static snapshot.** It reflects the last notebook run committed to the repo. There is no scheduled refresh, no database, and no ingestion at request time — by design.
- **The AS_OF_DATE gap is structural.** It is surfaced and corrected for, not removed. Any future re-run against fresher data should revisit both constants.
- **No predictive modelling.** Deliberately out of scope per the PRD.
- **No branch-level explanation for churn was found.** 0/40 branches flagged — a genuine negative result that redirects investigation toward product/onboarding rather than operations.
- **Segmentation does not separate churn.** Churn sits at ~93–95% across every segment cut tested, and even the highest-value RFM segment ("Champions") churns heavily — so behavioural segmentation is **not** a usable churn proxy at this aggregation level.
- **`source_event_id` is not unique.** Use `engagement_event_id`, the surrogate key added in PR6, for any downstream join.
- **No authentication.** The app is public. It contains no real PII, but do not extend it with real member data without adding an auth layer.
---
 
**Author:** Diya Shrivastava · B.Tech CSE (Software Product Engineering), Lovely Professional University
 
