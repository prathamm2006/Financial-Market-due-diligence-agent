"""
Streamlit demo front end.
Run from the project root with: streamlit run ui/app.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from orchestrator import run_due_diligence

st.set_page_config(page_title="AI Due Diligence Agent", layout="wide")
st.title("📊 AI Due-Diligence Agent")
st.caption("Multi-agent system: Extractor → Benchmarker → Risk Flagger → Briefing Agent")

ticker = st.text_input("Enter a stock ticker", value="AAPL").upper()
run_btn = st.button("Run Due Diligence", type="primary")

if run_btn:
    progress = st.empty()
    try:
        progress.info("🔍 Extractor agent: pulling SEC filings...")
        result = run_due_diligence(ticker)
        progress.empty()
    except Exception as e:
        st.error(f"Pipeline failed: {e}")
        st.stop()

    company_name = result.get("company_name", ticker)
    st.header(f"{company_name} ({ticker})")

    brief = result.get("brief", {})
    if "error" in brief:
        st.warning("Briefing agent had trouble parsing output — see raw below.")
        st.json(brief)
    else:
        st.subheader("Executive Verdict")
        st.markdown(f"**{brief.get('headline', '')}**")
        st.write(brief.get("financial_summary", ""))

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Competitive Position")
            st.write(brief.get("competitive_position", ""))
        with col2:
            st.subheader("Key Risks")
            for risk in brief.get("key_risks", []):
                st.write(f"- {risk}")

        st.subheader("Recommendation")
        st.info(brief.get("recommendation", ""))
        st.caption(f"⚠️ Limitations: {brief.get('limitations', '')}")

    # Raw metrics chart
    st.divider()
    st.subheader("Underlying Financials (SEC EDGAR, XBRL)")
    metrics = result.get("metrics", {})
    if metrics.get("revenue"):
        df = pd.DataFrame(metrics["revenue"]).rename(columns={"value": "Revenue"})
        st.bar_chart(df.set_index("year")["Revenue"])

    with st.expander("See competitor benchmark data"):
        st.json(result.get("competitor_summary", {}))
    with st.expander("See risk agent output"):
        st.json(result.get("risk_output", {}))
    with st.expander("See raw pipeline state (for debugging / interviews)"):
        st.json(result)
