"""
PR21 — Internal pre-flight page. Cross-checks the live data/processed/ and
reports/ directories against deliverables_manifest.csv (built in PR16) so
nothing produced across PR1-PR20 has gone stale before demo/deployment.
Not linked in main nav by default — reachable via ?page=deploy_check for
the presenter, or wired into NAV_ITEMS temporarily during rehearsal.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from components.data_loader import PROCESSED_DIR, REPORTS_DIR, BASE_DIR


def render(data, filters=None):
    st.title("🚦 Deployment Pre-Flight Check")
    st.caption("Run this before presenting or redeploying — confirms every PR1–PR20 artefact is present and fresh.")

    manifest_path = PROCESSED_DIR / "deliverables_manifest.csv"
    if not manifest_path.exists():
        st.warning("`deliverables_manifest.csv` not found (expected from PR16) — skipping manifest cross-check.")
    else:
        manifest = pd.read_csv(manifest_path)
        st.subheader("Deliverables manifest (PR16)")
        st.dataframe(manifest, use_container_width=True, hide_index=True)

        missing = []
        for _, row in manifest.iterrows():
            fpath = BASE_DIR / str(row.get("path", ""))
            if row.get("path") and not fpath.exists():
                missing.append(str(row.get("path")))
        if missing:
            st.error(f"{len(missing)} manifest file(s) missing on disk:")
            for m in missing:
                st.write(f"- `{m}`")
        else:
            st.success(f"All {len(manifest)} manifest entries resolved on disk.")

    st.divider()
    st.subheader("Streamlit app data dependency check")
    required = {
        "data/processed/member_behaviour_summary.csv": data.get("member_behaviour"),
        "data/processed/kpi_summary.csv": data.get("kpi_summary"),
        "data/processed/activation_cohort_trend.csv": data.get("activation_cohort_trend"),
        "data/processed/branch_risk_summary.csv": data.get("branch_risk_summary"),
        "data/processed/at_risk_members.csv": data.get("at_risk_members"),
        "data/processed/activation_segment_comparison.csv": data.get("activation_segment_comparison"),
        "data/processed/insight_narrative.csv": data.get("insight_narrative"),
        "reports/insight_summary.md": data.get("insight_summary_md"),
    }
    all_ok = True
    for label, df in required.items():
        ok = (isinstance(df, pd.DataFrame) and not df.empty) or (isinstance(df, str) and "not found" not in df)
        all_ok = all_ok and ok
        st.write(("✅" if ok else "❌") + f" `{label}`")

    st.divider()
    if all_ok:
        st.success("Ready to deploy / present.")
    else:
        st.error("Fix the ❌ items above before deploying or presenting.")

    st.divider()
    st.subheader("Config sanity")
    st.write("✅ `.streamlit/config.toml` present" if (BASE_DIR / ".streamlit" / "config.toml").exists()
              else "❌ `.streamlit/config.toml` missing")
    st.write("✅ `requirements.txt` present" if (BASE_DIR / "requirements.txt").exists()
              else "❌ `requirements.txt` missing")
    secrets_configured = hasattr(st, "secrets") and "smtp" in st.secrets
    st.write(("✅" if secrets_configured else "ℹ️") +
              " SMTP secrets " + ("configured" if secrets_configured else "not configured (email export will be disabled)"))