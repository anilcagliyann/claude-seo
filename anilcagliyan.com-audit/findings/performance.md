# Performance Findings: anilcagliyan.com (2026-10-08)

**Performance score: 58/100 (ESTIMATED, heuristic from lab/HTTP evidence; not a Lighthouse score).**

## Data provenance
- Field (CrUX): NOT available. No API key; keyless PSI returned 429 (daily quota exhausted on shared project) on repeated tries. lcp_subparts.py requires a key. No LCP/INP/CLS pass/fail can be asserted.
- Lab (measured via curl from sandbox, single run, proxy-affected): TTFB, transfer sizes, headers, resource lists. preload_check.py ran (score 75).
- Estimated: overall score, CWV risk levels.
- Pages: / ; /outbound-links-nedir/ (from post-sitemap.xml).

## Measurements (lab)
| Page | TTFB | HTML (br / raw) | DOM tags | Img | Sync JS |
|---|---|---|---|---|---|
| Home | 1.25s | 24 KB / 86 KB | 632 | 17 (all sized, none lazy) | 8 blocking |
| Post | 0.94s | 30 KB / 95 KB | 596 | 15 (10 lazy, 1 unsized) | 13 |
Note: sandbox TTFB includes proxy latency; treat as upper bound but consistently above 0.8s.

## Findings
1. HIGH - TTFB 0.94-1.25s (above 0.8s good threshold); HTML response has no Cache-Control header (no page/edge caching evident). Directly inflates LCP. Fix: full-page cache and/or CDN edge caching for HTML.
2. HIGH - Render-blocking JS in head without defer/async: jquery, jquery-migrate, 6-8 Jannah theme scripts (sliders, shortcodes, live-search, desktop, br-news, single) plus Easy TOC scripts (4) on posts. Hurts LCP and INP. Fix: defer/delay non-critical scripts, drop jquery-migrate, dequeue sliders/shortcodes where unused.
3. HIGH - 8-10 render-blocking stylesheets (Jannah base/style/widgets/helpers/fontawesome/shortcodes/single, plugin CSS). Fix: combine/minify, inline critical CSS, load rest async, subset FontAwesome.
4. MEDIUM - Post LCP image (Outbound-Links-Nedir.jpg, 1200x800, 115 KB JPEG) does have fetchpriority and width/height, good; but format is JPEG. Fix: serve WebP/AVIF (est. 30-50% saving). Homepage (first image is a 300x45 PNG logo; cards are 390x220 JPEG ~3 KB, fine) has no fetchpriority and no lazy-loading on 17 images: lazy-load below-fold cards, prioritize first card if it is LCP.
5. MEDIUM - Third-party: webfont.js loader preloaded from ajax.googleapis.com plus Google Fonts, cdnjs, Google Analytics, gravatar dns-prefetch. WebFont Loader JS adds a request chain and FOUT/CLS risk; no font-display found. Fix: self-host fonts, woff2, font-display: swap, preload main font.
6. MEDIUM - Inefficient large PNG: hemen-teklif-al.png 81 KB, no dimensions (CLS risk) on post. Convert to WebP and add width/height.
7. LOW - jquery.min.js served with no Cache-Control header; other static assets cache 7 days (max-age=604800). Raise to 1 year with versioned URLs.
8. LOW - DOM ~600 tags (well under 1,500); not a concern. Brotli enabled (good). HTTP/2 and HSTS present (good).
9. INFO - Speculation Rules prefetch present (good); no bfcache blockers (no-store/unload absent). Click-to-chat WhatsApp plugin adds JS+CSS on every page.

## Estimated CWV risk (not measured)
- LCP: Needs Improvement likely (slow TTFB + blocking CSS/JS), mobile risk of >2.5s.
- INP: Probably OK-to-borderline (jQuery theme, small DOM).
- CLS: Probably good; risks from font loader and unsized post PNG.

## Priority order
1) Page cache/CDN for HTML; 2) defer/delay JS and trim CSS; 3) WebP/AVIF + lazy-load; 4) self-host fonts; 5) re-run PSI with an API key to obtain CrUX field data and confirm.
