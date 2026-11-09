"""
Backtest the Forecaster across a basket of real companies and write up what
actually happened, whether flattering or not.

Run from the repo root (needs internet access to SEC EDGAR; first put a real
name/email in HEADERS in data/edgar_client.py, as SEC requires):

    python evaluation/run_backtest_suite.py
    python evaluation/run_backtest_suite.py --tickers AAPL MSFT JNJ

Outputs (in evaluation/results/):
    backtest_records.csv   every individual forecast vs actual
    backtest_summary.md    pooled results, ready to read or paste into a case study
"""
import argparse
import csv
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.backtester import (  # noqa: E402
    backtest_company, summarize_records, METRIC_LABELS, NOTES,
)
from data.company_data import get_company_profile  # noqa: E402

# Mixed sectors, all long-lived SEC filers. INTC is included on purpose: its
# profit collapse is the kind of regime change that tests a growth-extrapolation
# forecaster. Banks (e.g. JPM) often lack a standard revenue tag and may be skipped.
DEFAULT_BASKET = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "JNJ", "PG", "KO", "WMT",
    "XOM", "HD", "PFE", "CAT", "INTC", "JPM", "TGT",
]
METHOD_LABELS = {
    "base_cagr": "Base case (CAGR growth)",
    "linear_trend": "Linear trend",
    "naive_no_change": "Naive: no change",
    "naive_last_growth": "Naive: repeat last growth",
}
VERDICT_LABELS = {
    "beats_naive": "beats no-change",
    "comparable": "comparable",
    "worse_than_naive": "worse than no-change",
    "insufficient_sample": "too few checks",
}


def run_suite(tickers, fetch=get_company_profile, pause=0.5):
    """Returns (all_records, per_company_results, skipped). `fetch` is injectable for tests."""
    records, per_company, skipped = [], {}, {}
    for t in tickers:
        try:
            profile = fetch(t, years=3)
            bt = backtest_company(profile.get("metrics_long", profile["metrics"]), company=t)
        except Exception as e:
            skipped[t] = str(e)[:200]
            continue
        if not bt["available"]:
            skipped[t] = bt["reason"]
        else:
            per_company[t] = bt
            records.extend(bt["records"])
        time.sleep(pause)
    return records, per_company, skipped


def _pct(v):
    return f"{v:.1%}" if v is not None else "n/a"


def render_markdown(records, per_company, skipped):
    pooled = summarize_records(records)
    n_scored = sum(1 for r in records if r["method"] == "base_cagr")
    lines = [
        "# Forecast back-test results",
        "",
        f"Run on {date.today().isoformat()} across **{len(per_company)} companies** "
        f"({n_scored} scored base-case forecasts across the three metrics). Each forecast used only data "
        "available at its cutoff year, then was compared with what the company actually reported.",
        "",
    ]
    for metric in ("revenue", "net_income", "operating_income"):
        s = pooled.get(metric)
        if not s:
            continue
        lines += [f"## Pooled results: {METRIC_LABELS[metric]}", "",
                  "| Method | Checks | Median error | Beat no-change | Right direction | Inside bear-bull range |",
                  "|---|---|---|---|---|---|"]
        for key, label in METHOD_LABELS.items():
            m = s["methods"].get(key)
            if m:
                lines.append(f"| {label} | {m['n']} | {_pct(m['median_ape'])} | "
                             f"{_pct(m['beats_no_change_pct'])} | {_pct(m['directional_accuracy'])} | "
                             f"{_pct(m['band_coverage'])} |")
        if s["headline"]:
            lines += ["", f"**Reading:** {s['headline']}"]
        lines.append("")

    lines += ["## Per-company verdict (revenue)", "", "| Company | Verdict | Checks |", "|---|---|---|"]
    for t, bt in sorted(per_company.items()):
        rev = bt["summary"].get("revenue", {})
        lines.append(f"| {t} | {VERDICT_LABELS.get(rev.get('verdict'), 'n/a')} | {rev.get('n_points', 0)} |")

    if skipped:
        lines += ["", "## Skipped", ""] + [f"- **{t}**: {why}" for t, why in sorted(skipped.items())]

    lines += ["", "## How to read this", "",
              "- *Median error* is the typical size of the miss as a share of the actual figure (revenue only reliably; profit can be near zero or negative).",
              "- *Beat no-change* is how often the method was closer than simply assuming next year equals this year. Below 50% means the method adds nothing over that baseline.",
              "- *Inside bear-bull range* checks whether the stated uncertainty band is honest: if it rarely contains the outcome, the band is too narrow."]
    lines += [f"- {n}" for n in NOTES]
    return "\n".join(lines) + "\n"


def write_outputs(records, per_company, skipped, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fields = ["company", "metric", "cutoff_year", "horizon", "method", "forecast", "actual",
              "last_value", "abs_error", "ape", "scaled_error", "direction_correct", "in_band"]
    with open(out_dir / "backtest_records.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)
    md = render_markdown(records, per_company, skipped)
    (out_dir / "backtest_summary.md").write_text(md, encoding="utf-8")
    return md


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tickers", nargs="+", default=DEFAULT_BASKET)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "results"))
    args = ap.parse_args()
    print(f"Backtesting {len(args.tickers)} companies (this takes a minute or two)...")
    records, per_company, skipped = run_suite([t.upper() for t in args.tickers])
    if not records:
        sys.exit("No company produced a usable backtest. Check your internet access and the SEC User-Agent in data/edgar_client.py.")
    print(write_outputs(records, per_company, skipped, args.out))
    print(f"Written to {args.out}")


if __name__ == "__main__":
    main()
