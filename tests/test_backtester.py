"""
Known-answer tests for the backtester and the forecaster bugs it surfaced.
No network access needed: every case is a synthetic series whose correct
result can be worked out by hand.
"""
import random

from agents.backtester import (
    backtest_company, summarize_records, compact_for_prompt,
    _evaluate_metric, _years_needed,
)
from agents.forecaster_agent import forecast_metric


def series(values, start_year=2015):
    """Most-recent-first list of {year, value}, as the extractors return."""
    pts = [{"year": str(start_year + i), "value": float(v)} for i, v in enumerate(values)]
    return list(reversed(pts))


def test_perfect_compound_growth_is_forecast_exactly():
    # 10% growth every year: CAGR extrapolation is exactly right by construction.
    # Values are in the billions, like real company financials (the forecaster
    # rounds to whole currency units, which only matters for toy-sized numbers).
    s = series([100e9 * 1.1 ** k for k in range(10)])
    bt = backtest_company({"revenue": s})
    rev = bt["summary"]["revenue"]
    base = rev["methods"]["base_cagr"]
    assert bt["available"]
    assert base["median_ape"] < 1e-6
    assert base["beats_no_change_pct"] == 1.0
    assert base["band_coverage"] == 1.0
    assert rev["verdict"] == "beats_naive"


def test_linear_series_is_forecast_exactly_by_linear_trend():
    s = series([100 + 10 * k for k in range(10)])
    bt = backtest_company({"revenue": s})
    lin = bt["summary"]["revenue"]["methods"]["linear_trend"]
    assert lin["median_ape"] < 1e-9


def test_regime_change_is_reported_as_worse_than_naive():
    # Explosive growth that then stalls: extrapolating the old growth rate
    # overshoots badly, and "no change" is the better guess.
    s = series([100, 200, 400, 800] + [800 + 5 * k for k in range(1, 9)])
    bt = backtest_company({"revenue": s})
    assert bt["summary"]["revenue"]["verdict"] == "worse_than_naive"


def test_no_future_data_leaks_into_a_forecast():
    base_vals = [100, 108, 117, 125, 136, 147, 158, 171, 184, 199]
    altered = base_vals[:-2] + [10_000, 99_999]          # corrupt only the last two years
    a = _evaluate_metric("revenue", series(base_vals))
    b = _evaluate_metric("revenue", series(altered))
    first_altered_year = 2015 + len(base_vals) - 2
    early_a = {(r["cutoff_year"], r["horizon"], r["method"]): r["forecast"]
               for r in a if r["cutoff_year"] < first_altered_year}
    early_b = {(r["cutoff_year"], r["horizon"], r["method"]): r["forecast"]
               for r in b if r["cutoff_year"] < first_altered_year}
    assert early_a and early_a == early_b


def test_too_little_history_is_declined_not_faked():
    bt = backtest_company({"revenue": series([100, 110, 121, 133])})   # 4 years
    assert bt["available"] is False
    assert str(_years_needed()) in bt["reason"]


def test_profit_turning_to_loss_does_not_crash_anything():
    ni = series([19.9e9, 8.0e9, 1.7e9, -18.8e9, -4.0e9, -1.0e9, 2.0e9, 5.0e9])
    rev = series([79e9, 63e9, 54e9, 53e9, 54e9, 58e9, 61e9, 65e9])
    bt = backtest_company({"revenue": rev, "net_income": ni})
    assert "net_income" in bt["summary"]
    # forecaster itself, on the exact shape that used to raise TypeError
    r = forecast_metric(series([19.9e9, 8e9, 1.7e9, -18.8e9]), years_ahead=2)
    assert r["cagr_pct"] is None


def test_negative_volatile_series_is_not_called_moderate_confidence():
    r = forecast_metric(series([-9e9, -1e9, -12e9, -2e9]))
    assert r["confidence"] == "low"


def test_naive_no_change_has_no_direction_score():
    recs = _evaluate_metric("revenue", series([100 * 1.1 ** k for k in range(8)]))
    naive = [r for r in recs if r["method"] == "naive_no_change"]
    assert naive and all(r["direction_correct"] is None for r in naive)


def test_pooling_keeps_companies_separate():
    growth = _evaluate_metric("revenue", series([100 * 1.1 ** k for k in range(9)]), company="GROW")
    flat = _evaluate_metric("revenue", series([100, 101, 100, 99, 100, 101, 100, 99, 100]), company="FLAT")
    pooled = summarize_records(growth + flat)["revenue"]
    n_growth = sum(1 for r in growth if r["method"] == "base_cagr")
    n_flat = sum(1 for r in flat if r["method"] == "base_cagr")
    assert pooled["n_points"] == n_growth + n_flat


def test_all_reported_rates_are_valid_proportions():
    rng = random.Random(7)
    vals = [100.0]
    for _ in range(11):
        vals.append(max(1.0, vals[-1] * (1 + rng.uniform(-0.3, 0.4))))
    m = backtest_company({"revenue": series(vals)})["summary"]["revenue"]["methods"]
    for stats in m.values():
        for key in ("beats_no_change_pct", "band_coverage", "directional_accuracy"):
            v = stats[key]
            assert v is None or 0.0 <= v <= 1.0


def test_prompt_view_is_compact_and_safe():
    assert compact_for_prompt(None) == {"available": False}
    assert compact_for_prompt({"available": False}) == {"available": False}
    bt = backtest_company({"revenue": series([100 * 1.1 ** k for k in range(10)])})
    view = compact_for_prompt(bt)
    assert view["available"] and "headline" in view["metrics"]["revenue"]
    assert "records" not in view
