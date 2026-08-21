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


def get_all_tickers() -> list[dict]:
    """
    Returns the full list of tickers SEC currently tracks, as
    [{"ticker": "AAPL", "title": "Apple Inc."}, ...] sorted alphabetically.
    Used to power a searchable dropdown so users don't have to guess
    valid tickers or hit 'not found' errors.
    """
    resp = requests.get(TICKER_MAP_URL, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    tickers = [{"ticker": entry["ticker"], "title": entry["title"]} for entry in data.values()]
    tickers.sort(key=lambda t: t["ticker"])
    return tickers


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
