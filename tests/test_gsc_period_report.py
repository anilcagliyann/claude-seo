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


def test_ai_source_regex_matches_whole_hosts_only():
    import re
    pat = re.compile(r.AI_SOURCE_REGEX)
    assert pat.search("chatgpt.com") and pat.search("l.meta.ai")
    assert not pat.search("peekyou.com")


def test_opportunities_pick_position_4_to_15_by_impressions():
    rows = {"a": {"impressions": 10, "position": 5.0}, "b": {"impressions": 99, "position": 2.0},
            "c": {"impressions": 50, "position": 14.9}}
    assert [o["query"] for o in r.find_opportunities(rows)] == ["c", "a"]


def test_config_rejects_bad_page_group(tmp_path):
    bad = tmp_path / "c.json"
    bad.write_text('{"page_groups": {"x": {"y": ""}}}')
    with pytest.raises(ValueError):
        r.load_report_config(str(bad))
    good = tmp_path / "g.json"
    good.write_text('{"brand_regex": "acme", "page_groups": {"Types": {"Product": "-p-"}}}')
    assert r.load_report_config(str(good))["brand_regex"] == "acme"


def test_page_groups_and_turkish_render():
    periods = r.compute_periods("monthly", date(2026, 10, 9))
    tot = {"clicks": 10, "impressions": 100, "ctr": 10.0, "position": 4.2}
    grp = {"Types": {"Product": {"brand": tot, "nonbrand": tot}}}
    gsc = {"current": {"rows": [], "totals": {"brand": tot, "nonbrand": tot},
                       "pages": {"brand": [], "nonbrand": [
                           {"page": "https://acme.com/x-p-1", "clicks": 3}]},
                       "groups": grp},
           "previous": {"rows": [], "totals": {"brand": tot, "nonbrand": tot},
                        "pages": {}, "groups": grp},
           "warnings": [], "errors": []}
    rep = r.build_report("sc-domain:acme.com", "acme", periods, gsc, None)
    assert rep["segments"]["nonbrand"]["pages"]["risers"][0]["page"].endswith("x-p-1")
    md = r.render_markdown(rep, "tr")
    assert "aylık" in md and "Sayfa grupları" in md and "/x-p-1" in md
    assert "brand / non-brand ayrımı yapılamaz" in md
    assert "<table" in r.render_html(rep, "tr")


def test_exclude_regex_drops_queries_from_lists():
    import re
    rows = [{"query": "spam deal", "clicks": 1}, {"query": "shoes", "clicks": 2}]
    out = r.split_rows(rows, r.compile_brand_regex("acme"), re.compile("spam"))
    assert list(out["nonbrand"]) == ["shoes"]


def test_monthly_has_yoy_same_month_last_year():
    p = r.compute_periods("monthly", date(2026, 3, 3))
    assert p["yoy"] == {"start": "2025-02-01", "end": "2025-02-28"}
    assert "yoy" not in r.compute_periods("weekly", date(2026, 3, 3))


def _report(nonbrand_prev, summary=None):
    periods = r.compute_periods("weekly", date(2026, 10, 9))
    cur = {"clicks": 85, "impressions": 100, "ctr": 1.0, "position": 4.0}
    prev = dict(cur, clicks=nonbrand_prev)
    gsc = {"current": {"rows": [], "totals": {"brand": cur, "nonbrand": cur}},
           "previous": {"rows": [], "totals": {"brand": cur, "nonbrand": prev}},
           "warnings": [], "errors": []}
    organic = {"available": True,
               "totals": r.compare_totals_metrics(
                   {"sessions": 10, "keyEvents": 2, "transactions": 1, "purchaseRevenue": 99.5},
                   {"sessions": 8, "keyEvents": 2, "transactions": 0, "purchaseRevenue": 0},
                   r.ORGANIC_METRICS)}
    return r.build_report("sc-domain:acme.com", "acme", periods, gsc, None,
                          organic=organic, alert_threshold_pct=10, summary=summary)


def test_alert_adds_warning_sign_to_subject():
    hit = _report(100)  # 85 vs 100 = -15%
    assert hit["alert"]["triggered"] and r.build_subject(hit, "tr").startswith("⚠️ ")
    calm = _report(90)  # -5.6%
    assert not calm["alert"]["triggered"] and not r.build_subject(calm).startswith("⚠️")


def test_summary_and_organic_render():
    rep = _report(90, summary="Line one.\nLine two.")
    html = r.render_html(rep, "tr")
    assert "Yönetici özeti" in html and "Line two." in html and "Gelir" in html
    assert "Satış adedi" in r.render_markdown(rep, "tr")


def test_send_email_resend_posts_and_hides_key(monkeypatch):
    import requests

    calls = {}

    class Resp:
        status_code = 200

        def json(self):
            return {"id": "abc"}

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.update(url=url, headers=headers, json=json)
        return Resp()

    monkeypatch.setattr(requests, "post", fake_post)
    out = r.send_email_resend("re_secret", ["a@b.com"], "Subj", "<p>x</p>")
    assert out == {"sent": True, "id": "abc", "error": None}
    assert calls["url"] == r.RESEND_ENDPOINT and calls["json"]["to"] == ["a@b.com"]

    class Bad(Resp):
        status_code = 403

        def json(self):
            return {"message": "domain not verified"}

    monkeypatch.setattr(requests, "post", lambda *a, **k: Bad())
    out = r.send_email_resend("re_secret", ["a@b.com"], "S", "h")
    assert not out["sent"] and "403" in out["error"] and "re_secret" not in out["error"]
