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
