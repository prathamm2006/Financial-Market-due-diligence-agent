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
