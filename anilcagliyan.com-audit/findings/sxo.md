# SXO Findings: anilcagliyan.com

**Analysed:** 2026-10-08 | **Market:** Turkey (tr) | **Analyst:** seo-sxo agent
**Fetch method:** `render_page.py --mode always` (Playwright Chromium; site is not an SPA) + `parse_html.py`
**SXO Gap Score (homepage): 35/100**. This score is separate from the SEO Health Score.

---

## 1. Primary Finding: Page-Type Mismatch (CRITICAL)

The homepage title and meta say "SEO Uzmanı & Google Ürün Uzmanı". The page itself is a **blog index**. It has a post slider, the same 6 posts repeated in 3 modules (22 H2s, all post titles), pagination to /page/11/ and a 3-sentence "Ben Kimim?" sidebar. It has no service section, process, pricing, testimonials, contact form, or "SEO uzmanı/danışmanı" copy above the fold. The H1 is just "Anıl Çağlıyan".

`page-sitemap.xml` lists **only the homepage**. /hakkimda/, /iletisim/ and /seo-danismanligi/ all return 404. The site has no service page, about page or contact page that could rank for commercial queries.

| Target query | SERP dominant type (results analysed) | Consensus | Target page type | Severity |
|---|---|---|---|---|
| seo uzmanı (homepage) | Job listings + career guides (eleman.net x3, kariyer.net x3, cvbenim, kampusum) | ~89% career/job intent (8/9) | Blog index / personal hub | **CRITICAL**. Wrong intent and wrong type |
| seo danışmanı / seo danışmanlığı hizmeti (homepage, implied by title + bio) | Service marketplace listings (armut.com x7-8) + definition/career pages (kariyer.net, donanimhaber, youthall) + agency directories (Semrush) | ~60% commercial service listings / ~40% informational | Blog index | **CRITICAL**. Commercial-service SERP, no service page exists |
| seo uzmanı istanbul ... fiyat | armut.com x5, provider profiles, agency directories, 1 budget guide | ~70% service/provider profile | none | **HIGH**. No page targets it |
| e-ticaret seo danışmanı | Agency directories (Semrush x5), e-com platform blogs (ticimax, parasut), career page | Mixed directory/informational | /e-ticaret/ category (4 posts) | **HIGH** |
| site haritası okunamadı hatası (/site-haritasi-okunamadi-hatasi-cozumu/) | Official help docs (Yandex x6, Wix), WPBeginner tutorial, validator tool | ~90% troubleshooting guide/docs | Blog post / how-to (787 words, 7 H2) | **ALIGNED** (schema gap only) |
| google'da arama yapın veya bir url yazın (/googleda-arama-.../) | ranktracker blog, Google Help x2, milliyet, teknoblog, shiftdelete | ~70% informational blog/help | Blog post (731 words) | **ALIGNED** for type. **MEDIUM** for business value (off-topic traffic, no CTA) |
| /seo/ category ("SEO Blog - Google Algoritma Güncellemeleri") | n/a (hub) | — | CollectionPage, 480 words, no intro copy | **MEDIUM**. The only "SEO" hub is a post list |

**Interpretation:** "seo uzmanı" is mostly a **job-seeker / career** SERP in Turkey. A personal homepage cannot win it as a service page. It can win it as (a) a career guide ("SEO uzmanı nedir, nasıl olunur, maaşı") or (b) an expert profile with strong entity signals. "seo danışmanı / danışmanlığı" is the real commercial query. Marketplace profiles (Armut) dominate it, so the homepage needs to become a **Service page / expert profile** that is as good as or better than an Armut profile: services, process, proof, reviews, a contact CTA, and indicative pricing.

---

## 2. Findings by Severity

| # | Severity | Finding | Evidence | Fix |
|---|---|---|---|---|
| F1 | CRITICAL | Homepage is a blog index while title/meta target "SEO Uzmanı" | H1 "Anıl Çağlıyan". All 22 H2s are post titles (6 posts x3). Bio is 3 sentences in the sidebar. | Rebuild the homepage as an expert/service hub (see SOLL wireframe). Move the post feed to /blog/ |
| F2 | CRITICAL | The site has no service, about or contact page | page-sitemap.xml = homepage only. /hakkimda/, /iletisim/ and /seo-danismanligi/ return 404 | Create /seo-danismanligi/ (Service + ProfessionalService schema), /hakkimda/ (ProfilePage + Person) and /iletisim/ |
| F3 | HIGH | Off-topic sponsored-style post is pinned in the site-wide "Yeni" ticker: "İmplant Tedavisinde Modern Yaklaşımlar" | It is the first internal link on every page and the first thing visible on mobile (screenshots/home-mobile.png) | Remove it from the ticker. If it is paid placement, mark the post links `rel="sponsored"` and noindex it, or delete it (parasite/site-reputation risk for an SEO consultant's own site) |
| F4 | HIGH | The main proof asset undermines itself | ALB Yatırım case study (1,311 words, strong % uplift tables). Its legal note says "İçerikte geçen bilgiler ... şirketin gerçek verileri değildir ... ahrefs, semrush tahmini". It was also an in-house role, not a client engagement | Re-frame as an "in-house SEO lead" result. Show GSC screenshots (anonymised) or get client approval. Add 2-3 client testimonials. Add an end-of-article CTA |
| F5 | HIGH | Authority claims are not verifiable | "Google Elmas Ürün Uzmanı" has no link to the Google Product Experts profile. Person `sameAs` points only to the site itself. No LinkedIn. The photo filename is "WhatsApp-Image-2022-01-27..." | Link the Product Expert profile, LinkedIn, Twitter and Instagram in `sameAs`. Add `jobTitle`, `knowsAbout`, `award`/`hasCredential`. Use a professional headshot |
| F6 | HIGH | No commercial CTA anywhere except a floating WhatsApp button and a yandex.com email in the sidebar | No form, no "Ücretsiz SEO Analizi", no phone number visible | Add a primary CTA above the fold ("Ücretsiz SEO Ön Analizi Al" -> /iletisim/) and repeat it after the posts. Use a domain email |
| F7 | MEDIUM | Theme notice in the rendered DOM: "Jannah Theme License is not validated" (red bar, `display:block!important`, outbound link to tielabs.com) | Found in rendered HTML of every page. Not visible in the captured mobile viewport, so it may sit below the fold | Validate the licence or remove the bar. It is a strong negative trust signal for a web professional |
| F8 | MEDIUM | Article pages use `WebPage` instead of `Article`/`BlogPosting`. The homepage has no `ProfessionalService` | structured_data types on article pages: WebPage, BreadcrumbList, Person | Switch Yoast/Rank Math article type to BlogPosting with author Person. Add ProfessionalService on the service page (`/seo schema`) |
| F9 | MEDIUM | High-traffic informational posts do not convert | e.g. "Google'da arama yapın veya bir URL yazın" is off-niche and has no contextual CTA | Add an in-content CTA box linking to the service page on SEO-niche posts. Prune or merge off-niche posts (kurumsal mail, sosyal medya görgü kuralları, implant) |
| F10 | MEDIUM | /seo/ category hub has no intro copy and a generic title | 480 words, H1 "SEO", no hub text, no links to service/case study | Add a 150-250 word intro, a "Başlangıç rehberleri" block and a service CTA |
| F11 | LOW | Freshness: the latest post is 2026-02-20 (about 7.5 months ago). The homepage slider repeats Dec 2025 posts | publication dates on the rendered pages | Keep a monthly cadence, or show "Son güncelleme" on evergreen guides |
| F12 | LOW | 4 of 17 homepage images have empty alt text. The homepage repeats the same post blocks 3x | parse_html images list | Remove the duplicate modules. Add alt text |

---

## 3. User Stories (derived from SERP signals)

1. **Awareness (career):** As a *student/junior marketer*, I want to learn what an SEO uzmanı does and earns, because I am considering the career. I'm blocked because the site has no career guide; its homepage just lists posts. *Signal:* "seo uzmanı" SERP is 8/9 job/career pages (eleman.net maaş, "Seo Uzmanı Nasıl Olunur?", kariyer.net "Dijital çağın popüler mesleği").
2. **Consideration (service):** As an *SMB owner*, I want to compare SEO danışmanları by reviews, scope and price, because I fear paying for SEO with no result. I'm blocked because the site has no service scope, pricing signal, reviews or process. *Signal:* armut.com dominates "seo danışmanı/danışmanlığı" with review counts (avg 4.8, 505 providers in İstanbul) and a "teklif al" flow.
3. **Decision (service):** As a *business owner ready to hire*, I want to contact a credible consultant quickly. I'm blocked because the only paths are a WhatsApp icon or a yandex.com email, and there is no form or response-time promise. *Signal:* marketplace SERP results are built around quote request ("fiyat öğrenebilmek için iletişime geçmeniz gerekmektedir").
4. **Consideration (e-commerce):** As an *e-commerce manager*, I want evidence of e-com SEO expertise (category/product SEO, migrations), because platform migrations risk revenue. I'm blocked because /e-ticaret/ has 4 general posts and no e-com case study. *Signal:* "e-ticaret seo danışmanı" SERP = agency directories + ticimax/parasut consultancy explainers.
5. **Awareness (troubleshooting):** As a *site owner with a GSC error*, I want a fast, exact fix for "site haritası okunamadı". I'm blocked because the post lacks a step checklist above the fold, and the SERP competitors are official docs. *Signal:* Yandex/Wix help docs fill ~90% of results.

---

## 4. SXO Gap Score: Homepage (35/100)

| Dimension | Score | Evidence |
|---|---|---|
| Page Type | 3/15 | Blog index vs. career SERP ("seo uzmanı") and service-listing SERP ("seo danışmanı") |
| Content Depth | 4/15 | 814 words, almost all repeated excerpts. Bio is 3 sentences. No services/process/FAQ |
| UX Signals | 5/15 | WhatsApp float and dark mode are positive. No hero value proposition. Off-topic implant ticker. 3 duplicate post modules. Theme licence bar |
| Schema | 6/15 | Valid WebSite/WebPage/Person+Organization. `sameAs` is self-only. No ProfessionalService/Service/FAQ/Review |
| Media | 6/15 | 17 images, but no headshot hero, no video, no client logos. 4 empty alts |
| Authority | 5/15 | "Elmas Ürün Uzmanı" claim is unlinked. Case study disclaims its own data. No testimonials or logos |
| Freshness | 6/10 | dateModified 2026-07-04. Latest post 2026-02-20 |

Article page /site-haritasi-okunamadi-hatasi-cozumu/: page type ALIGNED. Estimated gap score 62/100. The main losses are schema (WebPage, not BlogPosting/HowTo), no quick-answer checklist at the top, and no screenshots of the GSC error state.

---

## 5. Persona Scores: Homepage

| Persona | Relevance | Clarity | Trust | Action | Total | Rating |
|---|---|---|---|---|---|---|
| E-commerce manager (hiring e-com SEO) | 5/25 | 5/25 | 7/25 | 7/25 | **24/100** | Critical Mismatch |
| SMB owner (prospective client) | 8/25 | 5/25 | 9/25 | 9/25 | **31/100** | Critical Mismatch |
| Recruiter / employer (job-intent SERP for "seo uzmanı") | 10/25 | 8/25 | 11/25 | 8/25 | **37/100** | Critical Mismatch |
| SEO learner / career starter | 15/25 | 10/25 | 12/25 | 10/25 | **47/100** | Needs Work |
| GSC troubleshooter (on article page, not homepage) | 20/25 | 17/25 | 14/25 | 12/25 | **63/100** | Good |

### Weakest Persona: E-commerce manager (24/100)
**Top issue:** No e-com service, no e-com case study. /e-ticaret/ has 4 generic posts.
**Recommended fix:** Add an "E-Ticaret SEO Danışmanlığı" section/page covering category/faceted navigation, product schema, migration 301 plans, and Ticimax/İkas/Shopify experience. Reuse the ALB 301/410 site-merge story as migration proof. CTA: "E-ticaret sitenizin ücretsiz SEO ön analizi".

### SMB owner (31/100)
**Fix:** Hero = "SEO Danışmanı Anıl Çağlıyan: Google Elmas Ürün Uzmanı, 9 yıllık deneyim" + primary CTA "Ücretsiz Ön Analiz Talep Et" + secondary "WhatsApp'tan Yaz". Below that, add a 3-4 step process, service packages ("başlangıç fiyatı ... TL'den" or "teklif al"), testimonials, and an FAQ ("SEO ne kadar sürede sonuç verir?", "SEO danışmanlığı fiyatları").

### Recruiter / employer (37/100)
**Fix:** Add a /hakkimda/ ProfilePage with work history (ALB Yatırım 2024-2025, etc.), LinkedIn link, downloadable CV and certifications. Add `Person.sameAs` to LinkedIn and the Google Product Experts profile.

### SEO learner (47/100)
**Fix:** Publish the pillar guide "SEO Uzmanı Nedir, Nasıl Olunur? (2026 Maaş, Yetkinlikler, Yol Haritası)". It matches the dominant SERP type for "seo uzmanı" and links to existing posts (MUVERA, Word Vector, Crawl Schedule) as a learning path.

### Systemic Issues
- **Action:** the lowest dimension across all personas. There is no form, no CTA beyond a WhatsApp icon, and no CTA at the end of articles.
- **Trust:** claims are unlinked, the case study disclaims its own data, the implant ticker is off-topic, and the licence bar is present.

### Priority Actions
1. Create /seo-danismanligi/ (Service page) and turn the homepage into an expert/service hub (F1, F2, F6).
2. Remove the implant ticker post. Fix the theme licence bar (F3, F7).
3. Add verifiable trust: `sameAs`, a Product Expert link, testimonials, and a reframed case study (F4, F5).
4. Add an e-commerce SEO section and case content (weakest persona).
5. Publish the "SEO uzmanı nedir / nasıl olunur" pillar to match the career-intent SERP.

---

## 6. SOLL Wireframe (homepage, condensed)

1. Hero: H1 "SEO Danışmanı Anıl Çağlıyan" | subline "Google Elmas Ürün Uzmanı · 2017'den beri" | CTA [Ücretsiz SEO Ön Analizi] -> /iletisim/ | [WhatsApp]
2. Proof strip: Google Product Expert badge (linked), client/brand logos (ALB Yatırım etc.), "+513% non-brand gösterim" (with source)
3. Hizmetler: Teknik SEO · E-Ticaret SEO · İçerik/Semantic SEO · Site Taşıma -> each links to a service page
4. Süreç: Analiz -> Yol haritası -> Uygulama -> Aylık raporlama
5. Case study card -> /alb-yatirim-seo-basari-hikayesi/
6. Testimonials (Review markup only for first-party reviews)
7. FAQ (fiyat, süre, garanti)
8. Latest 3 SEO posts -> /blog/
9. Repeat CTA + contact form

---

## 7. Cross-Skill Recommendations
- `/seo schema`: ProfessionalService, Service, BlogPosting, ProfilePage, Person.sameAs
- `/seo content`: E-E-A-T verification of credentials and case-study data
- `/seo local`: if targeting "seo uzmanı istanbul", consider a GBP listing (Armut-style local SERP)
- `/seo page`: thin category hubs (/seo/, /e-ticaret/)

---

## 8. Limitations
- The WebSearch backend is not a live Google.com.tr SERP. Ads, PAA, AI Overview, local pack and featured snippets could not be observed, and result order may differ from Google TR. A branded query ("anıl çağlıyan seo") did not return the site, which may be a backend artifact rather than a ranking fact.
- No GSC/ranking data was available. Target queries are inferred from title/meta/H1 and URL slugs.
- 5-9 results analysed per query (fewer than 10).
- Visibility of the Jannah licence bar was not confirmed in a full-page screenshot.
- Case-study metrics were not independently verified.

---

## 9. Structured Findings (audit-data.json, category: Search Experience)

```json
{
  "category": "Search Experience",
  "sxo_gap_score": 35,
  "findings": [
    {"id": "SXO-F1", "severity": "critical", "title": "Homepage is a blog index while targeting 'SEO Uzmanı' (career SERP) / 'SEO danışmanı' (service SERP)", "url": "https://www.anilcagliyan.com/"},
    {"id": "SXO-F2", "severity": "critical", "title": "No service, about or contact pages exist (page-sitemap lists homepage only; /hakkimda/, /iletisim/ 404)", "url": "https://www.anilcagliyan.com/page-sitemap.xml"},
    {"id": "SXO-F3", "severity": "high", "title": "Off-topic 'İmplant Tedavisinde Modern Yaklaşımlar' post pinned in site-wide ticker", "url": "https://www.anilcagliyan.com/implant-tedavisinde-modern-yaklasimlar/"},
    {"id": "SXO-F4", "severity": "high", "title": "Case study disclaims its own data as estimated third-party figures", "url": "https://www.anilcagliyan.com/alb-yatirim-seo-basari-hikayesi/"},
    {"id": "SXO-F5", "severity": "high", "title": "Unverifiable authority claims; Person sameAs self-only", "url": "https://www.anilcagliyan.com/"},
    {"id": "SXO-F6", "severity": "high", "title": "No commercial CTA beyond WhatsApp icon and yandex email", "url": "https://www.anilcagliyan.com/"},
    {"id": "SXO-F7", "severity": "medium", "title": "'Jannah Theme License is not validated' bar present in rendered DOM", "url": "https://www.anilcagliyan.com/"},
    {"id": "SXO-F8", "severity": "medium", "title": "Articles use WebPage not BlogPosting; no ProfessionalService", "url": "https://www.anilcagliyan.com/site-haritasi-okunamadi-hatasi-cozumu/"},
    {"id": "SXO-F9", "severity": "medium", "title": "Informational traffic pages have no conversion path; off-niche posts", "url": "https://www.anilcagliyan.com/googleda-arama-yapin-veya-bir-url-yazin/"},
    {"id": "SXO-F10", "severity": "medium", "title": "/seo/ hub has no intro copy or service link", "url": "https://www.anilcagliyan.com/seo/"},
    {"id": "SXO-F11", "severity": "low", "title": "Last post 2026-02-20 (~7.5 months)", "url": "https://www.anilcagliyan.com/"},
    {"id": "SXO-F12", "severity": "low", "title": "Duplicate post modules; 4 empty alt attributes on homepage", "url": "https://www.anilcagliyan.com/"}
  ],
  "personas": {"ecommerce_manager": 24, "smb_owner": 31, "recruiter": 37, "seo_learner": 47, "gsc_troubleshooter_article": 63}
}
```

Generate a PDF report? Use `/seo google report`
