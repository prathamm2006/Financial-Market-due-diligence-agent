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


def _scenario_projections(last_actual: float, last_year: int, cagr: float, years_ahead: int) -> dict:
    """
    Compound-growth scenario bands around the historical CAGR — this is
    the 'consultant lens' addition: a single-point forecast implies false
    precision, whereas a bear/base/bull range makes the uncertainty
    explicit and is how real financial models are actually presented.

    The spread is a simple ±50% of the historical CAGR (with a 3% floor
    so near-zero CAGRs still produce a visible range) — deliberately a
    transparent, explainable heuristic rather than a black-box model.
    """
    spread = max(abs(cagr) * 0.5, 0.03)
    bear_rate = cagr - spread
    bull_rate = cagr + spread
    scenarios = {"bear": [], "base": [], "bull": []}
    for i in range(1, years_ahead + 1):
        yr = str(last_year + i)
        scenarios["bear"].append({"year": yr, "value": round(last_actual * (1 + bear_rate) ** i)})
        scenarios["base"].append({"year": yr, "value": round(last_actual * (1 + cagr) ** i)})
        scenarios["bull"].append({"year": yr, "value": round(last_actual * (1 + bull_rate) ** i)})
    return scenarios


def forecast_metric(series: list[dict], years_ahead: int = 2) -> dict:
    """
    Given a metric's historical series (most-recent-first, from edgar_client),
    returns CAGR, a linear-trend projection, bull/base/bear scenario bands,
    and an honest confidence note.
    """
    if not series or len(series) < 2:
        return {
            "cagr_pct": None,
            "projections": [],
            "scenarios": {"bear": [], "base": [], "bull": []},
            "confidence": "insufficient_data",
            "note": "Fewer than 2 years of history available — cannot compute a reliable trend.",
        }

    chrono = list(reversed(series))
    start = chrono[0]["value"]
    end = chrono[-1]["value"]
    periods = int(chrono[-1]["year"]) - int(chrono[0]["year"])
    cagr = _cagr(start, end, periods) if periods > 0 else None

    projections = _linear_trend_forecast(series, years_ahead=years_ahead)

    scenarios = {"bear": [], "base": [], "bull": []}
    if cagr is not None:
        scenarios = _scenario_projections(
            last_actual=chrono[-1]["value"],
            last_year=int(chrono[-1]["year"]),
            cagr=cagr,
            years_ahead=years_ahead,
        )

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
        "scenarios": scenarios,
        "confidence": confidence,
        "note": (
            f"Linear trend on {len(chrono)} years of reported data. "
            "This is a naive projection method (no seasonality, macro, or "
            "competitive dynamics modeled) — treat as a directional estimate only. "
            "Bull/bear bands apply a ±50% spread around the historical CAGR as a "
            "simple sensitivity range, not a probabilistic forecast."
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
