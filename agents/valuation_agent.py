"""
Valuation agent — pulls live market data (price, market cap, shares
outstanding) via yfinance and computes standard valuation multiples,
then compares them against the same peer set the Benchmarker agent uses.

This is the piece that turns the tool from "financial summary" into
"is it cheap or expensive" — the question every real analyst brief
answers and which was previously missing entirely.

Deliberately NOT an LLM call: multiples are arithmetic on live prices,
and getting that arithmetic right matters more than making it sound good.
"""
from data.yfinance_client import get_cached_info


def _safe_ratio(numerator, denominator):
    if numerator is None or denominator in (None, 0):
        return None
    return round(numerator / denominator, 2)


def get_valuation_snapshot(ticker: str, net_income: float | None, operating_income: float | None) -> dict:
    """
    Returns live valuation multiples for a ticker. net_income and
    operating_income (as an EBITDA proxy — true EBITDA needs D&A add-back
    which isn't in our current XBRL pull, so this is explicitly flagged
    as an approximation) come from the already-extracted SEC data so we
    don't have two disagreeing sources of "latest earnings."
    """
    try:
        info = get_cached_info(ticker)
    except Exception as e:
        return {"available": False, "reason": f"Market data lookup failed: {e}"}

    price = info.get("currentPrice") or info.get("regularMarketPrice")
    market_cap = info.get("marketCap")
    shares_out = info.get("sharesOutstanding")
    total_debt = info.get("totalDebt")
    cash = info.get("totalCash")

    if market_cap is None:
        return {"available": False, "reason": "No market cap data returned — ticker may be illiquid or delisted."}

    enterprise_value = None
    if market_cap is not None and total_debt is not None and cash is not None:
        enterprise_value = market_cap + total_debt - cash

    pe_ratio = _safe_ratio(market_cap, net_income) if net_income and net_income > 0 else None
    ev_ebitda_proxy = _safe_ratio(enterprise_value, operating_income) if operating_income and operating_income > 0 else None
    revenue = info.get("totalRevenue")
    price_to_sales = _safe_ratio(market_cap, revenue)

    return {
        "available": True,
        "price": price,
        "market_cap": market_cap,
        "enterprise_value": enterprise_value,
        "pe_ratio": pe_ratio,
        "ev_ebitda_proxy": ev_ebitda_proxy,
        "price_to_sales": price_to_sales,
        "note": (
            "EV/EBITDA uses operating income as an EBITDA proxy (no D&A "
            "add-back available from current data sources) — treat as "
            "directionally indicative, not precise."
        ),
    }


def valuation_agent(ticker: str, metrics: dict, peer_tickers: list[str]) -> dict:
    """
    Computes valuation for the target and each peer so the Briefing agent
    can answer 'is it cheap or expensive relative to peers' — not just
    'is it growing.'
    """
    def latest(key):
        series = metrics.get(key, [])
        return series[0]["value"] if series else None

    target_val = get_valuation_snapshot(ticker, latest("net_income"), latest("operating_income"))
    target_val["ticker"] = ticker

    peer_valuations = {}
    for peer in peer_tickers:
        # Peers' own net_income/operating_income aren't available here without
        # another SEC round-trip, so peer P/E uses trailing P/E from yfinance
        # directly (Yahoo's own trailing EPS calc) rather than our SEC figures —
        # still apples-to-apples for a "cheap vs expensive" comparison.
        try:
            info = get_cached_info(peer)
            peer_valuations[peer] = {
                "pe_ratio": info.get("trailingPE"),
                "price_to_sales": info.get("priceToSalesTrailing12Months"),
                "market_cap": info.get("marketCap"),
            }
        except Exception:
            peer_valuations[peer] = {"pe_ratio": None, "price_to_sales": None, "market_cap": None}

    return {"target": target_val, "peers": peer_valuations}
