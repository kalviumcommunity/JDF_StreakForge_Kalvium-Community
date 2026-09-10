"""
StreakForge Streamlit App — entry point.
PR21: deployment-ready — About footer, optional pre-flight page via
?page=deploy_check (kept out of main nav so it doesn't clutter the
stakeholder-facing demo).
"""

import sys
import traceback
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent))

from components.data_loader import load_all, PROCESSED_DIR, REPORTS_DIR
from components.theme import inject_css, render_theme_toggle
from components.sidebar import render_sidebar
# from components.filters import render_filters
from components.sharing import render_sidebar_quick_share
from components.state import bootstrap_state, set_last_error, toast_once
from components.health import run_health_check, render_health_badge
from pages_content import overview, kpi_dashboard, insights, risk, activation, share, deploy_check

st.set_page_config(
    page_title="StreakForge — Retention Insight Platform",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _render_footer():
    st.divider()
    st.caption(
        "**StreakForge** — Fitness Engagement & Retention Insight Platform · "
        "Data analytics only, no predictive modelling (PRD Section 4) · "
        "Built across 21 PRs, notebooks 01–06 → `src/` → this Streamlit app."
    )


def main():
    bootstrap_state()

    # Pre-flight page: streamlit.app/?page=deploy_check
    query_page = st.query_params.get("page")

    with st.sidebar:
        with st.expander("⚙️ Appearance", expanded=False):
            dark = render_theme_toggle(st)
    inject_css(st, dark=dark)

    data = load_all()
    toast_once("Data loaded successfully", icon="📦")

    health = run_health_check(PROCESSED_DIR, REPORTS_DIR)

    if query_page == "deploy_check":
        deploy_check.render(data)
        _render_footer()
        return


    page, filters = render_sidebar(
        sharing_renderer=lambda active_filters: render_sidebar_quick_share(data, active_filters),
    )

    # page, filters = render_sidebar(
    #     # filters_renderer=lambda: render_filters(data),
    #     sharing_renderer=lambda active_filters: render_sidebar_quick_share(data, active_filters),
    # )

    router = {
        "Overview": overview.render,
        "KPI Dashboard": kpi_dashboard.render,
        "Insights & Narrative": insights.render,
        "At-Risk & Branch Risk": risk.render,
        "Activation Deep-Dive": activation.render,
        "Share & Export": share.render,
    }

    try:
        if page == "Overview":
            router[page](data, filters, health)
        else:
            router[page](data, filters)
        set_last_error(None)
    except Exception as e:
        set_last_error(str(e))
        st.error(f"Something went wrong rendering **{page}**: {e}")
        with st.expander("Technical details"):
            st.code(traceback.format_exc())
        st.info("If this persists, check the technical details above or reload the app.")

    _render_footer()


if __name__ == "__main__":
    main()