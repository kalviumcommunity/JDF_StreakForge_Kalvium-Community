"""
KPI Dashboard — official, notebook-computed KPIs from kpi_summary.csv.

Layout fix: the 15 KPIs used to render as a single Plotly Indicator subplot
grid. Plotly positions indicator titles *above* each subplot domain without
reserving space for them, so the first row collided with the figure subtitle
and every row carried dead space under the number. The cards are now native
HTML in a responsive CSS grid, grouped by category, so spacing is handled by
the browser and follows the light/dark CSS variables from theme.inject_css.

Display-only: values are formatted with the same per-unit rules as PR14's
format_kpi_value(); no KPI logic is recomputed here.
"""

import html

import pandas as pd
import streamlit as st

from components.theme import CARD_COLOR_MAP, CATEGORY_COLORS, BRAND
from components.filters import apply_member_filters, active_filter_count


def _format_kpi_value(value, unit) -> str:
    """Mirrors PR14 format_kpi_value(): one formatting rule per unit type."""
    if pd.isna(value):
        return "—"
    v = float(value)
    if unit == "%":
        return f"{v:.1%}"
    if unit == "INR":
        return f"₹{v:,.0f}"
    if unit == "INR/session":
        return f"₹{v:,.0f}"
    if unit == "count":
        return f"{v:,.0f}"
    if unit == "days":
        return f"{v:.1f}"
    if unit in ("sessions/wk", "CV"):
        return f"{v:.2f}"
    return f"{v:,.2f}"


# Unit shown under the value in plain words (kept neutral — the unit column
# says "%", not "% of members", so the label doesn't claim more than the data does).
_UNIT_LABEL = {
    "%": "percent",
    "INR": "rupees",
    "INR/session": "rupees per session",
    "count": "count",
    "days": "days",
    "sessions/wk": "sessions per week",
    "CV": "coefficient of variation",
}


def _display_value(row) -> str:
    # Prefer the PR14 pre-formatted string when the loaded CSV carries it.
    shown = row.get("value_display")
    if isinstance(shown, str) and shown.strip():
        return shown
    return _format_kpi_value(row.get("value"), row.get("unit"))


def _accent(row) -> str:
    raw = row.get("card_color")
    if isinstance(raw, str) and raw.startswith("#"):
        return raw
    if isinstance(raw, str) and raw in CARD_COLOR_MAP:
        return CARD_COLOR_MAP[raw]
    return CATEGORY_COLORS.get(row.get("category"), BRAND["muted"])


def _card_html(row) -> str:
    name = html.escape(str(row.get("kpi_name", row.get("kpi_id", ""))))
    value = html.escape(_display_value(row))
    unit = row.get("unit", "")
    unit_label = html.escape(_UNIT_LABEL.get(unit, str(unit)))
    definition = row.get("definition")
    tooltip = f' title="{html.escape(str(definition))}"' if isinstance(definition, str) else ""

    note = row.get("context_note")
    note_html = (f'<div class="sf-kpi-note">{html.escape(note)}</div>'
                 if isinstance(note, str) and note.strip() else "")

    # Single line, no indentation: st.markdown treats 4-space indents as code blocks.
    return (f'<div class="sf-kpi-card" style="--sf-accent:{_accent(row)}"{tooltip}>'
            f'<div class="sf-kpi-name">{name}</div>'
            f'<div class="sf-kpi-value">{value}</div>'
            f'<div class="sf-kpi-unit">{unit_label}</div>'
            f'{note_html}</div>')


def _render_category(category: str, rows: pd.DataFrame):
    accent = CATEGORY_COLORS.get(category, BRAND["muted"])
    count = len(rows)
    header = (f'<div class="sf-kpi-group-head" style="--sf-accent:{accent}">'
              f'<span class="sf-kpi-group-name">{html.escape(category)}</span>'
              f'<span class="sf-kpi-group-count">{count} metric{"s" if count != 1 else ""}</span></div>')
    cards = "".join(_card_html(r) for _, r in rows.iterrows())
    st.markdown(f'<section class="sf-kpi-group">{header}<div class="sf-kpi-grid">{cards}</div></section>',
                unsafe_allow_html=True)


def render(data, filters):
    st.title("📊 KPI Dashboard")
    kpi_df = data["kpi_summary"]
    member_df = data["member_behaviour"]
    if kpi_df.empty:
        st.warning("`kpi_summary.csv` not found.")
        return

    # Category order follows the notebook's KPI order (Retention first), not alphabetical.
    category_order = kpi_df["category"].dropna().unique().tolist()
    cat = st.selectbox("Filter by category", ["All"] + category_order)
    view = kpi_df if cat == "All" else kpi_df[kpi_df["category"] == cat]

    st.subheader("StreakForge KPI summary (official, full population)")
    scope = "across all categories" if cat == "All" else f"in {cat}"
    st.caption(f"Showing {len(view)} metric{'s' if len(view) != 1 else ''} {scope}. "
               "Hover a card to see how the metric is defined.")

    for category in [c for c in category_order if c in set(view["category"])]:
        _render_category(category, view[view["category"] == category])

    with st.expander("Full KPI table"):
        table = view.copy()
        if "value_display" not in table.columns:
            table.insert(table.columns.get_loc("value") + 1, "value_display",
                         table.apply(_display_value, axis=1))
        st.dataframe(table, use_container_width=True, hide_index=True)

    if active_filter_count(filters) and not member_df.empty:
        st.divider()
        st.subheader("Recompute a subset of metrics on your filter selection")
        filtered = apply_member_filters(member_df, filters)
        cc = st.columns(3)
        if "is_churned" in filtered.columns and len(filtered):
            cc[0].metric("Churn rate (selection)", f"{filtered['is_churned'].mean():.1%}",
                         help="Simple aggregate over the current filter — not the official pipeline-defined KPI.")
        if "recency_days" in filtered.columns and len(filtered):
            cc[1].metric("Median recency (days)", f"{filtered['recency_days'].median():.0f}")
        if "frequency_total_events" in filtered.columns and len(filtered):
            cc[2].metric("Median event frequency", f"{filtered['frequency_total_events'].median():.0f}")