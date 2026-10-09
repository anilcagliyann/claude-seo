#!/usr/bin/env python3
"""
Weekly / monthly Search Console comparison report with a brand split.

Compares the last complete period against the one before it:

- weekly:  last complete Monday-Sunday week vs the Monday-Sunday week before it
- monthly: last complete calendar month vs the calendar month before it

For each segment (brand, non-brand) it reports clicks, impressions, CTR and
position deltas, the 20 queries that lost the most clicks and the 20 that gained
the most. Brand queries are those matching --brand-regex (case-insensitive).

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
AI_SOURCE_REGEX = (
    r"chatgpt\.com|chat\.openai\.com|openai\.com|perplexity\.ai|gemini\.google\.com|"
    r"bard\.google\.com|copilot\.microsoft\.com|claude\.ai|deepseek\.com|grok\.com|"
    r"you\.com|meta\.ai|mistral\.ai"
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


def split_rows(rows: list, brand_re: re.Pattern) -> dict:
    """Split query rows into {'brand': {query: row}, 'nonbrand': {query: row}}."""
    out = {"brand": {}, "nonbrand": {}}
    for row in rows:
        query = row.get("query") or (row.get("keys") or [""])[0]
        if not query:
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


def compute_movers(cur_rows: dict, prev_rows: dict, top_n: int = TOP_N) -> dict:
    """Rank queries by click change between two periods.

    A query missing from one period counts as zero clicks there. Ties break on
    the impression change so the list stays stable.
    """
    movers = []
    for query in set(cur_rows) | set(prev_rows):
        c = cur_rows.get(query, {})
        p = prev_rows.get(query, {})
        c_clicks, p_clicks = c.get("clicks", 0), p.get("clicks", 0)
        c_impr, p_impr = c.get("impressions", 0), p.get("impressions", 0)
        c_pos, p_pos = c.get("position"), p.get("position")
        movers.append({
            "query": query,
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
        key=lambda m: (m["clicks_change"], m["impressions_change"], m["query"]),
    )[:top_n]
    risers = sorted(
        (m for m in movers if m["clicks_change"] > 0),
        key=lambda m: (-m["clicks_change"], -m["impressions_change"], m["query"]),
    )[:top_n]
    return {"decliners": decliners, "risers": risers}


# --------------------------------------------------------------------------- #
# Data fetching
# --------------------------------------------------------------------------- #

def _gsc_segment_filter(brand_regex: str, segment: str) -> list:
    operator = "includingRegex" if segment == "brand" else "excludingRegex"
    return [{"dimension": "query", "operator": operator, "expression": f"(?i){brand_regex}"}]


def fetch_gsc(property_url: str, brand_regex: str, periods: dict) -> dict:
    """Fetch per-query rows and brand/non-brand totals for both periods."""
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
                 gsc: dict, ai: Optional[dict]) -> dict:
    """Assemble the final report structure from fetched data."""
    brand_re = compile_brand_regex(brand_regex)
    cur = split_rows(gsc["current"]["rows"], brand_re)
    prev = split_rows(gsc["previous"]["rows"], brand_re)
    segments = {}
    for segment in ("brand", "nonbrand"):
        segments[segment] = {
            "totals": compare_totals(gsc["current"]["totals"].get(segment, {}),
                                     gsc["previous"]["totals"].get(segment, {})),
            **compute_movers(cur[segment], prev[segment]),
        }
    warnings = list(gsc.get("warnings", []))
    if periods["fresh_data"]:
        warnings.append(
            "The current period ended less than 3 days ago; recent Search Console "
            "data is preliminary. Schedule the report for Wednesday or later."
        )
    warnings.append(
        "Query rows exclude anonymized queries, so movers cover named queries only; "
        "segment totals come from filtered aggregate queries."
    )
    return {
        "property": property_url,
        "brand_regex": brand_regex,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "periods": periods,
        "segments": segments,
        "ai_performance": ai or {"available": False, "error": "No --ga4-property given.",
                                 "note": AI_BRAND_NOTE},
        "warnings": warnings,
        "errors": gsc.get("errors", []),
    }


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

SEGMENT_LABELS = {"nonbrand": "Non-brand", "brand": "Brand"}


def _fmt(value, pct=False) -> str:
    if value is None:
        return "-"
    if pct:
        return f"{value:+.1f}%"
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.2f}"
    return f"{int(value):,}"


def render_markdown(report: dict) -> str:
    """Render the report as Markdown (fits a routine summary or email body)."""
    p = report["periods"]
    lines = [
        f"# SEO {p['kind']} report: {report['property']}",
        f"Current: {p['current']['start']} to {p['current']['end']} | "
        f"Previous: {p['previous']['start']} to {p['previous']['end']}",
        "",
    ]
    for segment in ("nonbrand", "brand"):
        seg = report["segments"][segment]
        lines += [f"## {SEGMENT_LABELS[segment]}", "",
                  "| Metric | Current | Previous | Change | % |", "|---|---|---|---|---|"]
        for metric, t in seg["totals"].items():
            lines.append(f"| {metric} | {_fmt(t['current'])} | {_fmt(t['previous'])} | "
                         f"{_fmt(t['change'])} | {_fmt(t['change_pct'], True)} |")
        for key, title in (("decliners", "Top decliners"), ("risers", "Top risers")):
            lines += ["", f"### {title} ({len(seg[key])})", "",
                      "| Query | Clicks now | Clicks before | Change | Position now | Position before |",
                      "|---|---|---|---|---|---|"]
            for m in seg[key]:
                lines.append(f"| {m['query']} | {_fmt(m['clicks_current'])} | "
                             f"{_fmt(m['clicks_previous'])} | {m['clicks_change']:+d} | "
                             f"{_fmt(m['position_current'])} | {_fmt(m['position_previous'])} |")
        lines.append("")
    ai = report["ai_performance"]
    lines += ["## AI performance (GA4)", ""]
    if ai.get("available"):
        t = ai["totals"]
        lines.append(f"AI sessions: {_fmt(t['current'])} vs {_fmt(t['previous'])} "
                     f"({_fmt(t['change_pct'], True)})")
        lines += ["", "| Source | Current | Previous | Change |", "|---|---|---|---|"]
        for s in ai["sources"][:15]:
            lines.append(f"| {s['source']} | {_fmt(s['current'])} | {_fmt(s['previous'])} | "
                         f"{_fmt(s['change'])} |")
    else:
        lines.append(f"Not available: {ai.get('error')}")
    lines += ["", f"_{ai['note']}_", ""]
    for w in report["warnings"] + report["errors"]:
        lines.append(f"- {w}")
    return "\n".join(lines)


def render_html(report: dict) -> str:
    """Render the report as email-safe HTML (inline styles, tables only)."""
    navy, green, red = "#1e3a5f", "#2d6a4f", "#c53030"
    td = "padding:4px 8px;border-bottom:1px solid #e5e5e5;font-size:13px"

    def color(v):
        return green if (v or 0) > 0 else red if (v or 0) < 0 else "#333"

    def table(headers, rows):
        head = "".join(f'<th style="{td};text-align:left;color:{navy}">{escape(h)}</th>'
                       for h in headers)
        body = "".join("<tr>" + "".join(f'<td style="{td}">{c}</td>' for c in r) + "</tr>"
                       for r in rows)
        return f'<table style="border-collapse:collapse;width:100%">{head}{body}</table>'

    p = report["periods"]
    parts = [
        f'<div style="font-family:Arial,sans-serif;color:#222;max-width:760px">',
        f'<h1 style="color:{navy};font-size:20px">SEO {escape(p["kind"])} report: '
        f'{escape(report["property"])}</h1>',
        f'<p>Current: {p["current"]["start"]} to {p["current"]["end"]}<br>'
        f'Previous: {p["previous"]["start"]} to {p["previous"]["end"]}</p>',
    ]
    for segment in ("nonbrand", "brand"):
        seg = report["segments"][segment]
        parts.append(f'<h2 style="color:{navy};font-size:17px">{SEGMENT_LABELS[segment]}</h2>')
        parts.append(table(["Metric", "Current", "Previous", "Change", "%"], [
            [m, _fmt(t["current"]), _fmt(t["previous"]),
             # Lower position is better, so invert its colour.
             f'<span style="color:{color(-t["change"] if m == "position" else t["change"])}">'
             f'{_fmt(t["change"])}</span>', _fmt(t["change_pct"], True)]
            for m, t in seg["totals"].items()
        ]))
        for key, title in (("decliners", "Top decliners"), ("risers", "Top risers")):
            parts.append(f'<h3 style="font-size:15px">{title} ({len(seg[key])})</h3>')
            parts.append(table(
                ["Query", "Clicks now", "Before", "Change", "Pos. now", "Pos. before"],
                [[escape(m["query"]), _fmt(m["clicks_current"]), _fmt(m["clicks_previous"]),
                  f'<span style="color:{color(m["clicks_change"])}">{m["clicks_change"]:+d}</span>',
                  _fmt(m["position_current"]), _fmt(m["position_previous"])]
                 for m in seg[key]],
            ))
    ai = report["ai_performance"]
    parts.append(f'<h2 style="color:{navy};font-size:17px">AI performance (GA4)</h2>')
    if ai.get("available"):
        t = ai["totals"]
        parts.append(f'<p>AI sessions: <b>{_fmt(t["current"])}</b> vs {_fmt(t["previous"])} '
                     f'(<span style="color:{color(t["change"])}">{_fmt(t["change_pct"], True)}'
                     f'</span>)</p>')
        parts.append(table(["Source", "Current", "Previous", "Change"], [
            [escape(s["source"]), _fmt(s["current"]), _fmt(s["previous"]), _fmt(s["change"])]
            for s in ai["sources"][:15]
        ]))
    else:
        parts.append(f'<p>Not available: {escape(str(ai.get("error")))}</p>')
    parts.append(f'<p style="font-size:12px;color:#666">{escape(ai["note"])}</p>')
    notes = report["warnings"] + report["errors"]
    if notes:
        parts.append('<ul style="font-size:12px;color:#666">'
                     + "".join(f"<li>{escape(n)}</li>" for n in notes) + "</ul>")
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
    parser.add_argument("--period", choices=["weekly", "monthly"], default="weekly")
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

    if not prop:
        fail("No property given. Use --property or set GSC_PROPERTY.")
    try:
        compile_brand_regex(args.brand_regex or "")
    except (ValueError, re.error) as e:
        fail(f"Invalid --brand-regex: {e}")
    try:
        today = date.fromisoformat(args.as_of) if args.as_of else None
    except ValueError:
        fail("--as-of must be YYYY-MM-DD")

    periods = compute_periods(args.period, today)
    gsc = fetch_gsc(prop, args.brand_regex, periods)
    ai = fetch_ga4_ai(ga4, periods) if ga4 else None
    report = build_report(prop, args.brand_regex, periods, gsc, ai)

    if fmt == "json":
        text = json.dumps(report, indent=2, ensure_ascii=False)
    elif fmt == "html":
        text = render_html(report)
    else:
        text = render_markdown(report)
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
