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
