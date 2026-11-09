"""
Offline end-to-end tests: the whole LangGraph pipeline and the real Streamlit
page, with SEC / Yahoo Finance / Gemini replaced by fakes. These catch wiring
bugs (missing functions, mismatched progress labels, state-key typos) that
unit tests and compile checks cannot.
"""
import ast
from pathlib import Path

import pytest

APP_PATH = Path(__file__).resolve().parent.parent / "ui" / "app.py"

YEARS = list(range(2016, 2026))


def _series(start, growth):
    vals = [start * (1 + growth) ** i for i in range(len(YEARS))]
    return list(reversed([{"year": str(y), "value": float(v)} for y, v in zip(YEARS, vals)]))


def fake_profile(ticker, years=3):
    long_ = {
        "revenue": _series(100e9, 0.08),
        "net_income": _series(20e9, 0.07),
        "operating_income": _series(30e9, 0.07),
        "total_assets": _series(300e9, 0.05),
    }
    return {
        "ticker": ticker, "cik": "0000000001", "company_name": f"{ticker} Test Corp",
        "metrics": {k: v[:years] for k, v in long_.items()},
        "metrics_long": long_, "filing_index_url": "https://example.com/filings",
        "currency": "USD",
    }


FAKE_INFO = {"currentPrice": 200.0, "marketCap": 3.0e12, "totalDebt": 1.0e11,
             "totalCash": 6.0e10, "totalRevenue": 4.0e11, "trailingPE": 30.0,
             "priceToSalesTrailing12Months": 7.5, "longName": "Fake Co", "currency": "USD"}

BRIEF = {
    "headline": "Steady grower - proceed with discipline",
    "financial_summary": "Revenue grew steadily.", "forecast_analysis": "CAGR near 8%.",
    "valuation_analysis": "Trades at 30x earnings.", "competitive_position": "Leads peers.",
    "key_risks": ["Concentration"], "recommendation": "Proceed with caution.",
    "limitations": "Not a DCF.",
}
RISK = {"risk_flags": [{"flag": "Concentration", "severity": "low", "evidence": "x"}],
        "overall_risk_level": "low", "confidence_note": "n/a"}

captured_prompts = []


def fake_gemini(system, user, max_retries=3):
    if "credit risk analyst" in system:
        return RISK
    captured_prompts.append(user)
    return BRIEF


@pytest.fixture
def offline(monkeypatch):
    import orchestrator
    import agents.benchmarker_agent as bench
    import agents.valuation_agent as val
    import agents.llm_agents as llm
    import data.edgar_client as edgar
    captured_prompts.clear()
    monkeypatch.setattr(orchestrator, "get_company_profile", fake_profile)
    monkeypatch.setattr(bench, "get_company_profile", fake_profile)
    monkeypatch.setattr(orchestrator, "get_recent_news", lambda *a, **k: [])
    monkeypatch.setattr(val, "get_cached_info", lambda t: dict(FAKE_INFO))
    monkeypatch.setattr(llm, "_call_gemini_json", fake_gemini)
    monkeypatch.setattr(edgar, "get_all_tickers", lambda: [{"ticker": "AAPL", "title": "Apple Inc."}])
    return orchestrator


def test_full_pipeline_runs_and_produces_a_backtest(offline):
    app = offline.build_graph()
    events = list(app.stream({"ticker": "AAPL"}, stream_mode="values"))
    final = events[-1]
    assert len(events) == 8                                   # start state + 7 agents
    assert final["backtest_output"]["available"] is True
    assert final["brief"]["headline"] == BRIEF["headline"]
    assert "metrics_long" in final


def test_briefing_prompt_contains_the_computed_track_record(offline):
    offline.build_graph().invoke({"ticker": "AAPL"})
    prompt = captured_prompts[-1]
    assert "Forecast track record" in prompt
    assert "Across" in prompt and "past forecasts" in prompt   # headline from the backtester


def test_pipeline_survives_a_failing_backtest(offline, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("synthetic failure")
    monkeypatch.setattr(offline, "backtest_company", boom)
    final = offline.build_graph().invoke({"ticker": "AAPL"})
    assert final["backtest_output"]["available"] is False
    assert "synthetic failure" in final["backtest_output"]["reason"]
    assert final["brief"]["headline"]                          # brief still produced


def test_short_history_markets_degrade_gracefully(offline, monkeypatch):
    def short_profile(ticker, years=3):
        p = fake_profile(ticker, years)
        p["metrics_long"] = {k: v[:4] for k, v in p["metrics_long"].items()}   # Yahoo-style 4 years
        return p
    monkeypatch.setattr(offline, "get_company_profile", short_profile)
    final = offline.build_graph().invoke({"ticker": "AAPL"})
    assert final["backtest_output"]["available"] is False
    assert "meaningful check" in final["backtest_output"]["reason"]


def test_progress_labels_match_graph_nodes():
    import orchestrator
    tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
    labels = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "stage_labels" for t in node.targets):
            labels = [e.value for e in node.value.elts]
    nodes = [n for n in orchestrator.build_graph().nodes if n != "__start__"]
    assert labels is not None and len(labels) == len(nodes)


def test_streamlit_page_renders_the_track_record(offline):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(APP_PATH), default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
    at.button[0].click().run()
    assert not at.exception, [e.value for e in at.exception]
    text = " ".join(m.value for m in at.markdown)
    assert "Forecast track record" in text
    assert "beats a no-change guess" in text or "no-change guess" in text
    captions = " ".join(c.value for c in at.caption)
    assert "Revenue, scored over" in captions
