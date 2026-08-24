"""
Curated Indian equity list for the ticker dropdown — SEC has no equivalent
public API for NSE/BSE listings the way it does for US filers, so unlike
the US ticker list (fetched live from SEC), this is a maintained static
list. Nifty 50 composition changes periodically via index rebalancing —
this snapshot is accurate as of curation time; for guaranteed-current
constituents, cross-check nseindia.com.
"""

NIFTY_50 = [
    {"ticker": "RELIANCE.NS", "title": "Reliance Industries Ltd"},
    {"ticker": "TCS.NS", "title": "Tata Consultancy Services Ltd"},
    {"ticker": "HDFCBANK.NS", "title": "HDFC Bank Ltd"},
    {"ticker": "ICICIBANK.NS", "title": "ICICI Bank Ltd"},
    {"ticker": "INFY.NS", "title": "Infosys Ltd"},
    {"ticker": "HINDUNILVR.NS", "title": "Hindustan Unilever Ltd"},
    {"ticker": "ITC.NS", "title": "ITC Ltd"},
    {"ticker": "SBIN.NS", "title": "State Bank of India"},
    {"ticker": "BHARTIARTL.NS", "title": "Bharti Airtel Ltd"},
    {"ticker": "KOTAKBANK.NS", "title": "Kotak Mahindra Bank Ltd"},
    {"ticker": "LT.NS", "title": "Larsen & Toubro Ltd"},
    {"ticker": "AXISBANK.NS", "title": "Axis Bank Ltd"},
    {"ticker": "BAJFINANCE.NS", "title": "Bajaj Finance Ltd"},
    {"ticker": "ASIANPAINT.NS", "title": "Asian Paints Ltd"},
    {"ticker": "MARUTI.NS", "title": "Maruti Suzuki India Ltd"},
    {"ticker": "TITAN.NS", "title": "Titan Company Ltd"},
    {"ticker": "SUNPHARMA.NS", "title": "Sun Pharmaceutical Industries Ltd"},
    {"ticker": "ULTRACEMCO.NS", "title": "UltraTech Cement Ltd"},
    {"ticker": "WIPRO.NS", "title": "Wipro Ltd"},
    {"ticker": "NESTLEIND.NS", "title": "Nestle India Ltd"},
    {"ticker": "HCLTECH.NS", "title": "HCL Technologies Ltd"},
    {"ticker": "ONGC.NS", "title": "Oil & Natural Gas Corporation Ltd"},
    {"ticker": "NTPC.NS", "title": "NTPC Ltd"},
    {"ticker": "POWERGRID.NS", "title": "Power Grid Corporation of India Ltd"},
    {"ticker": "M&M.NS", "title": "Mahindra & Mahindra Ltd"},
    {"ticker": "TATASTEEL.NS", "title": "Tata Steel Ltd"},
    {"ticker": "TATAMOTORS.NS", "title": "Tata Motors Ltd"},
    {"ticker": "JSWSTEEL.NS", "title": "JSW Steel Ltd"},
    {"ticker": "ADANIENT.NS", "title": "Adani Enterprises Ltd"},
    {"ticker": "ADANIPORTS.NS", "title": "Adani Ports and SEZ Ltd"},
    {"ticker": "COALINDIA.NS", "title": "Coal India Ltd"},
    {"ticker": "BAJAJFINSV.NS", "title": "Bajaj Finserv Ltd"},
    {"ticker": "HDFCLIFE.NS", "title": "HDFC Life Insurance Company Ltd"},
    {"ticker": "SBILIFE.NS", "title": "SBI Life Insurance Company Ltd"},
    {"ticker": "GRASIM.NS", "title": "Grasim Industries Ltd"},
    {"ticker": "TECHM.NS", "title": "Tech Mahindra Ltd"},
    {"ticker": "INDUSINDBK.NS", "title": "IndusInd Bank Ltd"},
    {"ticker": "CIPLA.NS", "title": "Cipla Ltd"},
    {"ticker": "DRREDDY.NS", "title": "Dr. Reddy's Laboratories Ltd"},
    {"ticker": "DIVISLAB.NS", "title": "Divi's Laboratories Ltd"},
    {"ticker": "EICHERMOT.NS", "title": "Eicher Motors Ltd"},
    {"ticker": "HEROMOTOCO.NS", "title": "Hero MotoCorp Ltd"},
    {"ticker": "BRITANNIA.NS", "title": "Britannia Industries Ltd"},
    {"ticker": "APOLLOHOSP.NS", "title": "Apollo Hospitals Enterprise Ltd"},
    {"ticker": "BPCL.NS", "title": "Bharat Petroleum Corporation Ltd"},
    {"ticker": "SHRIRAMFIN.NS", "title": "Shriram Finance Ltd"},
    {"ticker": "BAJAJ-AUTO.NS", "title": "Bajaj Auto Ltd"},
    {"ticker": "HINDALCO.NS", "title": "Hindalco Industries Ltd"},
    {"ticker": "UPL.NS", "title": "UPL Ltd"},
    {"ticker": "LTIM.NS", "title": "LTIMindtree Ltd"},
]

# Notable large/actively-traded Indian names outside the current Nifty 50 —
# frequently searched, worth including even though not index constituents.
OTHER_NOTABLE_INDIAN_STOCKS = [
    {"ticker": "ZOMATO.NS", "title": "Eternal Ltd (Zomato)"},
    {"ticker": "PAYTM.NS", "title": "One97 Communications Ltd (Paytm)"},
    {"ticker": "IRCTC.NS", "title": "Indian Railway Catering & Tourism Corp"},
    {"ticker": "DMART.NS", "title": "Avenue Supermarts Ltd (DMart)"},
    {"ticker": "VBL.NS", "title": "Varun Beverages Ltd"},
    {"ticker": "PIDILITIND.NS", "title": "Pidilite Industries Ltd"},
    {"ticker": "GODREJCP.NS", "title": "Godrej Consumer Products Ltd"},
    {"ticker": "DABUR.NS", "title": "Dabur India Ltd"},
    {"ticker": "HAL.NS", "title": "Hindustan Aeronautics Ltd"},
    {"ticker": "BEL.NS", "title": "Bharat Electronics Ltd"},
]


def get_india_ticker_options() -> list[dict]:
    combined = NIFTY_50 + OTHER_NOTABLE_INDIAN_STOCKS
    combined.sort(key=lambda t: t["ticker"])
    return combined


# Sector peer groupings for the Benchmarker agent — mirrors the US PEER_MAP
# pattern in benchmarker_agent.py.
INDIA_PEER_MAP = {
    "RELIANCE.NS": ["ONGC.NS", "BPCL.NS"],
    "TCS.NS": ["INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "INFY.NS": ["TCS.NS", "WIPRO.NS", "HCLTECH.NS"],
    "WIPRO.NS": ["TCS.NS", "INFY.NS", "HCLTECH.NS"],
    "HCLTECH.NS": ["TCS.NS", "INFY.NS", "TECHM.NS"],
    "TECHM.NS": ["INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "HDFCBANK.NS": ["ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS"],
    "ICICIBANK.NS": ["HDFCBANK.NS", "KOTAKBANK.NS", "SBIN.NS"],
    "KOTAKBANK.NS": ["HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS"],
    "SBIN.NS": ["HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS"],
    "AXISBANK.NS": ["HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS"],
    "MARUTI.NS": ["TATAMOTORS.NS", "M&M.NS", "EICHERMOT.NS"],
    "TATAMOTORS.NS": ["MARUTI.NS", "M&M.NS"],
    "SUNPHARMA.NS": ["CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS"],
    "CIPLA.NS": ["SUNPHARMA.NS", "DRREDDY.NS"],
    "DRREDDY.NS": ["SUNPHARMA.NS", "CIPLA.NS"],
    "HINDUNILVR.NS": ["ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS"],
    "ITC.NS": ["HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS"],
    "TATASTEEL.NS": ["JSWSTEEL.NS", "HINDALCO.NS"],
    "JSWSTEEL.NS": ["TATASTEEL.NS", "HINDALCO.NS"],
}
