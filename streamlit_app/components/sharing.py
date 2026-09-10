"""
PR19 — Insight sharing & email report integration.

Builds shareable artefacts from already-computed processed data
(kpi_summary.csv, insight_narrative.csv, reports/insight_summary.md) and the
current dashboard filter selection. No KPI/insight logic is re-derived here —
this module only formats and transmits what notebooks 05/06 already produced.
"""

import io
import smtplib
import zipfile
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
import streamlit as st

from components.filters import apply_member_filters, active_filter_count

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


# ── Report assembly ──────────────────────────────────────────────────────

def _filter_summary_text(filters: dict) -> str:
    return "Full member population (no segmentation applied)."
    # if not filters or not active_filter_count(filters):
    #     return "No filters applied — full population."
    # parts = []
    # label_map = {
    #     "cities_tier": "City tier", "membership_types": "Membership type",
    #     "signup_channels": "Signup channel", "behavioural_segments": "Behavioural segment",
    #     "gym_branches": "Branch", "risk_tiers": "Risk tier",
    # }
    # for key, label in label_map.items():
    #     vals = filters.get(key)
    #     if vals:
    #         parts.append(f"{label}: {', '.join(map(str, vals))}")
    # if filters.get("join_date_range"):
    #     parts.append(f"Join date: {filters['join_date_range']}")
    # if filters.get("member_search"):
    #     parts.append(f"Member search: '{filters['member_search']}'")
    # return "; ".join(parts) if parts else "No filters applied — full population."


def generate_markdown_report(data: dict, filters: dict) -> str:
    kpi_df = data.get("kpi_summary", pd.DataFrame())
    narrative_df = data.get("insight_narrative", pd.DataFrame())
    member_df = data.get("member_behaviour", pd.DataFrame())

    lines = [
        "# StreakForge — Shared Insight Report",
        "",
        f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · Pipeline AS_OF_DATE 2026-08-14 "
        f"(data-realistic as-of 2025-10-05)_",
        "",
        f"**Scope:** {_filter_summary_text(filters)}",
        "",
        "## Core KPIs (official, full population)",
        "",
        "| KPI | Category | Value | Unit |",
        "|---|---|---|---|",
    ]
    for _, r in kpi_df.iterrows():
        lines.append(f"| {r.get('kpi_name','')} | {r.get('category','')} | "
                     f"{r.get('value_display', r.get('value',''))} | {r.get('unit','')} |")

    if not member_df.empty and active_filter_count(filters):
        filtered = apply_member_filters(member_df, filters)
        lines += ["", "## Filtered Selection Snapshot", "",
                  f"- Members in selection: **{len(filtered):,}** (of {len(member_df):,} total)"]
        if "is_churned" in filtered.columns and len(filtered):
            lines.append(f"- Churn rate (selection): **{filtered['is_churned'].mean():.1%}**")
        if "monetary_total_paid" in filtered.columns and len(filtered):
            lines.append(f"- Median spend (selection): **₹{filtered['monetary_total_paid'].median():,.0f}**")

    lines += ["", "## Key Insights", ""]
    for _, r in narrative_df.iterrows():
        lines += [
            f"### {r.get('insight_id','')} — {r.get('headline','')}", "",
            str(r.get("narrative", "")), "",
            f"**Evidence:** {r.get('supporting_evidence','')}  ",
            f"**Business impact:** {r.get('business_impact','')}  ",
            f"**Audience:** {r.get('audience','')}  ",
            f"**Recommended action:** {r.get('recommended_action','')}  ",
            f"**Confidence:** {r.get('confidence','')}", "",
        ]
    return "\n".join(lines)


def generate_csv_bundle(data: dict, filters: dict) -> bytes:
    """Zips the current filtered member view alongside the official KPI/insight CSVs."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        kpi_df = data.get("kpi_summary", pd.DataFrame())
        if not kpi_df.empty:
            zf.writestr("kpi_summary.csv", kpi_df.to_csv(index=False))

        narrative_df = data.get("insight_narrative", pd.DataFrame())
        if not narrative_df.empty:
            zf.writestr("insight_narrative.csv", narrative_df.to_csv(index=False))

        member_df = data.get("member_behaviour", pd.DataFrame())
        if not member_df.empty:
            filtered = apply_member_filters(member_df, filters) if active_filter_count(filters) else member_df
            zf.writestr("filtered_member_selection.csv", filtered.to_csv(index=False))

        at_risk = data.get("at_risk_members", pd.DataFrame())
        if not at_risk.empty:
            zf.writestr("at_risk_members.csv", at_risk.to_csv(index=False))

        zf.writestr("filter_context.txt", _filter_summary_text(filters))
    buf.seek(0)
    return buf.getvalue()


def generate_pdf_report(data: dict, filters: dict) -> bytes | None:
    if not FPDF_AVAILABLE:
        return None

    kpi_df = data.get("kpi_summary", pd.DataFrame())
    narrative_df = data.get("insight_narrative", pd.DataFrame())

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "StreakForge - Shared Insight Report", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
                          f"Pipeline AS_OF_DATE 2026-08-14 (data-realistic as-of 2025-10-05)\n"
                          f"Filters: {_filter_summary_text(filters)}")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Core KPIs", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for _, r in kpi_df.iterrows():
        val = r.get("value_display", r.get("value", ""))
        pdf.cell(0, 6, f"- {r.get('kpi_name','')}: {val} ({r.get('category','')})", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Key Insights", ln=True)
    for _, r in narrative_df.iterrows():
        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(0, 6, f"{r.get('insight_id','')} - {r.get('headline','')}")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, str(r.get("narrative", "")))
        pdf.set_font("Helvetica", "I", 8)
        pdf.multi_cell(0, 5, f"Audience: {r.get('audience','')} | Confidence: {r.get('confidence','')} | "
                              f"Action: {r.get('recommended_action','')}")
        pdf.ln(2)

    return bytes(pdf.output(dest="S"))


# ── Email delivery ───────────────────────────────────────────────────────

def _smtp_configured() -> bool:
    """`st.secrets` parses lazily, so a missing secrets.toml raises on first
    access rather than returning empty. Membership test must be guarded."""
    try:
        return "smtp" in st.secrets
    except Exception:
        return False


def send_email_report(recipient: str, subject: str, body_markdown: str,
                       attachment_bytes: bytes | None, attachment_name: str) -> tuple[bool, str]:
    if not _smtp_configured():
        return False, "SMTP is not configured. Add credentials to .streamlit/secrets.toml (see secrets_template.toml)."

    cfg = st.secrets["smtp"]
    try:
        msg = MIMEMultipart()
        msg["From"] = f"{cfg.get('sender_name', 'StreakForge')} <{cfg['username']}>"
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body_markdown, "plain"))

        if attachment_bytes:
            part = MIMEApplication(attachment_bytes, Name=attachment_name)
            part["Content-Disposition"] = f'attachment; filename="{attachment_name}"'
            msg.attach(part)

        with smtplib.SMTP(cfg["host"], int(cfg["port"])) as server:
            server.starttls()
            server.login(cfg["username"], cfg["password"])
            server.sendmail(cfg["username"], recipient, msg.as_string())

        return True, f"Report sent to {recipient}."
    except Exception as e:
        return False, f"Email send failed: {e}"


# ── Sidebar quick-share widget (compact, used on every page) ────────────

def render_sidebar_quick_share(data: dict, filters: dict):
    st.markdown("### 📤 Quick Share")
    md_report = generate_markdown_report(data, filters)
    st.download_button(
        "Download report (.md)", data=md_report,
        file_name="streakforge_insight_report.md", mime="text/markdown",
        use_container_width=True,
    )
    st.caption("Full export & email options → **Share & Export** page")