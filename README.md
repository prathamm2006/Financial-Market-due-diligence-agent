# AI Due-Diligence Agent

### 🔗 Live demo: https://due-diligence-ai-agent.streamlit.app/

Pick a company, press **Run analysis**, and receive a research brief in under a minute. It covers US-listed companies (SEC EDGAR) and Indian companies on the NSE, including the Nifty 50.

---

## What this is, in plain English

When an analyst at a bank or consulting firm is asked "is this company worth a closer look?", the first few hours go to gathering numbers: pulling filings, comparing competitors, checking the news, working out growth, and judging whether the share price is high or low. This project automates that first draft.

Seven specialised AI agents each handle one step, and the final agent writes everything up as a short brief with a recommendation. The brief can be downloaded as a PDF or Markdown file.

It is a **first-draft research aid**, not investment advice. Every brief states its own limitations.

---

## Glossary

### The basics

- **Due diligence**: the investigation done before an investment, acquisition or partnership, to check that a company is what it claims to be and to understand its risks.
- **AI agent**: a program that is given one specific job and uses tools (data sources, calculators, a language model) to complete it.
- **Multi-agent system**: several agents, each with a narrow job, passing their results along a chain. Splitting the work makes each step easier to check and to replace.
- **Agentic AI**: AI designed to carry out a multi-step task with some autonomy, rather than just answering a single question.
- **Orchestration**: the logic that decides which agent runs when, and passes results between them. This project uses **LangGraph**, which models the pipeline as an explicit, inspectable sequence of steps.
- **LLM (large language model)**: the kind of AI behind chatbots. Here it is **Google Gemini**, used only to interpret numbers and write the narrative, never to calculate them.
- **Hallucination**: when an LLM states something that sounds right but is invented. This is why the numbers in this project are computed by ordinary code and not by the LLM.

### Data sources

- **SEC (U.S. Securities and Exchange Commission)**: the US regulator that requires listed companies to publish audited financial reports.
- **EDGAR**: the SEC's public database of those reports. It is the primary source analysts use for US companies.
- **XBRL**: a standard tagging format that makes the figures in a filing readable by software, so the numbers can be read directly instead of being scraped from PDFs.
- **10-K**: the annual report filed by US companies. **20-F** is the equivalent for foreign companies listed in the US.
- **NSE / BSE**: India's two main stock exchanges (National Stock Exchange and Bombay Stock Exchange). Indian companies do not file with the SEC, so they need a separate data source.
- **Nifty 50**: the index of India's 50 largest listed companies on the NSE.
- **Yahoo Finance**: the source used for Indian company financials and for live share prices and valuation data in both markets.
- **Ticker**: the short code identifying a listed share, for example AAPL for Apple. Indian tickers carry a suffix: `.NS` for the NSE and `.BO` for the BSE.

### Financial terms

- **Revenue**: total money a company earns from selling its products or services.
- **Net income**: profit left after all costs, interest and taxes.
- **Operating income**: profit from the core business before interest and taxes.
- **Net margin**: net income divided by revenue; how many cents of profit each dollar of sales produces.
- **YoY (year over year)**: the change compared with the same measure one year earlier.
- **CAGR (compound annual growth rate)**: the smoothed yearly growth rate between two points in time. It is the standard way to describe growth over several years in one number.
- **Market capitalisation**: the total market value of a company's shares (share price × number of shares).
- **Enterprise value (EV)**: market capitalisation plus debt minus cash; roughly the price of buying the whole business.
- **P/E ratio (price to earnings)**: share price relative to profit. A higher number means investors are paying more for each unit of profit.
- **EV/EBITDA**: enterprise value relative to operating earnings, used to compare companies with different debt levels. This project uses operating income as a stand-in for EBITDA, so treat it as indicative rather than exact.
- **Price/Sales**: market capitalisation relative to revenue; useful for companies that are not yet profitable.
- **Lakh and Crore**: Indian number units. One lakh is 100,000 and one crore is 10,000,000. Indian figures are shown in these units with the ₹ symbol.

### Forecasting terms

- **Linear trend**: a straight line fitted through past results and extended forward. Simple and transparent, but it ignores seasonality, competition and the economy.
- **Bear / Base / Bull scenarios**: three projections instead of one. The base case follows the historical growth rate; the bear and bull cases lower and raise that rate by 50% of its size (with a small minimum gap), so the range shows how uncertain the forecast really is.
- **Confidence level**: an honest label (low or moderate) attached to every forecast. Short histories and volatile results are marked low.

### Testing the forecast

- **Backtesting**: checking a forecasting method by pretending to be in the past. The system forecasts year *T+1* using only data up to year *T*, then compares the forecast with what the company really reported. Repeating this over many past years shows how accurate the method has actually been.
- **Walk-forward**: the backtesting style used here, where the "present" moves forward one year at a time so each forecast only ever sees its own past.
- **Look-ahead bias**: the classic backtesting mistake of letting a forecast peek at information from after the date it is supposed to be forecasting from. The system is tested to make sure this cannot happen.
- **Naive baseline**: a deliberately simple guess a forecast must beat to be worth anything. Here: "next year equals this year" and "next year grows like last year did".
- **Median error**: the typical size of a miss, as a share of the actual figure. The median is used so one unusual year does not distort it.
- **Beat no-change rate**: how often the forecast was closer to reality than the "next year equals this year" guess. Below 50% means the forecast adds nothing.
- **Band coverage**: how often the actual result landed inside the bear-to-bull range. If it rarely does, the range is too narrow to be honest.
- **Restatement**: when a company later revises figures it already published. Backtests use today's figures for past years, which can make past accuracy look slightly better than it truly was.

### The seven agents

1. **Extractor**: pulls the company's reported financials from SEC EDGAR (US) or Yahoo Finance (India).
2. **Benchmarker**: compares the company's revenue, profit and margin with named competitors.
3. **Forecaster**: calculates CAGR and the bear, base and bull projections. This is plain arithmetic, not an LLM.
4. **Backtester**: re-runs the Forecaster on the company's own past years and scores it against what actually happened and against simple baselines, so the brief can say how much to trust the forecast. This is plain arithmetic, not an LLM.
5. **Valuation agent**: pulls live market data and calculates P/E, EV/EBITDA and price/sales for the company and its peers, to judge whether it looks cheap or expensive.
6. **Risk Flagger**: reads recent news and the financial trends and lists concrete, evidence-based risks. This agent uses the LLM.
7. **Briefing agent**: combines everything into the final brief with a recommendation. This agent uses the LLM.

Only agents 6 and 7 use the language model. Everything numerical is calculated by code.

### Reliability terms

- **Retry with backoff**: when a data provider briefly refuses a request, the system waits a moment and tries again, with longer waits each time, instead of failing at once.
- **Caching**: remembering a recent answer so the same data is not requested twice. Only complete, valid answers are remembered.
- **Rate limiting**: a data provider's cap on how many requests it will answer in a given time. Free services apply this strictly, so occasional "try again in a minute" messages are possible.
- **Source link**: every brief links to the company's filings (SEC EDGAR for US companies, screener.in for Indian ones) so any figure can be checked against the original.

---

## Coverage

| Market | Source of financials | Companies available |
|---|---|---|
| United States | SEC EDGAR | Companies SEC tracks that report standard annual financials, searchable in the dropdown |
| India | Yahoo Finance | About 60 companies: the Nifty 50 plus other widely followed names |

---

## Known limitations

- **A first draft, not advice.** The brief is meant to speed up research and should be checked against the filings before any decision.
- **Forecasts are simple.** They extend past trends and do not model the economy, competition or company-specific events. The built-in track record exists precisely to show how far to trust them.
- **The track record needs long history.** US companies provide about ten years of data, enough for a meaningful check. Free Yahoo Finance data for Indian companies covers only about four years, so the check is skipped for them and the app says so.
- **Free data has limits.** Yahoo Finance and the free AI tier can slow or refuse requests at busy times. Waiting a minute and running the analysis again usually resolves it.
- **The Indian company list is a snapshot.** Unlike the US list, which is fetched live from the SEC, the Indian list is maintained by hand, and companies occasionally change their ticker (Zomato became Eternal, symbol `ETERNAL.NS`, in 2025).
- **EV/EBITDA is approximate.** It uses operating income in place of true EBITDA.
- **Companies that are not listed in the US or on the NSE are not covered.**

---

## License

MIT
