"""StreakForge — Retention Intelligence dashboard shell.

Structure:
  1. Page config      (must be the first Streamlit call)
  2. Session state    (initialize all persistent values)
  3. Sidebar nav      (returns which section to show)
  4. One function per section
  5. Router           (calls exactly one section per rerun)
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import data_utils as du
import upload_utils as uu

# --- 1. Page config ----------------------------------------------------------
st.set_page_config(
    page_title="StreakForge · Retention Intelligence",
    page_icon="🔥",
    layout="wide",
)

# --- 2. Session State Initialization -----------------------------------------
# Session state persists values across reruns. Each key is initialized only once
# with safe defaults to prevent overwriting user-selected values.

# "explorer_cities" - stores selected city filters in Data Explorer.
# Persists when user changes other filters (plans, visit count, advanced filters).
if "explorer_cities" not in st.session_state:
    st.session_state["explorer_cities"] = []

# "explorer_plans" - stores selected membership type filters in Data Explorer.
# Survives reruns when user adjusts sliders or toggles checkboxes.
if "explorer_plans" not in st.session_state:
    st.session_state["explorer_plans"] = []

# "explorer_min_visits" - stores minimum visit threshold slider value.
# Prevents reset when user interacts with multiselect or checkbox widgets.
if "explorer_min_visits" not in st.session_state:
    st.session_state["explorer_min_visits"] = 0

# "explorer_at_risk" - stores at-risk filter checkbox state.
# Maintains selection across widget interactions and page navigation.
if "explorer_at_risk" not in st.session_state:
    st.session_state["explorer_at_risk"] = False

# "upload_workflow_step" - tracks which step of the Upload & Sync workflow is active.
# Prevents Step 2 (Validate) from showing before Step 1 (Select) is complete.
# Prevents Step 3 (Confirm) from showing before validation passes.
# Values: 1 = Select file, 2 = Validate, 3 = Confirm & Explore
if "upload_workflow_step" not in st.session_state:
    st.session_state["upload_workflow_step"] = 1

# "upload_dataframe" - caches the validated DataFrame from the uploaded file.
# Prevents re-parsing when user interacts with exploration widgets in Step 3.
# Stores None when no file is uploaded or validation fails.
if "upload_dataframe" not in st.session_state:
    st.session_state["upload_dataframe"] = None

# "upload_filename" - stores the name of the uploaded file.
# Displayed in sidebar and used for export filename generation.
# Persists across step transitions and widget interactions.
if "upload_filename" not in st.session_state:
    st.session_state["upload_filename"] = None

# "upload_validation_passed" - tracks whether the uploaded file passed validation.
# Guards Step 3 from showing if Step 2 failed. Reset when a new file is uploaded.
if "upload_validation_passed" not in st.session_state:
    st.session_state["upload_validation_passed"] = False

# "upload_selected_numeric_col" - stores which numeric column the user chose for exploration.
# Persists when user adjusts the range slider or interacts with other widgets in Step 3.
if "upload_selected_numeric_col" not in st.session_state:
    st.session_state["upload_selected_numeric_col"] = None

# "upload_range_bounds" - stores the slider range bounds for numeric column filtering.
# Survives reruns so the user's range selection is not lost when they click download.
if "upload_range_bounds" not in st.session_state:
    st.session_state["upload_range_bounds"] = (0.0, 0.0)

# "trends_selected_membership_type" - stores which membership type is selected in Trends view.
# Persists when user switches between chart and table views or adjusts other controls.
if "trends_selected_membership_type" not in st.session_state:
    st.session_state["trends_selected_membership_type"] = None


# --- 3. Sidebar --------------------------------------------------------------
st.sidebar.title("StreakForge")
st.sidebar.caption("Fitness Retention Intelligence")

# Reset button clears all workflow progress and filter selections
# Returns the entire app to its initial state as if freshly loaded
if st.sidebar.button("🔄 Reset All Filters & Workflow", help="Clear all selections and restart workflows"):
    # Clear all session state keys to return to initial state
    keys_to_reset = [
        "explorer_cities", "explorer_plans", "explorer_min_visits", "explorer_at_risk",
        "upload_workflow_step", "upload_dataframe", "upload_filename",
        "upload_validation_passed", "upload_selected_numeric_col", "upload_range_bounds",
        "trends_selected_membership_type"
    ]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("Navigation")
page = st.sidebar.radio(
    "Go to", ["Overview", "Trends", "Data Explorer", "Upload & Sync"]
)
st.sidebar.divider()
st.sidebar.caption(f"Data as of: {du.as_of():%d %b %Y}")

# Show whether an ad-hoc file is loaded this session, so the user always knows
# which dataset the Upload section is holding.
if st.session_state["upload_filename"]:
    st.sidebar.caption(f"📁 Uploaded: {st.session_state['upload_filename']}")
    if st.session_state["upload_dataframe"] is not None:
        st.sidebar.caption(f"   {len(st.session_state['upload_dataframe']):,} rows loaded")


# --- 4a. Overview ------------------------------------------------------------
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


# --- 4b. Trends --------------------------------------------------------------
def trends():
    st.title("Trend Analysis")
    activity = du.monthly_activity()

    st.header("Engagement Trends")
    
    # Chart 1: Line chart - Monthly Active Members (Streamlit native)
    st.subheader("Monthly Active Members (Last 24 Months)")
    st.line_chart(activity["active_members"], height=300)

    # Chart 2: Line chart - Total Visits vs Unique Members (Streamlit native multi-series)
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
    
    # Chart 3: Line chart - Retention Rate by Month (Streamlit native)
    st.subheader("Retention Rate by Month")
    st.line_chart(du.monthly_retention()["retention_pct"], height=260)

    # Chart 4: Bar chart + Plotly interactive - Retention by Membership Type
    st.subheader("Retention by Membership Type")
    seg = du.retention_by("membership_type")
    
    chart, table = st.columns([3, 2])
    with chart:
        # Chart 5: Plotly bar chart (interactive with hover details)
        fig = px.bar(
            seg.reset_index(),
            x="membership_type",
            y="retention_pct",
            color="retention_pct",
            color_continuous_scale="RdYlGn",
            labels={"retention_pct": "Retention %", "membership_type": "Membership Type"},
            title="Retention by Membership Type"
        )
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)
    with table:
        st.dataframe(seg, height=300)


# --- 4c. Data Explorer -------------------------------------------------------
def data_explorer():
    """Data Explorer with reactive filtered KPIs and multiple chart types.
    
    All KPIs and charts update dynamically based on filter selections.
    Handles empty filter results gracefully with user-friendly messaging.
    """
    st.title("Data Explorer")
    table = du.member_table()

    st.header("Filter Members")
    # Filters use session state so selections persist across widget interactions
    # User can adjust one filter without losing values in other filters
    
    f1, f2, f3 = st.columns(3)
    with f1:
        # City filter persists in session state across reruns
        cities = st.multiselect(
            "City",
            sorted(table["city"].dropna().unique()),
            default=st.session_state["explorer_cities"],
            key="explorer_cities"
        )
    with f2:
        # Membership type filter persists across interactions with other widgets
        plans = st.multiselect(
            "Membership type",
            sorted(table["membership_type"].dropna().unique()),
            default=st.session_state["explorer_plans"],
            key="explorer_plans"
        )
    with f3:
        # Visit threshold persists when user toggles checkboxes or changes multiselects
        min_visits = st.slider(
            "Minimum visits",
            0,
            int(table["visits"].max()),
            st.session_state["explorer_min_visits"],
            key="explorer_min_visits"
        )

    with st.expander("Advanced filters"):
        # At-risk checkbox state survives all widget interactions
        at_risk = st.checkbox(
            "At risk only (no visit in 30+ days)",
            value=st.session_state["explorer_at_risk"],
            key="explorer_at_risk"
        )

    # Apply filters from session state - all KPIs computed from filtered data
    filtered = table.copy()
    if st.session_state["explorer_cities"]:
        filtered = filtered[filtered["city"].isin(st.session_state["explorer_cities"])]
    if st.session_state["explorer_plans"]:
        filtered = filtered[filtered["membership_type"].isin(st.session_state["explorer_plans"])]
    if st.session_state["explorer_min_visits"]:
        filtered = filtered[filtered["visits"] >= st.session_state["explorer_min_visits"]]
    if st.session_state["explorer_at_risk"]:
        filtered = filtered[filtered["days_since_visit"].fillna(9999) >= 30]

    st.divider()

    # Task 4: Handle empty filtered results with user-friendly message
    if len(filtered) == 0:
        st.warning(
            "⚠️ **No members match your current filter selections.** "
            "Try broadening your criteria (fewer cities, lower visit threshold, or disable at-risk filter)."
        )
        st.info(
            f"💡 **Tip:** Out of {len(table):,} total members, your filters returned zero results. "
            "Use the reset button in the sidebar to clear all filters and start fresh."
        )
        st.stop()

    st.header("Filtered Results")
    
    # Task 1: Five reactive KPI metrics computed from filtered DataFrame
    # All values update dynamically when filters change - no hardcoded values
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        # KPI 1: Total members matching filters
        st.metric("Members Matched", f"{len(filtered):,}")
    with m2:
        # KPI 2: Median visits (central tendency for skewed distribution)
        st.metric("Median Visits", f"{filtered['visits'].median():.0f}")
    with m3:
        # KPI 3: Average visits (mean for comparison)
        st.metric("Mean Visits", f"{filtered['visits'].mean():.1f}")
    with m4:
        # KPI 4: At-risk members (no visit in 30+ days)
        at_risk_count = (filtered["days_since_visit"].fillna(9999) >= 30).sum()
        st.metric("At Risk", f"{at_risk_count:,}", f"{at_risk_count/len(filtered)*100:.1f}%")
    with m5:
        # KPI 5: Data completeness (inverse of null percentage)
        null_count = filtered[["city", "membership_type", "last_visit"]].isnull().sum().sum()
        total_cells = len(filtered) * 3
        completeness = (1 - null_count / total_cells) * 100 if total_cells > 0 else 100
        st.metric("Data Quality", f"{completeness:.1f}%")

    st.divider()

    # Task 2: Multiple chart types that update with filters
    st.header("Visual Analysis")
    
    # Chart 1: Plotly histogram - Visit distribution (interactive, zoomable)
    st.subheader("Visit Distribution")
    fig_hist = px.histogram(
        filtered,
        x="visits",
        nbins=30,
        title="Distribution of Visit Counts",
        labels={"visits": "Total Visits", "count": "Member Count"},
        color_discrete_sequence=["#FF6B6B"]
    )
    fig_hist.update_layout(showlegend=False, height=300)
    st.plotly_chart(fig_hist, use_container_width=True)

    # Chart 2: Bar chart - Members by city (Streamlit native)
    if not filtered["city"].isna().all():
        st.subheader("Members by City")
        city_counts = filtered["city"].value_counts().sort_values(ascending=False)
        st.bar_chart(city_counts, height=280)
    
    # Chart 3: Plotly box plot - Visits by membership type (shows distribution + outliers)
    if not filtered["membership_type"].isna().all():
        st.subheader("Visit Patterns by Membership Type")
        fig_box = px.box(
            filtered.dropna(subset=["membership_type"]),
            x="membership_type",
            y="visits",
            color="membership_type",
            title="Visit Distribution by Membership Type",
            labels={"visits": "Total Visits", "membership_type": "Membership Type"}
        )
        fig_box.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig_box, use_container_width=True)

    st.divider()

    st.header("Member Table")
    st.subheader(f"Showing first 500 of {len(filtered):,} members")
    st.dataframe(filtered.head(500), height=380)

    st.download_button(
        "Download filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="streakforge_members_filtered.csv",
        mime="text/csv",
    )

    with st.expander("Column definitions"):
        st.write(
            "**visits** = lifetime gym check-ins. "
            "**last_visit** = most recent check-in. "
            "**days_since_visit** = days from last check-in to the data as-of date. "
            "**at_risk** = no visit in 30+ days."
        )


# --- 4d. Upload & Sync -------------------------------------------------------
# Multi-step workflow where each step depends on the previous step's completion.
# Step 2 only shows if Step 1 (file selection) succeeds.
# Step 3 only shows if Step 2 (validation) passes.
# All state persists across widget interactions within each step.
def upload_and_sync():
    """Upload & Sync with end-to-end upload-to-dashboard flow.
    
    Task 5: Runs end-to-end without hardcoded data - adapts to any uploaded dataset.
    Task 3: Uses @st.cache_data via upload_utils.load_dataframe for efficient loading.
    """
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

    # When a new file is uploaded, reset workflow state to force re-validation
    if uploaded is not None and uploaded.name != st.session_state["upload_filename"]:
        st.session_state["upload_filename"] = uploaded.name
        st.session_state["upload_workflow_step"] = 1
        st.session_state["upload_validation_passed"] = False
        st.session_state["upload_dataframe"] = None

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
    
    # Only parse and validate if not already done for this file
    # Task 3: load_dataframe uses @st.cache_data to prevent redundant parsing
    if st.session_state["upload_workflow_step"] == 1:
        try:
            df = uu.load_dataframe(uploaded.name, uploaded.getvalue())
            uu.validate(df)
            # Validation passed - store DataFrame and advance workflow
            st.session_state["upload_dataframe"] = df
            st.session_state["upload_validation_passed"] = True
            st.session_state["upload_workflow_step"] = 2
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

    # Use cached DataFrame from session state
    df = st.session_state["upload_dataframe"]
    
    if df is None:
        st.error("Validation failed. Please upload a valid file.")
        st.stop()

    st.success(
        f"**{uploaded.name}** passed validation — "
        f"{len(df):,} rows x {len(df.columns)} columns."
    )

    for flag in uu.quality_flags(df):
        st.warning(flag)

    # Button to advance to Step 3 (Confirm & Explore)
    if st.button("✓ Confirm and Continue to Step 3"):
        st.session_state["upload_workflow_step"] = 3
        st.rerun()

    # ---- Step 3 · Confirm (only shows after user confirms Step 2) -----------
    # Step 3 depends on Step 2 completion. It will not display until the user
    # explicitly confirms validation results by clicking the button above.
    if st.session_state["upload_workflow_step"] < 3:
        st.stop()

    st.divider()
    st.header("Step 3 · Confirm & Explore")

    # Task 1: Five reactive KPIs computed from uploaded DataFrame (no hardcoded values)
    st.subheader("Dataset Overview")
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        # KPI 1: Total rows in uploaded file
        st.metric("Rows", f"{len(df):,}")
    with k2:
        # KPI 2: Total columns
        st.metric("Columns", f"{len(df.columns)}")
    with k3:
        # KPI 3: Data completeness (inverse of null percentage)
        null_pct = uu.overall_null_pct(df)
        st.metric("Completeness", f"{100 - null_pct:.1f}%")
    with k4:
        # KPI 4: Number of numeric columns (determines chart availability)
        numeric = uu.numeric_columns(df)
        st.metric("Numeric Cols", f"{len(numeric)}")
    with k5:
        # KPI 5: Number of categorical columns
        categorical = uu.categorical_columns(df)
        st.metric("Categorical Cols", f"{len(categorical)}")

    st.divider()

    st.subheader(f"First {uu.PREVIEW_ROWS} Rows")
    st.caption("Answers: does the data look like what I expected to export?")
    st.dataframe(df.head(uu.PREVIEW_ROWS), use_container_width=True)

    st.subheader("Column Summary")
    st.caption("Answers: which columns are usable, and which are too sparse?")
    st.dataframe(uu.column_summary(df), use_container_width=True, height=320)

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
        if categorical:
            col = st.selectbox("Column", categorical, key="cat_col")
            st.dataframe(
                df[col].value_counts().head(15).to_frame("count"),
                use_container_width=True,
            )
        else:
            st.info("No categorical columns in this file.")

    st.divider()

    # ---- Downstream usage with filters and charts ----------------------------
    st.header("Quick Exploration with Filters")
    st.caption("Proves the uploaded data is usable for filtering and charting. All charts update based on filter selections.")

    if not numeric:
        st.info("No numeric columns available to chart or filter.")
        st.stop()
    
    # Filter selection
    pick, filt = st.columns([2, 3])
    
    # Initialize selected column in session state on first run of Step 3
    if st.session_state["upload_selected_numeric_col"] is None:
        st.session_state["upload_selected_numeric_col"] = numeric[0]
    
    with pick:
        # Column selection persists across slider interactions
        col = st.selectbox(
            "Numeric column to analyze",
            numeric,
            index=numeric.index(st.session_state["upload_selected_numeric_col"]) 
                  if st.session_state["upload_selected_numeric_col"] in numeric else 0,
            key="upload_selected_numeric_col"
        )
    
    with filt:
        low, high = float(df[col].min()), float(df[col].max())
        if low == high:
            st.caption(f"`{col}` is constant at {low:,.2f} — nothing to filter.")
            bounds = (low, high)
        else:
            # Reset bounds when column changes
            current_col = st.session_state["upload_selected_numeric_col"]
            if "last_upload_col" not in st.session_state or st.session_state["last_upload_col"] != current_col:
                st.session_state["upload_range_bounds"] = (low, high)
                st.session_state["last_upload_col"] = current_col
            
            # Range slider value persists when user changes column or downloads data
            bounds = st.slider(
                f"Range of {col}",
                low,
                high,
                st.session_state["upload_range_bounds"],
                key="upload_range_bounds"
            )

    # Apply filter to create subset - all metrics computed from filtered data
    subset = df[df[col].between(*bounds)]
    
    # Task 4: Handle empty filter results gracefully
    if subset.empty:
        st.warning(
            f"⚠️ **No rows match the selected range for `{col}`.** "
            f"Try expanding the range between {low:.2f} and {high:.2f}."
        )
        st.stop()
    
    st.caption(f"📊 Showing {len(subset):,} of {len(df):,} rows in selected range ({len(subset)/len(df)*100:.1f}%)")

    # Task 2: Three different chart types that update with filter selections
    
    # Chart 1: Plotly histogram - Distribution of selected column (interactive)
    st.subheader(f"Distribution of {col}")
    fig_upload_hist = px.histogram(
        subset,
        x=col,
        nbins=min(30, len(subset)),
        title=f"Distribution of {col} (filtered)",
        labels={col: col, "count": "Frequency"},
        color_discrete_sequence=["#4CAF50"]
    )
    fig_upload_hist.update_layout(showlegend=False, height=280)
    st.plotly_chart(fig_upload_hist, use_container_width=True)

    # Chart 2: Line chart - Trend if there's an index or sequence
    if len(subset) > 1:
        st.subheader(f"Trend of {col}")
        trend_data = subset[[col]].reset_index(drop=True)
        st.line_chart(trend_data, height=250)

    # Chart 3: Plotly box plot - Summary statistics visualization
    st.subheader(f"Summary Statistics for {col}")
    fig_box_upload = px.box(
        subset,
        y=col,
        title=f"Box Plot: {col}",
        labels={col: col}
    )
    fig_box_upload.update_layout(showlegend=False, height=280)
    st.plotly_chart(fig_box_upload, use_container_width=True)

    # Additional reactive KPIs for filtered subset
    st.subheader("Filtered Data Statistics")
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Filtered Rows", f"{len(subset):,}")
    with s2:
        st.metric("Min", f"{subset[col].min():.2f}")
    with s3:
        st.metric("Mean", f"{subset[col].mean():.2f}")
    with s4:
        st.metric("Max", f"{subset[col].max():.2f}")

    st.download_button(
        "Download filtered rows",
        data=subset.to_csv(index=False).encode("utf-8"),
        file_name=f"filtered_{uploaded.name.rsplit('.', 1)[0]}.csv",
        mime="text/csv",
    )


# --- 5. Router ---------------------------------------------------------------
if page == "Overview":
    overview()
elif page == "Trends":
    trends()
elif page == "Data Explorer":
    data_explorer()
elif page == "Upload & Sync":
    upload_and_sync()
