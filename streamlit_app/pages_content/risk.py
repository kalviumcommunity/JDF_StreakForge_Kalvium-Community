import plotly.express as px
import streamlit as st

from components.theme import apply_streakforge_theme
from components.filters import (
    apply_member_filters, apply_risk_tier_filter, filtered_branch_ids, active_filter_count,
)


def render(data, filters):
    st.title("⚠️ At-Risk Cohort & Branch Risk")

    at_risk = data["at_risk_members"]
    branch_risk = data["branch_risk_summary"]
    member_df = data["member_behaviour"]

    branch_scope = None
    if active_filter_count(filters) and not member_df.empty:
        filtered_members = apply_member_filters(member_df, filters)
        branch_scope = filtered_branch_ids(filtered_members)
        st.caption(f"Cascading current filters → {len(branch_scope) if branch_scope else 'all'} branch(es) in scope")

    tab1, tab2 = st.tabs(["At-Risk Members", "Branch Risk"])

    with tab1:
        if at_risk.empty:
            st.warning("`at_risk_members.csv` not found.")
        else:
            view = apply_risk_tier_filter(at_risk, filters)
            if branch_scope and "gym_branch_id" in view.columns:
                view = view[view["gym_branch_id"].isin(branch_scope)]

            st.caption(f"{len(view)} currently-active member(s) in view (INS-05 baseline: 12 'High'-risk)")
            st.dataframe(view, use_container_width=True)

            signal_cols = [c for c in ["risk_high_recency", "risk_low_frequency",
                                        "risk_negative_trend", "risk_paying_not_showing"]
                           if c in view.columns]
            if signal_cols and len(view):
                signal_mix = view[signal_cols].sum().rename("members_with_signal").reset_index()
                signal_mix.columns = ["risk_signal", "members_with_signal"]
                fig = px.bar(signal_mix, x="risk_signal", y="members_with_signal",
                             text="members_with_signal", color_discrete_sequence=["#C0392B"])
                apply_streakforge_theme(fig, "Composite Risk Signal Mix", height=380)
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if branch_risk.empty:
            st.warning("`branch_risk_summary.csv` not found.")
        else:
            view = branch_risk[branch_risk["gym_branch_id"].isin(branch_scope)] if branch_scope else branch_risk
            n_outliers = int(view.get("is_churn_outlier", view.iloc[:, :0]).sum()) \
                if "is_churn_outlier" in view.columns else 0
            st.caption(f"{n_outliers} of {len(view)} branch(es) in view flagged as churn-rate outliers")

            min_activation, max_activation = 0.0, 1.0
            if "activation_rate" in view.columns and len(view):
                min_activation, max_activation = float(view["activation_rate"].min()), float(view["activation_rate"].max())
            act_threshold = st.slider(
                "Highlight branches with activation rate below", 0.0, 1.0,
                value=round(min_activation, 2), step=0.01, format="%.0f%%",
            )

            sort_col = "churn_rate" if "churn_rate" in view.columns else view.columns[1]
            plot_df = view.sort_values(sort_col).copy()
            if "activation_rate" in plot_df.columns:
                plot_df["below_threshold"] = plot_df["activation_rate"] < act_threshold
                color_col, color_map = "below_threshold", {True: "#E67E22", False: "#4C72B0"}
            else:
                color_col, color_map = None, None

            fig = px.bar(plot_df, x=sort_col, y="gym_branch_id", orientation="h",
                         color=color_col, color_discrete_map=color_map)
            apply_streakforge_theme(fig, "Churn Rate by Branch",
                                     f"Orange = activation rate below {act_threshold:.0%}", height=700)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(view, use_container_width=True, hide_index=True)