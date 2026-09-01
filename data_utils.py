"""Data loading and KPI logic for the StreakForge dashboard.

Kept separate from app.py so the caching lives in one place.
Streamlit reruns app.py on every click; @st.cache_data makes sure the CSVs
are only read once.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

# Paths are relative to this file, so `streamlit run app.py` works
# no matter which folder you launch it from.
DATA_DIR = Path(__file__).resolve().parent / "data" / "raw"

# The renewal file has 5 outcomes. Upgraded and Downgraded members are still
# paying customers, so they count as RETAINED, not churned.
RETAINED = ("Renewed", "Upgraded", "Downgraded")
CHURNED = ("Lapsed", "Auto-Renew Failed")


# ---------------------------------------------------------------- loaders ----
@st.cache_data
def load_members():
    df = pd.read_csv(DATA_DIR / "members_master.csv")
    # join_date mixes dd-mm-yyyy, yyyy/mm/dd and yyyy-mm-dd, so parse loosely.
    df["join_date"] = pd.to_datetime(
        df["join_date"], errors="coerce", dayfirst=True, format="mixed"
    )
    return df


@st.cache_data
def load_checkins():
    df = pd.read_csv(
        DATA_DIR / "gym_checkin_workout_logs.csv",
        usecols=["checkin_id", "member_id", "checkin_datetime",
                 "workout_type", "duration_minutes"],
    )
    df["checkin_datetime"] = pd.to_datetime(df["checkin_datetime"], errors="coerce")
    return df


@st.cache_data
def load_renewals():
    df = pd.read_csv(DATA_DIR / "subscription_renewal_records.csv")
    df["billing_cycle_end"] = pd.to_datetime(df["billing_cycle_end"], errors="coerce")
    return df


@st.cache_data
def load_streaks():
    df = pd.read_csv(DATA_DIR / "streak_history_episodes.csv")
    df["streak_start_date"] = pd.to_datetime(df["streak_start_date"], errors="coerce")
    return df


# ------------------------------------------------------------------ helpers ----
@st.cache_data
def as_of():
    """Latest date the data actually covers (2 Oct 2025), NOT today.

    The check-in file ends in Oct 2025. If you anchor a "last 30 days" window
    to the real calendar date, every activity KPI comes out as zero.
    """
    return load_checkins()["checkin_datetime"].max().normalize()


def _retention_pct(statuses):
    """Share of resolved billing cycles that stayed subscribed."""
    resolved = statuses[statuses.isin(RETAINED + CHURNED)]
    if resolved.empty:
        return 0.0
    return round(resolved.isin(RETAINED).mean() * 100, 1)


# --------------------------------------------------------------------- KPIs ----
@st.cache_data
def get_kpis():
    """The 5 headline numbers, each with a delta vs the previous 30 days."""
    checkins, renewals, streaks = load_checkins(), load_renewals(), load_streaks()
    end = as_of()
    d30, d60 = end - pd.Timedelta(days=30), end - pd.Timedelta(days=60)

    # 1. Active members = unique check-ins in the last 30 days
    now_active = checkins.loc[checkins["checkin_datetime"] >= d30, "member_id"].nunique()
    was_active = checkins.loc[
        checkins["checkin_datetime"].between(d60, d30), "member_id"
    ].nunique()

    # 2. Retention on cycles that ended in each window
    now_ret = _retention_pct(
        renewals.loc[renewals["billing_cycle_end"].between(d30, end), "renewal_status"]
    )
    was_ret = _retention_pct(
        renewals.loc[renewals["billing_cycle_end"].between(d60, d30), "renewal_status"]
    )

    # 3. Median streak length (median, not mean — the data is right-skewed)
    now_streak = streaks.loc[
        streaks["streak_start_date"].between(d30, end), "streak_length_days"
    ].median()
    was_streak = streaks.loc[
        streaks["streak_start_date"].between(d60, d30), "streak_length_days"
    ].median()

    return {
        "as_of": end,
        "total_members": len(load_members()),
        "active": int(now_active),
        "active_delta": round((now_active - was_active) / was_active * 100, 1),
        "retention": now_ret,
        "retention_delta": round(now_ret - was_ret, 1),
        "churn": round(100 - now_ret, 1),
        "churn_delta": round(was_ret - now_ret, 1),
        "streak": round(float(now_streak), 1),
        "streak_delta": round(float(now_streak - was_streak), 1),
        "visits": len(checkins),
    }


# --------------------------------------------------------------- aggregates ----
@st.cache_data
def monthly_activity():
    """Unique members and total visits per month, last 24 months."""
    checkins = load_checkins().dropna(subset=["checkin_datetime"])
    out = (
        checkins.groupby(pd.Grouper(key="checkin_datetime", freq="MS"))
        .agg(active_members=("member_id", "nunique"),
             total_visits=("checkin_id", "count"))
    )
    # Drop the final month — the export cuts off on the 2nd, so it looks like
    # a collapse when it is really just the end of the file.
    return out[out.index < as_of().to_period("M").to_timestamp()].tail(24)


@st.cache_data
def monthly_retention():
    """Retention rate per month, ignoring cycles that have not resolved yet."""
    renewals = load_renewals().dropna(subset=["billing_cycle_end"])
    renewals = renewals[renewals["billing_cycle_end"] <= as_of()]
    out = renewals.groupby(pd.Grouper(key="billing_cycle_end", freq="MS")).apply(
        lambda g: _retention_pct(g["renewal_status"]), include_groups=False
    ).to_frame("retention_pct")
    return out[out.index < as_of().to_period("M").to_timestamp()].tail(24)


@st.cache_data
def retention_by(column):
    """Retention rate and average spend, grouped by one member attribute."""
    joined = load_renewals().merge(
        load_members()[["member_id", column]], on="member_id"
    )
    out = joined.groupby(column).agg(
        members=("member_id", "nunique"),
        retention_pct=("renewal_status", _retention_pct),
        avg_spend_inr=("amount_paid_inr", lambda s: round(s.mean())),
    )
    return out.sort_values("retention_pct", ascending=False)


@st.cache_data
def break_reasons():
    """Why streaks end. "Unknown" is dropped — it means unresolved, not a cause."""
    reasons = load_streaks()["break_reason"].dropna()
    reasons = reasons[reasons != "Unknown"]
    return reasons.value_counts().to_frame("episodes")


@st.cache_data
def member_table():
    """One row per member, for the Data Explorer."""
    visits = load_checkins().groupby("member_id").agg(
        visits=("checkin_id", "count"), last_visit=("checkin_datetime", "max")
    )
    table = load_members()[
        ["member_id", "city", "membership_type", "primary_goal"]
    ].merge(visits, on="member_id", how="left")
    table["visits"] = table["visits"].fillna(0).astype(int)
    table["days_since_visit"] = (as_of() - table["last_visit"]).dt.days
    return table
