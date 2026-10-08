# Schema Audit: www.anilcagliyan.com
Date: 2026-10-08 | Schema score: **52/100**

Pages checked: homepage, /john-mueller-kimdir/, /outbound-links-nedir/, /301-yonlendirmesi-ne-zaman-kaldirilmalidir/, /google-gibi-getir-nedir/.
Note: /page-sitemap.xml contains only the homepage, so there is no separate about/service page to audit (itself a gap). Format is JSON-LD only, no Microdata/RDFa. Server-rendered.

## Detected
- Yoast graph (all pages): WebPage, WebSite (+SearchAction), BreadcrumbList, ImageObject, Person+Organization (combined type).
- Second, non-Yoast block on posts: BlogPosting (`@context` http://schema.org), with inline publisher Organization (`@id` "#Publisher"), author Person, image.
- FAQPage on 3 of 4 posts (outbound-links, 301, google-gibi-getir).

## Findings
| # | Severity | Finding |
|---|----------|---------|
| 1 | High | `sameAs` on the Person/Organization entity is only the site's own URL. Social profiles (Twitter/X, Facebook, Instagram, Pinterest; LinkedIn if one exists) are only on the duplicate publisher block. Weak entity identity. |
| 2 | High | Duplicate/conflicting entities on posts. Yoast Person+Organization (`/#/schema/person/...`) and the separate BlogPosting block's Organization `@id` "#Publisher" (relative, not resolvable) and author Person with no `@id`. They are not linked into one graph, so there are two competing "Anıl Çağlıyan" entities. |
| 3 | High | BlogPosting block uses `"@context": "http://schema.org"`. It should be https. |
| 4 | Medium | Homepage BreadcrumbList has a ListItem without `item`. On posts, the last crumb has no `item`. The last-crumb case is acceptable for Google. The homepage case is harmless but trivial to fix. |
| 5 | Medium | The Person is typed `["Person","Organization"]` with no `jobTitle`, `url`, `description`, `knowsAbout`, `worksFor` or `email`. Fix the entity: keep Person, add a ProfessionalService for the consultancy. |
| 6 | Medium | No ProfessionalService/Service schema anywhere. Home claims "SEO Uzmanı & Google Ürün Uzmanı" but no service entity, `areaServed` or `knowsLanguage`. |
| 7 | Medium | BlogPosting: `keywords` is an empty array, `description` is truncated mid-word at 200 chars, `articleBody` is embedded in full (bloat). The publisher logo has no dimensions and differs from the Yoast logo. The Yoast Article node is absent, so the post is not linked to the WebPage via `isPartOf`/`about`. |
| 8 | Medium | Stale freshness signals: posts last modified 2024-12-15 (bulk update). No `dateModified` benefit if content is unchanged. Verify it is accurate. |
| 9 | Low | Person `image`/`logo` is a WhatsApp screenshot filename (500x496). A proper square logo (min 112x112, ideally 512+) and a distinct headshot are better. |
| 10 | Low | No author archive `ProfilePage`/Person detail (`/author/anilcagliyan/`). Author `url` exists but has no `@id`/`sameAs`. |
| 11 | Info | FAQPage on 3 posts. Google retired FAQ rich results for all sites (2026-05-07), so there is no SERP benefit. Valid syntax, harmless. Do not add more for Google. Keep or remove at your discretion. |
| 12 | Info | WhatsApp API link with a phone number is in publisher `sameAs`. It is not a profile and exposes a phone number. Remove it from `sameAs`. |
| 13 | Info | SearchAction valid but Google no longer shows the sitelinks search box. Harmless. |

No placeholder text, no deprecated types (no HowTo) found. All URLs absolute except `#Publisher`.

## Missing opportunities
- Complete Person with sameAs/jobTitle/knowsAbout (Knowledge Graph, E-E-A-T)
- ProfessionalService with contact/areaServed
- Unified Article/BlogPosting inside the Yoast graph (fix: Yoast Settings > Content types > Article schema, then disable the second schema source in the theme/plugin)
- About/Hizmetler/İletişim pages with AboutPage/ContactPage/Service schema (pages do not exist in the sitemap)

## Recommended JSON-LD (homepage; replace `sameAs` placeholders only with real, verified profile URLs)
```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Person",
      "@id": "https://www.anilcagliyan.com/#/schema/person/8b5dfc43ea41b862e77bba8f4a861c35",
      "name": "Anıl Çağlıyan",
      "url": "https://www.anilcagliyan.com/",
      "jobTitle": "SEO Uzmanı",
      "description": "2017'den bu yana SEO danışmanlığı yapan SEO uzmanı ve Google ürün uzmanı.",
      "image": "https://www.anilcagliyan.com/wp-content/uploads/2022/09/WhatsApp-Image-2022-01-27-at-18.20.03-e1663673158771.jpg",
      "knowsAbout": ["SEO", "Teknik SEO", "Google Search Console", "İçerik Pazarlaması"],
      "knowsLanguage": "tr",
      "worksFor": {"@id": "https://www.anilcagliyan.com/#service"},
      "sameAs": [
        "https://twitter.com/anilcagliyan",
        "https://www.facebook.com/ANILLCAGLIYAN/",
        "https://www.instagram.com/anilcagliyan/",
        "https://tr.pinterest.com/anilcagliyan/"
      ]
    },
    {
      "@type": "ProfessionalService",
      "@id": "https://www.anilcagliyan.com/#service",
      "name": "Anıl Çağlıyan SEO Danışmanlığı",
      "url": "https://www.anilcagliyan.com/",
      "image": "https://www.anilcagliyan.com/wp-content/uploads/2022/09/Anil-CAGLIYAN-e1663268723947.png",
      "founder": {"@id": "https://www.anilcagliyan.com/#/schema/person/8b5dfc43ea41b862e77bba8f4a861c35"},
      "areaServed": {"@type": "Country", "name": "Türkiye"},
      "serviceType": "SEO Danışmanlığı",
      "sameAs": [
        "https://twitter.com/anilcagliyan",
        "https://www.facebook.com/ANILLCAGLIYAN/",
        "https://www.instagram.com/anilcagliyan/"
      ]
    }
  ]
}
```
Add telephone/email/address only if you want them public (not verified here).

## Recommended BlogPosting (per post; example, fix the second block)
```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "@id": "https://www.anilcagliyan.com/john-mueller-kimdir/#article",
  "isPartOf": {"@id": "https://www.anilcagliyan.com/john-mueller-kimdir/"},
  "mainEntityOfPage": {"@id": "https://www.anilcagliyan.com/john-mueller-kimdir/"},
  "headline": "John Mueller Kimdir?",
  "description": "John Mueller 2007 yılından beri Google'da çalışmaktadır; Senior Webmaster Trends Analyst olarak başlamış, şu an Search Advocate olarak görev yapmaktadır.",
  "datePublished": "2022-01-30T23:42:01+00:00",
  "dateModified": "2024-12-15T18:10:19+00:00",
  "inLanguage": "tr",
  "articleSection": "SEO",
  "image": "https://www.anilcagliyan.com/wp-content/uploads/2022/01/John-Mueller-Kimdir-1.jpg",
  "author": {"@id": "https://www.anilcagliyan.com/#/schema/person/8b5dfc43ea41b862e77bba8f4a861c35"},
  "publisher": {"@id": "https://www.anilcagliyan.com/#/schema/person/8b5dfc43ea41b862e77bba8f4a861c35"}
}
```
Drop `articleBody`, the empty `keywords`, and the `#Publisher` Organization.

## Homepage breadcrumb fix
Add `"item": "https://www.anilcagliyan.com/"` to the single ListItem.

## Priority order
1. Merge duplicate BlogPosting into Yoast graph (author/publisher by `@id`, https context)
2. Populate Person sameAs and attributes; add ProfessionalService
3. Create About/Services/Contact pages with matching schema
4. Clean logo/image assets; remove WhatsApp from sameAs
5. FAQPage: leave as is (Info only)
