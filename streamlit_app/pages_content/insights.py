import streamlit as st
from components.theme import BRAND


def render(data, filters):
    st.title("💡 Insights & Narrative")

    narrative_df = data["insight_narrative"]
    if narrative_df.empty:
        st.warning("`insight_narrative.csv` not found.")
        return

    audiences = ["All"] + sorted(narrative_df["audience"].dropna().unique().tolist())
    audience = st.selectbox("Filter by audience", audiences)
    view = narrative_df if audience == "All" else narrative_df[narrative_df["audience"] == audience]

    for _, row in view.iterrows():
        with st.container(border=True):
            st.markdown(f'<span class="streakforge-audience-tag">{row["audience"]}</span>', unsafe_allow_html=True)
            st.subheader(f"{row['insight_id']} — {row['headline']}")
            st.write(row["narrative"])
            c1, c2 = st.columns(2)
            with c1:
                st.caption(f"**Evidence:** {row['supporting_evidence']}")
                st.caption(f"**Business impact:** {row['business_impact']}")
            with c2:
                st.caption(f"**Recommended action:** {row['recommended_action']}")
                st.caption(f"**Confidence:** {row['confidence']}")

    st.divider()
    with st.expander("Full narrative report (reports/insight_summary.md)"):
        st.markdown(data["insight_summary_md"])