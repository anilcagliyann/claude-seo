# GEO / AI Search Readiness: www.anilcagliyan.com

Audit date: 2026-10-08. Pages sampled: homepage, `/301-yonlendirmesi-ne-zaman-kaldirilmalidir/`, `/john-mueller-kimdir/`, `/crawl-delay-nedir/`, `/ornek-robots-txt-kodlari/` (plus `/fiber-lazer-kesim-ve-metal-isleme-teknolojileri/` for a spot check). Fetched with `render_page.py --mode auto`. Every page was served as server-side HTML (`is_spa: false`, raw mode). Site runs WordPress with the Jannah theme and Yoast 28.6, and has 105 posts in `post-sitemap.xml`.

## AI Search Readiness Score: 55 / 100

| Dimension | Weight | Score | Weighted |
|---|---|---|---|
| Citability | 25% | 55 | 13.8 |
| Structural Readability | 20% | 60 | 12.0 |
| Multi-Modal Content | 15% | 45 | 6.8 |
| Authority & Brand Signals | 20% | 30 | 6.0 |
| Technical Accessibility | 20% | 80 | 16.0 |
| **Total** | | | **54.6 -> 55** |

Platform estimates are heuristic and were not measured. No DataForSEO, Profound or SE Ranking data was available.

| Platform | Score | Main limiter |
|---|---|---|
| Google AI Overviews / AI Mode | 55 | Pages are indexable and some answers are direct, but posts are thin (200-600 words) and E-E-A-T entity signals are weak |
| ChatGPT Search | 45 | The Person entity is weak, there are no Wikipedia/Wikidata or LinkedIn links, and the brand has little off-site corroboration |
| Perplexity | 50 | Passages are short and to the point, but few sources are cited and dates are stale |
| Bing Copilot | 50 | Same entity gaps. No IndexNow detected (not verified) |

## AI Crawler Access

robots.txt has no `User-agent: *` group and no AI-specific rules. It only blocks archive.org_bot, ia_archiver, AhrefsBot and several SemrushBot variants. Under RFC 9309, any crawler without a matching group is allowed.

I also sent requests with each crawler's user-agent string to check the server/WAF layer (homepage):

| Crawler | Governs | robots.txt | HTTP (UA test) | Status |
|---|---|---|---|---|
| OAI-SearchBot | ChatGPT Search citations | Allowed (no rule) | 200 | Allowed |
| GPTBot | OpenAI model training only | Allowed | 200 | Allowed (training) |
| Claude-SearchBot | Claude search citations | Allowed | 200 | Allowed |
| ClaudeBot | Anthropic training only | Allowed | 200 | Allowed (training) |
| PerplexityBot | Perplexity index | Allowed | 200 | Allowed |
| Googlebot | Google Search + AI Overviews | Allowed | 200 | Allowed |
| Google-Extended | Gemini/Vertex training and grounding (not Search/AIO) | Allowed | 200 | Allowed |
| Applebot-Extended | Apple Intelligence training only | Allowed | not tested | Allowed |
| CCBot | Common Crawl (training corpora) | Allowed in robots.txt | **403** | Blocked at server/WAF |
| ia_archiver / archive.org_bot | Wayback Machine | Disallow: / | n/a | Blocked |

## Findings (severity-ranked)

### HIGH

1. **No About/"Hakkımda" page, and the Person entity is weak.** `page-sitemap.xml` lists only the homepage. `/hakkimda/`, `/about/` and `/iletisim/` return 404. The homepage Yoast `Person`/`Organization` node has `sameAs: ["https://www.anilcagliyan.com/"]` (self only). It has no `jobTitle`, `knowsAbout`, `alumniOf` or `worksFor`, and no LinkedIn, YouTube or Google Product Experts profile URL. Post pages carry a different sameAs set (Facebook, Twitter, Pinterest, Instagram, WhatsApp). The bio facts that matter most ("Google Diamond Product Expert", "9 years in the industry", "ALB Yatırım") appear only in a sidebar widget. AI engines cannot reliably tie "Anıl Çağlıyan" to "Turkish SEO consultant". Effort: 2-4 h.
2. **Off-topic sponsored posts with followed links.** One example is `/fiber-lazer-kesim-ve-metal-isleme-teknolojileri/` (published 2026-07-04), which has a plain followed link to vionmachine.com. Another, "Yeni İmplant Tedavisinde Modern Yaklaşımlar", appears in the homepage ticker. The "Tanıtım" category has 2 posts. These dilute the site's topical identity and carry link-scheme/site-reputation risk. Fix: add `rel="sponsored"`, remove them from the homepage ticker, or noindex them. Effort: 30 min.
3. **Unlicensed-theme notice is visible to crawlers on every page.** The text "Jannah Theme License is not validated, Go to the theme options page..." comes first in the homepage's visible text, followed by a link to tielabs.com. It pollutes extracted passages and is a weak trust signal. Effort: 15 min (license the theme or hide the bar).

### MEDIUM

4. **Thin, aging posts.** Sampled posts have 212-587 words of main text. All four show `dateModified 2024-12-15` with times within minutes of each other, which suggests a bulk re-save rather than real updates. Some content is stale. For example, the John Mueller post says he "replaced Matt Cutts" and still uses "Twitter". The robots.txt examples post does not mention AI crawlers at all, a clear GEO content gap for an SEO consultant. Effort: 1-2 h per post.
5. **Few cited sources.** Across the four posts, only one external citation was found (Google robots.txt docs). Claims attributed to John Mueller rely on embedded YouTube videos and have no linked, dated source in the text. The post content has no statistics with attribution. The one first-hand data point is useful and should be expanded: "a 5,000-product e-commerce site took 4 months to reindex". Effort: 30 min per post.
6. **Homepage has no answer content.** The homepage has about 120 words of extracted text, all post excerpts. The H1 is just "Anıl Çağlıyan", and the H2s are post titles, each repeated twice (slider + list). There is no extractable "who / what / where" passage. Add a 130-170-word bio and services block near the top. Effort: 1 h.
7. **Invalid FAQPage JSON-LD** on `/ornek-robots-txt-kodlari/`. The answer text contains raw line breaks (JSONDecodeError at char 653), so the block is unparseable. Note: FAQ rich results are restricted to gov/health sites, so the value here is only machine readability. Effort: 10 min.
8. **CCBot returns 403** at the server even though robots.txt allows it. This is fine if intentional, since it only affects training corpora and not live AI search. If unintentional, it is inconsistent with robots.txt. Effort: 5 min to decide.

### LOW

9. **No `/llms.txt`.** It returns a 404 HTML page. It is optional, ignored by Google Search, and unlikely to change citations. It is a cheap add for an SEO-consultant brand that wants to showcase GEO practice. **No RSL 1.0 license** (`/license.xml` 404). Effort: 20 min.
10. **Wayback Machine blocked** (ia_archiver, archive.org_bot). This prevents independent historical verification. Minor. Effort: 5 min.
11. **Multi-modal:** posts have 1-2 images each, and the only videos are third-party YouTube embeds. There are no tables and only 1 list in 2 of the 4 posts. Comparison tables would improve extractability, for example on "crawl-delay support by search engine". Effort: 30 min per post.

### Positive signals

- SSR HTML, no SPA dependency, and fast raw fetch. Every AI search crawler gets a 200.
- Question-style H1/H2s ("Crawl Delay Nedir?", "Google Crawl Delay Yönergesini Dikkate Alıyor mu?"). First sentences give direct definitions, which is good answer-first structure.
- Short paragraphs (mostly 10-100 words). BlogPosting schema includes datePublished/dateModified, the author meta and an author box.

## Brand Mention Signals

| Source | Result |
|---|---|
| Wikipedia (tr/en) | 0 hits for "Anıl Çağlıyan" / "anilcagliyan" |
| Wikidata | No entity |
| Reddit | Not verifiable (blocked from this environment) |
| YouTube | Not verifiable (no API key). The site links to no owned channel |
| LinkedIn | Not linked from the site or schema (profile check returned 999 anti-bot) |
| X/Twitter | twitter.com/anilcagliyan linked |

## Top 5 Changes

1. Create a `/hakkimda/` About page and enrich the Person schema (jobTitle, knowsAbout, LinkedIn/YouTube/Product Experts profile in sameAs, image). Make the homepage and post sameAs sets match. **2-4 h, High impact.**
2. Mark sponsored posts `rel="sponsored"`, take them off the homepage, and fix or remove the Jannah license bar. **1 h, High.**
3. Add a 130-170-word answer-first bio/services block to the homepage. **1 h, Medium-High.**
4. Refresh the top 10 posts: add sourced, dated citations, add an AI-crawler section to the robots.txt post, expand to complete answers, and do genuine dateModified updates. **1-2 h per post, Medium-High.**
5. Build off-site entity corroboration: an owned YouTube channel or podcast appearances, Reddit/forum answers, a Wikidata item once notability sources exist, and a public Google Product Experts profile link. **Ongoing, High (long-term).**

## Structured findings (audit-data.json: AI Search Readiness)

```json
{"category":"AI Search Readiness","score":55,"subscores":{"citability":55,"structural_readability":60,"multimodal":45,"authority_brand":30,"technical_accessibility":80},
"findings":[
{"id":"geo-entity-about","severity":"high","title":"No About page; Person schema sameAs is self-only, no jobTitle/knowsAbout"},
{"id":"geo-sponsored-posts","severity":"high","title":"Off-topic sponsored posts with followed links (vionmachine.com) promoted on homepage"},
{"id":"geo-theme-nag","severity":"high","title":"Jannah 'License is not validated' bar rendered in crawlable HTML"},
{"id":"geo-thin-stale","severity":"medium","title":"Posts 200-600 words, bulk dateModified 2024-12-15, outdated facts"},
{"id":"geo-sources","severity":"medium","title":"Few attributed citations/statistics in posts"},
{"id":"geo-homepage-passage","severity":"medium","title":"Homepage lacks self-contained bio/answer passage (~120 words, duplicate H2s)"},
{"id":"geo-faq-invalid","severity":"medium","title":"Invalid FAQPage JSON-LD on /ornek-robots-txt-kodlari/"},
{"id":"geo-ccbot-403","severity":"medium","title":"CCBot 403 at server despite robots.txt allow"},
{"id":"geo-llms-txt","severity":"low","title":"No /llms.txt (optional) and no RSL license"},
{"id":"geo-wayback","severity":"low","title":"Wayback Machine crawlers disallowed"},
{"id":"geo-multimodal","severity":"low","title":"No tables; minimal lists; only third-party video"}],
"crawler_access":{"OAI-SearchBot":"allowed","GPTBot":"allowed","Claude-SearchBot":"allowed","ClaudeBot":"allowed","PerplexityBot":"allowed","Googlebot":"allowed","Google-Extended":"allowed","Applebot-Extended":"allowed","CCBot":"blocked_http_403"},
"llms_txt":"missing","rsl":"missing","rendering":"SSR"}
```
