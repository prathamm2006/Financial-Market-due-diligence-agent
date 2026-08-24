"""
Alternate data source for companies SEC EDGAR doesn't cover — primarily
Indian (NSE/BSE) listings, but works for any market Yahoo Finance tracks.
Mirrors edgar_client.get_company_profile()'s output shape exactly, so the
rest of the pipeline (forecaster, valuation, risk, briefing) doesn't need
to know or care which data source a given ticker came from.
"""
import yfinance as yf

# Maps yfinance's annual-statement row labels to our internal clean metric
# names — same target shape as edgar_client's extraction, different source.
INCOME_STMT_MAP = {
    "Total Revenue": "revenue",
    "Net Income": "net_income",
    "Operating Income": "operating_income",
}
BALANCE_SHEET_MAP = {
    "Total Assets": "total_assets",
    "Total Liabilities Net Minority Interest": "total_liabilities",
    "Cash And Cash Equivalents": "cash",
    "Long Term Debt": "long_term_debt",
}


def _extract_from_statement(df, row_map: dict, years: int = 3) -> dict:
    """Pulls up to `years` most recent annual values for each mapped row
    from a yfinance annual statement DataFrame (index=line items,
    columns=period-end dates)."""
    metrics = {}
    if df is None or df.empty:
        return metrics
    for row_name, clean_name in row_map.items():
        if row_name not in df.index:
            continue
        row = df.loc[row_name].dropna().sort_index(ascending=False)
        series = []
        for date, val in row.items():
            series.append({"year": str(date.year), "value": float(val)})
            if len(series) >= years:
                break
        if series:
            metrics[clean_name] = series
    return metrics


def get_company_profile_yf(ticker: str, years: int = 3) -> dict:
    """
    Same contract as edgar_client.get_company_profile(): given a ticker,
    returns {ticker, company_name, metrics, filing_index_url, currency}.
    Used for any ticker outside SEC's coverage — primarily NSE/BSE (.NS/.BO
    suffix) Indian listings.
    """
    t = yf.Ticker(ticker)
    try:
        info = t.info
    except Exception as e:
        raise ValueError(f"Could not reach Yahoo Finance for '{ticker}': {e}")

    if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
        raise ValueError(
            f"'{ticker}' returned no usable data from Yahoo Finance. This "
            "usually means one of: (1) the exchange suffix is wrong — NSE "
            "tickers need '.NS' (e.g. 'RELIANCE.NS'), BSE tickers need "
            "'.BO'; (2) the company underwent a corporate rename/symbol "
            "change and this ticker is now stale (this happens periodically "
            "in India — e.g. Zomato became 'ETERNAL.NS' in 2025); or (3) "
            "it's a typo. Try a well-known ticker like RELIANCE.NS or "
            "TCS.NS to confirm the pipeline itself is working."
        )

    company_name = info.get("longName") or info.get("shortName") or ticker
    currency = info.get("currency", "USD")

    metrics = {}
    try:
        metrics.update(_extract_from_statement(t.income_stmt, INCOME_STMT_MAP, years))
    except Exception:
        pass
    try:
        metrics.update(_extract_from_statement(t.balance_sheet, BALANCE_SHEET_MAP, years))
    except Exception:
        pass

    if not metrics:
        raise ValueError(
            f"Found '{company_name}' on Yahoo Finance but no usable annual "
            "financial statement data was available — this can happen for "
            "very recently listed or thinly-covered companies."
        )

    # screener.in is the standard free fundamentals-verification resource
    # for Indian equities (India's equivalent of "check the source filing").
    symbol_clean = ticker.split(".")[0]
    filing_index_url = f"https://www.screener.in/company/{symbol_clean}/"

    return {
        "ticker": ticker.upper(),
        "cik": None,
        "company_name": company_name,
        "metrics": metrics,
        "filing_index_url": filing_index_url,
        "currency": currency,
    }
