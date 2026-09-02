"""Threshold-based alert configuration and evaluation for StreakForge dashboard."""

import streamlit as st

ALERT_THRESHOLDS = {
    "churn_rate": {
        "metric": "Churn Rate",
        "threshold": 7.0,
        "direction": "above",
        "severity": "critical",
        "message": "Churn exceeds safe limit. Investigate retention.",
    },
    "avg_order_value": {
        "metric": "Avg Order Value",
        "threshold": 30.0,
        "direction": "below",
        "severity": "warning",
        "message": "AOV below target. Check pricing and product mix.",
    },
    "null_percentage": {
        "metric": "Data Quality",
        "threshold": 5.0,
        "direction": "above",
        "severity": "warning",
        "message": "Null percentage too high. Check data pipeline.",
    },
}


def evaluate_alerts(current_metrics: dict, thresholds: dict = ALERT_THRESHOLDS):
    """Evaluate current metrics against thresholds and return list of breached alerts."""
    breached_alerts = []
    for key, config in thresholds.items():
        value = current_metrics.get(key, 0)
        breached = False
        if config["direction"] == "above" and value > config["threshold"]:
            breached = True
        elif config["direction"] == "below" and value < config["threshold"]:
            breached = True

        if breached:
            alert_text = (
                "ALERT: "
                + config["metric"]
                + " is "
                + str(round(value, 1))
                + " (threshold: "
                + str(config["threshold"])
                + "). "
                + config["message"]
            )
            breached_alerts.append((config.get("severity", "warning"), alert_text))
    return breached_alerts


def render_alerts(current_metrics: dict, thresholds: dict = ALERT_THRESHOLDS):
    """Render visual alerts using st.error or st.warning at the top of the dashboard."""
    for severity, alert_text in evaluate_alerts(current_metrics, thresholds):
        if severity == "critical":
            st.error(alert_text)
        else:
            st.warning(alert_text)
