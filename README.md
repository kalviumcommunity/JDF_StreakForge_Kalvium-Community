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
├── requirements.txt           # Pinned dependencies
├── tests/
│   └── test_app_smoke.py      # 7 headless AppTest checks
├── data/
│   └── raw/                   # Source CSV extracts (5 files, ~27 MB)
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