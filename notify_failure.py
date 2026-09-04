"""Notify the team when data validation fails in CI.

Reads the JSON report written by validate_data.py and emails the failed
checks over SMTP. Runs as the `if: failure()` step in
.github/workflows/validate.yml.

This script is deliberately self-contained (no imports from the app package)
so the merge gate works even before other feature branches land. It uses the
same environment variables as email_sender.py:

    SENDER_EMAIL       - SMTP login / from address
    SENDER_PASSWORD    - SMTP app password
    SMTP_SERVER        - e.g. smtp.gmail.com
    SMTP_PORT          - e.g. 587
    NOTIFY_RECIPIENTS  - comma-separated recipients (optional, defaults to
                         SENDER_EMAIL)

The script never exits non-zero itself: if credentials are missing or the
report is absent it prints a warning and exits 0 so the original validation
failure is not masked by a secondary notification error.
"""

import json
import os
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path

DEFAULT_REPORT = "validation_report.json"


# --------------------------------------------------------------- email -------
def _email_config() -> dict:
    return {
        "sender": os.environ.get("SENDER_EMAIL", "").strip(),
        "password": os.environ.get("SENDER_PASSWORD", "").strip(),
        "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com").strip(),
        "smtp_port": os.environ.get("SMTP_PORT", "587").strip(),
    }


def _recipients() -> list[str]:
    raw = os.environ.get("NOTIFY_RECIPIENTS", "").strip()
    if raw:
        return [r.strip() for r in raw.split(",") if r.strip()]
    sender = _email_config()["sender"]
    return [sender] if sender else []


def send_email(subject: str, text_body: str, html_body: str) -> bool:
    """Send a plain+HTML email. Returns True on success."""
    cfg = _email_config()
    to = _recipients()

    if not cfg["sender"] or not cfg["password"]:
        print("WARNING: SENDER_EMAIL/SENDER_PASSWORD not configured; skipping email.")
        return False
    if not to:
        print("WARNING: no recipients (NOTIFY_RECIPIENTS or SENDER_EMAIL).")
        return False

    try:
        port = int(cfg["smtp_port"])
    except ValueError:
        print(f"WARNING: invalid SMTP_PORT '{cfg['smtp_port']}'; skipping email.")
        return False

    msg = MIMEText(html_body, "html", "utf-8")
    # Keep a readable plain-text alternative for non-HTML clients.
    msg.add_alternative(MIMEText(text_body, "plain", "utf-8"))
    msg["Subject"] = subject
    msg["From"] = cfg["sender"]
    msg["To"] = ", ".join(to)

    try:
        server = smtplib.SMTP(cfg["smtp_server"], port, timeout=15)
        server.starttls()
        server.login(cfg["sender"], cfg["password"])
        server.sendmail(cfg["sender"], to, msg.as_string())
        server.quit()
        print(f"SUCCESS: failure notification emailed to {', '.join(to)}")
        return True
    except smtplib.SMTPAuthenticationError as exc:
        print(f"WARNING: SMTP authentication failed ({exc}); email not sent.")
        return False
    except Exception as exc:  # network/timeout/etc - never crash the job
        print(f"WARNING: could not send email ({type(exc).__name__}: {exc}).")
        return False


# ----------------------------------------------------------------- report ----
def load_report(report_path: Path) -> dict | None:
    if not report_path.exists():
        print(f"WARNING: report not found at {report_path}; nothing to notify.")
        return None
    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"WARNING: could not parse {report_path}: {exc}")
        return None


def github_context() -> dict:
    """Pull useful context from GitHub Actions env vars (safe locally too)."""
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    ref = os.environ.get("GITHUB_REF_NAME", os.environ.get("GITHUB_REF", ""))
    sha = os.environ.get("GITHUB_SHA", "")
    actor = os.environ.get("GITHUB_ACTOR", "")
    run_url = f"{server}/{repo}/actions/runs/{run_id}" if repo and run_id else ""
    return {"repo": repo, "ref": ref, "sha": (sha or "")[:7],
            "actor": actor, "run_url": run_url}


def build_bodies(report: dict, ctx: dict) -> tuple[str, str]:
    """Return (text_body, html_body) for the failure email."""
    summary = report.get("summary", {})
    failed_checks = [c for c in report.get("checks", []) if c.get("status") != "PASS"]

    text = (
        "StreakForge data validation FAILED\n"
        "----------------------------------\n"
        f"Repository : {ctx.get('repo') or 'local'}\n"
        f"Branch     : {ctx.get('ref') or 'n/a'}\n"
        f"Commit     : {ctx.get('sha') or 'n/a'}\n"
        f"Triggered  : {ctx.get('actor') or 'n/a'}\n"
        f"Dataset    : {report.get('dataset')}\n"
        f"Rows       : {report.get('rows')}\n"
        f"Run        : {ctx.get('run_url') or 'n/a'}\n"
        f"Summary    : {summary.get('passed', 0)} passed, "
        f"{summary.get('failed', 0)} failed\n\n"
    )
    html = (
        "<h2 style='color:#b91c1c'>StreakForge data validation FAILED</h2>"
        "<table style='font-size:14px;border-collapse:collapse'>"
        f"<tr><td><b>Repository</b></td><td>{ctx.get('repo') or 'local'}</td></tr>"
        f"<tr><td><b>Branch</b></td><td>{ctx.get('ref') or 'n/a'}</td></tr>"
        f"<tr><td><b>Commit</b></td><td>{ctx.get('sha') or 'n/a'}</td></tr>"
        f"<tr><td><b>Dataset</b></td><td>{report.get('dataset')}</td></tr>"
        f"<tr><td><b>Rows</b></td><td>{report.get('rows')}</td></tr>"
        f"<tr><td><b>Summary</b></td><td style='color:#b91c1c'>"
        f"{summary.get('passed', 0)} passed, {summary.get('failed', 0)} failed</td></tr>"
    )
    if ctx.get("run_url"):
        html += (f"<tr><td><b>Run</b></td><td><a href='{ctx['run_url']}'>"
                 f"{ctx['run_url']}</a></td></tr>")
    html += "</table><h3>Failed checks</h3>"

    if failed_checks:
        text += "Failed checks:\n"
        html += "<ul>"
        for check in failed_checks:
            for error in check.get("errors", []) or ["unknown error"]:
                text += f"  ERROR [{check.get('check')}]: {error}\n"
                html += f"<li><b>{check.get('check')}</b>: {error}</li>"
        html += "</ul>"
    else:
        text += "No individual check details; see the workflow run logs.\n"
        html += "<p>No individual check details; see the workflow run logs.</p>"

    footer = (
        "Fix the schema/data change and push again. Merge to the protected "
        "branch remains blocked until the Data Validation job passes."
    )
    text += "\n" + footer + "\n"
    html += f"<p>{footer}</p>"
    return text, html


# ------------------------------------------------------------------- main ----
def main(argv: list[str] | None = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    report_path = Path(args[0]) if args else Path(DEFAULT_REPORT)

    report = load_report(report_path)
    if report is None:
        return 0

    if report.get("status") == "PASS":
        print("Validation passed; no failure notification needed.")
        return 0

    text_body, html_body = build_bodies(report, github_context())
    subject = f"[StreakForge CI] Data validation FAILED - {report.get('dataset', 'dataset')}"
    send_email(subject, text_body, html_body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
