"""
Navigation shell. Filters render first; the resulting `active_filters` dict
is then passed into sharing_renderer so PR19's quick-share respects them.
"""

import streamlit as st

NAV_ITEMS = [
    ("Overview", "🏠"),
    ("KPI Dashboard", "📊"),
    ("Insights & Narrative", "💡"),
    ("At-Risk & Branch Risk", "⚠️"),
    ("Activation Deep-Dive", "🚀"),
    ("Share & Export", "📤"),
]


def render_sidebar(filters_renderer=None, sharing_renderer=None):
    with st.sidebar:
        st.markdown("## 🏋️ StreakForge")
        st.caption("Fitness Engagement & Retention Insight Platform")

        if "nav_page" not in st.session_state:
            st.session_state.nav_page = NAV_ITEMS[0][0]

        page = st.radio(
            "Navigate",
            options=[label for label, _ in NAV_ITEMS],
            format_func=lambda label: f"{dict(NAV_ITEMS)[label]}  {label}",
            key="nav_page",
            label_visibility="collapsed",
        )

        st.divider()

        active_filters = {}
        if sharing_renderer is not None:
            sharing_renderer(active_filters)

        st.divider()
        st.caption("Pipeline AS_OF_DATE: **2026-08-14**")
        st.caption("Data-realistic as-of: **2025-10-05**")

    return page, active_filters