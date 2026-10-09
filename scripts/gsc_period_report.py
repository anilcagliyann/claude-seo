#!/usr/bin/env python3
"""
Weekly / monthly Search Console comparison report with a brand split.

Compares the last complete period against the one before it:

- weekly:  last complete Monday-Sunday week vs the Monday-Sunday week before it
- monthly: last complete calendar month vs the calendar month before it

Monthly reports also compare totals with the same month last year. GA4 adds
organic sessions, key events, purchases and revenue. --email-to sends the
HTML report through the Resend API (RESEND_API_KEY). The JSON carries an email
"subject" that starts with a warning sign when non-brand clicks fell by the
alert threshold or more; --summary-file puts an executive summary on top.

For each segment (brand, non-brand) it reports clicks, impressions, CTR and
position deltas, the 20 queries and 20 pages that lost the most clicks and the
20 of each that gained the most, and the queries ranking 4-15 with the most
impressions. Brand queries are those matching --brand-regex (case-insensitive).

An optional --config JSON file holds the brand regex and page groups, whose
clicks are compared per segment:

    {"brand_regex": "acme|acmee", "exclude_query_regex": "spam|casino",
     "alert_threshold_pct": 10,
     "page_groups": {"Categories": {"Shoes": "-c-12\\d*$"},
                     "Page types": {"Product": "-p-", "Brand": "/brand/"}}}

AI performance comes from GA4: sessions from the "AI Assistants" default
channel plus referrals from known AI domains, compared across the same two
periods. GA4 carries no search query, so AI traffic cannot be split into brand
and non-brand; the report says so instead of guessing. The Search Console
Generative AI performance report has no verified API, so it is not used.

Usage:
    python gsc_period_report.py --property sc-domain:example.com \
        --brand-regex "example|exmpl" --period weekly --json
    python gsc_period_report.py --property sc-domain:example.com \
        --brand-regex "example" --period monthly --ga4-property 123456789 \
        --format html --output report.html
"""

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from html import escape
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TOP_N = 20
GSC_LAG_DAYS = 3
QUERY_ROW_LIMIT = 25000
# Whole host names only, so e.g. peekyou.com never matches you.com.
AI_SOURCE_REGEX = (
    r"(^|\.)(chatgpt\.com|chat\.openai\.com|openai\.com|perplexity\.ai|gemini\.google\.com|"
    r"bard\.google\.com|copilot\.microsoft\.com|claude\.ai|deepseek\.com|grok\.com|"
    r"you\.com|meta\.ai|mistral\.ai)$"
)
FRESH_NOTE = (
    "The current period ended less than 3 days ago; recent Search Console "
    "data is preliminary. Schedule the report for Wednesday or later."
)
ANON_NOTE = (
    "Query rows exclude anonymized queries, so movers cover named queries only; "
    "segment totals come from filtered aggregate queries."
)
AI_BRAND_NOTE = (
    "GA4 has no search query for AI referrals, so AI traffic is reported as one "
    "total and cannot be split into brand and non-brand."
)


# --------------------------------------------------------------------------- #
# Periods
# --------------------------------------------------------------------------- #

def compute_periods(kind: str, today: Optional[date] = None) -> dict:
    """Return current and previous date ranges for a weekly or monthly report.

    Weekly ranges always run Monday-Sunday; monthly ranges are calendar months.
    """
    today = today or date.today()
    if kind == "weekly":
        # Most recent Sunday strictly before today.
        cur_end = today - timedelta(days=today.weekday() + 1)
        cur_start = cur_end - timedelta(days=6)
        prev_end = cur_start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=6)
    elif kind == "monthly":
        cur_end = today.replace(day=1) - timedelta(days=1)
        cur_start = cur_end.replace(day=1)
        prev_end = cur_start - timedelta(days=1)
        prev_start = prev_end.replace(day=1)
    else:
        raise ValueError("period must be 'weekly' or 'monthly'")
    periods = {
        "kind": kind,
        "current": {"start": cur_start.isoformat(), "end": cur_end.isoformat()},
        "previous": {"start": prev_start.isoformat(), "end": prev_end.isoformat()},
        "fresh_data": (today - cur_end).days < GSC_LAG_DAYS,
    }
    if kind == "monthly":
        # Same calendar month a year earlier, to separate seasonality.
        yoy_start = cur_start.replace(year=cur_start.year - 1)
        next_month = (yoy_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        periods["yoy"] = {"start": yoy_start.isoformat(),
                          "end": (next_month - timedelta(days=1)).isoformat()}
    return periods


def range_keys(periods: dict) -> tuple:
    """Date-range keys present in a periods dict, in display order."""
    return tuple(k for k in ("current", "previous", "yoy") if k in periods)


# --------------------------------------------------------------------------- #
# Brand split and movers (pure functions, unit tested)
# --------------------------------------------------------------------------- #

def compile_brand_regex(pattern: str) -> re.Pattern:
    """Compile the brand pattern case-insensitively, rejecting empty input."""
    if not pattern or not pattern.strip():
        raise ValueError("--brand-regex must not be empty")
    return re.compile(pattern, re.IGNORECASE)


def split_rows(rows: list, brand_re: re.Pattern,
               exclude_re: Optional[re.Pattern] = None) -> dict:
    """Split query rows into {'brand': {query: row}, 'nonbrand': {query: row}}.

    Queries matching exclude_re are dropped from the lists (totals keep them).
    """
    out = {"brand": {}, "nonbrand": {}}
    for row in rows:
        query = row.get("query") or (row.get("keys") or [""])[0]
        if not query or (exclude_re and exclude_re.search(query)):
            continue
        segment = "brand" if brand_re.search(query) else "nonbrand"
        out[segment][query] = row
    return out


def _pct(cur: float, prev: float) -> Optional[float]:
    if not prev:
        return None
    return round((cur - prev) / prev * 100, 1)


def compare_totals(cur: dict, prev: dict) -> dict:
    """Build a metric-by-metric comparison of two GSC totals blocks."""
    return compare_totals_metrics(cur, prev, ("clicks", "impressions", "ctr", "position"))


def compare_totals_metrics(cur: dict, prev: dict, metrics: tuple) -> dict:
    """Compare the named metrics of two totals blocks."""
    out = {}
    for metric in metrics:
        c = cur.get(metric, 0) or 0
        p = prev.get(metric, 0) or 0
        out[metric] = {
            "current": c,
            "previous": p,
            "change": round(c - p, 2),
            "change_pct": _pct(c, p),
        }
    return out


def compute_movers(cur_rows: dict, prev_rows: dict, top_n: int = TOP_N,
                   key_name: str = "query") -> dict:
    """Rank queries by click change between two periods.

    A query missing from one period counts as zero clicks there. Ties break on
    the impression change so the list stays stable.
    """
    movers = []
    for item in set(cur_rows) | set(prev_rows):
        c = cur_rows.get(item, {})
        p = prev_rows.get(item, {})
        c_clicks, p_clicks = c.get("clicks", 0), p.get("clicks", 0)
        c_impr, p_impr = c.get("impressions", 0), p.get("impressions", 0)
        c_pos, p_pos = c.get("position"), p.get("position")
        movers.append({
            key_name: item,
            "clicks_current": c_clicks,
            "clicks_previous": p_clicks,
            "clicks_change": c_clicks - p_clicks,
            "clicks_change_pct": _pct(c_clicks, p_clicks),
            "impressions_current": c_impr,
            "impressions_previous": p_impr,
            "impressions_change": c_impr - p_impr,
            "position_current": c_pos,
            "position_previous": p_pos,
            "position_change": (
                round(c_pos - p_pos, 1) if c_pos is not None and p_pos is not None else None
            ),
        })
    decliners = sorted(
        (m for m in movers if m["clicks_change"] < 0),
        key=lambda m: (m["clicks_change"], m["impressions_change"], m[key_name]),
    )[:top_n]
    risers = sorted(
        (m for m in movers if m["clicks_change"] > 0),
        key=lambda m: (-m["clicks_change"], -m["impressions_change"], m[key_name]),
    )[:top_n]
    return {"decliners": decliners, "risers": risers}


def find_opportunities(rows: dict, top_n: int = TOP_N) -> list:
    """Queries ranking 4-15 with the most impressions: the closest ranking wins."""
    picks = [
        {"query": q, "impressions": r.get("impressions", 0), "clicks": r.get("clicks", 0),
         "ctr": r.get("ctr"), "position": r.get("position")}
        for q, r in rows.items()
        if r.get("position") is not None and 4 <= r["position"] <= 15
    ]
    return sorted(picks, key=lambda r: (-r["impressions"], r["query"]))[:top_n]


def load_report_config(path: Optional[str]) -> dict:
    """Read the optional JSON config: brand_regex and page_groups.

    page_groups maps a group title to {label: regex}; each regex is matched
    against the page URL by Search Console (RE2 syntax).
    """
    if not path:
        return {}
    with open(path, encoding="utf-8") as fh:
        config = json.load(fh)
    groups = config.get("page_groups", {})
    if not isinstance(groups, dict) or not all(
        isinstance(g, dict) and all(isinstance(v, str) and v for v in g.values())
        for g in groups.values()
    ):
        raise ValueError("page_groups must map a title to {label: regex}")
    for g in groups.values():
        for regex in g.values():
            re.compile(regex)
    if config.get("exclude_query_regex"):
        re.compile(config["exclude_query_regex"])
    return config


# --------------------------------------------------------------------------- #
# Data fetching
# --------------------------------------------------------------------------- #

def _gsc_segment_filter(brand_regex: str, segment: str) -> list:
    operator = "includingRegex" if segment == "brand" else "excludingRegex"
    return [{"dimension": "query", "operator": operator, "expression": f"(?i){brand_regex}"}]


def fetch_gsc(property_url: str, brand_regex: str, periods: dict,
              page_groups: Optional[dict] = None) -> dict:
    """Fetch query rows, page rows and totals per segment for both periods."""
    from gsc_query import query_search_analytics

    data_state = "all" if periods["fresh_data"] else "final"
    out = {"errors": [], "warnings": []}
    for key in range_keys(periods):
        rng = periods[key]
        if key == "yoy":
            out[key] = {"rows": [], "totals": {}}
            for segment in ("brand", "nonbrand"):
                totals = query_search_analytics(
                    property_url, rng["start"], rng["end"], dimensions=[],
                    row_limit=1, data_state="final",
                    filters=_gsc_segment_filter(brand_regex, segment),
                )
                if totals.get("error"):
                    out["errors"].append(f"yoy {segment} totals: {totals['error']}")
                out["warnings"].extend(w for w in totals.get("warnings", [])
                                       if w not in out["warnings"])
                out[key]["totals"][segment] = totals.get("totals", {})
            continue
        rows = query_search_analytics(
            property_url, rng["start"], rng["end"], dimensions=["query"],
            row_limit=QUERY_ROW_LIMIT, data_state=data_state,
        )
        if rows.get("error"):
            out["errors"].append(f"{key} queries: {rows['error']}")
        out["warnings"].extend(w for w in rows.get("warnings", []) if w not in out["warnings"])
        out[key] = {"rows": rows.get("rows", []), "totals": {}}
        for segment in ("brand", "nonbrand"):
            totals = query_search_analytics(
                property_url, rng["start"], rng["end"], dimensions=[],
                row_limit=1, data_state=data_state,
                filters=_gsc_segment_filter(brand_regex, segment),
            )
            if totals.get("error"):
                out["errors"].append(f"{key} {segment} totals: {totals['error']}")
            out[key]["totals"][segment] = totals.get("totals", {})
            pages = query_search_analytics(
                property_url, rng["start"], rng["end"], dimensions=["page"],
                row_limit=QUERY_ROW_LIMIT, data_state=data_state,
                filters=_gsc_segment_filter(brand_regex, segment),
            )
            if pages.get("error"):
                out["errors"].append(f"{key} {segment} pages: {pages['error']}")
            out[key].setdefault("pages", {})[segment] = pages.get("rows", [])
            for title, group in (page_groups or {}).items():
                for label, regex in group.items():
                    g = query_search_analytics(
                        property_url, rng["start"], rng["end"], dimensions=[],
                        row_limit=1, data_state=data_state,
                        filters=_gsc_segment_filter(brand_regex, segment) + [
                            {"dimension": "page", "operator": "includingRegex",
                             "expression": regex}],
                    )
                    if g.get("error"):
                        out["errors"].append(f"{key} {segment} {label}: {g['error']}")
                    (out[key].setdefault("groups", {}).setdefault(title, {})
                     .setdefault(label, {}))[segment] = g.get("totals", {})
    return out


def _ga4_by_range(property_id: str, periods: dict, dimension: str, dim_filter,
                  metrics: tuple) -> tuple:
    """Run one GA4 report over every period; return ({dim: {range: {metric}}}, error)."""
    try:
        from google.analytics.data_v1beta.types import (
            DateRange, Dimension, Metric, RunReportRequest,
        )
        from ga4_report import _build_ga4_client, _resolve_property
    except (ImportError, SystemExit):
        return None, "google-analytics-data is not installed."
    client = _build_ga4_client()
    if not client:
        return None, "Could not build GA4 client. Check credentials and property access."
    keys = range_keys(periods)
    try:
        response = client.run_report(RunReportRequest(
            property=_resolve_property(property_id),
            dimensions=[Dimension(name=dimension)],
            metrics=[Metric(name=m) for m in metrics],
            date_ranges=[DateRange(start_date=periods[k]["start"], end_date=periods[k]["end"],
                                   name=k) for k in keys],
            dimension_filter=dim_filter,
            limit=1000,
        ))
    except Exception as e:
        return None, f"GA4 API error: {e}"
    out: dict = {}
    for row in response.rows:
        # With several date ranges GA4 appends a dateRange dimension.
        name = row.dimension_values[0].value
        range_name = row.dimension_values[1].value if len(keys) > 1 else keys[0]
        bucket = out.setdefault(name, {k: dict.fromkeys(metrics, 0.0) for k in keys})
        for metric, value in zip(metrics, row.metric_values):
            bucket[range_name][metric] += float(value.value or 0)
    return out, None


def _sum_ranges(data: dict, keys: tuple, metrics: tuple) -> dict:
    totals = {k: dict.fromkeys(metrics, 0.0) for k in keys}
    for bucket in data.values():
        for k in keys:
            for m in metrics:
                totals[k][m] += bucket[k][m]
    return totals


def fetch_ga4_ai(property_id: str, periods: dict) -> dict:
    """Fetch AI-assistant sessions by source for every period from GA4."""
    result = {"available": False, "error": None, "note": AI_BRAND_NOTE}
    try:
        from google.analytics.data_v1beta.types import (
            Filter, FilterExpression, FilterExpressionList,
        )
    except ImportError:
        result["error"] = "google-analytics-data is not installed."
        return result
    ai_filter = FilterExpression(or_group=FilterExpressionList(expressions=[
        FilterExpression(filter=Filter(
            field_name="sessionDefaultChannelGroup",
            string_filter=Filter.StringFilter(
                match_type=Filter.StringFilter.MatchType.EXACT, value="AI Assistants"),
        )),
        FilterExpression(filter=Filter(
            field_name="sessionSource",
            string_filter=Filter.StringFilter(
                match_type=Filter.StringFilter.MatchType.PARTIAL_REGEXP,
                value=AI_SOURCE_REGEX, case_sensitive=False),
        )),
    ]))
    metrics = ("sessions", "totalUsers", "engagedSessions", "keyEvents")
    data, error = _ga4_by_range(property_id, periods, "sessionSource", ai_filter, metrics)
    if error:
        result["error"] = error
        return result
    keys = range_keys(periods)
    totals = _sum_ranges(data, keys, metrics)
    result["available"] = True
    result["detail"] = totals
    result["totals"] = compare_totals({"clicks": totals["current"]["sessions"]},
                                      {"clicks": totals["previous"]["sessions"]})["clicks"]
    if "yoy" in keys:
        result["yoy"] = compare_totals({"clicks": totals["current"]["sessions"]},
                                       {"clicks": totals["yoy"]["sessions"]})["clicks"]
    result["sources"] = sorted(
        ({"source": s, "current": v["current"]["sessions"], "previous": v["previous"]["sessions"],
          "change": v["current"]["sessions"] - v["previous"]["sessions"]}
         for s, v in data.items()),
        key=lambda r: -r["current"],
    )
    return result


ORGANIC_METRICS = ("sessions", "keyEvents", "transactions", "purchaseRevenue")


def fetch_ga4_organic(property_id: str, periods: dict) -> dict:
    """Fetch organic-search sessions, key events, purchases and revenue from GA4."""
    result = {"available": False, "error": None}
    try:
        from google.analytics.data_v1beta.types import Filter, FilterExpression
    except ImportError:
        result["error"] = "google-analytics-data is not installed."
        return result
    organic = FilterExpression(filter=Filter(
        field_name="sessionDefaultChannelGroup",
        string_filter=Filter.StringFilter(
            match_type=Filter.StringFilter.MatchType.EXACT, value="Organic Search"),
    ))
    data, error = _ga4_by_range(property_id, periods, "sessionDefaultChannelGroup",
                                organic, ORGANIC_METRICS)
    if error:
        result["error"] = error
        return result
    totals = _sum_ranges(data, range_keys(periods), ORGANIC_METRICS)
    result["available"] = True
    result["detail"] = totals
    result["totals"] = compare_totals_metrics(totals["current"], totals["previous"],
                                              ORGANIC_METRICS)
    if "yoy" in totals:
        result["yoy"] = compare_totals_metrics(totals["current"], totals["yoy"],
                                               ORGANIC_METRICS)
    return result


def evaluate_alert(segments: dict, threshold_pct: float) -> dict:
    """Flag the report when non-brand clicks fell by more than threshold_pct."""
    change = segments["nonbrand"]["totals"]["clicks"]["change_pct"]
    return {
        "threshold_pct": threshold_pct,
        "nonbrand_clicks_change_pct": change,
        "triggered": change is not None and change <= -abs(threshold_pct),
    }


def build_report(property_url: str, brand_regex: str, periods: dict,
                 gsc: dict, ai: Optional[dict], exclude_regex: Optional[str] = None,
                 organic: Optional[dict] = None, alert_threshold_pct: float = 10.0,
                 summary: Optional[str] = None) -> dict:
    """Assemble the final report structure from fetched data."""
    brand_re = compile_brand_regex(brand_regex)
    exclude_re = re.compile(exclude_regex, re.IGNORECASE) if exclude_regex else None
    cur = split_rows(gsc["current"]["rows"], brand_re, exclude_re)
    prev = split_rows(gsc["previous"]["rows"], brand_re, exclude_re)
    segments = {}
    for segment in ("brand", "nonbrand"):
        segments[segment] = {
            "totals": compare_totals(gsc["current"]["totals"].get(segment, {}),
                                     gsc["previous"]["totals"].get(segment, {})),
            **compute_movers(cur[segment], prev[segment]),
            "pages": compute_movers(
                {r["page"]: r for r in gsc["current"].get("pages", {}).get(segment, [])},
                {r["page"]: r for r in gsc["previous"].get("pages", {}).get(segment, [])},
                key_name="page"),
            "opportunities": find_opportunities(cur[segment]),
        }
        if "yoy" in gsc:
            segments[segment]["yoy"] = compare_totals(
                gsc["current"]["totals"].get(segment, {}),
                gsc["yoy"]["totals"].get(segment, {}))
    groups = {}
    for title, labels in gsc["current"].get("groups", {}).items():
        groups[title] = {
            label: {seg: compare_totals(
                        vals.get(seg, {}),
                        gsc["previous"].get("groups", {}).get(title, {}).get(label, {}).get(seg, {}))
                    for seg in ("nonbrand", "brand")}
            for label, vals in labels.items()
        }
    warnings = list(gsc.get("warnings", []))
    if periods["fresh_data"]:
        warnings.append(FRESH_NOTE)
    warnings.append(ANON_NOTE)
    return {
        "property": property_url,
        "brand_regex": brand_regex,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "periods": periods,
        "segments": segments,
        "page_groups": groups,
        "alert": evaluate_alert(segments, alert_threshold_pct),
        "summary": summary,
        "organic_ga4": organic or {"available": False, "error": "No --ga4-property given."},
        "ai_performance": ai or {"available": False, "error": "No --ga4-property given.",
                                 "note": AI_BRAND_NOTE},
        "warnings": warnings,
        "errors": gsc.get("errors", []),
    }


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

LABELS = {
    "en": {
        "lang": "en", "title": "SEO {kind} report", "weekly": "weekly", "monthly": "monthly",
        "current": "Current", "previous": "Previous", "to": "to", "yoy": "Last year",
        "yoy_pct": "YoY %", "nonbrand": "Non-brand", "brand": "Brand",
        "metric": "Metric", "change": "Change",
        "clicks": "Clicks", "impressions": "Impressions", "ctr": "CTR %", "position": "Position",
        "decliners": "Top declining queries", "risers": "Top rising queries",
        "page_decliners": "Top declining pages", "page_risers": "Top rising pages",
        "opportunities": "Opportunities: position 4-15, most impressions",
        "query": "Query", "page": "Page", "now": "Now", "before": "Before",
        "pos_now": "Pos. now", "pos_before": "Pos. before",
        "groups": "Page groups (clicks)", "group": "Group",
        "ai": "AI performance (GA4)", "ai_sessions": "AI sessions", "source": "Source",
        "organic": "Organic search business results (GA4)",
        "sessions": "Sessions", "keyEvents": "Key events", "transactions": "Purchases",
        "purchaseRevenue": "Revenue", "revenue": "Organic revenue",
        "summary": "Executive summary", "alert_on": "Alert: non-brand clicks fell {pct}",
        "alert_off": "No alert: non-brand clicks {pct} (threshold -{thr}%)",
        "vs_prev": "vs previous", "vs_yoy": "vs last year", "na": "Not available",
        "subject": "SEO {kind} report: {site} | Non-brand clicks {pct}",
    },
    "tr": {
        "lang": "tr", "title": "SEO {kind} raporu", "weekly": "haftalık", "monthly": "aylık",
        "current": "Bu dönem", "previous": "Önceki dönem", "to": "-", "yoy": "Geçen yıl",
        "yoy_pct": "Yıllık %", "nonbrand": "Non-brand", "brand": "Brand",
        "metric": "Metrik", "change": "Değişim",
        "clicks": "Tıklama", "impressions": "Gösterim", "ctr": "TO %", "position": "Pozisyon",
        "decliners": "En çok düşen kelimeler", "risers": "En çok yükselen kelimeler",
        "page_decliners": "En çok düşen sayfalar", "page_risers": "En çok yükselen sayfalar",
        "opportunities": "Fırsatlar: 4-15. sıradaki en çok gösterim alan kelimeler",
        "query": "Kelime", "page": "Sayfa", "now": "Şimdi", "before": "Önce",
        "pos_now": "Poz. şimdi", "pos_before": "Poz. önce",
        "groups": "Sayfa grupları (tıklama)", "group": "Grup",
        "ai": "AI performansı (GA4)", "ai_sessions": "AI oturumları", "source": "Kaynak",
        "organic": "Organik arama iş sonuçları (GA4)",
        "sessions": "Oturum", "keyEvents": "Dönüşüm (key event)", "transactions": "Satış adedi",
        "purchaseRevenue": "Gelir", "revenue": "Organik gelir",
        "summary": "Yönetici özeti", "alert_on": "Uyarı: Non-brand tıklama {pct} düştü",
        "alert_off": "Uyarı yok: Non-brand tıklama {pct} (eşik -{thr}%)",
        "vs_prev": "önceki döneme göre", "vs_yoy": "geçen yıla göre", "na": "Veri yok",
        "subject": "SEO {kind} raporu: {site} | Non-brand tıklama {pct}",
    },
}
SEGMENTS = ("nonbrand", "brand")
ACCENTS = {"nonbrand": "#2563eb", "brand": "#b8860b", "groups": "#6d28d9",
           "organic": "#2d6a4f", "ai": "#0f766e", "summary": "#b8860b"}
NOTES = {
    "organic": "GA4 has no search query, so organic sessions, purchases and revenue "
               "are one total for brand and non-brand search together.",
}
NOTES_TR = {
    NOTES["organic"]: "GA4 arama kelimesi tutmadığı için organik oturum, satış ve gelir "
                      "brand ve non-brand aramaların toplamıdır.",
    AI_BRAND_NOTE: "GA4 AI yönlendirmelerinde arama kelimesi tutmadığı için AI trafiği tek "
                   "toplam olarak verilir; brand / non-brand ayrımı yapılamaz.",
    ANON_NOTE: "Kelime satırları Google'ın gizlediği (anonim) sorguları içermez; düşen/yükselen "
               "listeleri yalnızca görünen kelimeleri kapsar. Segment toplamları filtreli "
               "toplam sorgularından gelir.",
    "GSC impressions logging error affected impressions, CTR, and average position from "
    "2025-05-13 through 2026-04-27; clicks were not affected.":
        "Google'ın 13.05.2025 - 27.04.2026 arasındaki gösterim kayıt hatası gösterim, TO ve "
        "ortalama pozisyonu etkiledi; tıklamalar etkilenmedi. Yıllık gösterim kıyasını "
        "dikkatli okuyun.",
    FRESH_NOTE: "Dönem 3 günden kısa süre önce bitti; son günlerin Search Console verisi "
                "henüz kesinleşmedi.",
}


def _note(text: str, lang: str) -> str:
    return NOTES_TR.get(text, text) if lang == "tr" else text


def _fmt(value, pct=False) -> str:
    if value is None:
        return "-"
    if pct:
        return f"{value:+.1f}%"
    if isinstance(value, float) and not value.is_integer() and abs(value) < 1000:
        return f"{value:,.2f}"
    return f"{int(value):,}"


def _sgn(value) -> str:
    """Format a change with an explicit sign."""
    if value is None:
        return "-"
    if isinstance(value, float) and not value.is_integer() and abs(value) < 1000:
        return f"{value:+,.2f}"
    return f"{int(value):+,}"


def _short_url(url: str) -> str:
    return re.sub(r"^https?://[^/]+", "", url) or "/"


def _site(report: dict) -> str:
    return re.sub(r"^(sc-domain:|https?://)", "", report["property"]).rstrip("/")


def build_subject(report: dict, lang: str = "en") -> str:
    """Email subject line, prefixed with a warning sign when the alert fired."""
    L = LABELS[lang]
    pct = _fmt(report["alert"]["nonbrand_clicks_change_pct"], True)
    subject = L["subject"].format(kind=L[report["periods"]["kind"]], site=_site(report), pct=pct)
    return ("⚠️ " + subject) if report["alert"]["triggered"] else subject


def _totals_table(comp: dict, yoy: Optional[dict], metrics: tuple, L: dict) -> tuple:
    headers = [L["metric"], L["current"], L["previous"], L["change"], "%"]
    if yoy:
        headers += [L["yoy"], L["yoy_pct"]]
    rows = []
    for m in metrics:
        t = comp[m]
        row = [L[m], _fmt(t["current"]), _fmt(t["previous"]), _sgn(t["change"]),
               _fmt(t["change_pct"], True)]
        if yoy:
            row += [_fmt(yoy[m]["previous"]), _fmt(yoy[m]["change_pct"], True)]
        rows.append(row)
    signed = (3, 4, 6) if yoy else (3, 4)
    return ("table", headers, rows, signed)


def _blocks(report: dict, L: dict) -> list:
    """Describe the report as render-neutral blocks.

    ("h2", title, accent) | ("p", text) | ("summary", text) | ("alert", text, on)
    | ("kpis", [(label, value, pct, sub)]) | ("table", headers, rows, signed_cols).
    """
    segs = report["segments"]
    org = report.get("organic_ga4", {})
    ai = report["ai_performance"]
    out = []
    alert = report["alert"]
    pct = _fmt(alert["nonbrand_clicks_change_pct"], True)
    out.append(("alert", (L["alert_on"] if alert["triggered"] else L["alert_off"]).format(
        pct=pct, thr=_fmt(alert["threshold_pct"])), alert["triggered"]))
    if report.get("summary"):
        out.append(("h2", L["summary"], ACCENTS["summary"]))
        out.append(("summary", report["summary"]))

    def kpi(label, comp, yoy):
        sub = f'{L["vs_yoy"]}: {_fmt(yoy["change_pct"], True)}' if yoy else ""
        return (label, _fmt(comp["current"]), _fmt(comp["change_pct"], True), sub)

    kpis = [kpi(f'{L["nonbrand"]} {L["clicks"].lower()}', segs["nonbrand"]["totals"]["clicks"],
                segs["nonbrand"].get("yoy", {}).get("clicks")),
            kpi(f'{L["brand"]} {L["clicks"].lower()}', segs["brand"]["totals"]["clicks"],
                segs["brand"].get("yoy", {}).get("clicks"))]
    if org.get("available"):
        kpis.append(kpi(L["revenue"], org["totals"]["purchaseRevenue"],
                        org.get("yoy", {}).get("purchaseRevenue")))
    if ai.get("available"):
        kpis.append(kpi(L["ai_sessions"], ai["totals"], ai.get("yoy")))
    out.append(("kpis", kpis))

    for segment in SEGMENTS:
        seg = segs[segment]
        out.append(("h2", L[segment], ACCENTS[segment]))
        out.append(_totals_table(seg["totals"], seg.get("yoy"),
                                 ("clicks", "impressions", "ctr", "position"), L))
        for key in ("decliners", "risers"):
            out.append(("h3", f"{L[key]} ({len(seg[key])})"))
            out.append(("table", [L["query"], L["now"], L["before"], L["change"],
                                  L["pos_now"], L["pos_before"]],
                        [[m["query"], _fmt(m["clicks_current"]), _fmt(m["clicks_previous"]),
                          f'{m["clicks_change"]:+d}', _fmt(m["position_current"]),
                          _fmt(m["position_previous"])] for m in seg[key]], (3,)))
        for key in ("decliners", "risers"):
            rows = seg.get("pages", {}).get(key, [])
            out.append(("h3", f"{L['page_' + key]} ({len(rows)})"))
            out.append(("table", [L["page"], L["now"], L["before"], L["change"],
                                  L["pos_now"], L["pos_before"]],
                        [[_short_url(m["page"]), _fmt(m["clicks_current"]),
                          _fmt(m["clicks_previous"]), f'{m["clicks_change"]:+d}',
                          _fmt(m["position_current"]), _fmt(m["position_previous"])]
                         for m in rows], (3,)))
        opps = seg.get("opportunities", [])
        if opps:
            out.append(("h3", f"{L['opportunities']} ({len(opps)})"))
            out.append(("table", [L["query"], L["impressions"], L["clicks"], L["ctr"],
                                  L["position"]],
                        [[o["query"], _fmt(o["impressions"]), _fmt(o["clicks"]),
                          _fmt(o["ctr"]), _fmt(o["position"])] for o in opps], ()))
    for title, labels in report.get("page_groups", {}).items():
        out.append(("h2", f"{L['groups']}: {title}", ACCENTS["groups"]))
        out.append(("table", [L["group"]] + [f"{L[s]} {h}" for s in SEGMENTS
                                             for h in (L["now"], L["before"], "%")], [
            [label] + [v for s in SEGMENTS for v in (
                _fmt(c[s]["clicks"]["current"]), _fmt(c[s]["clicks"]["previous"]),
                _fmt(c[s]["clicks"]["change_pct"], True))]
            for label, c in labels.items()
        ], (3, 6)))
    out.append(("h2", L["organic"], ACCENTS["organic"]))
    if org.get("available"):
        out.append(_totals_table(org["totals"], org.get("yoy"), ORGANIC_METRICS, L))
        out.append(("p", NOTES["organic"]))
    else:
        out.append(("p", f'{L["na"]}: {org.get("error")}'))
    out.append(("h2", L["ai"], ACCENTS["ai"]))
    if ai.get("available"):
        out.append(("table", [L["source"], L["current"], L["previous"], L["change"]],
                    [[x["source"], _fmt(x["current"]), _fmt(x["previous"]), _sgn(x["change"])]
                     for x in ai["sources"][:15]], (3,)))
    else:
        out.append(("p", f'{L["na"]}: {ai.get("error")}'))
    out.append(("p", ai["note"]))
    return out


def _header(report: dict, L: dict) -> tuple:
    p = report["periods"]
    title = f'{L["title"].format(kind=L[p["kind"]])}: {_site(report)}'
    sub = (f'{L["current"]}: {p["current"]["start"]} {L["to"]} {p["current"]["end"]} | '
           f'{L["previous"]}: {p["previous"]["start"]} {L["to"]} {p["previous"]["end"]}')
    if "yoy" in p:
        sub += f' | {L["yoy"]}: {p["yoy"]["start"]} {L["to"]} {p["yoy"]["end"]}'
    return title, sub


def render_markdown(report: dict, lang: str = "en") -> str:
    """Render the report as Markdown (fits a routine summary or email body)."""
    L = LABELS[lang]
    title, sub = _header(report, L)
    lines = [f"# {title}", sub, ""]
    for block in _blocks(report, L):
        kind = block[0]
        if kind == "h2":
            lines += [f"## {block[1]}", ""]
        elif kind == "h3":
            lines += [f"### {block[1]}", ""]
        elif kind in ("p", "summary"):
            lines += [_note(block[1], lang), ""]
        elif kind == "alert":
            lines += [("**⚠️ " if block[2] else "**") + block[1] + "**", ""]
        elif kind == "kpis":
            lines += [" | ".join(f"**{k[0]}**: {k[1]} ({k[2]})" for k in block[1]), ""]
        elif kind == "table":
            _, headers, rows, _signed = block
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("|" + "---|" * len(headers))
            lines += ["| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |"
                      for r in rows]
            lines.append("")
    lines += [f"- {_note(w, lang)}" for w in report["warnings"] + report["errors"]]
    return "\n".join(lines)


def render_html(report: dict, lang: str = "en") -> str:
    """Render the report as colourful, email-safe HTML (inline styles, tables only)."""
    L = LABELS[lang]
    navy, green, red, cream = "#1e3a5f", "#2d6a4f", "#c53030", "#faf9f7"
    font = "font-family:Arial,Helvetica,sans-serif"
    accent = navy

    def pill(text, invert=False):
        text = escape(str(text))
        if text in ("-", "", "0", "+0", "+0.0%", "+0.00"):
            return text
        good = text.startswith("-") == invert
        fg, bg = (green, "#e6f4ec") if good else (red, "#fdecec")
        return (f'<span style="background:{bg};color:{fg};padding:2px 7px;border-radius:10px;'
                f'font-weight:bold;white-space:nowrap">{text}</span>')

    title, sub = _header(report, L)
    parts = [
        f'<div style="{font};background:#eef2f7;padding:16px 0">',
        f'<table role="presentation" align="center" width="100%" cellpadding="0" cellspacing="0" '
        f'style="max-width:900px;background:#ffffff;border-radius:8px;overflow:hidden">',
        f'<tr><td style="background:{navy};padding:22px 24px;color:#ffffff">'
        f'<div style="font-size:22px;font-weight:bold">{escape(title)}</div>'
        f'<div style="font-size:13px;color:#c9d6e8;margin-top:6px">{escape(sub)}</div>'
        f'</td></tr><tr><td style="padding:8px 24px 24px">',
    ]
    for block in _blocks(report, L):
        kind = block[0]
        if kind == "h2":
            accent = block[2]
            parts.append(f'<h2 style="margin:26px 0 10px;padding:6px 12px;font-size:18px;'
                         f'color:{accent};border-left:5px solid {accent};background:{cream}">'
                         f"{escape(block[1])}</h2>")
        elif kind == "h3":
            parts.append(f'<h3 style="margin:18px 0 6px;font-size:15px;color:#333">'
                         f"{escape(block[1])}</h3>")
        elif kind == "p":
            parts.append(f'<p style="font-size:12px;color:#666">{escape(_note(block[1], lang))}</p>')
        elif kind == "summary":
            paras = "".join(f'<p style="margin:6px 0">{escape(t)}</p>'
                            for t in block[1].split("\n") if t.strip())
            parts.append(f'<div style="background:#fff8e6;border-left:5px solid #b8860b;'
                         f'padding:10px 16px;font-size:14px;line-height:1.5;color:#222">{paras}</div>')
        elif kind == "alert":
            bg, fg, icon = ("#fdecec", red, "⚠️ ") if block[2] else ("#e6f4ec", green, "✓ ")
            parts.append(f'<div style="margin-top:16px;padding:10px 14px;border-radius:6px;'
                         f'background:{bg};color:{fg};font-weight:bold;font-size:14px">'
                         f"{icon}{escape(block[1])}</div>")
        elif kind == "kpis":
            width = int(100 / max(len(block[1]), 1))
            cells = "".join(
                f'<td width="{width}%" style="padding:6px"><div style="background:{cream};'
                f'border:1px solid #e3e3e3;border-radius:8px;padding:12px;text-align:center">'
                f'<div style="font-size:12px;color:#666">{escape(k[0])}</div>'
                f'<div style="font-size:22px;font-weight:bold;color:{navy};margin:4px 0">'
                f"{escape(k[1])}</div><div>{pill(k[2])}</div>"
                f'<div style="font-size:11px;color:#888;margin-top:4px">{escape(k[3])}</div>'
                f"</div></td>"
                for k in block[1])
            parts.append(f'<table role="presentation" width="100%" style="margin-top:12px">'
                         f"<tr>{cells}</tr></table>")
        elif kind == "table":
            _, headers, rows, signed = block
            th = "".join(f'<th style="padding:6px 8px;text-align:left;font-size:12px;'
                         f'color:#ffffff;background:{accent}">{escape(h)}</th>' for h in headers)
            body = "".join(
                f'<tr style="background:{"#ffffff" if n % 2 == 0 else "#f6f8fb"}">' + "".join(
                    f'<td style="padding:5px 8px;font-size:13px;border-bottom:1px solid #eeeeee">'
                    f'{pill(c, r[0] == L["position"]) if i in signed else escape(str(c))}</td>'
                    for i, c in enumerate(r)) + "</tr>"
                for n, r in enumerate(rows))
            parts.append(f'<table width="100%" cellpadding="0" cellspacing="0" '
                         f'style="border-collapse:collapse">{"<tr>" + th + "</tr>"}{body}</table>')
    notes = report["warnings"] + report["errors"]
    if notes:
        parts.append('<ul style="font-size:11px;color:#888;margin-top:24px">'
                     + "".join(f"<li>{escape(_note(n, lang))}</li>" for n in notes) + "</ul>")
    parts.append("</td></tr></table></div>")
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Email
# --------------------------------------------------------------------------- #

RESEND_ENDPOINT = "https://api.resend.com/emails"
DEFAULT_SENDER = "SEO Raporu <onboarding@resend.dev>"


def send_email_resend(api_key: str, to: list, subject: str, html: str,
                      sender: str = DEFAULT_SENDER) -> dict:
    """Send the HTML report through the Resend HTTPS API.

    The endpoint is fixed (not user supplied), so no URL validation applies.
    Returns {"sent": bool, "id": ..., "error": ...}; the key is never echoed.
    """
    import requests

    try:
        response = requests.post(
            RESEND_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": sender, "to": to, "subject": subject, "html": html},
            timeout=30,
        )
    except requests.RequestException as e:
        return {"sent": False, "id": None, "error": f"Resend request failed: {type(e).__name__}"}
    if response.status_code >= 300:
        try:
            message = response.json().get("message", "")
        except ValueError:
            message = response.text[:200]
        return {"sent": False, "id": None,
                "error": f"Resend HTTP {response.status_code}: {message}"}
    return {"sent": True, "id": response.json().get("id"), "error": None}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Weekly/monthly GSC comparison with brand split and GA4 AI traffic")
    parser.add_argument("--property", "-p", help="GSC property (default from config)")
    parser.add_argument("--brand-regex", "-b", default=os.environ.get("SEO_BRAND_REGEX"),
                        help="Regex for brand queries, case-insensitive (env SEO_BRAND_REGEX)")
    parser.add_argument("--config", "-c",
                        help="JSON file with brand_regex and page_groups (see docstring)")
    parser.add_argument("--period", choices=["weekly", "monthly"], default="weekly")
    parser.add_argument("--lang", choices=sorted(LABELS), default="en",
                        help="Language of Markdown/HTML labels (default: en)")
    parser.add_argument("--ga4-property", help="GA4 property ID for AI traffic (default from config)")
    parser.add_argument("--as-of", help="Pretend today is YYYY-MM-DD (for backfills)")
    parser.add_argument("--format", choices=["json", "markdown", "html"], default="markdown")
    parser.add_argument("--json", "-j", action="store_true", help="Shortcut for --format json")
    parser.add_argument("--output", "-o", help="Write to this file instead of stdout")
    parser.add_argument("--summary-file",
                        help="Text file with an executive summary shown at the top")
    parser.add_argument("--email-to", default=os.environ.get("REPORT_EMAIL_TO"),
                        help="Comma-separated recipients; sends the HTML report via Resend "
                             "(needs RESEND_API_KEY; env REPORT_EMAIL_TO)")
    parser.add_argument("--alert-threshold", type=float,
                        help="Alert when non-brand clicks fall by this %% or more (default 10)")
    args = parser.parse_args()

    from google_auth import load_config
    config = load_config()
    prop = args.property or config.get("default_property")
    ga4 = args.ga4_property or config.get("ga4_property_id")
    fmt = "json" if args.json else args.format

    def fail(msg):
        print(json.dumps({"error": msg}) if fmt == "json" else f"Error: {msg}", file=sys.stderr)
        sys.exit(1)

    try:
        report_config = load_report_config(args.config)
    except (OSError, ValueError, re.error) as e:
        fail(f"Invalid --config: {e}")
    brand_regex = args.brand_regex or report_config.get("brand_regex")
    prop = prop or report_config.get("property")
    if not prop:
        fail("No property given. Use --property or set GSC_PROPERTY.")
    try:
        compile_brand_regex(brand_regex or "")
    except (ValueError, re.error) as e:
        fail(f"Invalid --brand-regex: {e}")
    try:
        today = date.fromisoformat(args.as_of) if args.as_of else None
    except ValueError:
        fail("--as-of must be YYYY-MM-DD")

    periods = compute_periods(args.period, today)
    summary = None
    if args.summary_file:
        try:
            with open(args.summary_file, encoding="utf-8") as fh:
                summary = fh.read().strip() or None
        except OSError as e:
            fail(f"Cannot read --summary-file: {e}")
    threshold = args.alert_threshold
    if threshold is None:
        threshold = float(report_config.get("alert_threshold_pct", 10))

    gsc = fetch_gsc(prop, brand_regex, periods, report_config.get("page_groups"))
    ai = fetch_ga4_ai(ga4, periods) if ga4 else None
    organic = fetch_ga4_organic(ga4, periods) if ga4 else None
    report = build_report(prop, brand_regex, periods, gsc, ai,
                          report_config.get("exclude_query_regex"), organic, threshold, summary)
    report["subject"] = build_subject(report, args.lang)

    if args.email_to:
        api_key = os.environ.get("RESEND_API_KEY", "").strip()
        recipients = [a.strip() for a in args.email_to.split(",") if a.strip()]
        if not api_key:
            report["email"] = {"sent": False, "error": "RESEND_API_KEY is not set."}
        else:
            report["email"] = send_email_resend(
                api_key, recipients, report["subject"], render_html(report, args.lang),
                os.environ.get("REPORT_EMAIL_FROM", DEFAULT_SENDER))
        report["email"]["to"] = recipients

    if fmt == "json":
        text = json.dumps(report, indent=2, ensure_ascii=False)
    elif fmt == "html":
        text = render_html(report, args.lang)
    else:
        text = render_markdown(report, args.lang)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(json.dumps({"output": args.output, "subject": report["subject"],
                          "email": report.get("email"),
                          "alert": report["alert"]["triggered"], "errors": report["errors"]},
                         ensure_ascii=False))
    else:
        print(text)
    if report["errors"] and not gsc["current"]["rows"]:
        sys.exit(1)
    if report.get("email") and not report["email"]["sent"]:
        print(f"Email not sent: {report['email']['error']}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
