"""Period maths, brand split and mover ranking for gsc_period_report."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import gsc_period_report as r  # noqa: E402


def test_weekly_is_monday_to_sunday():
    p = r.compute_periods("weekly", date(2026, 10, 9))  # a Friday
    assert p["current"] == {"start": "2026-09-28", "end": "2026-10-04"}
    assert p["previous"] == {"start": "2026-09-21", "end": "2026-09-27"}
    assert date.fromisoformat(p["current"]["start"]).weekday() == 0
    assert not p["fresh_data"]


def test_weekly_on_monday_uses_yesterday_and_flags_fresh():
    p = r.compute_periods("weekly", date(2026, 10, 5))
    assert p["current"]["end"] == "2026-10-04"
    assert p["fresh_data"]


def test_monthly_calendar_months():
    p = r.compute_periods("monthly", date(2026, 3, 3))
    assert p["current"] == {"start": "2026-02-01", "end": "2026-02-28"}
    assert p["previous"] == {"start": "2026-01-01", "end": "2026-01-31"}


def test_brand_split_case_insensitive():
    rows = [{"query": "Acme shoes", "clicks": 1}, {"query": "running shoes", "clicks": 2}]
    out = r.split_rows(rows, r.compile_brand_regex("acme"))
    assert list(out["brand"]) == ["Acme shoes"]
    assert list(out["nonbrand"]) == ["running shoes"]


def test_empty_brand_regex_rejected():
    with pytest.raises(ValueError):
        r.compile_brand_regex("  ")


def test_movers_rank_and_handle_missing_queries():
    cur = {"a": {"clicks": 10, "impressions": 100, "position": 3.0},
           "b": {"clicks": 1, "impressions": 50, "position": 9.0},
           "new": {"clicks": 7, "impressions": 20, "position": 5.0}}
    prev = {"a": {"clicks": 2, "impressions": 80, "position": 6.0},
            "b": {"clicks": 9, "impressions": 60, "position": 4.0},
            "gone": {"clicks": 4, "impressions": 30, "position": 7.0}}
    m = r.compute_movers(cur, prev, top_n=20)
    assert [x["query"] for x in m["risers"]] == ["a", "new"]
    assert [x["query"] for x in m["decliners"]] == ["b", "gone"]
    assert m["risers"][0]["position_change"] == -3.0
    assert m["decliners"][1]["position_change"] is None


def test_movers_capped_at_top_n():
    cur = {f"q{i}": {"clicks": i + 1} for i in range(30)}
    assert len(r.compute_movers(cur, {}, top_n=20)["risers"]) == 20


def test_build_and_render_report():
    periods = r.compute_periods("weekly", date(2026, 10, 9))
    tot = {"clicks": 10, "impressions": 100, "ctr": 10.0, "position": 4.2}
    gsc = {"current": {"rows": [{"query": "acme <x>", "clicks": 5, "impressions": 9,
                                 "position": 1.0}],
                       "totals": {"brand": tot, "nonbrand": tot}},
           "previous": {"rows": [], "totals": {"brand": {}, "nonbrand": tot}},
           "warnings": [], "errors": []}
    rep = r.build_report("sc-domain:acme.com", "acme", periods, gsc, None)
    assert rep["segments"]["brand"]["risers"][0]["query"] == "acme <x>"
    assert rep["segments"]["brand"]["totals"]["clicks"]["change_pct"] is None
    html = r.render_html(rep)
    assert "acme &lt;x&gt;" in html and "<x>" not in html
    assert "Non-brand" in r.render_markdown(rep)
    assert not rep["ai_performance"]["available"]
