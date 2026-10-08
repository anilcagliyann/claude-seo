# Sitemap Audit: https://www.anilcagliyan.com (2026-10-08)

## Counts
- Index /sitemap_index.xml: 3 child sitemaps (post, page, category), declared in robots.txt, 200, valid XML (Yoast)
- post-sitemap.xml: 105 URLs (56 KB, 295 image entries)
- page-sitemap.xml: 1 URL (homepage only)
- category-sitemap.xml: 8 URLs
- Total: 114 URLs, far under 50k/50MB limits

## Passed
- XML valid, all 114 URLs return 200 with no redirects
- No noindex (meta or X-Robots-Tag) on any URL
- Canonical matches the sitemap URL on all 114
- No priority/changefreq tags (good)
- No tag/author sitemaps (no thin archives listed)

## Findings
1. MEDIUM - lastmod quality: 79 of 105 post URLs share lastmod 2024-12-15, indicating a bulk update/migration rather than real edits. Google will discount lastmod. Fix: only update on significant content changes.
2. LOW - 4 posts and several categories/homepage share 2026-07-04 (bulk touch, same cause).
3. MEDIUM - Thin category pages: /case-study/ (203 words), /tanitim/ (234), /e-ticaret/ (291), /wordpress/ (325). Others (/seo/, /sosyal-medya/, /dijital-pazarlama/) ~480 words, mostly listing boilerplate. Add unique intro copy, or noindex and drop from sitemap those with few posts. Word counts are rough (HTML-stripped, nav/footer removed).
4. MEDIUM - /blog/ is a category-sitemap entry, not a category (a posts/blog listing page), and homepage is the only entry in page-sitemap. Verify /blog/ is intended as indexable; ok if so.
5. MEDIUM - Missing important pages: no About, Contact, or Services pages exist in the sitemap (/hakkimda, /iletisim, /hizmetler, /about, /contact all 404). Page-sitemap has only the homepage. Weak E-E-A-T and conversion paths; create and add these pages (or confirm they exist under other slugs and are not noindexed).
6. LOW - Index lastmod values are all from 2026-07-04; no activity since (about 3 months). Content freshness signal is stale.
7. LOW - Sitemap uses xml-stylesheet with protocol-relative URL (//www...); cosmetic only.
8. INFO - robots.txt blocks several SEO crawlers (Ahrefs, Semrush, etc.), which limits third-party audits. Not an indexing issue. Sitemap declared correctly.
9. INFO - Homepage paginated archive links (/page/2/ to /page/11/) are not in the sitemap, which is correct.
