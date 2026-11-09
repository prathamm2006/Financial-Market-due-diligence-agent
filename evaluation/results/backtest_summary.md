# Forecast back-test results

Run on 2026-11-09 across **14 companies** (478 scored base-case forecasts across the three metrics). Each forecast used only data available at its cutoff year, then was compared with what the company actually reported.

## Pooled results: revenue

| Method | Checks | Median error | Beat no-change | Right direction | Inside bear-bull range |
|---|---|---|---|---|---|
| Base case (CAGR growth) | 177 | 11.5% | 45.2% | 70.6% | 31.1% |
| Linear trend | 177 | 13.2% | 45.8% | 59.3% | n/a |
| Naive: no change | 177 | 11.0% | n/a | n/a | n/a |
| Naive: repeat last growth | 177 | 12.2% | 49.2% | 77.4% | n/a |

**Reading:** Across 177 past forecasts, the base case missed revenue by a median of 11.5% (a no-change guess missed by 11.0%). It beat the no-change guess in 45% of cases. The actual result landed inside the bear-to-bull range 31% of the time.

## Pooled results: net income

| Method | Checks | Median error | Beat no-change | Right direction | Inside bear-bull range |
|---|---|---|---|---|---|
| Base case (CAGR growth) | 156 | 28.6% | 42.9% | 61.5% | 16.7% |
| Linear trend | 160 | 22.8% | 52.5% | 62.5% | n/a |
| Naive: no change | 160 | 18.9% | n/a | n/a | n/a |
| Naive: repeat last growth | 154 | 49.0% | 32.5% | 53.2% | n/a |

**Reading:** Across 156 past forecasts, the base case missed net income by a median of 28.6% (a no-change guess missed by 18.9%). It beat the no-change guess in 43% of cases. The actual result landed inside the bear-to-bull range 17% of the time.

## Pooled results: operating income

| Method | Checks | Median error | Beat no-change | Right direction | Inside bear-bull range |
|---|---|---|---|---|---|
| Base case (CAGR growth) | 145 | 28.7% | 43.4% | 64.8% | 17.2% |
| Linear trend | 146 | 19.6% | 48.6% | 56.8% | n/a |
| Naive: no change | 146 | 17.1% | n/a | n/a | n/a |
| Naive: repeat last growth | 145 | 27.8% | 40.0% | 60.7% | n/a |

**Reading:** Across 145 past forecasts, the base case missed operating income by a median of 28.7% (a no-change guess missed by 17.1%). It beat the no-change guess in 43% of cases. The actual result landed inside the bear-to-bull range 17% of the time.

## Per-company verdict (revenue)

| Company | Verdict | Checks |
|---|---|---|
| AAPL | worse than no-change | 13 |
| AMZN | worse than no-change | 13 |
| CAT | worse than no-change | 13 |
| GOOGL | beats no-change | 13 |
| HD | comparable | 13 |
| INTC | worse than no-change | 13 |
| JNJ | worse than no-change | 8 |
| JPM | beats no-change | 13 |
| KO | comparable | 13 |
| MSFT | worse than no-change | 13 |
| PFE | worse than no-change | 13 |
| PG | comparable | 13 |
| TGT | comparable | 13 |
| WMT | beats no-change | 13 |

## Skipped

- **XOM**: Found 'ExxonMobil Holdings Corporation' in SEC EDGAR (CIK 0002115436), but no usable 10-K/20-F annual financial data was available in the standard XBRL tags this tool reads. This can happen for holdin

## How to read this

- *Median error* is the typical size of the miss as a share of the actual figure (revenue only reliably; profit can be near zero or negative).
- *Beat no-change* is how often the method was closer than simply assuming next year equals this year. Below 50% means the method adds nothing over that baseline.
- *Inside bear-bull range* checks whether the stated uncertainty band is honest: if it rarely contains the outcome, the band is too narrow.
- Each forecast used only data available up to its cutoff year.
- Baselines: 'no change' repeats the last value; 'last growth' repeats the last year's growth rate.
- Reported figures may have been restated since, which makes past accuracy look slightly better than a true point-in-time test.
- Overlapping windows are not independent observations, so treat results as indicative.
