# JDF_StreakForge_Kalvium-Community

**Fitness Retention Intelligence** — a data pipeline and analytics dashboard for a
multi-branch Indian gym chain, built to answer one question: *why do members stop
showing up, and who is about to?*

---

## 👥 Team Charter

### Team Members

| Member | Role | Technical Strength |
|---|---|---|
| **Diya Shrivastava** | Project Admin | Python, Pandas, Visualization, SQL |
| **Jannat** | Team Member | NumPy, Data Cleaning, EDA |
| **Furkhan** | Team Member | Streamlit App Development |

### Working Agreements

- **PR Review:** Pull requests will be reviewed within the same day.
- **Blockers:** Team members will first reach out through the GChat Space created.
- **Standups:** One person will report for the entire team.
- **Primary Team Channel:** GChat space named **JDF**.

### Sprint Commitment

> We commit to building a reliable, data-driven foundation by keeping our data clean,
> validated, and well-documented before moving to insights and dashboard development.

---

## 📊 Current Standing

_Last updated: 20 August 2026_

| Workstream | Owner | Status |
|---|---|---|
| Data cleaning, SQL views, visualization | Diya | In progress |
| NumPy, data cleaning, EDA | Jannat | In progress |
| Streamlit app shell (2.51) | Furkhan | ✅ Code complete — PR open for review |

**Dashboard reports as of 2 Oct 2025** (latest date the extract covers):

| KPI | Value | Δ vs prior 30 days |
|---|---|---|
| Active Members | 3,355 | +4.4% |
| Retention Rate | 83.3% | −2.5 pts |
| Churn Rate | 16.7% | +2.5 pts |
| Median Streak | 10 days | −11.0 |
| Total Members | 17,500 | — |

---

## 🗂 Repository Structure

```
.
├── app.py                     # Streamlit shell: nav, sections, layout
├── data_utils.py              # Cached loaders + KPI and aggregation logic
├── validate_data.py           # CI schema/quality gate (exit 1 on failure)
├── schema.json                # Declarative schema contract for the gate
├── notify_failure.py          # Failure-alert email via email_sender.py
├── requirements.txt           # Pinned dependencies
├── .github/workflows/
│   ├── pipeline.yml           # Weekly scheduled pipeline
│   └── validate.yml           # Data validation on push/PR (merge gate)
├── tests/
│   ├── test_app_smoke.py      # Headless AppTest checks
│   └── test_validate_data.py  # 10 pass/fail cases for the validator
├── data/
│   ├── raw/                   # Source CSV extracts (5 files, ~27 MB)
│   └── processed/             # Cleaned + aggregated outputs (incl. contract target)
├── docs/                      # Project documentation
└── notebooks/                 # EDA and exploration
```

---

## 🚀 Running the Dashboard

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Opens on <http://localhost:8501>.

### Tests

```bash
python -m pip install pytest
python -m pytest tests -q          # expect: 7 passed
```

> **Using Conda?** Always invoke tools as `python -m <tool>` rather than the bare
> command. With a Conda base environment active, bare `pytest` resolves to Conda's
> interpreter — which has no Streamlit installed — and collection fails on
> `ModuleNotFoundError`.

---

---

## 🛡️ Automated Data Validation (CI Gate)

Every push to `main`, `develop`, or a `feature/*` branch (and every PR into `main`)
runs `.github/workflows/validate.yml`, which executes `validate_data.py` against
`data/processed/member_behaviour_summary.csv`. If any check fails, the script exits
`1`, the GitHub Actions job fails, and — with branch protection enabled — the merge
is blocked.

### What schema drift is

Schema drift is when the *shape* of the data changes without warning: a column is
renamed (`member_id` → `mem_id`), removed, added, or changes type (`int` → `string`).
A billing update adds a `discount_code` column; a CRM migration renames
`customer_id` to `account_id`; an API starts returning amounts as strings. Each one
silently breaks downstream dashboards. Validating on every push catches the drift the
moment it appears, in the PR of the person who introduced it — not Monday morning
when the dashboard errors.

### The contract: `schema.json`

The expected schema lives in a declarative JSON contract — not inline in the YAML —
so changing it is a deliberate, reviewable data decision:

```json
{
  "dataset": "data/processed/member_behaviour_summary.csv",
  "min_rows": 1000,
  "primary_key": "member_id",
  "allow_extra_columns": false,
  "columns": {
    "member_id":              { "dtype": "string", "unique": true, "max_null_pct": 0 },
    "membership_type":        { "dtype": "string", "allowed": ["Basic", "Standard", "Premium", "PT-Combo"] },
    "total_amount_paid_inr":  { "dtype": "int", "min": 0 },
    "avg_streak_length_days": { "dtype": "float", "min": 0, "max_null_pct": 20 },
    "behavioural_segment":    { "dtype": "string", "allowed": ["At Risk", "Champions", "Dormant / Lapsed", "Loyal / Engaged"] }
  }
}
```

### Checks performed (each logs `PASS:` or `ERROR:`)

| # | Check | What it catches |
|---|---|---|
| 1 | Required columns | Missing columns, unexpected new columns, and a "possible rename" hint when one disappears while another appears |
| 2 | Data types | `int`/`float`/`string`/`bool`/`datetime` mismatches, e.g. `total_amount_paid_inr` becoming a string |
| 3 | Minimum row count | Truncated or empty pipeline output |
| 4 | Null quality | Fully-null columns and per-column `max_null_pct` breaches (with the actual % in the error) |
| 5 | Primary-key uniqueness | Duplicate `member_id` values |
| 6 | Domain / range | Values outside the `allowed` set, or below `min` / above `max` |

### Run it locally

```bash
python validate_data.py data/processed/member_behaviour_summary.csv \
  --schema schema.json --report validation_report.json
# echo $?  ->  0 means PASS, 1 means FAIL
```

A machine-readable `validation_report.json` is written for the workflow's artifact
and for the failure notification step. The validator has 10 pytest cases in
`tests/test_validate_data.py`.

### Blocking merges (branch protection)

The workflow failing is not enough by itself — you must *require* the check:

1. Repo → **Settings → Branches → Add branch protection rule** (or edit the `main` rule).
2. Branch name pattern: `main`.
3. Tick **Require status checks to pass before merging**.
4. Search for **Data Validation** and add it (it must have run once to appear).
5. Save. PRs whose `validate` job fails can no longer be merged.

### Failure notifications

The workflow's last step runs only when validation fails
(`if: failure()`). It calls `notify_failure.py`, which reads
`validation_report.json` and emails the failed checks over SMTP (self-contained, same env vars as `email_sender.py`).
Configure these repository secrets (mirroring the local `.env`):

| Secret | Purpose |
|---|---|
| `SENDER_EMAIL` | SMTP login / from address |
| `SENDER_PASSWORD` | SMTP app password |
| `SMTP_SERVER` | e.g. `smtp.gmail.com` |
| `SMTP_PORT` | e.g. `587` |
| `NOTIFY_RECIPIENTS` | Comma-separated recipients |

If secrets are absent, the step logs a warning and exits `0` so it never masks the
original validation failure.

### Intentionally changing the schema

Add/rename/remove a column or change a type? Update `schema.json` in the **same PR**
as the data change, and mention it in the PR description. The contract is the source
of truth for every downstream consumer, so it changes deliberately and with review —
never silently.

---

## 🧭 Dashboard Sections

| Section | Question it answers | Contents |
|---|---|---|
| **Overview** | Is the business healthy right now? | Five KPI cards above the fold, monthly activity trend, streak-break mix |
| **Trends** | Which direction are we moving? | Monthly actives, visits vs uniques, retention rate, retention by membership type |
| **Data Explorer** | Show me the members behind the number | Three filters, advanced filters in an expander, member table, CSV export |

**Layout principles applied throughout:**

- KPI row is the first element on the page — no hero banner, no welcome copy
- `st.columns` only where content is genuinely compared side by side
- `st.expander` for anything most users skip most visits (definitions, raw tables, advanced filters)
- One `st.title` per page → `st.header` per block → `st.subheader` per chart → `st.divider` only between headers
- Sidebar holds navigation only; page-specific filters stay on their page

---

## 📁 Data Sources

All files live in `data/raw/`.

| File | Rows | Contents |
|---|---|---|
| `members_master.csv` | 17,500 | Demographics, membership type, branch, goals |
| `gym_checkin_workout_logs.csv` | 108,744 | Check-in/checkout timestamps, workout type, duration |
| `streak_history_episodes.csv` | 40,202 | Streak episodes with length and break reason |
| `subscription_renewal_records.csv` | 45,764 | Billing cycles, amounts, renewal outcomes |
| `app_engagement_events.csv` | 97,988 | In-app events, platform, session duration |

---

## ⚠️ Data Gotchas — Read Before Writing Analysis

These are real properties of the extract. Each one silently produces
wrong-but-plausible output if missed.

### 1. `renewal_status` has five values, not two

```
Renewed 34,855 | Lapsed 4,523 | Auto-Renew Failed 2,757 | Upgraded 1,840 | Downgraded 1,789
```

An **upgrade is the best possible outcome**. Filtering `status != "Renewed"` buckets
upgrades and downgrades as churn and understates retention by ~13 points
(70.4% vs the true 83.3%).

```python
RETAINED = ("Renewed", "Upgraded", "Downgraded")
CHURNED  = ("Lapsed", "Auto-Renew Failed")
```

### 2. The check-in extract ends 2 Oct 2025 — never anchor windows to `now()`

Any "last 30 days" window computed against the real calendar date matches **zero
rows**. Active members, streak length, and stickiness all return 0 while the output
still looks correctly formatted. Derive the anchor from the data:

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

Cycles with `billing_cycle_end` after the as-of date have no outcome yet. Including
them reports retention on the future.

### 5. Partial trailing months distort trend charts

The extract's final month holds only a handful of rows, drawing a cliff that reads as
a collapse but is just the export boundary. Drop it before charting.

### 6. `break_reason == "Unknown"` is not a cause

It marks unresolved or ongoing episodes and accounts for ~39% of rows. Excluded from
the break-reason chart, it would otherwise bury the seven actionable reasons.

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

Two of the top four — **Festival/Holiday and Monsoon Disruption, 33% combined** — are
calendar-predictable. They are addressable with scheduled interventions rather than
generic re-engagement campaigns.