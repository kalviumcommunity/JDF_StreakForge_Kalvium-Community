"""
StreakForge — shared visual theme. PR20 adds a light/dark toggle; the brand
accent palette stays fixed (matches notebook 06's BRAND dict) so charts read
consistently in both modes — only backgrounds/text invert.
"""

BRAND = {
    "primary": "#2C3E50",
    "accent": "#2980B9",
    "positive": "#27AE60",
    "warning": "#F39C12",
    "high_risk": "#C0392B",
    "muted": "#7F8C8D",
    "background": "#F7F9FA",
}

CARD_COLOR_MAP = {
    "green": BRAND["positive"], "red": BRAND["high_risk"], "amber": BRAND["warning"],
    "blue": BRAND["accent"], "grey": BRAND["muted"],
}

# KPI category → accent colour, following PR14's category mapping
# (Retention→orange, Acquisition & Activation→blue, Revenue→amber,
#  Engagement→green, Product / Streak Health→grey). Used as card accents only,
# never as text colour, so amber stays legible on white.
CATEGORY_COLORS = {
    "Retention": "#D95F02",
    "Acquisition & Activation": BRAND["accent"],
    "Revenue": BRAND["warning"],
    "Engagement": BRAND["positive"],
    "Product / Streak Health": BRAND["muted"],
}

RISK_TIER_COLORS = {"Low": BRAND["positive"], "Moderate": BRAND["warning"],
                     "Elevated": "#E67E22", "High": BRAND["high_risk"]}

SEGMENT_COLORS = {"Champions": BRAND["positive"], "Loyal / Engaged": BRAND["accent"],
                   "At Risk": BRAND["warning"], "Dormant / Lapsed": BRAND["high_risk"]}

_DARK_VARS = {"--sf-bg": "#111827", "--sf-card-bg": "#1F2937", "--sf-border": "#374151",
              "--sf-text": "#F3F4F6", "--sf-plot-bg": "#1A2233"}
_LIGHT_VARS = {"--sf-bg": "#F7F9FA", "--sf-card-bg": "#FFFFFF", "--sf-border": "#E5E8E8",
               "--sf-text": "#2C3E50", "--sf-plot-bg": "#F7F9FA"}


def apply_streakforge_theme(fig, title: str, subtitle: str = "", height: int = 420, dark: bool = False):
    full_title = f"<b>{title}</b>"
    if subtitle:
        full_title += f"<br><span style='font-size:11px;color:{BRAND['muted']}'>{subtitle}</span>"
    plot_bg = _DARK_VARS["--sf-plot-bg"] if dark else _LIGHT_VARS["--sf-plot-bg"]
    paper_bg = _DARK_VARS["--sf-card-bg"] if dark else "white"
    font_color = _DARK_VARS["--sf-text"] if dark else BRAND["primary"]
    fig.update_layout(
        title={"text": full_title, "x": 0.02, "xanchor": "left"},
        height=height, margin=dict(l=40, r=30, t=70, b=40),
        plot_bgcolor=plot_bg, paper_bgcolor=paper_bg,
        font=dict(family="Segoe UI, Arial", color=font_color, size=12),
        hoverlabel=dict(bgcolor="white" if not dark else "#1F2937"),
    )
    grid_color = "#374151" if dark else "#E5E8E8"
    fig.update_xaxes(gridcolor=grid_color, zeroline=False)
    fig.update_yaxes(gridcolor=grid_color, zeroline=False)
    return fig


def inject_css(st, dark: bool = False):
    import pathlib
    css_vars = _DARK_VARS if dark else _LIGHT_VARS
    vars_css = "\n".join(f"{k}: {v};" for k, v in css_vars.items())

    css_path = pathlib.Path(__file__).resolve().parent.parent / "assets" / "style.css"
    base_css = css_path.read_text() if css_path.exists() else ""

    st.markdown(
        f"""<style>
        :root {{ {vars_css} }}
        .stApp {{ background-color: var(--sf-bg); color: var(--sf-text); }}
        div[data-testid="stMetric"] {{
            background: var(--sf-card-bg); border: 1px solid var(--sf-border);
            border-radius: 10px; padding: 14px 16px;
        }}
        section[data-testid="stSidebar"] {{ background-color: var(--sf-card-bg); }}
        {base_css}
        </style>""",
        unsafe_allow_html=True,
    )


def render_theme_toggle(st):
    mode = st.radio("Appearance", ["Light", "Dark"], horizontal=True, key="theme_mode")
    return mode == "Dark"