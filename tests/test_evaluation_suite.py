"""Tests for the evaluation runner using injected fake data (no network)."""
import csv

from evaluation.run_backtest_suite import run_suite, render_markdown, write_outputs


def _series(start, growth, n=10):
    return list(reversed([{"year": str(2016 + i), "value": start * (1 + growth) ** i} for i in range(n)]))


def fake_fetch(ticker, years=3):
    if ticker == "BROKEN":
        raise ValueError("no data")
    if ticker == "SHORT":
        return {"metrics": {}, "metrics_long": {"revenue": _series(100e9, 0.05, n=4)}}
    g = {"GROW": 0.10, "SLOW": 0.02}[ticker]
    return {"metrics": {}, "metrics_long": {"revenue": _series(100e9, g), "net_income": _series(10e9, g)}}


def test_suite_pools_skips_and_writes_files(tmp_path):
    records, per_company, skipped = run_suite(["GROW", "SLOW", "SHORT", "BROKEN"], fetch=fake_fetch, pause=0)
    assert set(per_company) == {"GROW", "SLOW"}
    assert set(skipped) == {"SHORT", "BROKEN"}
    md = write_outputs(records, per_company, skipped, tmp_path)
    assert "Pooled results: revenue" in md and "## Skipped" in md
    rows = list(csv.DictReader(open(tmp_path / "backtest_records.csv", encoding="utf-8")))
    assert rows and {r["company"] for r in rows} == {"GROW", "SLOW"}
    assert (tmp_path / "backtest_summary.md").exists()


def test_markdown_renders_with_no_skips():
    records, per_company, skipped = run_suite(["GROW"], fetch=fake_fetch, pause=0)
    assert "Skipped" not in render_markdown(records, per_company, skipped)
