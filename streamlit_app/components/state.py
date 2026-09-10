"""
PR20 — Centralised session-state bootstrapping and small state helpers,
so app.py and pages don't repeat st.session_state.setdefault(...) calls.
"""

import streamlit as st

DEFAULT_STATE = {
    "theme_mode": "Light",
    "last_error": None,
    "data_loaded_at": None,
}


def bootstrap_state():
    for key, default in DEFAULT_STATE.items():
        st.session_state.setdefault(key, default)


def set_last_error(message: str | None):
    st.session_state["last_error"] = message


def toast_once(message: str, icon: str = "✅", state_key: str = "toast_shown"):
    """Fires a toast at most once per session for a given key (e.g. on first
    successful data load), instead of re-toasting on every rerun."""
    if not st.session_state.get(state_key):
        st.toast(message, icon=icon)
        st.session_state[state_key] = True