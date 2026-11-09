"""
Backtester — measures how good the Forecaster's predictions would actually
have been on a company's own history.

Method (walk-forward): for each past year T that has at least MIN_TRAIN_YEARS
of data behind it, run the *same* forecasting code the live app uses, giving
it ONLY data up to T, then compare its predictions for T+1 and T+2 with what
was really reported. Nothing from after T is visible to the forecast.

A forecast number on its own proves nothing, so every method is scored against
naive baselines:
  - naive_no_change:   "next year will equal this year"
  - naive_last_growth: "next year grows by the same rate as last year"
If the model cannot beat these, it adds no information, and the report says so.

Deliberately NOT an LLM: this is measurement, so it must be deterministic.

Known limitations (also returned in the output so the UI can show them):
  - Reported figures can be restated in later filings, so using today's
    numbers for past years is mildly flattering (a fully point-in-time test
    would need each fact's original filing date).
  - Consecutive windows overlap, so the observations are not independent:
    treat results as indicative, especially for a single company.
"""
import statistics
from collections import defaultdict

from agents.forecaster_agent import forecast_metric

HORIZONS = (1, 2)              # years ahead to test
MIN_TRAIN_YEARS = 3            # history required before a forecast is allowed
MIN_POINTS_TO_REPORT = 4       # fewer scored forecasts than this = not enough to judge
SMALL_SAMPLE_POINTS = 8        # below this, flag the result as indicative only
BACKTEST_METRICS = ("revenue", "net_income", "operating_income")
METRIC_LABELS = {
    "revenue": "revenue",
    "net_income": "net income",
    "operating_income": "operating income",
}
METHODS = ("base_cagr", "linear_trend", "naive_no_change", "naive_last_growth")

NOTES = [
    "Each forecast used only data available up to its cutoff year.",
    "Baselines: 'no change' repeats the last value; 'last growth' repeats the last year's growth rate.",
    "Reported figures may have been restated since, which makes past accuracy look slightly better than a true point-in-time test.",
    "Overlapping windows are not independent observations, so treat results as indicative.",
]


def _chrono(series: list[dict]) -> list[dict]:
    """Oldest-first list of {year:int, value:float}; one point per year."""
    by_year = {}
    for p in series:
        try:
            by_year[int(p["year"])] = float(p["value"])
        except (KeyError, TypeError, ValueError):
            continue
    return [{"year": y, "value": by_year[y]} for y in sorted(by_year)]


def _naive_last_growth(prev: float, last: float, h: int):
    if prev is not None and prev > 0 and last > 0:
        return last * (last / prev) ** h
    return None


def _evaluate_metric(metric: str, series: list[dict], company: str = "",
                     horizons=HORIZONS, min_train: int = MIN_TRAIN_YEARS) -> list[dict]:
    pts = _chrono(series)
    actual = {p["year"]: p["value"] for p in pts}
    records = []

    for i in range(min_train - 1, len(pts) - 1):
        train = pts[: i + 1]                      # <- nothing after this index is visible
        cutoff_year = train[-1]["year"]
        last, prev = train[-1]["value"], train[-2]["value"]
        scale = statistics.mean(abs(p["value"]) for p in train)

        train_desc = [{"year": str(p["year"]), "value": p["value"]} for p in reversed(train)]
        fc = forecast_metric(train_desc, years_ahead=max(horizons))
        linear = {int(p["year"]): p["value"] for p in fc.get("projections", [])}
        scen = fc.get("scenarios", {})
        base = {int(p["year"]): p["value"] for p in scen.get("base", [])}
        bear = {int(p["year"]): p["value"] for p in scen.get("bear", [])}
        bull = {int(p["year"]): p["value"] for p in scen.get("bull", [])}

        for h in horizons:
            target_year = cutoff_year + h
            if target_year not in actual:
                continue
            a = actual[target_year]
            forecasts = {
                "base_cagr": base.get(target_year),
                "linear_trend": linear.get(target_year),
                "naive_no_change": last,
                "naive_last_growth": _naive_last_growth(prev, last, h),
            }
            for method, f in forecasts.items():
                if f is None:
                    continue
                abs_err = abs(f - a)
                direction = None
                if method != "naive_no_change":   # a flat forecast has no direction to score
                    direction = (f > last) == (a > last)
                in_band = None
                if method == "base_cagr" and target_year in bear and target_year in bull:
                    lo, hi = sorted((bear[target_year], bull[target_year]))
                    in_band = lo <= a <= hi
                records.append({
                    "company": company, "metric": metric, "cutoff_year": cutoff_year,
                    "horizon": h, "method": method, "forecast": f, "actual": a,
                    "last_value": last, "abs_error": abs_err,
                    "ape": (abs_err / a) if a > 0 else None,        # % error only meaningful for positive actuals
                    "scaled_error": (abs_err / scale) if scale else None,
                    "direction_correct": direction, "in_band": in_band,
                })
    return records


def _years_needed(horizons=HORIZONS, min_train=MIN_TRAIN_YEARS,
                  min_points=MIN_POINTS_TO_REPORT) -> int:
    """Smallest number of annual data points that yields at least
    `min_points` scored forecasts (derived, so it can't drift from the rules)."""
    n = min_train + 1
    while sum(max(0, n - min_train - h + 1) for h in horizons) < min_points:
        n += 1
    return n


def _median(vals):
    vals = [v for v in vals if v is not None]
    return statistics.median(vals) if vals else None


def _mean_bool(vals):
    vals = [v for v in vals if v is not None]
    return (sum(1 for v in vals if v) / len(vals)) if vals else None


def summarize_records(records: list[dict]) -> dict:
    """Aggregates raw records (one company or many pooled) into per-metric,
    per-method statistics plus a plain-English headline."""
    summary = {}
    by_metric = defaultdict(list)
    for r in records:
        by_metric[r["metric"]].append(r)

    for metric, recs in by_metric.items():
        # naive baseline error at every scored point, for head-to-head comparison
        naive_err = {}
        for r in recs:
            if r["method"] == "naive_no_change":
                naive_err[(r["company"], r["cutoff_year"], r["horizon"])] = r["abs_error"]

        by_method = defaultdict(list)
        for r in recs:
            by_method[r["method"]].append(r)

        methods = {}
        for method, mrecs in by_method.items():
            wins = total = 0
            if method != "naive_no_change":
                for r in mrecs:
                    base_err = naive_err.get((r["company"], r["cutoff_year"], r["horizon"]))
                    if base_err is not None:
                        total += 1
                        wins += 1 if r["abs_error"] < base_err else 0
            methods[method] = {
                "n": len(mrecs),
                "median_ape": _median([r["ape"] for r in mrecs]),
                "median_scaled_error": _median([r["scaled_error"] for r in mrecs]),
                "directional_accuracy": _mean_bool([r["direction_correct"] for r in mrecs]),
                "beats_no_change_pct": (wins / total) if total else None,
                "band_coverage": _mean_bool([r["in_band"] for r in mrecs]) if method == "base_cagr" else None,
            }

        base = methods.get("base_cagr")
        naive = methods.get("naive_no_change")
        n_points = base["n"] if base else 0
        verdict, headline = "insufficient_sample", None
        if base and naive and n_points >= MIN_POINTS_TO_REPORT:
            beats = base["beats_no_change_pct"]
            if beats is None:
                verdict = "insufficient_sample"
            elif beats >= 0.60:
                verdict = "beats_naive"
            elif beats <= 0.40:
                verdict = "worse_than_naive"
            else:
                verdict = "comparable"
            label = METRIC_LABELS.get(metric, metric)
            if base["median_ape"] is not None and naive["median_ape"] is not None:
                err_txt = (f"the base case missed {label} by a median of {base['median_ape']:.1%} "
                           f"(a no-change guess missed by {naive['median_ape']:.1%})")
            else:
                err_txt = (f"the base case's median error on {label} was {base['median_scaled_error']:.0%} "
                           f"of the metric's typical size")
            parts = [f"Across {n_points} past forecasts, {err_txt}."]
            if beats is not None:
                parts.append(f"It beat the no-change guess in {beats:.0%} of cases.")
            if base["band_coverage"] is not None:
                parts.append(f"The actual result landed inside the bear-to-bull range {base['band_coverage']:.0%} of the time.")
            headline = " ".join(parts)

        summary[metric] = {
            "n_points": n_points,
            "small_sample": 0 < n_points < SMALL_SAMPLE_POINTS,
            "verdict": verdict,
            "headline": headline,
            "methods": methods,
        }
    return summary


def backtest_company(metrics_long: dict, company: str = "") -> dict:
    """Backtest one company from its (multi-year) metrics dict, in the same
    shape the extractors return: {metric: [{year, value}, ...]}."""
    records = []
    for metric in BACKTEST_METRICS:
        if metric in metrics_long:
            records.extend(_evaluate_metric(metric, metrics_long[metric], company=company))

    years = max((len(metrics_long.get(m, [])) for m in BACKTEST_METRICS), default=0)
    summary = summarize_records(records)
    rev = summary.get("revenue")
    if not rev or rev["n_points"] < MIN_POINTS_TO_REPORT:
        return {
            "available": False,
            "reason": (f"Not enough history to test the forecast: {years} years of data "
                       f"found, and at least {_years_needed()} are needed "
                       "for a meaningful check (free Yahoo Finance data provides only about 4 years; "
                       "SEC EDGAR provides 10 or more)."),
            "years_of_history": years,
            "summary": summary,
            "records": records,
            "notes": NOTES,
        }
    return {
        "available": True,
        "reason": None,
        "years_of_history": years,
        "summary": summary,
        "records": records,
        "notes": NOTES,
    }


def compact_for_prompt(backtest: dict | None) -> dict:
    """Small, LLM-friendly view of the results: headlines and verdicts only,
    never raw records."""
    if not backtest or not backtest.get("available"):
        return {"available": False}
    out = {"available": True, "metrics": {}}
    for metric in ("revenue", "net_income"):
        s = backtest["summary"].get(metric)
        if s and s["headline"]:
            out["metrics"][metric] = {
                "verdict": s["verdict"],
                "small_sample": s["small_sample"],
                "headline": s["headline"],
            }
    return out
