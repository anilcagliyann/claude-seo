#!/usr/bin/env python3
"""
Weekly / monthly Search Console comparison report with a brand split.

Compares the last complete period against the one before it:

- weekly:  last complete Monday-Sunday week vs the Monday-Sunday week before it
- monthly: last complete calendar month vs the calendar month before it

For each segment (brand, non-brand) it reports clicks, impressions, CTR and
position deltas, the 20 queries and 20 pages that lost the most clicks and the
20 of each that gained the most, and the queries ranking 4-15 with the most
impressions. Brand queries are those matching --brand-regex (case-insensitive).

An optional --config JSON file holds the brand regex and page groups, whose
clicks are compared per segment:

    {"brand_regex": "acme|acmee", "exclude_query_regex": "spam|casino",
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
    return {
        "kind": kind,
        "current": {"start": cur_start.isoformat(), "end": cur_end.isoformat()},
        "previous": {"start": prev_start.isoformat(), "end": prev_end.isoformat()},
        "fresh_data": (today - cur_end).days < GSC_LAG_DAYS,
    }


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
    """Build a metric-by-metric comparison of two totals blocks."""
    out = {}
    for metric in ("clicks", "impressions", "ctr", "position"):
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
    for key in ("current", "previous"):
        rng = periods[key]
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


def fetch_ga4_ai(property_id: str, periods: dict) -> dict:
    """Fetch AI-assistant sessions by source for both periods from GA4."""
    result = {"available": False, "error": None, "note": AI_BRAND_NOTE}
    try:
        from google.analytics.data_v1beta.types import (
            DateRange, Dimension, Filter, FilterExpression, FilterExpressionList,
            Metric, RunReportRequest,
        )
        from ga4_report import _build_ga4_client, _resolve_property
    except (ImportError, SystemExit):
        result["error"] = "google-analytics-data is not installed."
        return result

    client = _build_ga4_client()
    if not client:
        result["error"] = "Could not build GA4 client. Check credentials and property access."
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
    try:
        response = client.run_report(RunReportRequest(
            property=_resolve_property(property_id),
            dimensions=[Dimension(name="sessionSource")],
            metrics=[Metric(name="sessions"), Metric(name="totalUsers"),
                     Metric(name="engagedSessions"), Metric(name="keyEvents")],
            date_ranges=[
                DateRange(start_date=periods["current"]["start"],
                          end_date=periods["current"]["end"], name="current"),
                DateRange(start_date=periods["previous"]["start"],
                          end_date=periods["previous"]["end"], name="previous"),
            ],
            dimension_filter=ai_filter,
            limit=1000,
        ))
    except Exception as e:
        result["error"] = f"GA4 API error: {e}"
        return result

    metrics = ("sessions", "users", "engaged_sessions", "key_events")
    totals = {k: dict.fromkeys(metrics, 0) for k in ("current", "previous")}
    sources: dict = {}
    for row in response.rows:
        # With two date ranges GA4 appends a dateRange dimension.
        source = row.dimension_values[0].value
        range_name = row.dimension_values[1].value
        values = [float(v.value or 0) for v in row.metric_values]
        bucket = sources.setdefault(source, {k: dict.fromkeys(metrics, 0) for k in totals})
        for name, value in zip(metrics, values):
            bucket[range_name][name] += value
            totals[range_name][name] += value
    result["available"] = True
    result["totals"] = compare_totals(
        {"clicks": totals["current"]["sessions"]}, {"clicks": totals["previous"]["sessions"]}
    )["clicks"]
    result["detail"] = totals
    result["sources"] = sorted(
        ({"source": s, "current": v["current"]["sessions"], "previous": v["previous"]["sessions"],
          "change": v["current"]["sessions"] - v["previous"]["sessions"]}
         for s, v in sources.items()),
        key=lambda r: -r["current"],
    )
    return result


def build_report(property_url: str, brand_regex: str, periods: dict,
                 gsc: dict, ai: Optional[dict], exclude_regex: Optional[str] = None) -> dict:
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
        "current": "Current", "previous": "Previous", "to": "to",
        "nonbrand": "Non-brand", "brand": "Brand",
        "metric": "Metric", "change": "Change",
        "clicks": "Clicks", "impressions": "Impressions", "ctr": "CTR %", "position": "Position",
        "decliners": "Top declining queries", "risers": "Top rising queries",
        "page_decliners": "Top declining pages", "page_risers": "Top rising pages",
        "opportunities": "Opportunities: position 4-15, most impressions",
        "query": "Query", "page": "Page", "now": "Now", "before": "Before",
        "pos_now": "Pos. now", "pos_before": "Pos. before",
        "groups": "Page groups (clicks)", "group": "Group",
        "ai": "AI performance (GA4)", "ai_sessions": "AI sessions", "source": "Source",
        "na": "Not available",
    },
    "tr": {
        "lang": "tr", "title": "SEO {kind} raporu", "weekly": "haftalık", "monthly": "aylık",
        "current": "Bu dönem", "previous": "Önceki dönem", "to": "-",
        "nonbrand": "Non-brand", "brand": "Brand",
        "metric": "Metrik", "change": "Değişim",
        "clicks": "Tıklama", "impressions": "Gösterim", "ctr": "TO %", "position": "Pozisyon",
        "decliners": "En çok düşen kelimeler", "risers": "En çok yükselen kelimeler",
        "page_decliners": "En çok düşen sayfalar", "page_risers": "En çok yükselen sayfalar",
        "opportunities": "Fırsatlar: 4-15. sıradaki en çok gösterim alan kelimeler",
        "query": "Kelime", "page": "Sayfa", "now": "Şimdi", "before": "Önce",
        "pos_now": "Poz. şimdi", "pos_before": "Poz. önce",
        "groups": "Sayfa grupları (tıklama)", "group": "Grup",
        "ai": "AI performansı (GA4)", "ai_sessions": "AI oturumları", "source": "Kaynak",
        "na": "Veri yok",
    },
}
SEGMENTS = ("nonbrand", "brand")
NOTES_TR = {
    AI_BRAND_NOTE: "GA4 AI yönlendirmelerinde arama kelimesi tutmadığı için AI trafiği tek "
                   "toplam olarak verilir; brand / non-brand ayrımı yapılamaz.",
    ANON_NOTE: "Kelime satırları Google'ın gizlediği (anonim) sorguları içermez; düşen/yükselen "
               "listeleri yalnızca görünen kelimeleri kapsar. Segment toplamları filtreli "
               "toplam sorgularından gelir.",
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
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.2f}"
    return f"{int(value):,}"


def _short_url(url: str) -> str:
    return re.sub(r"^https?://[^/]+", "", url) or "/"


def _sections(report: dict, L: dict) -> list:
    """Describe the report as (level, title, headers, rows, signed_cols) blocks.

    signed_cols lists column indexes holding a signed change, so renderers can
    colour them; a negative index marks a column where lower is better.
    """
    out = []
    for segment in SEGMENTS:
        seg = report["segments"][segment]
        out.append((2, L[segment], None, None, ()))
        out.append((3, "", [L["metric"], L["current"], L["previous"], L["change"], "%"], [
            [L[m], _fmt(t["current"]), _fmt(t["previous"]), _fmt(t["change"]),
             _fmt(t["change_pct"], True)]
            for m, t in seg["totals"].items()
        ], (3, 4)))
        for key in ("decliners", "risers"):
            out.append((3, f"{L[key]} ({len(seg[key])})",
                        [L["query"], L["now"], L["before"], L["change"], L["pos_now"],
                         L["pos_before"]],
                        [[m["query"], _fmt(m["clicks_current"]), _fmt(m["clicks_previous"]),
                          f'{m["clicks_change"]:+d}', _fmt(m["position_current"]),
                          _fmt(m["position_previous"])] for m in seg[key]], (3,)))
        for key in ("decliners", "risers"):
            rows = seg.get("pages", {}).get(key, [])
            out.append((3, f"{L['page_' + key]} ({len(rows)})",
                        [L["page"], L["now"], L["before"], L["change"], L["pos_now"],
                         L["pos_before"]],
                        [[_short_url(m["page"]), _fmt(m["clicks_current"]),
                          _fmt(m["clicks_previous"]), f'{m["clicks_change"]:+d}',
                          _fmt(m["position_current"]), _fmt(m["position_previous"])]
                         for m in rows], (3,)))
        opps = seg.get("opportunities", [])
        if opps:
            out.append((3, f"{L['opportunities']} ({len(opps)})",
                        [L["query"], L["impressions"], L["clicks"], L["ctr"], L["position"]],
                        [[o["query"], _fmt(o["impressions"]), _fmt(o["clicks"]),
                          _fmt(o["ctr"]), _fmt(o["position"])] for o in opps], ()))
    for title, labels in report.get("page_groups", {}).items():
        out.append((2, f"{L['groups']}: {title}", None, None, ()))
        out.append((3, "", [L["group"]] + [f"{L[s]} {h}" for s in SEGMENTS
                                           for h in (L["now"], L["before"], "%")], [
            [label] + [v for s in SEGMENTS for v in (
                _fmt(c[s]["clicks"]["current"]), _fmt(c[s]["clicks"]["previous"]),
                _fmt(c[s]["clicks"]["change_pct"], True))]
            for label, c in labels.items()
        ], (3, 6)))
    ai = report["ai_performance"]
    out.append((2, L["ai"], None, None, ()))
    if ai.get("available"):
        t = ai["totals"]
        out.append((0, f'{L["ai_sessions"]}: {_fmt(t["current"])} / {_fmt(t["previous"])} '
                       f'({_fmt(t["change_pct"], True)})', None, None, ()))
        out.append((3, "", [L["source"], L["current"], L["previous"], L["change"]],
                    [[x["source"], _fmt(x["current"]), _fmt(x["previous"]), _fmt(x["change"])]
                     for x in ai["sources"][:15]], (3,)))
    else:
        out.append((0, f'{L["na"]}: {ai.get("error")}', None, None, ()))
    out.append((0, _note(ai["note"], L["lang"]), None, None, ()))
    return out


def _header(report: dict, L: dict) -> tuple:
    p = report["periods"]
    title = f'{L["title"].format(kind=L[p["kind"]])}: {report["property"]}'
    sub = (f'{L["current"]}: {p["current"]["start"]} {L["to"]} {p["current"]["end"]} | '
           f'{L["previous"]}: {p["previous"]["start"]} {L["to"]} {p["previous"]["end"]}')
    return title, sub


def render_markdown(report: dict, lang: str = "en") -> str:
    """Render the report as Markdown (fits a routine summary or email body)."""
    L = LABELS[lang]
    title, sub = _header(report, L)
    lines = [f"# {title}", sub, ""]
    for level, heading, headers, rows, _ in _sections(report, L):
        if level == 0:
            lines += [heading, ""]
            continue
        if heading:
            lines += [f'{"#" * level} {heading}', ""]
        if headers:
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("|" + "---|" * len(headers))
            for r in rows:
                lines.append("| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |")
            lines.append("")
    lines += [f"- {_note(w, lang)}" for w in report["warnings"] + report["errors"]]
    return "\n".join(lines)


def render_html(report: dict, lang: str = "en") -> str:
    """Render the report as email-safe HTML (inline styles, tables only)."""
    L = LABELS[lang]
    navy, green, red = "#1e3a5f", "#2d6a4f", "#c53030"
    td = "padding:4px 8px;border-bottom:1px solid #e5e5e5;font-size:13px"

    def cell(value, signed, invert=False):
        text = escape(str(value))
        if not signed or text in ("-", "", "0"):
            return text
        # A falling position is an improvement, so its colours flip.
        colour = red if text.startswith("-") != invert else green
        return f'<span style="color:{colour}">{text}</span>'

    title, sub = _header(report, L)
    parts = ['<div style="font-family:Arial,sans-serif;color:#222;max-width:860px">',
             f'<h1 style="color:{navy};font-size:20px">{escape(title)}</h1>',
             f"<p>{escape(sub)}</p>"]
    for level, heading, headers, rows, signed in _sections(report, L):
        if level == 0:
            parts.append(f'<p style="font-size:13px">{escape(heading)}</p>')
            continue
        if heading:
            size = 17 if level == 2 else 15
            parts.append(f'<h{level} style="color:{navy};font-size:{size}px">'
                         f"{escape(heading)}</h{level}>")
        if headers:
            head = "".join(f'<th style="{td};text-align:left;color:{navy}">{escape(h)}</th>'
                           for h in headers)
            body = "".join(
                "<tr>" + "".join(
                    f'<td style="{td}">{cell(c, i in signed, r[0] == L["position"])}</td>'
                    for i, c in enumerate(r)) + "</tr>"
                for r in rows)
            parts.append(f'<table style="border-collapse:collapse;width:100%">'
                         f"<tr>{head}</tr>{body}</table>")
    notes = report["warnings"] + report["errors"]
    if notes:
        parts.append('<ul style="font-size:12px;color:#666">'
                     + "".join(f"<li>{escape(_note(n, lang))}</li>" for n in notes) + "</ul>")
    parts.append("</div>")
    return "\n".join(parts)


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
    gsc = fetch_gsc(prop, brand_regex, periods, report_config.get("page_groups"))
    ai = fetch_ga4_ai(ga4, periods) if ga4 else None
    report = build_report(prop, brand_regex, periods, gsc, ai,
                          report_config.get("exclude_query_regex"))

    if fmt == "json":
        text = json.dumps(report, indent=2, ensure_ascii=False)
    elif fmt == "html":
        text = render_html(report, args.lang)
    else:
        text = render_markdown(report, args.lang)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(json.dumps({"output": args.output, "errors": report["errors"]}))
    else:
        print(text)
    if report["errors"] and not gsc["current"]["rows"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
