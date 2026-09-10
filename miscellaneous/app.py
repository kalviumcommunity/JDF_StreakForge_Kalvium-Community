"""StreakForge — Retention Intelligence dashboard shell.

Structure:
  1. Page config      (must be the first Streamlit call)
  2. Sidebar nav      (returns which section to show)
  3. One function per section
  4. Router           (calls exactly one section per rerun)
"""

import pandas as pd
import streamlit as st

import data_utils as du
import upload_utils as uu

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
page = st.sidebar.radio(
    "Go to", ["Overview", "Trends", "Data Explorer", "Upload & Sync"]
)
st.sidebar.divider()
st.sidebar.caption(f"Data as of: {du.as_of():%d %b %Y}")

# Show whether an ad-hoc file is loaded this session, so the user always knows
# which dataset the Upload section is holding.
if "upload" in st.session_state:
    st.sidebar.caption(f"Uploaded: {st.session_state['upload']['name']}")


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


# --- 3d. Upload & Sync -------------------------------------------------------
# Three visible steps — select, validate, confirm — so a monthly refresh never
# silently half-lands. Mirrors Screen 5 of the mock UX.
def upload_and_sync():
    st.title("Upload & Sync")
    st.caption(
        "Bring your own CSV or JSON export and see its shape, types and data "
        "quality immediately. This preview is standalone — the dashboard "
        "sections above continue to read from data/raw."
    )

    # ---- Step 1 · Select ----------------------------------------------------
    st.header("Step 1 · Select a file")
    uploaded = st.file_uploader(
        "Upload a dataset",
        type=["csv", "json"],
        help="CSV or JSON, up to 200 MB. Nothing is written to disk — the file "
             "lives in memory for this browser session only.",
    )

    if uploaded is None:
        # Empty state: say what is empty, why, and offer exactly one action.
        st.info(
            "**No file loaded yet.** Nothing has been uploaded in this session, "
            "so there is nothing to preview. Drop a `.csv` or `.json` export "
            "into the box above to begin."
        )
        with st.expander("What happens after I upload?"):
            st.write(
                "The file is parsed in memory, checked for common problems "
                "(empty file, missing headers, inconsistent rows), and then "
                "profiled: row and column counts, null percentage, the first "
                "10 rows, per-column types and completeness, and descriptive "
                "statistics. Nothing is saved to the server."
            )
        st.stop()

    # ---- Step 2 · Validate --------------------------------------------------
    st.header("Step 2 · Validate")
    try:
        df = uu.load_dataframe(uploaded.name, uploaded.getvalue())
        uu.validate(df)
    except uu.UploadError as err:
        # Error-state rule: what went wrong, the consequence, the way out.
        st.error(f"**{err}**")
        st.caption(
            "Nothing was loaded, so no numbers on this page have changed. "
            "Fix the file and upload it again."
        )
        st.stop()
    except Exception:
        st.error(
            "**Could not read this file.** It may be corrupted or in an "
            "unexpected format."
        )
        st.caption("Nothing was loaded. Try re-exporting the file as CSV.")
        st.stop()

    st.success(
        f"**{uploaded.name}** passed validation — "
        f"{len(df):,} rows x {len(df.columns)} columns."
    )

    for flag in uu.quality_flags(df):
        st.warning(flag)

    # Persist so the file survives reruns and switching sections.
    st.session_state["upload"] = {"name": uploaded.name, "rows": len(df)}

    st.divider()

    # ---- Step 3 · Confirm ---------------------------------------------------
    st.header("Step 3 · Confirm")

    st.subheader("Shape and Completeness")
    st.caption("Answers: did the whole file arrive, and how much is missing?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Rows", f"{len(df):,}")
    with c2:
        st.metric("Columns", f"{len(df.columns)}")
    with c3:
        st.metric("Null %", f"{uu.overall_null_pct(df):.1f}%")

    st.subheader(f"First {uu.PREVIEW_ROWS} Rows")
    st.caption("Answers: does the data look like what I expected to export?")
    st.dataframe(df.head(uu.PREVIEW_ROWS), use_container_width=True)

    st.subheader("Column Summary")
    st.caption("Answers: which columns are usable, and which are too sparse?")
    st.dataframe(uu.column_summary(df), use_container_width=True, height=320)

    numeric = uu.numeric_columns(df)

    with st.expander("Descriptive statistics (numeric columns)"):
        if numeric:
            st.caption(
                "Answers: are there impossible values — negative amounts, "
                "zero durations, outliers at the max?"
            )
            st.dataframe(df[numeric].describe(), use_container_width=True)
        else:
            st.info("No numeric columns in this file, so there is nothing to describe.")

    with st.expander("Top values (categorical columns)"):
        categorical = uu.categorical_columns(df)
        if categorical:
            col = st.selectbox("Column", categorical, key="cat_col")
            st.dataframe(
                df[col].value_counts().head(15).to_frame("count"),
                use_container_width=True,
            )
        else:
            st.info("No categorical columns in this file.")

    st.divider()

    # ---- Downstream usage ---------------------------------------------------
    st.header("Quick Exploration")
    st.caption("Proves the uploaded data is usable for filtering and charting.")

    if not numeric:
        st.info("No numeric columns available to chart.")
    else:
        pick, filt = st.columns([2, 3])
        with pick:
            col = st.selectbox("Numeric column", numeric, key="explore_col")
        with filt:
            low, high = float(df[col].min()), float(df[col].max())
            if low == high:
                st.caption(f"`{col}` is constant at {low:,.2f} — nothing to filter.")
                bounds = (low, high)
            else:
                bounds = st.slider(
                    f"Range of {col}", low, high, (low, high)
                )

        subset = df[df[col].between(*bounds)]
        st.caption(f"{len(subset):,} of {len(df):,} rows in range.")

        st.subheader(f"Distribution of {col}")
        if subset.empty:
            st.info("No rows in the selected range.")
        else:
            counts = pd.cut(subset[col], bins=20).value_counts().sort_index()
            counts.index = [f"{interval.left:,.0f}" for interval in counts.index]
            st.bar_chart(counts, height=260)

        st.download_button(
            "Download filtered rows",
            data=subset.to_csv(index=False).encode("utf-8"),
            file_name=f"filtered_{uploaded.name.rsplit('.', 1)[0]}.csv",
            mime="text/csv",
        )


# --- 4. Router ---------------------------------------------------------------
if page == "Overview":
    overview()
elif page == "Trends":
    trends()
elif page == "Data Explorer":
    data_explorer()
elif page == "Upload & Sync":
    upload_and_sync()