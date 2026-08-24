"""
Single entry point the orchestrator calls — decides which underlying data
source a ticker needs and returns a result in the same shape either way,
so downstream agents (forecaster, valuation, risk, briefing) never need
to know or care where the numbers came from.
"""
from data.edgar_client import get_company_profile as _get_profile_sec
from data.yfinance_client import get_company_profile_yf as _get_profile_yf

# Exchange suffixes Yahoo Finance uses for non-US markets we route away
# from SEC EDGAR (which only covers US-registered / ADR-filing companies).
NON_SEC_SUFFIXES = (".NS", ".BO")  # NSE, BSE (India)


def get_company_profile(ticker: str, years: int = 3) -> dict:
    ticker = ticker.upper()
    if ticker.endswith(NON_SEC_SUFFIXES):
        return _get_profile_yf(ticker, years=years)

    profile = _get_profile_sec(ticker, years=years)
    profile.setdefault("currency", "USD")
    return profile
