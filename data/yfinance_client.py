"""
Alternate data source for companies SEC EDGAR doesn't cover — primarily
Indian (NSE/BSE) listings, but works for any market Yahoo Finance tracks.
Mirrors edgar_client.get_company_profile()'s output shape exactly, so the
rest of the pipeline (forecaster, valuation, risk, briefing) doesn't need
to know or care which data source a given ticker came from.
"""
import time
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

# Exchange suffixes whose home currency we know even if Yahoo's reply is
# empty — prevents an Indian stock being mislabeled as USD.
_SUFFIX_CURRENCY = {".NS": "INR", ".BO": "INR"}

# --- Shared cache + retry layer --------------------------------------------
# A single pipeline run can touch the same ticker from several agents
# (Extractor, Benchmarker, Valuation), so results are cached briefly to
# keep the number of Yahoo requests low. IMPORTANT: only *valid* responses
# are cached. Yahoo frequently answers a throttled request with a nearly
# empty dictionary instead of raising an error; caching that would poison
# every retry for the next few minutes even though the ticker is fine.
_CACHE_TTL_SECONDS = 300
_info_cache: dict[str, tuple[float, dict]] = {}
_statement_cache: dict[str, tuple[float, tuple]] = {}

_PRICE_KEYS = ("regularMarketPrice", "currentPrice", "previousClose")
_TRANSIENT_MARKERS = (
    "Too Many Requests", "Rate limited", "YFRateLimitError", "429",
    "timeout", "timed out", "Connection",
)


def _retry_yfinance_call(fn, max_retries: int = 3):
    """Retries a yfinance call with exponential backoff on rate-limit /
    transient errors, rather than failing the whole pipeline on the first
    'Too Many Requests' response."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            last_error = e
            is_transient = any(s in str(e) for s in _TRANSIENT_MARKERS)
            if is_transient and attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s
                continue
            raise
    raise last_error


def _info_is_valid(info) -> bool:
    """True if a yfinance .info reply actually identifies the company or
    quotes a price. Throttled replies are often near-empty dicts."""
    if not info or not isinstance(info, dict):
        return False
    if any(info.get(k) is not None for k in _PRICE_KEYS):
        return True
    if info.get("longName") or info.get("shortName"):
        return True
    return info.get("marketCap") is not None


def _df_has_data(df) -> bool:
    return df is not None and hasattr(df, "empty") and not df.empty


def _info_from_fast_info(ticker: str) -> dict:
    """Last-resort fallback: yfinance's lighter 'fast_info' endpoint often
    still works when the full .info call is being throttled."""
    try:
        fi = yf.Ticker(ticker).fast_info
        price = getattr(fi, "last_price", None)
        if price is None:
            return {}
        return {
            "currentPrice": price,
            "currency": getattr(fi, "currency", None),
            "marketCap": getattr(fi, "market_cap", None),
        }
    except Exception:
        return {}


def get_cached_info(ticker: str, max_attempts: int = 3) -> dict:
    """Returns yfinance's .info dict for a ticker, cached for 5 minutes and
    shared across every agent that needs it. Empty or partial replies are
    retried (and never cached); if the full call stays empty, falls back to
    the lighter fast_info endpoint."""
    now = time.time()
    cached = _info_cache.get(ticker)
    if cached and (now - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    info = {}
    for attempt in range(max_attempts):
        info = _retry_yfinance_call(lambda: yf.Ticker(ticker).info)
        if _info_is_valid(info):
            _info_cache[ticker] = (time.time(), info)
            return info
        if attempt < max_attempts - 1:
            time.sleep(2 ** attempt)

    fallback = _info_from_fast_info(ticker)
    if _info_is_valid(fallback):
        return fallback  # deliberately not cached, so the next call retries the full lookup
    return info or {}


def get_cached_statements(ticker: str, max_attempts: int = 2):
    """Returns (income_stmt, balance_sheet) for a ticker, cached for 5
    minutes. Empty statements are retried and never cached."""
    now = time.time()
    cached = _statement_cache.get(ticker)
    if cached and (now - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    income = balance = None
    for attempt in range(max_attempts):
        t = yf.Ticker(ticker)
        income = _retry_yfinance_call(lambda: t.income_stmt)
        balance = _retry_yfinance_call(lambda: t.balance_sheet)
        if _df_has_data(income) or _df_has_data(balance):
            _statement_cache[ticker] = (time.time(), (income, balance))
            return income, balance
        if attempt < max_attempts - 1:
            time.sleep(2 ** attempt)
    return income, balance


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

    The annual financial statements are what the analysis truly needs, so a
    missing live price (which Yahoo omits when throttling) no longer blocks
    the run — only a total absence of both identity and financials does.
    """
    ticker = ticker.upper()
    default_currency = next(
        (cur for suffix, cur in _SUFFIX_CURRENCY.items() if ticker.endswith(suffix)),
        "USD",
    )

    info: dict = {}
    try:
        info = get_cached_info(ticker)
    except Exception:
        info = {}  # keep going: the statements may still load

    metrics: dict = {}
    try:
        income_stmt, balance_sheet = get_cached_statements(ticker)
        metrics.update(_extract_from_statement(income_stmt, INCOME_STMT_MAP, years))
        metrics.update(_extract_from_statement(balance_sheet, BALANCE_SHEET_MAP, years))
    except Exception:
        pass

    if not metrics:
        if _info_is_valid(info):
            name = info.get("longName") or info.get("shortName") or ticker
            raise ValueError(
                f"Found '{name}' on Yahoo Finance but no annual financial "
                "statements came back. This is usually temporary throttling "
                "- wait about a minute and run it again. If it keeps "
                "happening, the company may be very recently listed or thinly "
                "covered."
            )
        raise ValueError(
            f"Yahoo Finance returned no data for '{ticker}'. Most often this "
            "is temporary throttling (Yahoo limits requests from shared "
            "cloud servers) - wait about a minute and run it again. If it "
            "persists, check that: (1) the suffix is right (NSE '.NS', BSE "
            "'.BO'), or (2) the company has not been renamed and given a new "
            "symbol (e.g. Zomato became 'ETERNAL.NS' in 2025)."
        )

    company_name = info.get("longName") or info.get("shortName") or ticker
    currency = info.get("currency") or default_currency

    # screener.in is the standard free fundamentals-verification resource
    # for Indian equities (India's equivalent of "check the source filing").
    symbol_clean = ticker.split(".")[0]
    filing_index_url = f"https://www.screener.in/company/{symbol_clean}/"

    return {
        "ticker": ticker,
        "cik": None,
        "company_name": company_name,
        "metrics": metrics,
        "filing_index_url": filing_index_url,
        "currency": currency,
    }
