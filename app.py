"""StreakForge — Retention Intelligence dashboard shell.

Structure:
  1. Page config      (must be the first Streamlit call)
  2. Sidebar nav      (returns which section to show)
  3. One function per section
  4. Router           (calls exactly one section per rerun)
"""

import streamlit as st

import data_utils as du

# --- 1. Page config ----------------------------------------------------------
st.set_page_config(
    page_title="StreakForge · Retention Intelligence",
    page_icon="🔥",
    layout="wide",
)

# --- 2. Sidebar --------------------------------------------------------------
st.sidebar.title("StreakForge")
st.sidebar.caption("Fitness Retention Intelligence")
st.sidebar.subheader("Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Trends", "Data Explorer"])
st.sidebar.divider()
st.sidebar.caption(f"Data as of: {du.as_of():%d %b %Y}")


# --- 3a. Overview ------------------------------------------------------------
def overview():
    st.title("Business Overview")
    k = du.get_kpis()

    # KPI row is the FIRST thing on the page — no banner, no intro text.
    st.header("Key Performance Indicators")
    st.caption(f"Last 30 days to {k['as_of']:%d %b %Y}, vs the 30 days before that.")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Active Members", f"{k['active']:,}", f"{k['active_delta']:+.1f}%")
    with c2:
        st.metric("Retention Rate", f"{k['retention']}%", f"{k['retention_delta']:+.1f} pts")
    with c3:
        st.metric("Churn Rate", f"{k['churn']}%", f"{k['churn_delta']:+.1f} pts",
                  delta_color="inverse")  # rising churn must show red, not green
    with c4:
        st.metric("Median Streak", f"{k['streak']:.0f} days", f"{k['streak_delta']:+.1f}")
    with c5:
        st.metric("Total Members", f"{k['total_members']:,}")

    with st.expander("About these metrics"):
        st.write(
            "Active Members = unique gym check-ins in the last 30 days. "
            "Retention counts Renewed, Upgraded and Downgraded cycles as retained; "
            "only Lapsed and Auto-Renew Failed count as churn. "
            "Churn is 100 minus retention. Median streak uses the median because "
            "streak length is heavily right-skewed."
        )

    st.divider()

    st.header("Retention Snapshot")
    left, right = st.columns([3, 2])   # 60/40 — the trend matters more
    with left:
        st.subheader("Active Members by Month")
        st.line_chart(du.monthly_activity()["active_members"], height=260)
    with right:
        st.subheader("Why Streaks Break")
        st.bar_chart(du.break_reasons()["episodes"], height=260)

    with st.expander("View monthly activity data"):
        st.dataframe(du.monthly_activity())


# --- 3b. Trends --------------------------------------------------------------
def trends():
    st.title("Trend Analysis")
    activity = du.monthly_activity()

    st.header("Engagement Trends")
    st.subheader("Monthly Active Members (Last 24 Months)")
    st.line_chart(activity["active_members"], height=300)

    st.subheader("Total Visits vs Unique Members")
    st.line_chart(activity[["total_visits", "active_members"]], height=280)

    with st.expander("How to read this"):
        st.write(
            "Visits rising faster than unique members means existing members are "
            "training more often. The reverse means you are signing up members "
            "who visit once and stop."
        )

    st.divider()

    st.header("Commercial Trends")
    st.subheader("Retention Rate by Month")
    st.line_chart(du.monthly_retention()["retention_pct"], height=260)

    st.subheader("Retention by Membership Type")
    seg = du.retention_by("membership_type")
    chart, table = st.columns([3, 2])
    with chart:
        st.bar_chart(seg["retention_pct"], height=260)
    with table:
        st.dataframe(seg, height=260)


# --- 3c. Data Explorer -------------------------------------------------------
def data_explorer():
    st.title("Data Explorer")
    table = du.member_table()

    st.header("Filter Members")
    f1, f2, f3 = st.columns(3)
    with f1:
        cities = st.multiselect("City", sorted(table["city"].dropna().unique()))
    with f2:
        plans = st.multiselect(
            "Membership type", sorted(table["membership_type"].dropna().unique())
        )
    with f3:
        min_visits = st.slider("Minimum visits", 0, int(table["visits"].max()), 0)

    with st.expander("Advanced filters"):
        at_risk = st.checkbox("At risk only (no visit in 30+ days)")

    filtered = table.copy()
    if cities:
        filtered = filtered[filtered["city"].isin(cities)]
    if plans:
        filtered = filtered[filtered["membership_type"].isin(plans)]
    if min_visits:
        filtered = filtered[filtered["visits"] >= min_visits]
    if at_risk:
        filtered = filtered[filtered["days_since_visit"].fillna(9999) >= 30]

    st.divider()

    st.header("Member Table")
    m1, m2 = st.columns(2)
    m1.metric("Members Matched", f"{len(filtered):,}")
    m2.metric("Median Visits", f"{filtered['visits'].median() if len(filtered) else 0:.0f}")

    st.subheader(f"Showing first 500 of {len(filtered):,} members")
    st.dataframe(filtered.head(500), height=380)

    st.download_button(
        "Download filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="streakforge_members.csv",
        mime="text/csv",
    )

    with st.expander("Column definitions"):
        st.write(
            "visits = lifetime gym check-ins. "
            "last_visit = most recent check-in. "
            "days_since_visit = days from last check-in to the data as-of date."
        )


# --- 4. Router ---------------------------------------------------------------
if page == "Overview":
    overview()
elif page == "Trends":
    trends()
elif page == "Data Explorer":
    data_explorer()