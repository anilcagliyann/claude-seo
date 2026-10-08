# Content Quality / E-E-A-T: anilcagliyan.com

Audit date: 2026-10-08. Scope: homepage, `/tanitim/` category, probes for about/contact/service URLs, 15 posts read in depth, and all 105 posts in `post-sitemap.xml` crawled for word count, dates and metadata.
Tools used: `render_page.py --mode never`, `content_quality.py`, `metadata_template.py`, plus Ateşman readability (Turkish) computed on `extracted_text`.

## Score

| Area | Score |
|---|---|
| **Content score (overall)** | **42 / 100** |
| E-E-A-T composite | 40 / 100 |
| AI citation readiness | 52 / 100 |

### E-E-A-T breakdown (skill-internal weights, not Google's)

| Factor | Weight | Score | Basis |
|---|---|---|---|
| Experience | 20% | 50 | Real first-hand case study (ALB Yatırım), a Google Product Expert forum role and personal anecdotes. Most posts are generic definitions with no first-hand input. |
| Expertise | 25% | 50 | The author bio claims Google "Elmas Ürün Uzmanı" (Diamond Product Expert), but nothing verifies it. Technical posts are mostly sound, though some contain factual and terminology errors. |
| Authoritativeness | 25% | 35 | No About page. Person schema `sameAs` points only to the site itself. Google docs citations are mostly `nofollow`. No press mentions, talks or third-party profiles are linked. |
| Trustworthiness | 30% | 30 | Paid posts with followed links, including a YMYL dental advertorial. No About, Contact or Privacy page. A bulk lastmod rewrite. No visible dates. The case study's own disclaimer says its numbers are estimates. |

Weighted: 0.2x50 + 0.25x50 + 0.25x35 + 0.3x30 = **40**.

## Site-wide numbers

- 105 posts. The page sitemap contains only the homepage.
- Word counts: median 471. 14 posts are under 300 words, 57 under 500, 88 under 800, and only 1 reaches 1,500 or more (the floor for blog posts).
- Publishing years: 2022 = 32, 2023 = 48, 2024 = 5, 2025 = 17, 2026 = 3 (2 of the 3 are paid placements).
- Metadata (`metadata_template.py`, 105 pairs): `site_risk: low`, `templated_ratio: 0.0`, no `shared_cta_phrases`. Secondary flags: `description-echoes-title` x4, `brand-suffix-in-description` x2, `missing-metadata` x1 (`/html-lang-etiketi-nedir/` has no meta description).
- Readability (Ateşman, higher = easier): 48-74, typically 50-63, which is "medium". Sentences average 7-14 words. Readability is not a problem.
- `content_quality.py`: overall scores 70-86, filler and AI-pattern scores 0 on every page. **Low confidence:** the pattern lexicons appear to be English-only, so Turkish AI phrasing is not detected. A manual review was done instead (below).

## Findings

### C1. CRITICAL: Paid off-topic posts with followed commercial links, one of them YMYL medical
- **Evidence:** `/implant-tedavisinde-modern-yaklasimlar/` (242 words) promotes a named dentist and links `drhilalselamet.com` twice with no `rel` attribute. `/fiber-lazer-kesim-ve-metal-isleme-teknolojileri/` (230 words) promotes VION MACHINE and links `vionmachine.com` twice with no `rel`, and says "Reklamdır." (this is an ad). Both sit in the `/tanitim/` (Promotion) category, are bylined "Anıl Çağlıyan", and are pushed through the site-wide "breaking news" ticker. The implant post says "reklam değildir" (this is not an ad) while being a clinic promotion with a "tıklayın" (click here) CTA in its meta description.
- **Impact:** Followed paid links break Google's link-spam policy. Health advice written under an SEO consultant's byline, with no medical reviewer, is a low-quality YMYL signal under the QRG. A false "not an ad" disclosure damages trust directly. These posts are also the freshest content on the site, so they set the site's current image.
- **Fix:** Add `rel="sponsored"` to every outbound link in `/tanitim/`. Label the posts "Sponsorlu İçerik" (Sponsored content) above the fold and remove the "reklam değildir" claim. Better still, noindex the `/tanitim/` posts and take them out of the ticker. Do not accept YMYL (health or finance) advertorials.

### C2. HIGH: No About, Contact, Privacy or service page; entity is unverified
- **Evidence:** `/hakkimda/`, `/hakkinda/`, `/iletisim/`, `/about/`, `/contact/`, `/hizmetler/`, `/seo-danismanligi/`, `/gizlilik-politikasi/` and `/kvkk/` all return 404. The nav and footer contain only categories. The page sitemap lists only `/`. Person schema `sameAs: ["https://www.anilcagliyan.com/"]`. The profile image filename is `WhatsApp-Image-2022-01-27...jpg`. Contact information exists only inside the post author box (a yandex email and WhatsApp).
- **Impact:** For a personal-brand consultant site, the "who is responsible / who is the author" question is central to trust under the QRG. Turkish law also requires a KVKK privacy notice.
- **Fix:** Create `/hakkimda/` covering career timeline, employers (for example ALB Yatırım 2024-2025), a link to the Google Product Expert profile, talks and certifications, plus `/iletisim/`, `/gizlilik-politikasi-kvkk/` and a `/seo-danismanligi/` service page of at least 800 words. Add LinkedIn, X, the Product Expert profile and other real profiles to the Person schema `sameAs`, and set `jobTitle`, `knowsAbout`, `worksFor`/`alumniOf`. Use a proper headshot filename and alt text.

### C3. HIGH: Thin content at scale
- **Evidence:** 57 of 105 posts are under 500 words and 14 are under 300, for example `/arama-sonuclarinda-girilen-basligin-gozukmemesi/` (172), `/tiktok-mavi-tik-ne-ise-yarar/` (197), `/hashtag-iceren-urller-taranir-mi/` (198), `/html-butona-link-nasil-verilir/` (198), `/seo-uyumlu-ne-demek/` (202), `/crawl-delay-nedir/` (212). The homepage has about 120 words of main text (a post listing only).
- **Fix:** Triage. Expand roughly 15 core SEO topics into reference-grade guides with screenshots, GSC examples and real cases. Merge overlapping posts (C4). Noindex or 410 off-niche thin posts (C5). Add 500 or more words of positioning copy to the homepage: who you are, what you do, proof, and calls to action.

### C4. HIGH: Keyword cannibalization and duplicate intents
- **Evidence (URL pairs targeting the same intent):**
  - `/google-analytics-ve-search-console-verileri-neden-farklidir/` (589w) vs `/google-analytics-ve-search-console-arasindaki-farklar-nelerdir/` (299w)
  - `/indexifembedded-etiketi-nedir/` vs `/indexifembedded-etiketi-calisiyor-mu/`
  - `/301-yonlendirmesi-nasil-yapilir/` vs `/301-yonlendirmesi-ne-zaman-kaldirilmalidir/`
  - `/pagerank-algoritmasi-nedir/` vs `/pagerank-puani-nasil-yulseltilir/` (the slug also has a typo: "yulseltilir")
  - `/mail-imza-olusturma/` vs `/kurumsal-mail-imza-ornekleri/` vs `/kurumsal-mail-ornegi-kurumsal-mail-nasil-yazilir/`
  - `/instagram-bot-nasil-basilir-...` vs `/instagram-bot-takipci-zararlari/` (also contradictory, see C6)
  - `/wayback-machine-nedir/` vs `/web-site-gecmisi-goruntuleme/`
  - `/google-analytics-...` pair, `/trueview-discovery-reklam-nedir/` vs `/trueview-for-action-nedir/` (likely candidates for a single TrueView guide)
- **Fix:** Merge each pair into the stronger URL, 301 the weaker one, and update internal links. Check in GSC which URL already earns the impressions before choosing.

### C5. MEDIUM: Topical dilution from off-niche posts
- **Evidence:** Posts with no link to SEO consulting: `/matbu-fatura-nedir/`, `/unlulere-hediye-nasil-gonderilir/`, `/guido-van-rossum-kimdir/`, `/amazon-arbitraj-nedir/`, `/swot-analizi-unsurlari/`, `/yandex-pop3-ayarlari/`, `/chromeda-site-engelleme-kaldirma/`, `/tezin-kopya-olup-olmadigini-anlama/`, `/pop-up-magaza-nedir/`, `/127-0-0-1-nedir/`, plus the two paid posts.
- **Fix:** Prune or noindex anything without search value or a link to the consulting niche. Focus future publishing on SEO, technical SEO, GSC and AI search, where the Product Expert credential is relevant.

### C6. MEDIUM: Advice that contradicts the author's expertise, and factual errors
- **Evidence:**
  - `/instagram-bot-nasil-basilir-ucretsiz-ve-ucretli-yontemler/` lists "free" and "paid" bot services (InstaZood, Like4Like, Jarvee) and wrongly groups Hootsuite under "bots". Jarvee has been reported as discontinued, which should be checked. The same site also publishes `/instagram-bot-takipci-zararlari/` (the harms of bot followers). The post is generic and AI-like in structure.
  - `/john-mueller-kimdir/` (unchanged since 2022) translates "Search Advocate" as "arama avukatı" (literally "search lawyer"), says Mueller "replaced Matt Cutts as spokesperson" (a simplification), misspells "Matt Cuts", and refers to "2022" as current.
  - `/indexifembedded-etiketi-calisiyor-mu/` retells Dave Smart's (tamethebots) test but switches to first person ("izledim", I monitored, "kullandım", I used). That claims first-hand experience the author did not have.
- **Fix:** Rewrite the bot post as a "why not / risks / safe alternatives" piece, or merge it into the harms post. Fix the Mueller facts and terminology. Put the indexifembedded post in the third person with clear attribution, or run your own replication test and publish your own screenshots.

### C7. MEDIUM: Freshness signals are misleading or missing
- **Evidence:** 79 posts in `post-sitemap.xml` share a `lastmod` of 2024-12-15 between 18:08 and 18:31 UTC (a bulk re-save), but the content was not updated (for example the Mueller post still describes 2022 as current). Single posts show **no byline and no published/updated date** in the article header (`.entry-header` holds only the category and H1). The only visible dates come from sidebar widgets. The MUVERA post has no `article:modified_time`.
- **Fix:** Show "Yayın: … / Güncelleme: …" (published / updated) plus the author name and photo under the H1. Change `lastmod` and `dateModified` only after real content changes. Publish a visible changelog line on substantive updates.

### C8. MEDIUM: Case study undermines its own credibility
- **Evidence:** `/alb-yatirim-seo-basari-hikayesi/` (1,027w) is the site's strongest experience asset: a dated role (Sept 2024 to Sept 2025), steps taken, a site merger with 301/410, and quarter-over-quarter metrics. Its disclaimer, however, says the figures "are not the company's real data … based on estimated third-party (Ahrefs, Semrush) data." The metrics are still labelled "Non-Brand Clicks/Impressions", which are GSC metrics that Ahrefs and Semrush cannot measure. The "6% A/B test" on internal linking has no method behind it. There are no screenshots or charts.
- **Fix:** Label the metrics "Ahrefs tahmini organik trafik" (Ahrefs estimated organic traffic) or, with permission, show anonymised GSC screenshots. Add a before/after chart and a client quote or LinkedIn reference. Build 2-3 more case studies and link them from the homepage and `/case-study/`.

### C9. LOW: Citations to primary sources are nofollowed or sparse
- **Evidence:** Older posts link Google docs with `rel="nofollow"` (`/301-yonlendirmesi-nasil-yapilir/`, `/google-analytics-ve-search-console-verileri-neden-farklidir/`, `/indexifembedded-etiketi-nedir/`). Many posts have no outbound citations, for example `/john-mueller-kimdir/` and `/sentiment-analysis-duygu-analizi-nedir/`. Newer posts (`/site-haritasi-okunamadi-hatasi-cozumu/`, `/muvera-algoritmasi-nedir/`) do cite Google sources with followed links, which is good.
- **Fix:** Remove `nofollow` from editorial citations and cite Google Search Central or primary research for every factual claim.

### C10. LOW: AI-style generic structure in newer posts
- **Evidence:** `/muvera-algoritmasi-nedir/` uses emoji bullets, rhetorical openers ("Peki…?", "İşte…") and generic examples (vitamin D, Everest). `/site-haritasi-okunamadi-hatasi-cozumu/` uses one-sentence-per-line formatting and says "Bu yazıda: …" (in this post: …). Both are accurate, but neither carries a first-hand signal (no GSC screenshot from your own properties).
- **Fix:** Add one proprietary element per post, such as your own GSC screenshot, a forum case as a Product Expert, or a test result. That element is what separates the post from AI-written versions of the same topic.

## AI citation readiness (52/100)
- Positives: table of contents with anchor links (ez-toc), question-form H2s, definition-first opening sentences ("X, …dir."), BlogPosting, BreadcrumbList and Person schema, and `max-snippet:-1`.
- Gaps: no visible dates or byline (C7), a weak author entity (C2), few quotable statistics or original data, no FAQ blocks or summary boxes, and thin answers on many URLs. Add a 40-60 word "Kısaca" (In short) answer box under each H1 and a table of key facts on comparison posts (for example GA vs GSC).

## Prioritised actions
1. Apply `rel="sponsored"` and an honest disclosure to `/tanitim/`, or noindex it. Stop accepting YMYL advertorials. (C1)
2. Publish About, Contact, KVKK/Privacy and a service page. Strengthen Person schema `sameAs`. (C2)
3. Merge the cannibalising pairs and prune off-niche thin posts. (C4, C5, C3)
4. Show a byline and published/updated dates on posts. Stop bulk `lastmod` rewrites. (C7)
5. Fix the case-study data labelling and the factual errors. Rewrite the bot post. (C8, C6)

## Structured findings (audit-data.json, category: Content Quality)
```json
{"category":"Content Quality","score":42,"eeat":{"experience":50,"expertise":50,"authoritativeness":35,"trustworthiness":30,"composite":40},"ai_citation_readiness":52,
"findings":[
{"id":"C1","severity":"critical","title":"Paid off-topic/YMYL advertorials with followed links","urls":["/implant-tedavisinde-modern-yaklasimlar/","/fiber-lazer-kesim-ve-metal-isleme-teknolojileri/"]},
{"id":"C2","severity":"high","title":"No About/Contact/Privacy/service page; sameAs self-only"},
{"id":"C3","severity":"high","title":"57/105 posts <500 words; homepage ~120 words"},
{"id":"C4","severity":"high","title":"Keyword cannibalization across 7+ URL groups"},
{"id":"C5","severity":"medium","title":"Off-niche topical dilution"},
{"id":"C6","severity":"medium","title":"Factual errors and expertise-contradicting advice (Instagram bots, John Mueller, borrowed first-person test)"},
{"id":"C7","severity":"medium","title":"Bulk lastmod 2024-12-15 on 79 posts; no visible byline/dates"},
{"id":"C8","severity":"medium","title":"Case study metrics disclaimed as estimates yet labelled as GSC metrics"},
{"id":"C9","severity":"low","title":"Primary-source citations nofollowed or absent"},
{"id":"C10","severity":"low","title":"Generic AI-style structure, no proprietary evidence"}],
"metadata_template":{"site_risk":"low","templated_ratio":0.0,"shared_cta_phrases":{}}}
```
