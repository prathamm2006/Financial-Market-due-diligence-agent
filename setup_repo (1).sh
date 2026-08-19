#!/bin/bash
set -e
mkdir -p data agents ui .devcontainer .streamlit .github/workflows

cat > 'requirements.txt' << 'FILEEOF'
google-genai>=0.3.0
plotly>=5.24.0
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

- **Ticker coverage**: works for any company SEC currently tracks with standard
  XBRL financial tags — both US-domestic filers (Form 10-K) and foreign
  private issuers (Form 20-F, e.g. Toyota, Sony). It will NOT work for
  companies that have delisted/deregistered from US markets (e.g. Tata
  Motors, ticker `TTM`, delisted from NYSE in Jan 2023) or that never filed
  with the SEC at all (most non-US-listed companies).
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
    raise ValueError(
        f"Ticker '{ticker}' was not found in SEC's active filer list. "
        "This usually means: (1) it's not a US-listed company SEC currently "
        "tracks, (2) it was delisted/deregistered, or (3) it's a typo. "
        "Try a well-known ticker like AAPL, MSFT, TGT, or JPM to confirm the "
        "pipeline itself is working."
    )


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

    Supports both US-domestic annual filers (Form 10-K) and foreign private
    issuers (Form 20-F, e.g. Toyota, Sony, Alibaba) — without this, any
    non-US-domestic ticker would silently return empty metrics even when
    its CIK/filings are found, which reads as a confusing bug rather than
    a coverage limit.
    """
    us_gaap = company_facts.get("facts", {}).get("us-gaap", {})
    ANNUAL_FORMS = {"10-K", "20-F"}
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
        # Keep only annual (full fiscal year) data points, most recent first
        annual = [
            f for f in usd_facts
            if f.get("form") in ANNUAL_FORMS and f.get("fp") == "FY"
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
    if not metrics:
        raise ValueError(
            f"Found '{company_name}' in SEC EDGAR (CIK {cik}), but no usable "
            "10-K/20-F annual financial data was available in the standard "
            "XBRL tags this tool reads. This can happen for holding "
            "companies, recent IPOs with limited filing history, or filers "
            "using non-standard GAAP tags."
        )
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

cat > 'agents/forecaster_agent.py' << 'FILEEOF'
"""
Forecasting agent — computes real trend-based financial projections from
historical SEC data. Deliberately NOT an LLM call: forecasting is arithmetic
(CAGR, linear regression), and having code do arithmetic instead of an LLM
is both more accurate and the correct engineering call. The LLM's job
(in the Briefing agent) is to interpret these numbers, not calculate them.
"""
import statistics


def _cagr(start_value: float, end_value: float, periods: int) -> float | None:
    """Compound Annual Growth Rate between two points, `periods` years apart."""
    if start_value is None or end_value is None or start_value <= 0 or periods <= 0:
        return None
    return (end_value / start_value) ** (1 / periods) - 1


def _linear_trend_forecast(series: list[dict], years_ahead: int = 2) -> list[dict]:
    """
    Simple linear regression on historical (year, value) pairs, extrapolated
    forward. `series` is expected most-recent-first (as EDGAR client returns),
    so we reverse it for chronological fitting.
    """
    chrono = list(reversed(series))  # oldest -> newest
    if len(chrono) < 2:
        return []

    years = [int(pt["year"]) for pt in chrono]
    values = [pt["value"] for pt in chrono]
    n = len(years)
    x_mean = statistics.mean(years)
    y_mean = statistics.mean(values)

    numerator = sum((years[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((years[i] - x_mean) ** 2 for i in range(n))
    if denominator == 0:
        return []

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean

    last_year = max(years)
    projections = []
    for i in range(1, years_ahead + 1):
        proj_year = last_year + i
        proj_value = slope * proj_year + intercept
        projections.append({"year": str(proj_year), "value": round(proj_value, 0), "projected": True})
    return projections


def forecast_metric(series: list[dict], years_ahead: int = 2) -> dict:
    """
    Given a metric's historical series (most-recent-first, from edgar_client),
    returns CAGR, a linear-trend projection, and an honest confidence note.
    """
    if not series or len(series) < 2:
        return {
            "cagr_pct": None,
            "projections": [],
            "confidence": "insufficient_data",
            "note": "Fewer than 2 years of history available — cannot compute a reliable trend.",
        }

    chrono = list(reversed(series))
    start = chrono[0]["value"]
    end = chrono[-1]["value"]
    periods = int(chrono[-1]["year"]) - int(chrono[0]["year"])
    cagr = _cagr(start, end, periods) if periods > 0 else None

    projections = _linear_trend_forecast(series, years_ahead=years_ahead)

    # Confidence is honest, not decorative: short history or wildly volatile
    # trends get flagged, not silently smoothed over.
    values = [pt["value"] for pt in chrono]
    volatility = statistics.pstdev(values) / statistics.mean(values) if statistics.mean(values) else None
    if len(chrono) < 3:
        confidence = "low"
    elif volatility is not None and volatility > 0.25:
        confidence = "low"
    elif len(chrono) >= 4:
        confidence = "moderate"
    else:
        confidence = "low"

    return {
        "cagr_pct": round(cagr * 100, 1) if cagr is not None else None,
        "projections": projections,
        "confidence": confidence,
        "note": (
            f"Linear trend on {len(chrono)} years of reported data. "
            "This is a naive projection method (no seasonality, macro, or "
            "competitive dynamics modeled) — treat as a directional estimate only."
        ),
    }


def forecast_agent(metrics: dict, years_ahead: int = 2) -> dict:
    """
    Runs forecasts on the key metrics that matter most for a due-diligence
    read: revenue and net income. Returns a clean dict ready for both the
    chart and the LLM synthesis step.
    """
    result = {}
    for key in ("revenue", "net_income", "operating_income"):
        if key in metrics:
            result[key] = forecast_metric(metrics[key], years_ahead=years_ahead)
    return result
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
from google import genai
from google.genai import types


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


MODEL = "gemini-2.5-flash"
_client = None


def _get_client():
    """Lazily creates the Gemini client so importing this module never
    crashes just because the API key isn't set yet — only calling an
    agent function requires it."""
    global _client
    if _client is None:
        api_key = _get_secret("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. Get a free key at "
                "https://aistudio.google.com/apikey and export it, e.g.\n"
                '  export GOOGLE_API_KEY="your-key-here"'
            )
        _client = genai.Client(api_key=api_key)
    return _client


def _call_gemini_json(system: str, user: str) -> dict:
    """Helper: call Gemini, force JSON-only output via response_mime_type, parse it safely."""
    resp = _get_client().models.generate_content(
        model=MODEL,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
        ),
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
                    competitor_summary: dict, risk_output: dict,
                    forecast_output: dict) -> dict:
    """
    The synthesis agent — takes everything the other agents produced
    (including COMPUTED forecasts, not LLM-guessed ones) and writes the
    executive-ready brief. The LLM's job here is interpretation and
    narrative, not arithmetic — the numbers it's given are already correct.
    """
    system = (
        "You are a senior equity research analyst with 15+ years of experience "
        "writing due-diligence briefs for investment committee partners. "
        "You write with the precision and directness of a real analyst note — "
        "specific numbers, specific percentages, explicit reasoning for your "
        "call. You never write generic filler like 'the company shows strong "
        "fundamentals' without citing the exact figure that supports it. "
        "You are given ALREADY-COMPUTED forecast figures (CAGR, trend "
        "projections) — use them, cite them, but never invent numbers not "
        "given to you. Respond with ONLY valid JSON."
    )
    user = f"""
Company: {company_name} ({ticker})

Historical financial metrics (most recent year first):
{json.dumps(metrics, indent=2)}

Computed forward-looking forecasts (CAGR + linear trend projections,
already calculated — cite these directly, do not recompute):
{json.dumps(forecast_output, indent=2)}

Competitor benchmark:
{json.dumps(competitor_summary, indent=2)}

Risk analysis:
{json.dumps(risk_output, indent=2)}

Return JSON in exactly this shape:
{{
  "headline": "one sharp sentence verdict, e.g. 'Steady grower with margin pressure — proceed with valuation discipline'",
  "financial_summary": "3-4 sentences citing exact revenue/net income figures and YoY or CAGR growth rates from the data given",
  "forecast_analysis": "2-3 sentences interpreting the computed CAGR and trend projections — what it implies, and explicitly flag the confidence level given (low/moderate) and why that matters for reliance on the number",
  "competitive_position": "2-3 sentences vs the named competitors, citing specific margin/revenue comparisons from the data",
  "key_risks": ["short bullet citing a specific figure or event", "short bullet citing a specific figure or event"],
  "recommendation": "one paragraph: proceed / proceed with caution / pass — with explicit reasoning tied to the numbers above, not generic advice",
  "limitations": "one sentence on what this brief does NOT cover (e.g. qualitative diligence, legal review, macro assumptions, DCF-grade valuation)"
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
from agents.forecaster_agent import forecast_agent
from agents.llm_agents import risk_flagger_agent, briefing_agent


class DDState(TypedDict, total=False):
    ticker: str
    company_name: str
    metrics: dict
    competitor_summary: dict
    forecast_output: dict
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


def node_forecaster(state: DDState) -> DDState:
    forecasts = forecast_agent(state["metrics"], years_ahead=2)
    return {"forecast_output": forecasts}


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
        forecast_output=state["forecast_output"],
    )
    return {"brief": brief}


def build_graph():
    graph = StateGraph(DDState)
    graph.add_node("extractor", node_extractor)
    graph.add_node("benchmarker", node_benchmarker)
    graph.add_node("forecaster", node_forecaster)
    graph.add_node("risk_flagger", node_risk_flagger)
    graph.add_node("briefing", node_briefing)

    graph.set_entry_point("extractor")
    graph.add_edge("extractor", "benchmarker")
    graph.add_edge("benchmarker", "forecaster")
    graph.add_edge("forecaster", "risk_flagger")
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
st.markdown(
    f"""
    <div class="ledger-header">
      <div>
        <div class="ledger-title">Due-Diligence Agent</div>
        <div class="ledger-sub">multi-agent research pipeline · SEC EDGAR · live synthesis</div>
      </div>
      <div class="ledger-tag">{datetime.now().strftime('%d %b %Y')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

col_input, col_btn = st.columns([4, 1])
with col_input:
    ticker = st.text_input("Ticker", value="AAPL", label_visibility="collapsed", placeholder="Enter ticker, e.g. AAPL").upper()
with col_btn:
    run_btn = st.button("Run analysis", use_container_width=True)

# ---------------------------------------------------------------------------
# PIPELINE EXECUTION — visible agent-by-agent progress (this IS the product;
# showing the pipeline work is more credible than a spinner hiding it)
# ---------------------------------------------------------------------------
def run_with_progress(ticker: str):
    app = build_graph()
    state = {"ticker": ticker}
    stages = [
        ("extractor", "Pulling SEC EDGAR filings"),
        ("benchmarker", "Benchmarking against peers"),
        ("forecaster", "Computing trend forecasts"),
        ("risk_flagger", "Scanning for risk signals"),
        ("briefing", "Synthesizing executive brief"),
    ]
    progress_box = st.empty()
    completed = []
    result = {}
    for node_name, label in stages:
        with progress_box.container():
            lines = [f"<span class='pos'>✓</span> {done}" for done in completed]
            lines.append(f"<span class='neu'>▸</span> {label}...")
            st.markdown(
                f"<div class='metric-card'><div style='font-family:IBM Plex Mono,monospace; font-size:0.85rem; line-height:1.9;'>"
                + "<br>".join(lines) + "</div></div>",
                unsafe_allow_html=True,
            )
        for event in app.stream(state, stream_mode="values"):
            result = event
        completed.append(label)
        state = result
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

    if "error" in brief:
        st.warning("Briefing agent had trouble parsing output — see raw below.")
        st.json(brief)
        st.stop()

    # -- Headline verdict -----------------------------------------------
    st.markdown(f"### {company_name} <span style='color:var(--muted); font-family:IBM Plex Mono,monospace; font-size:1rem;'>{ticker}</span>", unsafe_allow_html=True)
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

    def fmt_usd(val):
        if val is None:
            return "—"
        if abs(val) >= 1e9:
            return f"${val/1e9:.1f}B"
        if abs(val) >= 1e6:
            return f"${val/1e6:.1f}M"
        return f"${val:,.0f}"

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

    # -- Chart: history + projection ----------------------------------------
    st.markdown("<div class='section-label'>Revenue — historical &amp; projected</div>", unsafe_allow_html=True)
    if metrics.get("revenue"):
        hist = list(reversed(metrics["revenue"]))
        proj = forecast.get("revenue", {}).get("projections", [])
        conf = forecast.get("revenue", {}).get("confidence", "low")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[p["year"] for p in hist], y=[p["value"] for p in hist],
            name="Reported", marker_color="#C99A3C", width=0.5,
        ))
        if proj:
            fig.add_trace(go.Bar(
                x=[p["year"] for p in proj], y=[p["value"] for p in proj],
                name="Projected (linear trend)", marker_color="rgba(201,154,60,0.28)",
                marker_line=dict(color="#C99A3C", width=1), width=0.5,
            ))
        fig.update_layout(
            plot_bgcolor="#131A2B", paper_bgcolor="#131A2B",
            font=dict(family="IBM Plex Mono, monospace", color="#8792AB", size=11),
            margin=dict(l=10, r=10, t=10, b=10), height=280,
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

    st.divider()
    with st.expander("Competitor benchmark data"):
        st.json(result.get("competitor_summary", {}))
    with st.expander("Forecast agent raw output"):
        st.json(forecast)
    with st.expander("Risk agent raw output"):
        st.json(result.get("risk_output", {}))
    with st.expander("Full pipeline state (debugging / interview walkthrough)"):
        st.json(result)
FILEEOF

echo "All files created/updated."