"""
PR20 — Data health / freshness checks surfaced to the user, so a stale or
partially-missing data/processed/ directory fails loudly instead of silently
rendering an empty dashboard.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

EXPECTED_FILES = [
    "member_behaviour_summary.csv",
    "kpi_summary.csv",
    "activation_cohort_trend.csv",
    "branch_risk_summary.csv",
    "at_risk_members.csv",
    "activation_segment_comparison.csv",
]


def run_health_check(processed_dir: Path, reports_dir: Path) -> dict:
    results = {"files": [], "all_present": True, "insight_summary_present": False}

    for fname in EXPECTED_FILES:
        path = processed_dir / fname
        present = path.exists()
        n_rows = None
        if present:
            try:
                n_rows = sum(1 for _ in open(path, "r", encoding="utf-8")) - 1
            except Exception:
                n_rows = None
        results["files"].append({"file": fname, "present": present, "rows": n_rows})
        results["all_present"] = results["all_present"] and present

    results["insight_summary_present"] = (reports_dir / "insight_summary.md").exists()
    return results


def render_health_badge(health: dict):
    if health["all_present"] and health["insight_summary_present"]:
        st.success("✅ All expected processed data files found.", icon="✅")
    else:
        st.error("⚠️ Some expected data files are missing — parts of the dashboard may be empty.")
        with st.expander("Details"):
            for f in health["files"]:
                icon = "✅" if f["present"] else "❌"
                rows_txt = f"{f['rows']:,} rows" if f["rows"] is not None else "—"
                st.write(f"{icon} `{f['file']}` — {rows_txt}")
            st.write(("✅" if health["insight_summary_present"] else "❌") + " `reports/insight_summary.md`")