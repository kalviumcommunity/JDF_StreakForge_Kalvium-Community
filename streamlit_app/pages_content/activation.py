import plotly.express as px
import streamlit as st

from components.theme import apply_streakforge_theme


def render(data, filters):
    st.title("🚀 Activation Deep-Dive")

    trend = data["activation_cohort_trend"]
    segments = data["activation_segment_comparison"]

    if not trend.empty:
        month_col = "join_month" if "join_month" in trend.columns else trend.columns[0]
        rate_col = "activation_rate" if "activation_rate" in trend.columns else trend.columns[-1]

        months = trend[month_col].astype(str).tolist()
        start_m, end_m = st.select_slider(
            "Cohort month range", options=months, value=(months[0], months[-1])
        )
        view = trend[(trend[month_col].astype(str) >= start_m) & (trend[month_col].astype(str) <= end_m)]

        fig = px.line(view, x=month_col, y=rate_col, markers=True)
        fig.update_traces(line_color="#2980B9")
        apply_streakforge_theme(
            fig, "7-Day Activation Rate — Monthly Signup Cohort Trend",
            "14.6% (late 2024) → 36.6% (Sep 2025) — activation is improving on its own (INS-03)",
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("`activation_cohort_trend.csv` not found.")

    st.divider()
    if not segments.empty:
        seg_col = st.selectbox(
            "Segment column",
            sorted(segments["segment_col"].unique().tolist()) if "segment_col" in segments.columns else [],
        )
        min_members = st.slider("Minimum members per segment level", 0,
                                 int(segments["members"].max()) if "members" in segments.columns else 100, 0)

        view = segments[segments["segment_col"] == seg_col] if seg_col else segments
        if "members" in view.columns:
            view = view[view["members"] >= min_members]

        fig2 = px.bar(view.sort_values("activation_rate"), x="activation_rate", y="segment_level", orientation="h",
                       color_discrete_sequence=["#2980B9"])
        cramers_v = view["cramers_v"].iloc[0] if "cramers_v" in view.columns and len(view) else None
        subtitle = f"Cramér's V = {cramers_v:.3f} — near-zero across all tested segments (INS-02)" if cramers_v is not None else ""
        apply_streakforge_theme(fig2, f"Activation Rate by {seg_col}", subtitle, height=380)
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(view, use_container_width=True, hide_index=True)
    else:
        st.warning("`activation_segment_comparison.csv` not found.")