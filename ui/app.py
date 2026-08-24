"""
Streamlit demo front end — "analyst terminal" design language.
Run from the project root with: streamlit run ui/app.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

from orchestrator import build_graph
from data.edgar_client import get_all_tickers
from data.india_tickers import get_india_ticker_options
from agents.report_generator import build_markdown_report, build_pdf_report

st.set_page_config(
    page_title="Due-Diligence Agent",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# DESIGN TOKENS — analyst-terminal palette: dark navy ledger, serif headline
# + monospace numerals (how real research desks set financial data), amber
# accent as the single signature color.
# ---------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
  --bg: #0B0F1A;
  --panel: #131A2B;
  --panel-border: #232D45;
  --ink: #E7EAF2;
  --muted: #8792AB;
  --amber: #C99A3C;
  --amber-soft: rgba(201, 154, 60, 0.12);
  --green: #4ADE80;
  --amber-risk: #FBBF24;
  --red: #F87171;
}

.stApp { background: var(--bg); color: var(--ink); }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2rem; max-width: 1100px; }

h1, h2, h3 { font-family: 'Source Serif 4', serif !important; color: var(--ink) !important; letter-spacing: -0.01em; }
p, div, span, label { font-family: 'Inter', sans-serif; }

.ledger-header {
  display: flex; justify-content: space-between; align-items: baseline;
  border-bottom: 1px solid var(--panel-border); padding-bottom: 1rem; margin-bottom: 0.5rem;
}
.ledger-title { font-family: 'Source Serif 4', serif; font-size: 2.1rem; font-weight: 700; color: var(--ink); }
.ledger-sub { font-family: 'IBM Plex Mono', monospace; color: var(--muted); font-size: 0.85rem; }
.ledger-tag { font-family: 'IBM Plex Mono', monospace; color: var(--amber); font-size: 0.78rem; border: 1px solid var(--amber); padding: 3px 9px; border-radius: 3px; }

.metric-card {
  background: var(--panel); border: 1px solid var(--panel-border); border-radius: 8px;
  padding: 1.1rem 1.3rem; height: 100%;
}
.metric-label { font-family: 'IBM Plex Mono', monospace; color: var(--muted); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; }
.metric-value { font-family: 'IBM Plex Mono', monospace; color: var(--ink); font-size: 1.55rem; font-weight: 600; margin-top: 0.2rem; }
.metric-sub { font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; margin-top: 0.15rem; }
.pos { color: var(--green); } .neg { color: var(--red); } .neu { color: var(--muted); }

.verdict-band {
  border-left: 3px solid var(--amber); background: var(--amber-soft);
  padding: 1rem 1.3rem; border-radius: 4px; margin: 1.2rem 0;
}
.verdict-headline { font-family: 'Source Serif 4', serif; font-size: 1.25rem; font-weight: 600; color: var(--ink); }

.section-label {
  font-family: 'IBM Plex Mono', monospace; color: var(--amber); font-size: 0.75rem;
  text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; margin-top: 1.6rem;
}

.risk-pill {
  display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem;
  padding: 3px 10px; border-radius: 12px; margin: 2px 6px 2px 0;
}
.risk-low { background: rgba(74, 222, 128, 0.12); color: var(--green); border: 1px solid rgba(74, 222, 128, 0.35); }
.risk-medium { background: rgba(251, 191, 36, 0.12); color: var(--amber-risk); border: 1px solid rgba(251, 191, 36, 0.35); }
.risk-high { background: rgba(248, 113, 113, 0.12); color: var(--red); border: 1px solid rgba(248, 113, 113, 0.35); }

.confidence-tag {
  font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: var(--muted);
  border: 1px dashed var(--panel-border); padding: 2px 8px; border-radius: 3px;
}

.limitation-note {
  font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; color: var(--muted);
  border-top: 1px dashed var(--panel-border); padding-top: 0.7rem; margin-top: 1.2rem;
}

.stTextInput input {
  font-family: 'IBM Plex Mono', monospace !important; background: var(--panel) !important;
  border: 1px solid var(--panel-border) !important; color: var(--amber) !important;
}
.stButton button {
  background: var(--amber) !important; color: #0B0F1A !important; border: none !important;
  font-family: 'Inter', sans-serif !important; font-weight: 600 !important; border-radius: 5px !important;
}
.stButton button:hover { background: #dcae4e !important; }

[data-testid="stExpander"] { background: var(--panel); border: 1px solid var(--panel-border); border-radius: 6px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
@st.cache_data(ttl=86400, show_spinner=False)
def _load_us_ticker_options():
    """Cached for 24h so we don't hit SEC's ticker map on every rerun."""
    tickers = get_all_tickers()
    return [f"{t['ticker']} — {t['title']}" for t in tickers]


@st.cache_data(ttl=86400, show_spinner=False)
def _load_india_ticker_options():
    tickers = get_india_ticker_options()
    return [f"{t['ticker']} — {t['title']}" for t in tickers]


market = st.radio(
    "Market", ["🇺🇸 US (SEC EDGAR)", "🇮🇳 India (NSE)"],
    horizontal=True, label_visibility="collapsed",
)

data_source_label = "NSE · Yahoo Finance" if market.startswith("🇮🇳") else "SEC EDGAR"

st.markdown(
    f"""
    <div class="ledger-header">
      <div>
        <div class="ledger-title">Due-Diligence Agent</div>
        <div class="ledger-sub">multi-agent research pipeline · {data_source_label} · live synthesis</div>
      </div>
      <div class="ledger-tag">{datetime.now().strftime('%d %b %Y')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

col_input, col_btn = st.columns([4, 1])
with col_input:
    if market.startswith("🇮🇳"):
        options = _load_india_ticker_options()
        default_idx = next((i for i, o in enumerate(options) if o.startswith("RELIANCE.NS —")), 0)
        selection = st.selectbox(
            "Ticker", options, index=default_idx,
            label_visibility="collapsed",
            help="Start typing a ticker or company name to search",
        )
        ticker = selection.split(" — ")[0].strip()
    else:
        try:
            options = _load_us_ticker_options()
            default_idx = next((i for i, o in enumerate(options) if o.startswith("AAPL —")), 0)
            selection = st.selectbox(
                "Ticker", options, index=default_idx,
                label_visibility="collapsed",
                help="Start typing a ticker or company name to search",
            )
            ticker = selection.split(" — ")[0].strip()
        except Exception:
            # Graceful fallback if SEC's ticker list is briefly unreachable
            st.caption("Couldn't load the ticker list — type one manually instead.")
            ticker = st.text_input("Ticker", value="AAPL", label_visibility="collapsed").upper()
with col_btn:
    run_btn = st.button("Run analysis", use_container_width=True)

# ---------------------------------------------------------------------------
# PIPELINE EXECUTION — visible agent-by-agent progress (this IS the product;
# showing the pipeline work is more credible than a spinner hiding it)
# ---------------------------------------------------------------------------
def run_with_progress(ticker: str):
    """
    Runs the graph ONCE via a single app.stream() call and updates the
    progress display as each node completes. (Previous version called
    .stream() once per displayed stage label and drained the whole
    generator each time — since LangGraph has no checkpointing here,
    that silently re-ran the ENTIRE pipeline, including both Gemini
    calls, multiple times per click. That extra load is what was
    triggering Gemini's 503 UNAVAILABLE — not bad luck.)
    """
    app = build_graph()
    stage_labels = [
        "Pulling SEC EDGAR filings",
        "Benchmarking against peers",
        "Computing trend forecasts",
        "Pulling live valuation multiples",
        "Scanning for risk signals",
        "Synthesizing executive brief",
    ]
    progress_box = st.empty()
    completed = []
    result = {}

    # stream_mode="values" yields the initial state first (index 0, before
    # any node has run), then the accumulated state after each subsequent
    # node — so event i>0 corresponds to stage_labels[i-1] finishing.
    for i, event in enumerate(app.stream({"ticker": ticker}, stream_mode="values")):
        result = event
        if i > 0:
            completed.append(stage_labels[i - 1])
        with progress_box.container():
            lines = [f"<span class='pos'>✓</span> {done}" for done in completed]
            if len(completed) < len(stage_labels):
                lines.append(f"<span class='neu'>▸</span> {stage_labels[len(completed)]}...")
            st.markdown(
                f"<div class='metric-card'><div style='font-family:IBM Plex Mono,monospace; font-size:0.85rem; line-height:1.9;'>"
                + "<br>".join(lines) + "</div></div>",
                unsafe_allow_html=True,
            )
    progress_box.empty()
    return result


if run_btn:
    try:
        result = run_with_progress(ticker)
    except Exception as e:
        st.error(f"Pipeline failed: {e}")
        st.stop()

    company_name = result.get("company_name", ticker)
    brief = result.get("brief", {})
    metrics = result.get("metrics", {})
    forecast = result.get("forecast_output", {})
    valuation = result.get("valuation_output", {})
    filing_url = result.get("filing_index_url", "")

    if "error" in brief:
        st.warning("Briefing agent had trouble parsing output — see raw below.")
        st.json(brief)
        st.stop()

    # -- Headline verdict -----------------------------------------------
    filing_link_html = (
        f" · <a href='{filing_url}' target='_blank' style='color:var(--amber); text-decoration:none;'>view SEC filings ↗</a>"
        if filing_url else ""
    )
    st.markdown(
        f"### {company_name} <span style='color:var(--muted); font-family:IBM Plex Mono,monospace; font-size:1rem;'>{ticker}{filing_link_html}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""<div class="verdict-band">
              <div class="verdict-headline">{brief.get('headline', '')}</div>
            </div>""",
        unsafe_allow_html=True,
    )

    # -- Key metric cards --------------------------------------------------
    def latest_and_prior(series):
        if not series or len(series) < 1:
            return None, None
        latest = series[0]["value"]
        prior = series[1]["value"] if len(series) > 1 else None
        return latest, prior

    currency = result.get("currency", "USD")
    currency_symbol = {"USD": "$", "INR": "\u20b9", "EUR": "\u20ac", "GBP": "\u00a3"}.get(currency, currency + " ")

    def fmt_usd(val):
        """Currency-aware formatter — Indian numbering (Crore/Lakh) for INR,
        standard B/M for USD and other currencies, since Indian financial
        reporting conventionally uses lakh/crore rather than million/billion."""
        if val is None:
            return "—"
        if currency == "INR":
            if abs(val) >= 1e7:
                return f"{currency_symbol}{val/1e7:,.1f} Cr"
            if abs(val) >= 1e5:
                return f"{currency_symbol}{val/1e5:,.1f} L"
            return f"{currency_symbol}{val:,.0f}"
        if abs(val) >= 1e9:
            return f"{currency_symbol}{val/1e9:.1f}B"
        if abs(val) >= 1e6:
            return f"{currency_symbol}{val/1e6:.1f}M"
        return f"{currency_symbol}{val:,.0f}"

    rev_latest, rev_prior = latest_and_prior(metrics.get("revenue", []))
    ni_latest, ni_prior = latest_and_prior(metrics.get("net_income", []))
    rev_yoy = ((rev_latest - rev_prior) / rev_prior * 100) if rev_latest and rev_prior else None
    ni_yoy = ((ni_latest - ni_prior) / ni_prior * 100) if ni_latest and ni_prior else None
    rev_cagr = forecast.get("revenue", {}).get("cagr_pct")

    c1, c2, c3, c4 = st.columns(4)
    for col, label, value, sub, sub_class in [
        (c1, "Revenue (latest FY)", fmt_usd(rev_latest), f"{rev_yoy:+.1f}% YoY" if rev_yoy is not None else "—", "pos" if (rev_yoy or 0) >= 0 else "neg"),
        (c2, "Net income (latest FY)", fmt_usd(ni_latest), f"{ni_yoy:+.1f}% YoY" if ni_yoy is not None else "—", "pos" if (ni_yoy or 0) >= 0 else "neg"),
        (c3, "Revenue CAGR", f"{rev_cagr:+.1f}%" if rev_cagr is not None else "—", "trailing period", "neu"),
        (c4, "Risk level", (result.get("risk_output", {}).get("overall_risk_level", "—")).upper(), "agent-assessed", "neu"),
    ]:
        with col:
            st.markdown(
                f"""<div class="metric-card">
                      <div class="metric-label">{label}</div>
                      <div class="metric-value">{value}</div>
                      <div class="metric-sub {sub_class}">{sub}</div>
                    </div>""",
                unsafe_allow_html=True,
            )

    # -- Valuation cards (live market data) ---------------------------------
    target_val = valuation.get("target", {})
    if target_val.get("available"):
        v1, v2, v3, v4 = st.columns(4)
        for col, label, value, sub in [
            (v1, "Price", f"{currency_symbol}{target_val.get('price', '—')}" if target_val.get("price") else "—", "live quote"),
            (v2, "Market cap", fmt_usd(target_val.get("market_cap")), "—"),
            (v3, "P/E ratio", f"{target_val.get('pe_ratio', '—')}x" if target_val.get("pe_ratio") else "n/a", "trailing"),
            (v4, "EV/EBITDA (proxy)", f"{target_val.get('ev_ebitda_proxy', '—')}x" if target_val.get("ev_ebitda_proxy") else "n/a", "operating income proxy"),
        ]:
            with col:
                st.markdown(
                    f"""<div class="metric-card">
                          <div class="metric-label">{label}</div>
                          <div class="metric-value">{value}</div>
                          <div class="metric-sub neu">{sub}</div>
                        </div>""",
                    unsafe_allow_html=True,
                )
        st.caption(target_val.get("note", ""))
    else:
        st.caption(f"Live valuation data unavailable: {target_val.get('reason', 'unknown')}")

    # -- Chart: history + scenario bands ----------------------------------------
    st.markdown("<div class='section-label'>Revenue — historical &amp; scenario forecast</div>", unsafe_allow_html=True)
    if metrics.get("revenue"):
        hist = list(reversed(metrics["revenue"]))
        rev_forecast = forecast.get("revenue", {})
        scenarios = rev_forecast.get("scenarios", {"bear": [], "base": [], "bull": []})
        conf = rev_forecast.get("confidence", "low")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[p["year"] for p in hist], y=[p["value"] for p in hist],
            name="Reported", marker_color="#C99A3C", width=0.5,
        ))
        if scenarios.get("bull"):
            fig.add_trace(go.Bar(
                x=[p["year"] for p in scenarios["bull"]], y=[p["value"] for p in scenarios["bull"]],
                name="Bull case", marker_color="rgba(74,222,128,0.25)",
                marker_line=dict(color="#4ADE80", width=1), width=0.28,
            ))
        if scenarios.get("base"):
            fig.add_trace(go.Bar(
                x=[p["year"] for p in scenarios["base"]], y=[p["value"] for p in scenarios["base"]],
                name="Base case", marker_color="rgba(201,154,60,0.28)",
                marker_line=dict(color="#C99A3C", width=1), width=0.28,
            ))
        if scenarios.get("bear"):
            fig.add_trace(go.Bar(
                x=[p["year"] for p in scenarios["bear"]], y=[p["value"] for p in scenarios["bear"]],
                name="Bear case", marker_color="rgba(248,113,113,0.25)",
                marker_line=dict(color="#F87171", width=1), width=0.28,
            ))
        fig.update_layout(
            barmode="group",
            plot_bgcolor="#131A2B", paper_bgcolor="#131A2B",
            font=dict(family="IBM Plex Mono, monospace", color="#8792AB", size=11),
            margin=dict(l=10, r=10, t=10, b=10), height=300,
            legend=dict(orientation="h", y=1.15, font=dict(color="#E7EAF2")),
            xaxis=dict(gridcolor="#232D45"), yaxis=dict(gridcolor="#232D45"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown(f"<span class='confidence-tag'>forecast confidence: {conf}</span>", unsafe_allow_html=True)
    else:
        st.caption("No multi-year revenue history available from SEC EDGAR for this ticker.")

    # -- Narrative sections -------------------------------------------------
    left, right = st.columns(2)
    with left:
        st.markdown("<div class='section-label'>Financial summary</div>", unsafe_allow_html=True)
        st.write(brief.get("financial_summary", ""))
        st.markdown("<div class='section-label'>Forecast analysis</div>", unsafe_allow_html=True)
        st.write(brief.get("forecast_analysis", ""))
        st.markdown("<div class='section-label'>Valuation</div>", unsafe_allow_html=True)
        st.write(brief.get("valuation_analysis", ""))
    with right:
        st.markdown("<div class='section-label'>Competitive position</div>", unsafe_allow_html=True)
        st.write(brief.get("competitive_position", ""))
        st.markdown("<div class='section-label'>Key risks</div>", unsafe_allow_html=True)
        risk_level_map = {"low": "risk-low", "medium": "risk-medium", "high": "risk-high"}
        overall = result.get("risk_output", {}).get("overall_risk_level", "medium")
        for flag in result.get("risk_output", {}).get("risk_flags", []):
            sev = flag.get("severity", "medium")
            st.markdown(
                f"<span class='risk-pill {risk_level_map.get(sev, 'risk-medium')}'>{flag.get('flag', '')}</span>",
                unsafe_allow_html=True,
            )
        for bullet in brief.get("key_risks", []):
            st.write(f"— {bullet}")

    st.markdown("<div class='section-label'>Recommendation</div>", unsafe_allow_html=True)
    st.info(brief.get("recommendation", ""))
    st.markdown(f"<div class='limitation-note'>LIMITATIONS: {brief.get('limitations', '')}</div>", unsafe_allow_html=True)

    # -- Downloads -----------------------------------------------------
    st.markdown("<div class='section-label'>Export this brief</div>", unsafe_allow_html=True)
    dl1, dl2 = st.columns(2)
    with dl1:
        try:
            pdf_bytes = build_pdf_report(company_name, ticker, result)
            st.download_button(
                "⬇ Download PDF report",
                data=pdf_bytes,
                file_name=f"{ticker}_due_diligence_brief.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.caption(f"PDF export unavailable: {e}")
    with dl2:
        md_report = build_markdown_report(company_name, ticker, result)
        st.download_button(
            "⬇ Download Markdown report",
            data=md_report,
            file_name=f"{ticker}_due_diligence_brief.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.divider()
    with st.expander("Competitor benchmark data"):
        comp = result.get("competitor_summary", {})
        target_snap = comp.get("target_snapshot", {})
        rows = [{
            "Company": f"{ticker} (target)",
            "Revenue": fmt_usd(target_snap.get("revenue")),
            "Net income": fmt_usd(target_snap.get("net_income")),
            "Net margin": f"{target_snap.get('net_margin_pct', '—')}%" if target_snap.get("net_margin_pct") is not None else "—",
        }]
        for peer_ticker, peer_data in comp.get("peers", {}).items():
            if "error" in peer_data:
                rows.append({"Company": peer_ticker, "Revenue": "—", "Net income": "—", "Net margin": "no data"})
            else:
                rows.append({
                    "Company": f"{peer_data.get('company_name', peer_ticker)} ({peer_ticker})",
                    "Revenue": fmt_usd(peer_data.get("revenue")),
                    "Net income": fmt_usd(peer_data.get("net_income")),
                    "Net margin": f"{peer_data.get('net_margin_pct', '—')}%" if peer_data.get("net_margin_pct") is not None else "—",
                })
        st.table(rows)

    with st.expander("Valuation data (target vs peers)"):
        val_target = valuation.get("target", {})
        if val_target.get("available"):
            rows = [{
                "Company": f"{ticker} (target)",
                "P/E": val_target.get("pe_ratio", "—"),
                "Price/Sales": val_target.get("price_to_sales", "—"),
                "Market cap": fmt_usd(val_target.get("market_cap")),
            }]
            for peer_ticker, pv in valuation.get("peers", {}).items():
                rows.append({
                    "Company": peer_ticker,
                    "P/E": pv.get("pe_ratio", "—"),
                    "Price/Sales": pv.get("price_to_sales", "—"),
                    "Market cap": fmt_usd(pv.get("market_cap")),
                })
            st.table(rows)
        else:
            st.caption(f"Valuation data unavailable: {val_target.get('reason', 'unknown')}")

    with st.expander("Forecast agent output"):
        for metric_name, fdata in forecast.items():
            st.markdown(f"**{metric_name.replace('_', ' ').title()}**")
            cagr = fdata.get("cagr_pct")
            conf = fdata.get("confidence", "—")
            st.write(f"CAGR: {cagr:+.1f}%" if cagr is not None else "CAGR: not enough data")
            st.write(f"Confidence: {conf}")
            st.caption(fdata.get("note", ""))
            projections = fdata.get("projections", [])
            if projections:
                st.write("Projected values:")
                for p in projections:
                    st.write(f"— {p['year']}: {fmt_usd(p['value'])}")
            st.markdown("---")

    with st.expander("Risk agent output"):
        risk_out = result.get("risk_output", {})
        st.write(f"**Overall risk level:** {risk_out.get('overall_risk_level', '—')}")
        for flag in risk_out.get("risk_flags", []):
            st.markdown(f"**{flag.get('flag', '')}** — *{flag.get('severity', '')}*")
            st.caption(flag.get("evidence", ""))
        st.caption(f"Confidence note: {risk_out.get('confidence_note', '')}")

    with st.expander("Full pipeline state (raw JSON — debugging / interview walkthrough)"):
        st.json(result)
