"""Export the static JSON the website reads (web/public/data/*.json).

The site never computes analytics: every number comes from data/processed/*.csv
(produced by the notebooks). Display copy that the notebooks do not produce
(KPI definitions and reading notes, insight wording) lives in src/web_copy.json,
copied verbatim from the approved prototype.

Run from the repo root:  python src/export_web_data.py
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
OUT = ROOT / "web" / "public" / "data"
COPY = json.loads((Path(__file__).parent / "web_copy.json").read_text(encoding="utf-8"))
OUT.mkdir(parents=True, exist_ok=True)


def clean(v):
    """numpy -> plain python, NaN -> None, floats rounded to 4 dp."""
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, (np.integer, int)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return None if np.isnan(v) else round(float(v), 4)
    return v


def dump(name, rows):
    rows = [{k: clean(v) for k, v in r.items()} for r in rows]
    (OUT / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{name}.json: {len(rows)} rows")


def display(value, unit):
    if unit == "%":
        return f"{value * 100:.1f}%"
    if unit == "count":
        return f"{round(value):,}"
    if unit.startswith("INR"):
        return "₹" + f"{round(value):,}"
    if unit == "days":
        return f"{value:.1f}"
    return f"{value:.2f}"


# ---- KPIs ----
kpi = pd.read_csv(PROC / "kpi_summary.csv")
rows = []
for r in kpi.to_dict("records"):
    c = COPY["kpis"][r["kpi_id"]]
    rows.append({
        "id": r["kpi_id"], "name": c["name"], "cat": c["cat"],
        "value": round(float(r["value"]), 4), "display": display(r["value"], r["unit"]),
        "unit": COPY["kpi_units"].get(r["unit"], r["unit"]),
        "defn": c["defn"], "note": c["note"], "pair": c["pair"],
    })
dump("kpis", rows)

# ---- branches, cohorts, segments ----
dump("branches", pd.read_csv(PROC / "branch_risk_summary.csv").to_dict("records"))
dump("cohorts", pd.read_csv(PROC / "activation_cohort_trend.csv").to_dict("records"))
dump("segments", pd.read_csv(PROC / "activation_segment_comparison.csv").to_dict("records"))

# ---- at-risk (all twelve real rows; no sample rows) ----
ar = pd.read_csv(PROC / "at_risk_members.csv")
flags = ["risk_high_recency", "risk_low_frequency", "risk_negative_trend", "risk_paying_not_showing"]
dump("at_risk", [{
    "id": r["member_id"], "branch": r["gym_branch_id"], "recency": r["recency_days"],
    "events": r["frequency_total_events"], "slope": r["engagement_trend_slope"],
    "ratio": r["plan_to_engagement_ratio"], "sig": [int(bool(r[f])) for f in flags], "sample": False,
} for r in ar.to_dict("records")])

# ---- insights: audience/confidence parsed from reports/insight_summary.md and
#      cross-checked against the verbatim prototype copy ----
md = (ROOT / "reports" / "insight_summary.md").read_text(encoding="utf-8")
parsed = {}
for block in re.split(r"\n### ", md)[1:]:
    iid = block.split(" ")[0]
    aud = re.search(r"\*\*Audience:\*\* (.+?)\s*\n", block).group(1).strip()
    conf = re.search(r"\*\*Confidence:\*\* (.+?)\s*(\n|$)", block).group(1).strip()
    parsed[iid] = (aud, conf)
for i in COPY["insights"]:
    aud, conf = parsed[i["id"]]
    assert aud == i["aud"] and conf == i["conf"], f"{i['id']} differs from insight_summary.md: {aud}/{conf}"
dump("insights", COPY["insights"])

# ---- funnel: same cascading logic as notebook 04 (section 10.3) ----
feat = pd.read_csv(PROC / "streakforge_features.csv", low_memory=False,
                   usecols=["member_id", "is_churned", "tenure_days_at_event", "renewal_id", "streak_id", "streak_length_days"])
flags_df = feat.drop_duplicates("member_id").set_index("member_id")[["is_churned"]].copy()
flags_df["activated"] = feat.loc[feat["tenure_days_at_event"] <= 7].groupby("member_id").size().reindex(flags_df.index).fillna(0).gt(0)
subs = feat.dropna(subset=["renewal_id"]).drop_duplicates("renewal_id")
flags_df["renewed_once"] = subs.groupby("member_id")["renewal_id"].nunique().reindex(flags_df.index).fillna(0).gt(1)
st = feat.dropna(subset=["streak_length_days"]).drop_duplicates("streak_id")
flags_df["formed_streak7"] = st.loc[st["streak_length_days"] >= 7].groupby("member_id").size().reindex(flags_df.index).fillna(0).gt(0)
flags_df["retained"] = ~flags_df["is_churned"].astype(bool)
mask = pd.Series(True, index=flags_df.index)
counts = [int(mask.sum())]
for col in ["activated", "renewed_once", "formed_streak7", "retained"]:
    mask &= flags_df[col]
    counts.append(int(mask.sum()))
dump("funnel", [{"stage": s, "members": n} for s, n in zip(COPY["funnel_labels"], counts)])

# ---- RFM segment mix (member grain) ----
seg = pd.read_csv(PROC / "member_behaviour_summary.csv", usecols=["behavioural_segment"])["behavioural_segment"].value_counts()
colour = {r[0]: r[2] for r in COPY["rfm"]}
(OUT / "rfm.json").write_text(json.dumps([[k, int(v), colour[k]] for k, v in seg.items()], separators=(",", ":")))
print("rfm.json:", dict(seg))
