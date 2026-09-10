"""
PR18 — Sidebar filters & cascading filter-application helpers.

Filters are built off member_behaviour_summary.csv (member grain) and
persisted in st.session_state so they survive page navigation. Downstream
pages call apply_member_filters() / filtered_branch_ids() / filtered_member_ids()
to cascade the same selection onto at_risk_members.csv and branch_risk_summary.csv.
"""

import pandas as pd
import streamlit as st

DEFAULTS = {
    "cities_tier": [],
    "membership_types": [],
    "behavioural_segments": [],
    "signup_channels": [],
    "gym_branches": [],
    "join_date_range": None,
    "risk_tiers": [],
    "member_search": "",
}


def _multiselect_options(df: pd.DataFrame, col: str):
    if col not in df.columns:
        return []
    return sorted(df[col].dropna().unique().tolist())


def render_filters(data) -> dict:
    member_df = data.get("member_behaviour", pd.DataFrame())

    for key, default in DEFAULTS.items():
        st.session_state.setdefault(f"flt_{key}", default)

    st.markdown("### 🔎 Filters")

    if member_df.empty:
        st.caption("Filters unavailable — member data not loaded.")
        return {}

    with st.expander("Demographics & Membership", expanded=True):
        st.multiselect(
            "City tier", _multiselect_options(member_df, "city_tier"), key="flt_cities_tier"
        )
        st.multiselect(
            "Membership type", _multiselect_options(member_df, "membership_type"), key="flt_membership_types"
        )
        st.multiselect(
            "Signup channel", _multiselect_options(member_df, "signup_channel"), key="flt_signup_channels"
        )

    with st.expander("Behaviour & Risk", expanded=True):
        st.multiselect(
            "Behavioural segment", _multiselect_options(member_df, "behavioural_segment"), key="flt_behavioural_segments"
        )
        if "gym_branch_id" in member_df.columns:
            st.multiselect(
                "Gym branch", _multiselect_options(member_df, "gym_branch_id"), key="flt_gym_branches"
            )
        st.multiselect(
            "Risk tier (active members)", ["Low", "Moderate", "Elevated", "High"], key="flt_risk_tiers"
        )

    with st.expander("Signup date range", expanded=False):
        if "join_date" in member_df.columns and member_df["join_date"].notna().any():
            min_d = member_df["join_date"].min().date()
            max_d = member_df["join_date"].max().date()
            st.date_input(
                "Join date between", value=(min_d, max_d), min_value=min_d, max_value=max_d,
                key="flt_join_date_range",
            )
        else:
            st.caption("`join_date` not available.")

    st.text_input("Search member ID", key="flt_member_search", placeholder="e.g. MBR-000763")

    if st.button("↺ Reset all filters", use_container_width=True):
        for key, default in DEFAULTS.items():
            st.session_state[f"flt_{key}"] = default
        st.rerun()

    return {
        "cities_tier": st.session_state.flt_cities_tier,
        "membership_types": st.session_state.flt_membership_types,
        "signup_channels": st.session_state.flt_signup_channels,
        "behavioural_segments": st.session_state.flt_behavioural_segments,
        "gym_branches": st.session_state.flt_gym_branches,
        "risk_tiers": st.session_state.flt_risk_tiers,
        "join_date_range": st.session_state.get("flt_join_date_range"),
        "member_search": st.session_state.flt_member_search.strip(),
    }


def apply_member_filters(member_df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Applies the sidebar filter selection to member_behaviour_summary.csv."""
    if member_df.empty or not filters:
        return member_df

    df = member_df.copy()

    def _in(col, values):
        nonlocal df
        if values and col in df.columns:
            df = df[df[col].isin(values)]

    _in("city_tier", filters.get("cities_tier"))
    _in("membership_type", filters.get("membership_types"))
    _in("signup_channel", filters.get("signup_channels"))
    _in("behavioural_segment", filters.get("behavioural_segments"))
    _in("gym_branch_id", filters.get("gym_branches"))

    date_range = filters.get("join_date_range")
    if date_range and isinstance(date_range, (tuple, list)) and len(date_range) == 2 and "join_date" in df.columns:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        df = df[(df["join_date"] >= start) & (df["join_date"] <= end)]

    search = filters.get("member_search")
    if search:
        id_col = "member_id" if "member_id" in df.columns else df.index.name
        if id_col == "member_id":
            df = df[df["member_id"].str.contains(search, case=False, na=False)]
        else:
            df = df[df.index.astype(str).str.contains(search, case=False, na=False)]

    return df


def apply_risk_tier_filter(at_risk_df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """at_risk_members.csv only ever contains 'High' tier rows (PR11), so this
    is a pass-through unless the user explicitly narrows to other tiers (in
    which case it correctly returns empty, since none exist in this file)."""
    tiers = filters.get("risk_tiers") if filters else []
    if not tiers or "risk_tier" not in at_risk_df.columns:
        return at_risk_df
    return at_risk_df[at_risk_df["risk_tier"].isin(tiers)]


def filtered_branch_ids(filtered_member_df: pd.DataFrame):
    if "gym_branch_id" not in filtered_member_df.columns:
        return None
    return set(filtered_member_df["gym_branch_id"].dropna().unique())


def filtered_member_ids(filtered_member_df: pd.DataFrame):
    if "member_id" in filtered_member_df.columns:
        return set(filtered_member_df["member_id"].dropna().unique())
    return set(filtered_member_df.index.astype(str))


def active_filter_count(filters: dict) -> int:
    if not filters:
        return 0
    count = 0
    for k, v in filters.items():
        if k == "join_date_range":
            continue
        if isinstance(v, (list, tuple)) and v:
            count += 1
        elif isinstance(v, str) and v:
            count += 1
    return count