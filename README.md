# JDF_StreakForge_Kalvium-Community

**StreakForge — Fitness Retention Intelligence**

An end-to-end data product for a multi-branch Indian gym chain. It ingests raw
member, check-in, subscription, streak, and app-engagement data, cleans and
validates it, computes KPIs, renders an interactive dashboard, raises threshold
alerts, generates shareable reports, and emails them — with an automated weekly
pipeline and a CI schema-validation gate that blocks bad changes from reaching
production.

Built for the **operations and retention teams** who need to answer one question:
*why do members stop showing up, and who is about to?*

---

## 📦 Overview

StreakForge turns five raw CSV extracts into a self-documenting, maintainable
analytics product:

| Capability | What it does | Where |
|---|---|---|
| Dashboard | KPIs, trends, filters, member explorer | `app.py` (Streamlit) |
| Upload & Sync | Upload a CSV/JSON, profile it, sync it into the data lake | `upload_utils.py` + `app.py` |
| Alerts | Threshold checks rendered as warnings/errors | `alert_config.py` |
| Reports | Text / CSV / HTML summaries of KPIs and findings | `report_generator.py` |
| Email | SMTP delivery of reports and failure alerts | `email_sender.py`, `notify_failure.py` |
| Pipeline | Ingest → clean → aggregate → output, scheduled weekly | `pipeline.py`, `.github/workflows/pipeline.yml` |
| Validation | Schema + quality gate on every push/PR, blocks merge on failure | `validate_data.py`, `schema.json`, `.github/workflows/validate.yml` |

**The product works because every stage is documented here.** If this README and
the code disagree, the README wins — and a PR fixing either is welcome.

---

## 📁 Dataset Description

### Raw sources (`data/raw/`)

| File | Rows | Contents |
|---|---|---|
| `members_master.csv` | 17,500 | Demographics, membership type, branch, goals |
| `gym_checkin_workout_logs.csv` | 108,744 | Check-in/checkout timestamps, workout type, duration |
| `streak_history_episodes.csv` | 40,202 | Streak episodes with length and break reason |
| `subscription_renewal_records.csv` | 45,764 | Billing cycles, amounts, renewal outcomes |
| `app_engagement_events.csv` | 97,988 | In-app events, platform, session duration |

The extract ends **2 Oct 2025**. Every "last 30 days" computation in the code is
anchored to that date via `data_utils.as_of()` — never to the real calendar.

### Processed outputs

| File | Rows × Columns | Purpose |
|---|---|---|
| `data/processed/member_behaviour_summary.csv` | 16,956 × 34 | One row per member with derived behaviour/RFM features — the schema contract target |
| `data/processed/streakforge_merged.csv` | 206,732 × 62 | Fully joined event-level dataset |
| `data/processed/streakforge_features.csv` | — | Git LFS pointer; regenerated feature matrix |
| `data/interim/*_clean.csv` | — | Per-source cleaned extracts |
| `output/cleaned.csv`, `output/aggregated.csv` | — | Pipeline artifacts written by `pipeline.py` |

---

## 🚀 Getting Started

Four commands, from zero to running dashboard:

```bash
# 1. Clone and enter the repo
git clone https://github.com/kalviumcommunity/JDF_StreakForge_Kalvium-Community.git && cd JDF_StreakForge_Kalvium-Community

# 2. Create and activate a virtual environment
python3 -m venv .venv && source .venv/bin/activate     # Windows: python -m venv .venv  then  .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the dashboard
streamlit run app.py
```

Opens on <http://localhost:8501>.

**Optional — enable email reports** (the app runs fine without it; email
features warn and skip when credentials are missing):

```bash
cp .env.example .env      # then edit .env with your SMTP credentials
```

### Requirements

```
streamlit==1.50.0
pandas==2.3.3
plotly==5.18.0
python-dotenv==1.0.0
```

### Tests

```bash
python -m pip install pytest
python -m pytest tests -q          # expect: 46 passed
```

> **Using Conda?** Invoke tools as `python -m <tool>` rather than the bare
> command. With a Conda base environment active, bare `pytest` resolves to
> Conda's interpreter and collection fails on `ModuleNotFoundError`.

---

## 🧭 Usage Guide

### Dashboard sections

| Section | Question it answers | Contents |
|---|---|---|
| **Overview** | Is the business healthy right now? | Five KPI cards, monthly activity trend, streak-break mix |
| **Trends** | Which direction are we moving? | Monthly actives, visits vs uniques, retention rate, retention by membership type |
| **Data Explorer** | Show me the members behind the number | Filters (city, goal, membership), advanced filters, member table, CSV export |
| **Upload & Sync** | Is this new file safe to use? | Upload → validate → confirm sync → generate & email report |

### Upload & Sync (4 steps)

1. **Select a file** — choose a `.csv` or `.json`.
2. **Validate** — `upload_utils.py` detects the format, parses it, and shows
   overall null %, a column summary, and quality flags before anything is saved.
3. **Confirm** — sync the file into `data/raw/`.
4. **Generate & Share Report** — build a text, CSV, or HTML report and email it
   via `report_generator.py` + `email_sender.py`.

### Alerts

`alert_config.py` defines threshold rules rendered at the top of the dashboard:

| Rule | Threshold | Direction | Severity | Message |
|---|---|---|---|---|
| `churn_rate` | 7.0% | above | critical | "Churn exceeds safe limit. Investigate retention." |
| `null_percentage` | 5.0% | above | warning | "Null percentage too high. Check data pipeline." |

### Running the pipeline manually

```bash
python pipeline.py --input data/raw/test.csv --output output
# or via config file:  python pipeline.py --config pipeline_config.json
```

Logs each stage with a timestamp and writes `output/cleaned.csv` and
`output/aggregated.csv`.

---

## 🔧 Pipeline Architecture

### Data flow diagram

```
  CSV/JSON upload ──► Upload & Sync ──► data/raw/*.csv
  (manual, in-app)   validate+profile          │
                                               │
                         GitHub Actions (Mon 06:00 UTC, workflow_dispatch)
                                               │
                                     pipeline.py: ingest
                                               │
                                     pipeline.py: clean
                                               │
                                     pipeline.py: aggregate
                                               │
                                     pipeline.py: output
                                               │
                                     output/cleaned.csv
                                     output/aggregated.csv  ──► committed back to repo
                                               │
              ┌────────────────────────────────┼───────────────────────────────┐
              ▼                                ▼                               ▼
   Streamlit dashboard                CI validation gate               Reports & email
   KPIs · charts · filters           validate_data.py                 report_generator.py
   alerts · data explorer            + schema.json                    email_sender.py
              │                                │                               │
              ▼                                ▼                               ▼
   business decisions               PASS → merge allowed             text / CSV / HTML
                                    FAIL → merge blocked +           delivered over SMTP
                                           notify_failure.py email
```

### Stage-by-stage

| Stage | Trigger | Input | Transformations | Output / destination |
|---|---|---|---|---|
| **Upload & Sync** | Manual, in-app | `.csv`/`.json` bytes | format detection, parse, null %, column profile, quality flags | `data/raw/` |
| **Ingest** | Weekly schedule or manual | CSV/JSON path | `pd.read_csv`/`read_json`, existence check | DataFrame |
| **Clean** | `pipeline.py clean()` | raw DataFrame | drop null key rows, coerce numerics, drop non-positive amounts, schema-aware cases (`customer_id+amount`, `member_id+amount_paid_inr`, generic) | cleaned DataFrame |
| **Aggregate** | `pipeline.py aggregate()` | cleaned DataFrame | group by segment/membership type → sum revenue + count orders | aggregated DataFrame |
| **Output** | `pipeline.py output()` | both DataFrames | write CSVs | `output/cleaned.csv`, `output/aggregated.csv` |
| **Validation gate** | Every push / PR | `member_behaviour_summary.csv` | 6 schema & quality checks | `validation_report.json` + exit code |
| **Dashboard** | `streamlit run app.py` | `data/raw/*.csv` | cached loaders, KPI math, monthly aggregates, member table | interactive UI |
| **Alerts** | Dashboard render | KPIs | compare against thresholds | `st.error` / `st.warning` |
| **Reports & email** | Dashboard Step 4 / manual | KPIs + members | format text/CSV/HTML | SMTP email |

---

## 📐 Derived Features

Every engineered column in `data/processed/member_behaviour_summary.csv`, with
type, source, description, and a real example value. Raw columns (carried
through from `members_master.csv`) are marked **Raw** so downstream consumers
know exactly which fields the pipeline computes.

| Column | Type | Source | Description | Example |
|---|---|---|---|---|
| `member_id` | string | Raw | Unique member identifier (primary key) | `MBR-005512` |
| `age` | float | Derived | Age computed from `date_of_birth` (3.1% null) | `32.9` |
| `gender` | string | Raw | Self-reported gender | `Female` |
| `city` | string | Raw | Home city | `Pune` |
| `city_tier` | string | Derived | Tier1/2/3 mapped from city | `Tier1` |
| `state` | string | Raw | Home state | `Maharashtra` |
| `occupation` | string | Raw | Occupation category | `Salaried-IT` |
| `marital_status` | string | Raw | Marital status | `Married` |
| `membership_type` | string | Raw | Plan tier | `Premium` |
| `referral_source` | string | Raw | Acquisition channel | `Walk-in` |
| `preferred_workout_time` | string | Raw | Preferred time slot | `Evening (6-9pm)` |
| `has_personal_trainer` | bool | Raw | Personal-trainer flag | `True` |
| `primary_goal` | string | Raw | Fitness goal | `Weight Loss` |
| `signup_channel` | string | Raw | Signup channel | `App` |
| `join_date` | datetime | Raw | Membership join date (mixed formats) | `2021-01-02` |
| `is_churned` | bool | Derived | `True` when last renewal outcome is Lapsed or Auto-Renew Failed | `True` |
| `plan_to_engagement_ratio` | float | Derived | Ratio of plan value to observed engagement | `931.5` |
| `engagement_trend_slope` | float | Derived | Slope of engagement over time (+ rising, − falling) | `0.06` |
| `total_amount_paid_inr` | int | Derived | Total INR paid across renewals | `18630` |
| `avg_discount_pct` | float | Derived | Average discount % across renewals | `0.0` |
| `avg_price_per_day_inr` | float | Derived | Effective price paid per day | `204.73` |
| `n_renewals` | int | Derived | Number of subscription renewals | `1` |
| `avg_days_before_expiry_renewed` | float | Derived | Avg days before cycle expiry the renewal happened | `14.0` |
| `avg_streak_length_days` | float | Derived | Average streak episode length | `75.5` |
| `max_streak_length_days` | float | Derived | Longest streak episode | `137.0` |
| `n_streaks` | float | Derived | Number of streak episodes | `2.0` |
| `total_gym_sessions` | float | Derived | Total check-in sessions | `20.0` |
| `avg_sessions_per_week_rolling_4wk` | float | Derived | Weekly visit frequency, 4-week rolling | `0.39` |
| `session_consistency_score` | float | Derived | Regularity of the visit cadence | `1.41` |
| `tenure_days_at_last_event` | int | Derived | Days between join and last event | `1700` |
| `recency_days` | int | Derived | Days since last event (as of extract end) | `349` |
| `frequency_total_events` | int | Derived | Total engagement events (RFM F) | `33` |
| `monetary_total_paid` | int | Derived | Total spend (RFM M) | `18630` |
| `behavioural_segment` | string | Derived | Engagement segment from behaviour/RFM | `Champions` |

### Computed KPIs (`data_utils.get_kpis()`)

| KPI | Formula | As of 2 Oct 2025 |
|---|---|---|
| Active Members | unique `member_id` in check-ins, last 30 days | 3,355 |
| Retention Rate | retained ÷ resolved billing cycles, last 30 days | 83.3% |
| Churn Rate | 100 − retention | 16.7% |
| Median Streak | median `streak_length_days`, last 30 days | 10 days |
| Total Members | `len(members_master)` | 17,500 |

**Retention convention:** `Renewed`, `Upgraded`, and `Downgraded` all count as
*retained*; only `Lapsed` and `Auto-Renew Failed` count as churn. An upgrade is
the best possible outcome — filtering `status == "Renewed"` understates retention
by ~13 points.

---

## ⚠️ Known Limitations

- **Static snapshot, not real-time.** The extract ends 2 Oct 2025 and the
  dashboard reflects that snapshot. "Last 30 days" windows are anchored to
  `as_of()` (2 Oct 2025), not today; maximum staleness is the age of the
  extract.
- **Weekly refresh only.** The scheduled pipeline runs Monday 06:00 UTC and
  refreshes pipeline artifacts — it does not stream live data.
- **Retention convention is a choice.** Upgrades/downgrades count as retained.
  If a different convention is required, change `RETAINED`/`CHURNED` in
  `data_utils.py` — and update any KPIs that depend on it.
- **`break_reason == "Unknown"` is excluded** from streak-break charts (~39% of
  rows). It means "unresolved/ongoing", not a real cause.
- **Revenue excludes refunds** and any post-renewal adjustments beyond
  `renewal_status`; net revenue after refunds is not computed.
- **Alert thresholds are static** (`churn > 7%`, `null > 5%`). No seasonal or
  historical-variance adjustment.
- **Email requires SMTP configuration.** Without `.env` (local) or repository
  secrets (CI), email features log a warning and skip — they are silently
  disabled, never failing the run.
- **Schema changes must update the contract.** `schema.json` is the source of
  truth for downstream consumers. Rename/remove/change a column and the CI
  validation gate fails until `schema.json` is updated in the same PR.
- **Pipeline assumes known schemas.** It handles `customer_id+amount`,
  `member_id+amount_paid_inr`, and a generic fallback; exotic schemas degrade to
  generic grouping.
- **City/tier and category allow-lists are static.** A new city, membership
  type, or segment value fails validation until added to `schema.json`.
- **`streakforge_features.csv` is LFS-backed** and gitignored; cloning without
  Git LFS leaves it as a pointer.
- **`join_date` mixes three formats.** Parsed loosely
  (`dayfirst=True, format="mixed"`); unparseable values become `NaT`.

---

## 🛡️ Automated Data Validation (CI Gate)

Every push to `main`, `develop`, or `feature/*` — and every PR into `main` —
runs `.github/workflows/validate.yml`, which executes `validate_data.py` against
`data/processed/member_behaviour_summary.csv`. **If any check fails, the script
exits `1`, the job fails, and the merge is blocked** (when branch protection is
enabled).

### What schema drift is

Schema drift is when the *shape* of the data changes without warning: a column is
renamed (`member_id` → `mem_id`), removed, added, or changes type (`int` →
`string`). Validating on every push catches it in the PR of the person who
introduced it — not Monday morning when the dashboard errors.

### Checks (each logs `PASS:` or `ERROR:`)

| # | Check | What it catches |
|---|---|---|
| 1 | Required columns | Missing columns, unexpected new columns, and a "possible rename" hint |
| 2 | Data types | int/float/string/bool/datetime mismatches |
| 3 | Minimum row count | Truncated or empty output |
| 4 | Null quality | Fully-null columns and per-column `max_null_pct` breaches |
| 5 | Primary-key uniqueness | Duplicate `member_id` values |
| 6 | Domain / range | Values outside `allowed`, `min`, or `max` |

```bash
python validate_data.py data/processed/member_behaviour_summary.csv \
  --schema schema.json --report validation_report.json
# echo $?  ->  0 = PASS, 1 = FAIL
```

### Blocking merges (branch protection)

1. Repo → **Settings → Branches → Add branch protection rule**.
2. Branch name pattern: `main`.
3. Tick **Require status checks to pass before merging**.
4. Add **Data Validation** (it must have run once to appear).
5. Save.

### Failure notifications

On failure (`if: failure()`), `notify_failure.py` reads `validation_report.json`
and emails the failed checks over SMTP. Secrets: `SENDER_EMAIL`,
`SENDER_PASSWORD`, `SMTP_SERVER`, `SMTP_PORT`, `NOTIFY_RECIPIENTS`. Missing
secrets → warning + exit 0 (never masks the real failure).

---

## 🗂 Repository Structure

```
├── app.py                       # Streamlit dashboard (4 sections)
├── data_utils.py                # Cached loaders, KPIs, aggregates
├── upload_utils.py              # Upload parsing, validation, profiling
├── alert_config.py              # Threshold alert rules + rendering
├── report_generator.py          # Text/CSV/HTML report generation
├── email_sender.py              # SMTP delivery (reports)
├── notify_failure.py            # Self-contained SMTP failure alerter (CI)
├── pipeline.py                  # Ingest → clean → aggregate → output
├── pipeline_config.json         # Default pipeline CLI config
├── validate_data.py             # CI schema/quality gate (exit 1 on failure)
├── schema.json                  # Declarative schema contract
├── requirements.txt             # Pinned dependencies
├── .env.example                 # Template for SMTP credentials (copy to .env)
├── .github/workflows/
│   ├── pipeline.yml             # Weekly scheduled pipeline (Mon 06:00 UTC)
│   └── validate.yml             # Data validation on push/PR (merge gate)
├── tests/
│   ├── test_app_smoke.py        # Headless dashboard checks
│   ├── test_upload.py           # Upload parser/validator checks
│   ├── test_pipeline.py         # Pipeline stage checks
│   └── test_validate_data.py    # 10 validator pass/fail cases
├── data/
│   ├── raw/                     # Source extracts (5 files, ~27 MB)
│   ├── interim/                 # Per-source cleaned extracts
│   └── processed/               # Merged + member behaviour summaries
├── output/                      # Pipeline artifacts (cleaned/aggregated)
├── docs/                        # Project documentation
└── notebooks/                   # EDA and exploration
```

---

## 👥 Team Charter

| Member | Role | Technical Strength |
|---|---|---|
| **Diya Shrivastava** | Project Admin | Python, Pandas, Visualization, SQL |
| **Jannat** | Team Member | NumPy, Data Cleaning, EDA |
| **Furkhan** | Team Member | Streamlit App Development |

**Working agreements:** PRs reviewed same-day · blockers raised in the GChat
space **JDF** · one reporter per standup.

> **Sprint commitment:** keep data clean, validated, and well-documented before
> moving to insights and dashboard development.

---

## 📊 Current Standing

_Last updated: 20 August 2026_

| Workstream | Owner | Status |
|---|---|---|
| Data cleaning, SQL views, visualization | Diya | In progress |
| NumPy, data cleaning, EDA | Jannat | In progress |
| Streamlit app shell (2.51) | Furkhan | ✅ Code complete — PR open for review |

**Dashboard KPIs as of 2 Oct 2025** (latest date the extract covers):

| KPI | Value | Δ vs prior 30 days |
|---|---|---|
| Active Members | 3,355 | +4.4% |
| Retention Rate | 83.3% | −2.5 pts |
| Churn Rate | 16.7% | +2.5 pts |
| Median Streak | 10 days | −11.0 |
| Total Members | 17,500 | — |

---

## ⚠️ Data Gotchas — Read Before Writing Analysis

Real properties of the extract. Each one silently produces wrong-but-plausible
output if missed.

### 1. `renewal_status` has five values, not two

```
Renewed 34,855 | Lapsed 4,523 | Auto-Renew Failed 2,757 | Upgraded 1,840 | Downgraded 1,789
```

An **upgrade is the best possible outcome**. Filtering `status != "Renewed"`
buckets upgrades and downgrades as churn and understates retention by ~13 points
(70.4% vs the true 83.3%).

```python
RETAINED = ("Renewed", "Upgraded", "Downgraded")
CHURNED  = ("Lapsed", "Auto-Renew Failed")
```

### 2. The check-in extract ends 2 Oct 2025 — never anchor windows to `now()`

Any "last 30 days" window computed against the real calendar date matches **zero
rows**. Derive the anchor from the data:

```python
def as_of():
    return load_checkins()["checkin_datetime"].max().normalize()
```

### 3. `join_date` mixes three date formats in one column

`26-01-2000`, `2024/07/27`, and `2023-01-10` all appear. A strict format string
silently drops real members.

```python
pd.to_datetime(df["join_date"], errors="coerce", dayfirst=True, format="mixed")
```

### 4. Unresolved billing cycles must be excluded

Cycles with `billing_cycle_end` after the as-of date have no outcome yet.
Including them reports retention on the future.

### 5. Partial trailing months distort trend charts

The extract's final month holds only a handful of rows, drawing a cliff that
reads as a collapse but is just the export boundary. Drop it before charting.

### 6. `break_reason == "Unknown"` is not a cause

It marks unresolved or ongoing episodes and accounts for ~39% of rows. Excluded
from the break-reason chart, it would otherwise bury the seven actionable
reasons.

---

## 💡 Current Insight

With `Unknown` excluded, the leading reasons streaks break are:

| Reason | Share |
|---|---|
| Motivation Loss | 22.0% |
| Festival/Holiday | 20.6% |
| Work Pressure | 14.3% |
| Monsoon Disruption | 12.6% |
| Travel | 11.6% |
| Illness | 11.5% |
| Injury | 7.5% |

Two of the top four — **Festival/Holiday and Monsoon Disruption, 33% combined** —
are calendar-predictable and addressable with scheduled interventions rather
than generic re-engagement campaigns.
