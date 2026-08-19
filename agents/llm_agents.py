"""
The two 'thinking' agents in the pipeline. Both call Claude with structured
prompts and JSON-mode output so results are predictable and chartable,
not free-text blobs.

Requires: ANTHROPIC_API_KEY environment variable.
"""
import os
import json
import anthropic


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


client = anthropic.Anthropic(api_key=_get_secret("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


def _call_claude_json(system: str, user: str) -> dict:
    """Helper: call Claude, force JSON-only output, parse it safely."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = resp.content[0].text.strip()
    # Strip accidental markdown fences
    text = text.replace("```json", "").replace("```", "").strip()
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
    return _call_claude_json(system, user)


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
    return _call_claude_json(system, user)
