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
