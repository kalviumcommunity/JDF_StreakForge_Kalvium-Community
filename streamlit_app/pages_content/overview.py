import plotly.express as px
import streamlit as st

from components.filters import apply_member_filters, active_filter_count
from components.health import render_health_badge
from components.theme import apply_streakforge_theme, SEGMENT_COLORS


def render(data, filters, health=None):
    st.title("StreakForge — Retention Insight Platform")
    st.caption("Indian gym-chain engagement, retention, streak & activation analytics")

    if health is not None:
        render_health_badge(health)

    kpi_df = data["kpi_summary"]
    member_df = data["member_behaviour"]

    if kpi_df.empty:
        st.info("KPI summary not loaded yet.")
        return

    st.markdown(
        f"""<div class="streakforge-context-note">
        ⚠️ <b>AS_OF_DATE duality:</b> the pipeline cutoff (<code>2026-08-14</code>) sits well
        past the dataset's real last event (<code>2025-10-05</code>), inflating headline churn
        to 94.0% vs. a data-realistic 84.0%. Both figures are shown throughout this app —
        see INS-01.</div>""",
        unsafe_allow_html=True,
    )

    st.subheader("Official KPIs (full population, notebook-computed)")
    headline_ids = ["kpi_01", "kpi_15", "kpi_04", "kpi_03"]
    id_col = "kpi_id" if "kpi_id" in kpi_df.columns else kpi_df.columns[0]
    headline = kpi_df[kpi_df[id_col].isin(headline_ids)]
    cols = st.columns(4)
    for i, (_, row) in enumerate(headline.iterrows()):
        with cols[i % 4]:
            st.metric(row.get("kpi_name", row[id_col]), row.get("value_display", row.get("value")),
                      help=row.get("context_note") if "context_note" in row else None)

    st.divider()

    n_active = active_filter_count(filters)
    st.subheader(f"Filtered snapshot{' — ' + str(n_active) + ' filter(s) active' if n_active else ' (no filters applied)'}")

    if not member_df.empty:
        filtered = apply_member_filters(member_df, filters)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Members in selection", f"{len(filtered):,}", delta=f"{len(filtered) - len(member_df):,} vs. full")
        if "is_churned" in filtered.columns and len(filtered):
            c2.metric("Churn rate (selection)", f"{filtered['is_churned'].mean():.1%}")
        if "avg_streak_length_days" in filtered.columns and len(filtered):
            c3.metric("Avg streak length", f"{filtered['avg_streak_length_days'].mean():.1f} days")
        if "monetary_total_paid" in filtered.columns and len(filtered):
            c4.metric("Median spend", f"₹{filtered['monetary_total_paid'].median():,.0f}")
        st.caption("Live aggregates over the current filter selection — not a replacement for the 15 official KPIs above.")

        if "behavioural_segment" in filtered.columns and len(filtered):
            st.divider()
            st.subheader("Behavioural segment mix (RFM-based, PR10)")
            seg_counts = filtered["behavioural_segment"].value_counts(normalize=True).rename("share").reset_index()
            seg_counts.columns = ["behavioural_segment", "share"]
            fig = px.pie(seg_counts, names="behavioural_segment", values="share", hole=0.45,
                         color="behavioural_segment", color_discrete_map=SEGMENT_COLORS)
            apply_streakforge_theme(fig, "Behavioural Segment Mix (current selection)", height=360)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Project story, in one line")
    st.write(
        "~17,500 members and a 94% headline churn look like a crisis — but the real, "
        "actionable leak is **activation**: 81.2% of members never engage within their "
        "first 7 days, and it isn't explained by channel, branch, or demographics. "
        "Activation is already improving on its own (14.6% → 36.6% over the last year)."
    )