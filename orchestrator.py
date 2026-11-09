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

from data.company_data import get_company_profile
from data.news_client import get_recent_news
from agents.benchmarker_agent import benchmark_against_peers, get_peers
from agents.forecaster_agent import forecast_agent
from agents.backtester import backtest_company, compact_for_prompt
from agents.valuation_agent import valuation_agent
from agents.llm_agents import risk_flagger_agent, briefing_agent


class DDState(TypedDict, total=False):
    ticker: str
    company_name: str
    metrics: dict
    metrics_long: dict
    currency: str
    filing_index_url: str
    competitor_summary: dict
    forecast_output: dict
    backtest_output: dict
    valuation_output: dict
    news_snippets: list
    risk_output: dict
    brief: dict
    error: Optional[str]


def node_extractor(state: DDState) -> DDState:
    profile = get_company_profile(state["ticker"])
    return {
        "company_name": profile["company_name"],
        "metrics": profile["metrics"],
        "metrics_long": profile.get("metrics_long", profile["metrics"]),
        "filing_index_url": profile.get("filing_index_url", ""),
        "currency": profile.get("currency", "USD"),
    }


def node_benchmarker(state: DDState) -> DDState:
    profile = {"ticker": state["ticker"], "metrics": state["metrics"]}
    comparison = benchmark_against_peers(profile)
    return {"competitor_summary": comparison}


def node_forecaster(state: DDState) -> DDState:
    forecasts = forecast_agent(state["metrics"], years_ahead=2)
    return {"forecast_output": forecasts}


def node_backtester(state: DDState) -> DDState:
    """Scores the forecasting method against this company's own past years.
    Non-critical: if it fails for any reason the brief is still produced,
    just without a track record."""
    try:
        result = backtest_company(state.get("metrics_long", state["metrics"]), company=state["ticker"])
    except Exception as e:
        result = {"available": False, "reason": f"Backtest skipped: {e}", "summary": {}, "records": [], "notes": []}
    return {"backtest_output": result}


def node_valuation(state: DDState) -> DDState:
    peers = get_peers(state["ticker"])
    valuation = valuation_agent(state["ticker"], state["metrics"], peers)
    return {"valuation_output": valuation}


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
        valuation_output=state.get("valuation_output", {}),
        currency=state.get("currency", "USD"),
        backtest_context=compact_for_prompt(state.get("backtest_output")),
    )
    return {"brief": brief}


def build_graph():
    graph = StateGraph(DDState)
    graph.add_node("extractor", node_extractor)
    graph.add_node("benchmarker", node_benchmarker)
    graph.add_node("forecaster", node_forecaster)
    graph.add_node("backtester", node_backtester)
    graph.add_node("valuation", node_valuation)
    graph.add_node("risk_flagger", node_risk_flagger)
    graph.add_node("briefing", node_briefing)

    graph.set_entry_point("extractor")
    graph.add_edge("extractor", "benchmarker")
    graph.add_edge("benchmarker", "forecaster")
    graph.add_edge("forecaster", "backtester")
    graph.add_edge("backtester", "valuation")
    graph.add_edge("valuation", "risk_flagger")
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
