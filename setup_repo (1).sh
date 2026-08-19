#!/bin/bash
set -e
mkdir -p data agents ui .devcontainer .streamlit .github/workflows

cat > 'requirements.txt' << 'FILEEOF'
google-generativeai>=0.8.0
langgraph>=0.2.0
requests>=2.31.0
streamlit>=1.38.0
pandas>=2.2.0
FILEEOF

cat > '.gitignore' << 'FILEEOF'
# Secrets — never commit these
.env
.streamlit/secrets.toml

# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/
env/
*.egg-info/

# OS/editor
.DS_Store
.vscode/*
!.vscode/settings.json

# Streamlit
.streamlit/cache/
FILEEOF

cat > '.env.example' << 'FILEEOF'
# Copy this file to .env and fill in your keys, then run:
#   export $(cat .env | xargs)
# (Never commit the real .env — it's in .gitignore)

GOOGLE_API_KEY=your-google-gemini-key-here
TAVILY_API_KEY=your-tavily-key-here
FILEEOF

cat > 'LICENSE' << 'FILEEOF'
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
FILEEOF

cat > 'README.md' << 'FILEEOF'
# AI Due-Diligence Agent

[![CI](https://github.com/YOUR_USERNAME/due-diligence-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/due-diligence-agent/actions/workflows/ci.yml)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/YOUR_USERNAME/due-diligence-agent)

🔗 **Live demo:** _add your Streamlit Cloud URL here once deployed (see below)_

A multi-agent system that automates the first draft of equity/credit due-diligence
research — the kind of work analysts at investment banks and consulting firms
spend hours doing manually before a client meeting or investment decision.

## The problem

Building an initial due-diligence brief on a company — financial summary,
competitor benchmark, risk flags — typically takes an analyst several hours:
pulling filings, cross-referencing competitors, scanning news for red flags,
then writing it up. This agent produces a structured first draft in under a
minute, which the analyst then reviews and refines rather than starting from
a blank page.

## Architecture

```
   ticker
     │
     ▼
┌─────────────┐     ┌───────────────┐     ┌────────────────┐     ┌────────────────┐
│  Extractor   │ --> │  Benchmarker  │ --> │  Risk Flagger   │ --> │  Briefing Agent │
│ (SEC EDGAR   │     │ (peer metric  │     │ (news + metric  │     │ (Gemini:        │
│  XBRL facts) │     │  comparison)  │     │  red flags,     │     │  synthesizes    │
│              │     │               │     │  Gemini-powered)│     │  exec brief)    │
└─────────────┘     └───────────────┘     └────────────────┘     └────────────────┘
```

Orchestrated as an explicit [LangGraph](https://github.com/langchain-ai/langgraph)
state machine — each agent is a node with one job, and the full state is
inspectable at every step. This makes the pipeline debuggable and each node
independently swappable/testable, versus one large prompt.

- **Extractor**: pulls real structured financials (revenue, net income, debt,
  cash) directly from SEC's XBRL API — no PDF scraping, no hallucinated numbers.
- **Benchmarker**: pure arithmetic (not LLM) comparison against named
  competitors — deliberately avoids using an LLM where a calculator suffices.
- **Risk Flagger**: Gemini reads recent news + the metric trend and flags
  concrete, evidence-cited risks (never speculative).
- **Briefing Agent**: Gemini synthesizes everything into a partner-ready brief
  with an explicit recommendation and a stated limitation.

## Run it in GitHub Codespaces (recommended — zero local setup)

1. Click **Code → Codespaces → Create codespace on main** on this repo
   (or use the badge above). The devcontainer auto-installs everything.
2. Once the codespace opens, set your API key for the session:
   ```bash
   export GOOGLE_API_KEY="your-google-gemini-key-here"
   export TAVILY_API_KEY="your-key-here"   # optional
   ```
3. Run the app:
   ```bash
   streamlit run ui/app.py
   ```
4. Codespaces will pop up a "Open in Browser" prompt on port 8501 — click it.

## Run it locally

```bash
git clone https://github.com/YOUR_USERNAME/due-diligence-agent.git
cd due-diligence-agent
pip install -r requirements.txt
cp .env.example .env        # then fill in your keys
export $(cat .env | xargs)
streamlit run ui/app.py
```

Try tickers: `AAPL`, `TGT`, `JPM`, `KO` (peer maps are pre-populated for these —
add more in `agents/benchmarker_agent.py`).

## Deploy the live demo (Streamlit Community Cloud — free)

1. Push this repo to GitHub (see **Push to GitHub** below).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select your repo, branch `main`, and set the main file path to `ui/app.py`.
4. In **Advanced settings → Secrets**, paste:
   ```toml
   GOOGLE_API_KEY = "your-google-gemini-key-here"
   TAVILY_API_KEY = "your-google-gemini-key-here"
   ```
5. Deploy. You'll get a public URL like `https://due-diligence-agent.streamlit.app`
   — put that at the top of this README and on your LinkedIn/portfolio.

## Push this repo to GitHub

```bash
cd due-diligence-agent
git init
git add .
git commit -m "Initial commit: multi-agent due diligence system"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/due-diligence-agent.git
git push -u origin main
```

## What this demonstrates

- Multi-agent orchestration with explicit state (not a single mega-prompt)
- Grounding LLM output in real structured data (SEC XBRL) rather than letting
  the model "remember" financials, which reduces hallucination risk
- Structured JSON output contracts between agents — predictable, chartable,
  testable
- Explicit uncertainty handling — every brief states its own limitations,
  which matters for any AI system used in a regulated/high-stakes decision context

## Limitations (be upfront about these in interviews — it's a strength, not a weakness)

- Financial metric extraction should be spot-checked against filings before
  any real decision is made on it — this is a first-draft tool, not a
  replacement for verified diligence
- Peer/competitor sets are currently hardcoded; a production version would
  derive peers dynamically (SIC code matching or embedding similarity)
- News-based risk flagging is only as good as the search API's recency and
  coverage — not a substitute for a Bloomberg/FactSet-grade news feed
- No audit trail / versioning yet — needed before this could be used in any
  regulated (SOX, financial services) context

## Next steps (roadmap, good to mention in interviews)

- Add a human-in-the-loop approval step before the brief is finalized
- Dynamic peer selection via SIC code or sector embeddings
- Cache SEC pulls to avoid redundant API calls across repeated runs
- Add a confidence score per extracted metric (was it found directly in
  XBRL, or interpolated?)
FILEEOF

cat > '.devcontainer/devcontainer.json' << 'FILEEOF'
{
  "name": "AI Due Diligence Agent",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "postCreateCommand": "pip install -r requirements.txt",
  "forwardPorts": [8501],
  "portsAttributes": {
    "8501": {
      "label": "Streamlit App",
      "onAutoForward": "openPreview"
    }
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python"
      }
    }
  },
  "remoteEnv": {
    "PYTHONPATH": "${containerWorkspaceFolder}"
  }
}
FILEEOF

cat > '.streamlit/secrets.toml.example' << 'FILEEOF'
# Streamlit Community Cloud reads secrets from this file's contents,
# pasted into the app's "Secrets" settings in the dashboard — NOT from
# this file directly (this file is gitignored and stays local/unused
# except as a template for what to paste).
#
# For local runs, Streamlit also auto-loads a REAL .streamlit/secrets.toml
# if you create one (copy this file there and fill in values).

GOOGLE_API_KEY = "your-google-gemini-key-here"
TAVILY_API_KEY = "your-tavily-key-here"
FILEEOF

cat > '.github/workflows/ci.yml' << 'FILEEOF'
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Compile check (catches syntax errors)
        run: python -m py_compile data/*.py agents/*.py ui/*.py orchestrator.py

      - name: Import check (catches missing dependencies / broken imports)
        run: |
          python -c "from orchestrator import build_graph; build_graph(); print('Graph builds successfully')"
FILEEOF

cat > 'data/edgar_client.py' << 'FILEEOF'
"""
SEC EDGAR client — pulls real company filings and structured financial facts.
No API key required. SEC just requires a descriptive User-Agent header.

Docs: https://www.sec.gov/edgar/sec-api-documentation
"""
import requests
import time

# SEC requires a real identifying User-Agent (name + email). Replace with yours.
HEADERS = {"User-Agent": "DueDiligenceAgent research@example.com"}

BASE = "https://data.sec.gov"
TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"


def get_cik_for_ticker(ticker: str) -> str:
    """Map a stock ticker (e.g. 'AAPL') to its 10-digit zero-padded CIK number."""
    resp = requests.get(TICKER_MAP_URL, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    ticker = ticker.upper()
    for entry in data.values():
        if entry["ticker"] == ticker:
            return str(entry["cik_str"]).zfill(10)
    raise ValueError(f"Ticker '{ticker}' not found in SEC ticker map.")


def get_company_facts(cik: str) -> dict:
    """
    Pull ALL structured XBRL financial facts SEC has for this company —
    revenue, net income, assets, liabilities, cash flow, etc.
    This is cleaner than parsing raw 10-K text and is what most real
    fin-analysis tools use under the hood.
    """
    url = f"{BASE}/api/xbrl/companyfacts/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def extract_key_metrics(company_facts: dict, years: int = 3) -> dict:
    """
    Pulls the most recent N annual values for a curated list of key metrics
    from the raw companyfacts blob. Returns a clean dict ready for the LLM
    or for direct charting — no need to hand the whole XBRL blob to an LLM.
    """
    us_gaap = company_facts.get("facts", {}).get("us-gaap", {})
    wanted = {
        "Revenues": "revenue",
        "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",
        "NetIncomeLoss": "net_income",
        "Assets": "total_assets",
        "Liabilities": "total_liabilities",
        "CashAndCashEquivalentsAtCarryingValue": "cash",
        "LongTermDebtNoncurrent": "long_term_debt",
        "OperatingIncomeLoss": "operating_income",
    }

    metrics = {}
    for gaap_tag, clean_name in wanted.items():
        if gaap_tag not in us_gaap:
            continue
        usd_facts = us_gaap[gaap_tag].get("units", {}).get("USD", [])
        # Keep only annual (10-K, full-year) data points, most recent first
        annual = [
            f for f in usd_facts
            if f.get("form") == "10-K" and f.get("fp") == "FY"
        ]
        annual.sort(key=lambda f: f["end"], reverse=True)
        seen_years = set()
        series = []
        for f in annual:
            yr = f["end"][:4]
            if yr in seen_years:
                continue
            seen_years.add(yr)
            series.append({"year": yr, "value": f["val"]})
            if len(series) >= years:
                break
        if clean_name not in metrics and series:
            metrics[clean_name] = series

    return metrics


def get_company_profile(ticker: str, years: int = 3) -> dict:
    """One-call convenience wrapper: ticker -> clean metrics dict."""
    cik = get_cik_for_ticker(ticker)
    time.sleep(0.2)  # be polite to SEC rate limits
    facts = get_company_facts(cik)
    metrics = extract_key_metrics(facts, years=years)
    company_name = facts.get("entityName", ticker)
    return {"ticker": ticker.upper(), "cik": cik, "company_name": company_name, "metrics": metrics}


if __name__ == "__main__":
    # Quick manual test — run: python edgar_client.py
    profile = get_company_profile("AAPL")
    import json
    print(json.dumps(profile, indent=2))
FILEEOF

cat > 'data/news_client.py' << 'FILEEOF'
"""
Pulls recent news snippets for a company to feed the Risk Flagger agent.
Uses Tavily (free tier, generous limits, built for LLM agents) if a key
is set. If not, gracefully degrades to an empty list so the rest of the
pipeline still runs — the demo should never hard-crash on a missing key.
"""
import os
import requests


def _get_tavily_key() -> str | None:
    val = os.environ.get("TAVILY_API_KEY")
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get("TAVILY_API_KEY")
    except Exception:
        return None


def get_recent_news(company_name: str, max_results: int = 5) -> list[str]:
    tavily_key = _get_tavily_key()
    if not tavily_key:
        return []

    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": tavily_key,
                "query": f"{company_name} risk litigation earnings news",
                "max_results": max_results,
                "search_depth": "basic",
            },
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return [f"{r['title']}: {r.get('content', '')[:200]}" for r in results]
    except Exception:
        return []
FILEEOF

cat > 'agents/benchmarker_agent.py' << 'FILEEOF'
"""
Benchmarker agent — pulls the same metrics for competitor tickers and
computes simple relative comparisons. Deliberately NOT LLM-based:
this is arithmetic, and doing arithmetic with a calculator instead of
an LLM is itself a signal of good engineering judgment.
"""
from data.edgar_client import get_company_profile

# Simple starter peer map — expand this per sector as you demo more companies.
PEER_MAP = {
    "AAPL": ["MSFT", "GOOGL"],
    "TGT": ["WMT", "COST"],
    "JPM": ["BAC", "WFC"],
    "KO": ["PEP"],
}


def get_peers(ticker: str) -> list[str]:
    return PEER_MAP.get(ticker.upper(), [])


def latest_value(series: list[dict]) -> float | None:
    if not series:
        return None
    return series[0]["value"]


def benchmark_against_peers(target_profile: dict) -> dict:
    """
    Returns latest-year metric comparisons between the target and its peers.
    Growth/margin figures where derivable, raw numbers otherwise.
    """
    ticker = target_profile["ticker"]
    peers = get_peers(ticker)
    comparison = {"target": ticker, "peers": {}}

    target_metrics = target_profile["metrics"]
    target_revenue = latest_value(target_metrics.get("revenue", []))
    target_net_income = latest_value(target_metrics.get("net_income", []))
    target_margin = (
        round(target_net_income / target_revenue * 100, 1)
        if target_revenue and target_net_income else None
    )
    comparison["target_snapshot"] = {
        "revenue": target_revenue,
        "net_income": target_net_income,
        "net_margin_pct": target_margin,
    }

    for peer_ticker in peers:
        try:
            peer_profile = get_company_profile(peer_ticker, years=1)
        except Exception as e:
            comparison["peers"][peer_ticker] = {"error": str(e)}
            continue

        peer_revenue = latest_value(peer_profile["metrics"].get("revenue", []))
        peer_net_income = latest_value(peer_profile["metrics"].get("net_income", []))
        peer_margin = (
            round(peer_net_income / peer_revenue * 100, 1)
            if peer_revenue and peer_net_income else None
        )
        comparison["peers"][peer_ticker] = {
            "company_name": peer_profile["company_name"],
            "revenue": peer_revenue,
            "net_income": peer_net_income,
            "net_margin_pct": peer_margin,
        }

    return comparison
FILEEOF

cat > 'agents/llm_agents.py' << 'FILEEOF'
"""
The two 'thinking' agents in the pipeline. Both call Gemini with structured
prompts and JSON-mode output so results are predictable and chartable,
not free-text blobs.

Requires: GOOGLE_API_KEY environment variable (free, no credit card —
get one at https://aistudio.google.com/apikey)
"""
import os
import json
import google.generativeai as genai


def _get_secret(key: str) -> str | None:
    """Reads a secret from env var first (local/Codespaces), then falls
    back to Streamlit's secrets store (Streamlit Community Cloud deploy)."""
    val = os.environ.get(key)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key)
    except Exception:
        return None


genai.configure(api_key=_get_secret("GOOGLE_API_KEY"))
MODEL = "gemini-2.5-flash"


def _call_gemini_json(system: str, user: str) -> dict:
    """Helper: call Gemini, force JSON-only output via response_mime_type, parse it safely."""
    model = genai.GenerativeModel(model_name=MODEL, system_instruction=system)
    resp = model.generate_content(
        user,
        generation_config={"response_mime_type": "application/json"},
    )
    text = resp.text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "Could not parse model output", "raw": text}


def risk_flagger_agent(company_name: str, metrics: dict, news_snippets: list[str]) -> dict:
    """
    Scans recent news + the metric trend for red flags an analyst would
    care about: margin compression, debt growth, leadership turnover,
    litigation, guidance cuts, etc.
    """
    system = (
        "You are a careful equity/credit risk analyst. You flag concrete, "
        "evidence-based risks only — never speculate beyond what's given. "
        "Respond with ONLY valid JSON, no prose, no markdown fences."
    )
    user = f"""
Company: {company_name}

Recent financial metrics (most recent year first):
{json.dumps(metrics, indent=2)}

Recent news snippets:
{json.dumps(news_snippets, indent=2)}

Return JSON in exactly this shape:
{{
  "risk_flags": [
    {{"flag": "short label", "severity": "low|medium|high", "evidence": "one sentence, cite the specific number or news item"}}
  ],
  "overall_risk_level": "low|medium|high",
  "confidence_note": "one sentence on what data would improve this assessment"
}}
"""
    return _call_gemini_json(system, user)


def briefing_agent(company_name: str, ticker: str, metrics: dict,
                    competitor_summary: dict, risk_output: dict) -> dict:
    """
    The synthesis agent — takes everything the other agents produced and
    writes the executive-ready brief. This is the deliverable a human
    actually reads.
    """
    system = (
        "You are a senior consulting analyst writing a due-diligence brief "
        "for a partner who has 90 seconds to read it. Be direct, quantified, "
        "and explicit about uncertainty. Respond with ONLY valid JSON."
    )
    user = f"""
Company: {company_name} ({ticker})

Financial metrics:
{json.dumps(metrics, indent=2)}

Competitor benchmark:
{json.dumps(competitor_summary, indent=2)}

Risk analysis:
{json.dumps(risk_output, indent=2)}

Return JSON in exactly this shape:
{{
  "headline": "one sentence verdict",
  "financial_summary": "2-3 sentences, cite actual numbers",
  "competitive_position": "2-3 sentences vs the named competitors",
  "key_risks": ["short bullet", "short bullet"],
  "recommendation": "one paragraph: proceed / proceed with caution / pass, and why",
  "limitations": "one sentence on what this brief does NOT cover (e.g. qualitative diligence, legal review)"
}}
"""
    return _call_gemini_json(system, user)
FILEEOF

cat > 'orchestrator.py' << 'FILEEOF'
"""
The orchestrator — a LangGraph state machine wiring together:
  Extractor -> Benchmarker -> Risk Flagger -> Briefing Agent

Using an explicit graph (vs. a single mega-prompt) is the whole point:
each node has one job, state is inspectable at every step, and you can
swap/retry any single node without touching the others. That's the
architecture story you tell in interviews.
"""
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from data.edgar_client import get_company_profile
from data.news_client import get_recent_news
from agents.benchmarker_agent import benchmark_against_peers
from agents.llm_agents import risk_flagger_agent, briefing_agent


class DDState(TypedDict, total=False):
    ticker: str
    company_name: str
    metrics: dict
    competitor_summary: dict
    news_snippets: list
    risk_output: dict
    brief: dict
    error: Optional[str]


def node_extractor(state: DDState) -> DDState:
    profile = get_company_profile(state["ticker"])
    return {
        "company_name": profile["company_name"],
        "metrics": profile["metrics"],
    }


def node_benchmarker(state: DDState) -> DDState:
    profile = {"ticker": state["ticker"], "metrics": state["metrics"]}
    comparison = benchmark_against_peers(profile)
    return {"competitor_summary": comparison}


def node_risk_flagger(state: DDState) -> DDState:
    news = get_recent_news(state["company_name"])
    risk = risk_flagger_agent(state["company_name"], state["metrics"], news)
    return {"news_snippets": news, "risk_output": risk}


def node_briefing(state: DDState) -> DDState:
    brief = briefing_agent(
        company_name=state["company_name"],
        ticker=state["ticker"],
        metrics=state["metrics"],
        competitor_summary=state["competitor_summary"],
        risk_output=state["risk_output"],
    )
    return {"brief": brief}


def build_graph():
    graph = StateGraph(DDState)
    graph.add_node("extractor", node_extractor)
    graph.add_node("benchmarker", node_benchmarker)
    graph.add_node("risk_flagger", node_risk_flagger)
    graph.add_node("briefing", node_briefing)

    graph.set_entry_point("extractor")
    graph.add_edge("extractor", "benchmarker")
    graph.add_edge("benchmarker", "risk_flagger")
    graph.add_edge("risk_flagger", "briefing")
    graph.add_edge("briefing", END)

    return graph.compile()


def run_due_diligence(ticker: str) -> DDState:
    app = build_graph()
    result = app.invoke({"ticker": ticker.upper()})
    return result


if __name__ == "__main__":
    import json
    result = run_due_diligence("AAPL")
    print(json.dumps(result, indent=2, default=str))
FILEEOF

cat > 'ui/app.py' << 'FILEEOF'
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
FILEEOF

echo "All files created/updated."
