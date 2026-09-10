import streamlit as st

from components.sharing import (
    generate_markdown_report, generate_csv_bundle, generate_pdf_report,
    send_email_report, FPDF_AVAILABLE, _smtp_configured,
)

# Email delivery is parked for now. The SMTP backend in components/sharing.py
# is kept intact — flip this to True to restore the original email form.
EMAIL_EXPORT_ENABLED = False

# PDF export is parked for now. generate_pdf_report() in components/sharing.py
# is kept intact — flip this to True to restore the PDF download button.
PDF_EXPORT_ENABLED = False
PDF_READY = PDF_EXPORT_ENABLED and FPDF_AVAILABLE


def _render_email_under_development():
    with st.container(border=True):
        st.markdown("### 🚧 Under development")
        st.markdown(
            "Emailing the insight report straight from the dashboard is planned, "
            "but it isn't enabled in this version of StreakForge."
        )
        st.caption(
            "In the meantime, use the **Download** tab to export the Markdown report "
            "or CSV bundle and share it manually."
        )


def render(data, filters):
    st.title("📤 Share & Export")
    st.caption("Export the current KPI/insight view over the full member population.")

    tab_export, tab_email = st.tabs(["Download", "Email report 🚧"])

    with tab_export:
        col1, col2, col3 = st.columns(3)

        md_report = generate_markdown_report(data, filters)
        with col1:
            st.download_button(
                "⬇️ Markdown report", data=md_report,
                file_name="streakforge_insight_report.md", mime="text/markdown",
                use_container_width=True,
            )

        with col2:
            csv_bundle = generate_csv_bundle(data, filters)
            st.download_button(
                "⬇️ CSV bundle (.zip)", data=csv_bundle,
                file_name="streakforge_export_bundle.zip", mime="application/zip",
                use_container_width=True,
            )

        with col3:
            if PDF_READY:
                pdf_bytes = generate_pdf_report(data, filters)
                st.download_button(
                    "⬇️ PDF report", data=pdf_bytes,
                    file_name="streakforge_insight_report.pdf", mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.button(
                    "⬇️ PDF report 🚧", disabled=True, use_container_width=True,
                    help="PDF export is under development. Use the Markdown report or CSV bundle for now.",
                )
                st.caption("🚧 PDF export is under development.")

        st.divider()
        st.subheader("Preview")
        st.markdown(md_report)

    with tab_email:
        # Guard clause: this must remain the last block in render(), since the
        # early return skips anything that follows it.
        if not EMAIL_EXPORT_ENABLED:
            _render_email_under_development()
            return

        if not _smtp_configured():
            st.info(
                "SMTP isn't configured yet. Copy `.streamlit/secrets_template.toml` to "
                "`.streamlit/secrets.toml` and fill in your SMTP credentials "
                "(or add them under the app's Secrets manager if deployed on Streamlit Community Cloud)."
            )

        with st.form("email_form"):
            recipient = st.text_input("Recipient email")
            subject = st.text_input("Subject", value="StreakForge — Insight Report")
            attach_choice = st.radio(
                "Attachment", ["Markdown (.md)", "PDF" if FPDF_AVAILABLE else "PDF (unavailable)", "None"],
                horizontal=True,
            )
            submitted = st.form_submit_button("Send report", use_container_width=True)

        if submitted:
            if not recipient or "@" not in recipient:
                st.error("Enter a valid recipient email address.")
            else:
                md_report = generate_markdown_report(data, filters)
                attachment_bytes, attachment_name = None, ""
                if attach_choice.startswith("Markdown"):
                    attachment_bytes, attachment_name = md_report.encode("utf-8"), "streakforge_insight_report.md"
                elif attach_choice.startswith("PDF") and FPDF_AVAILABLE:
                    attachment_bytes, attachment_name = generate_pdf_report(data, filters), "streakforge_insight_report.pdf"

                with st.spinner("Sending..."):
                    ok, msg = send_email_report(recipient, subject, md_report, attachment_bytes, attachment_name)
                (st.success if ok else st.error)(msg)