"""
Centralised, cached CSV loaders for the Streamlit app.
CSV-only persistence throughout (no parquet/pickle).

PR20: caching keyed off each file's mtime, so a re-run of the notebooks
(fresh CSVs dropped into data/processed/) invalidates the Streamlit cache
without needing a manual "Clear cache" — st.cache_data still avoids re-reading
unchanged files on every rerun.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"

AS_OF_DATE_PIPELINE = pd.Timestamp("2026-08-14")
AS_OF_DATE_DATA_REALISTIC = pd.Timestamp("2025-10-05")


def _mtime(path: Path) -> float:
    return path.stat().st_mtime if path.exists() else -1.0


def _safe_read_csv(filename: str, **kwargs) -> pd.DataFrame:
    path = PROCESSED_DIR / filename
    if not path.exists():
        st.error(f"Missing processed file: `{filename}`. Expected at `{path}`.")
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, **kwargs)
        if df.empty:
            st.warning(f"`{filename}` loaded but has 0 rows.")
        return df
    except Exception as e:
        st.error(f"Failed to load `{filename}`: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner="Loading member behaviour summary...")
def load_member_behaviour_summary(_mtime_key: float = None) -> pd.DataFrame:
    return _safe_read_csv("member_behaviour_summary.csv", parse_dates=["join_date"])


@st.cache_data(show_spinner="Loading KPI summary...")
def load_kpi_summary(_mtime_key: float = None) -> pd.DataFrame:
    return _safe_read_csv("kpi_summary.csv")


@st.cache_data(show_spinner=False)
def load_activation_cohort_trend(_mtime_key: float = None) -> pd.DataFrame:
    return _safe_read_csv("activation_cohort_trend.csv")


@st.cache_data(show_spinner=False)
def load_branch_risk_summary(_mtime_key: float = None) -> pd.DataFrame:
    return _safe_read_csv("branch_risk_summary.csv")


@st.cache_data(show_spinner=False)
def load_at_risk_members(_mtime_key: float = None) -> pd.DataFrame:
    return _safe_read_csv("at_risk_members.csv")


@st.cache_data(show_spinner=False)
def load_activation_segment_comparison(_mtime_key: float = None) -> pd.DataFrame:
    return _safe_read_csv("activation_segment_comparison.csv")


@st.cache_data(show_spinner=False)
def load_insight_narrative(_mtime_key: float = None) -> pd.DataFrame:
    return _safe_read_csv("insight_narrative.csv")


@st.cache_data(show_spinner=False)
def load_insights_payload(_mtime_key: float = None) -> dict:
    path = PROCESSED_DIR / "insights_payload.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_insight_summary_md(_mtime_key: float = None) -> str:
    path = REPORTS_DIR / "insight_summary.md"
    if not path.exists():
        return "_`reports/insight_summary.md` not found._"
    return path.read_text(encoding="utf-8")


def load_all():
    """Warms the cache once per rerun; each loader's cache key includes the
    source file's mtime so edits to the underlying CSV bust the cache."""
    files = {
        "member_behaviour": ("member_behaviour_summary.csv", load_member_behaviour_summary),
        "kpi_summary": ("kpi_summary.csv", load_kpi_summary),
        "activation_cohort_trend": ("activation_cohort_trend.csv", load_activation_cohort_trend),
        "branch_risk_summary": ("branch_risk_summary.csv", load_branch_risk_summary),
        "at_risk_members": ("at_risk_members.csv", load_at_risk_members),
        "activation_segment_comparison": ("activation_segment_comparison.csv", load_activation_segment_comparison),
        "insight_narrative": ("insight_narrative.csv", load_insight_narrative),
    }
    data = {key: loader_fn(_mtime(PROCESSED_DIR / fname)) for key, (fname, loader_fn) in files.items()}
    data["insights_payload"] = load_insights_payload(_mtime(PROCESSED_DIR / "insights_payload.json"))
    data["insight_summary_md"] = load_insight_summary_md(_mtime(REPORTS_DIR / "insight_summary.md"))
    return data