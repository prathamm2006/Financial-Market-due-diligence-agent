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

    IMPORTANT: many companies report the same concept under DIFFERENT GAAP
    tags in different eras — e.g. revenue was tagged "Revenues" before the
    2018 ASC 606 accounting standard change, and
    "RevenueFromContractWithCustomerExcludingAssessedTax" after. A company's
    full historical XBRL record includes BOTH tags. For each metric we
    therefore check every known synonym tag and merge results by year
    (newest-tag-first on any year both tags report), instead of stopping at
    the first tag that has any data at all — otherwise we can silently lock
    onto a years-stale tag even though fresh data exists under the newer one.
    """
    us_gaap = company_facts.get("facts", {}).get("us-gaap", {})
    ANNUAL_FORMS = {"10-K", "20-F"}
    # Lists are ordered newest-tag-first — on a year reported under multiple
    # tags, the earlier (newer-standard) tag's value wins.
    wanted_groups = {
        "revenue": [
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "RevenueFromContractWithCustomerIncludingAssessedTax",
            "Revenues",
        ],
        "net_income": ["NetIncomeLoss"],
        "total_assets": ["Assets"],
        "total_liabilities": ["Liabilities"],
        "cash": ["CashAndCashEquivalentsAtCarryingValue"],
        "long_term_debt": ["LongTermDebtNoncurrent"],
        "operating_income": ["OperatingIncomeLoss"],
    }

    metrics = {}
    for clean_name, tag_list in wanted_groups.items():
        year_to_value = {}  # year -> value; first (newest) tag to report a year wins
        for gaap_tag in tag_list:
            if gaap_tag not in us_gaap:
                continue
            usd_facts = us_gaap[gaap_tag].get("units", {}).get("USD", [])
            annual = [
                f for f in usd_facts
                if f.get("form") in ANNUAL_FORMS and f.get("fp") == "FY"
            ]
            for f in annual:
                yr = f["end"][:4]
                if yr not in year_to_value:
                    year_to_value[yr] = f["val"]
        if year_to_value:
            top_years = sorted(year_to_value.keys(), reverse=True)[:years]
            metrics[clean_name] = [{"year": y, "value": year_to_value[y]} for y in top_years]

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
    # Direct link to this company's actual filing index on SEC EDGAR — lets
    # a user verify any extracted number against the primary source, which
    # matters a lot for a due-diligence tool specifically.
    filing_index_url = (
        f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
        f"&CIK={cik}&type=10-K&dateb=&owner=include&count=10"
    )
    return {
        "ticker": ticker.upper(),
        "cik": cik,
        "company_name": company_name,
        "metrics": metrics,
        "filing_index_url": filing_index_url,
    }


if __name__ == "__main__":
    # Quick manual test — run: python edgar_client.py
    profile = get_company_profile("AAPL")
    import json
    print(json.dumps(profile, indent=2))
