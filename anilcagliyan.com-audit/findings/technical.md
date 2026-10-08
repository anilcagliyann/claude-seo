# Technical + On-Page Findings: https://www.anilcagliyan.com (2026-10-08)

**Technical score: 82/100** | **On-Page score: 74/100**

Scope: 22 sampled URLs (home, 8 section/category pages, 12+ posts) for full detail. All 105 posts in post-sitemap were also checked for title, description, H1 and canonical. HTML-source analysis only. No Playwright render, no lab CWV.

## Category status
| Category | Status |
|---|---|
| Crawlability | Pass, with notes |
| Indexability | Pass, with a gap (page sitemap has only the homepage) |
| Security headers | Partial |
| URL structure / redirects | Pass |
| Mobile | Pass (viewport present; no CSS audit) |
| Rendering | Pass (server-rendered WordPress, Jannah/TieLabs theme, lang="tr") |
| Structured data | Pass (Yoast graph on every page) |
| Hreflang | N/A: single-language site, no hreflang emitted, none needed |
| IndexNow | Not implemented |

## Findings

### High
1. **No service, about or contact pages are indexable or in the sitemap.** (On-Page/Indexability)
   - Evidence: page-sitemap.xml contains only `/`. /hakkimda/, /iletisim/, /seo-danismanligi/, /seo-uzmani/ and /hizmetler/ all return 404. The site is a consultant site with no commercial landing page beyond the homepage.
   - Fix: Publish dedicated service pages (SEO consultancy, technical SEO, etc.), About and Contact. Link them from the main nav and add Person/ProfessionalService schema.
2. **Homepage and section pages are the only ranking assets for commercial terms.** The `title` is "Anıl Çağlıyan: SEO Uzmanı & Google Ürün Uzmanı" and the homepage has 741 words. Same fix as above.

### Medium
3. **Stale content.** (On-Page)
   - Evidence: post-sitemap lastmod by year is 79 in 2024, 21 in 2025 and 5 in 2026. No sampled sitemap URL has a recent lastmod pattern beyond that.
   - Fix: Refresh top posts and add publish cadence.
4. **Missing meta description on /html-lang-etiketi-nedir/.**
   - Evidence: no `meta name="description"` tag.
   - Fix: Add a 120-155 character description in Yoast.
5. **Meta descriptions over 160 characters on 10 of 105 posts, and titles over 60 characters on 5 of 105.** Likely truncated in SERPs. Trim to about 155 and 60.
6. **/tanitim/ category has no meta description** (0 length) and its title is the default "Tanıtım arşivleri - Anıl Çağlıyan". 314 words, thin archive. Add a custom title, description and intro text, or noindex it if it is low value.
7. **Image alt text gaps.** Most sampled pages have 1-6 `<img>` without alt (e.g. kurumsal-mail-imza-ornekleri 6 of 19, nosnippet-nedir 6 of 16, pagerank 4 of 14, homepage 3 of 17). Add descriptive alts.
8. **Homepage carries 95 internal links** (blog index and category pages 70-76). This is heavy but not blocking. Ensure primary service links are prominent once they exist.
9. **No IndexNow.** /indexnow.txt returns 404 and no key file was found. Bing, Yandex and Naver are not notified of changes. Fix: Yoast IndexNow or the Bing Webmaster extension (`/seo bing`), then host the key file.
10. **Weak security headers.**
    - Present: HSTS (max-age=63072000, no includeSubDomains or preload), X-Frame-Options SAMEORIGIN, X-Content-Type-Options nosniff, Referrer-Policy strict-origin-when-cross-origin, Permissions-Policy.
    - Weak or missing: CSP is only `upgrade-insecure-requests`. `cross-origin-opener-policy: unsafe-none` and `cross-origin-resource-policy: cross-origin` are permissive.
    - Fix: Add includeSubDomains (and preload, if wanted) to HSTS. Add a real CSP in report-only mode first. Set COOP to same-origin-allow-popups if feasible.
11. **Slow TTFB.** About 1.0 s for the homepage (24 KB transferred, 86 KB uncompressed HTML). No `Cache-Control` header was seen on the HTML response. Fix: Enable full-page caching (a cache plugin or server-level cache) to bring TTFB under 600 ms. This affects LCP.

### Low
12. **robots.txt has no `User-agent: *` group.** It only disallows specific bots (archive.org_bot, ia_archiver, AhrefsBot, SiteAuditBot, SemrushBot-BA/SI/SWA/CT/COUB, SplitSignalBot). The sitemap is declared and valid. This is intentional and fine, but it means no AI-crawler policy or `/wp-admin/` rule. Note that blocking AhrefsBot hides your site from Ahrefs backlink data. Consider an explicit policy for AI crawlers (see seo-technical AI Crawler Management).
13. **Search results are noindex,follow** (`/?s=seo`). Correct. Paginated archives (`/blog/page/2/`) are indexable with a self-canonical and rel=prev. Acceptable.
14. **No lazy-loading signal on homepage images** (0 `loading="lazy"`; 17 images) and no `fetchpriority` or LCP preload. Fix: Lazy-load below-the-fold images and prioritise the hero/LCP image. Also 17 CSS/JS assets on the homepage; consider minify/defer.
15. **Title and description quality.**
    - Titles are HTML-entity-encoded in source (`&amp;`, `&#039;`). This is normal.
    - Typo in a live title: "Pagerank Puanı Nasıl **Yülseltilir**?" (should be Yükseltilir). The URL slug carries the same typo (`yulseltilir`). Fix the title now. Fix the slug only with a 301.
    - Title formats are consistent ("... - Anıl Çağlıyan").
16. **/wp-json/ is public** and /wp-json/wp/v2/users returns 401 (good). /xmlrpc.php returns 403 (good).
17. **Missing standard files.** /llms.txt, /ads.txt and /.well-known/security.txt all return 404. Optional.

### Info / Passed
- Apex http/https and www-http all 301 to https://www.anilcagliyan.com/ in a single hop. No redirect chains observed. /sitemap.xml and /wp-sitemap.xml 301 to /sitemap_index.xml. /feed/ 301s to the homepage (feeds disabled).
- Real 404 status for missing URLs (soft-404 check passed).
- sitemap_index.xml is valid and declared in robots.txt. It lists post (105 URLs), page (1) and category (8) sitemaps. Discovery helper validated it (200, sitemapindex).
- All 22 sampled URLs return 200 with a self-referencing canonical and `robots: index, follow, max-image-preview:large`. Across all 105 posts: 0 canonical mismatches, 0 duplicate titles, 0 duplicate descriptions, and exactly 1 H1 each.
- Internal links on the homepage (30 unique sampled) all return 200.
- Viewport meta present, html lang="tr", og:locale tr_TR, Open Graph tags and JSON-LD on every sampled page.
- Clean, flat, lowercase, hyphenated slugs with trailing slashes. Slugs are ASCII-transliterated Turkish.
- HTTP/2, HSTS and HTTPS everywhere.

## Score rationale
- **Technical 82:** solid redirects, canonicals, sitemaps and schema. Deductions for the missing IndexNow, weak CSP/COOP, no cache/TTFB, and sitemap and page-structure gaps.
- **On-Page 74:** titles, descriptions and H1s are clean sitewide. Deductions for the absence of service, about and contact pages, long descriptions, image alt gaps, thin archives, a title typo and content staleness.
