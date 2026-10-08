# Visual + Image Audit: anilcagliyan.com (2026-10-08)
Screenshots: /home/user/claude-seo/anilcagliyan.com-audit/screenshots/{home,post}-{desktop,mobile}.png
Post tested: /muvera-algoritmasi-nedir/

## Images score: 66/100

## Visual findings
| Sev | Finding |
|---|---|
| High | No clear primary CTA above the fold on homepage (desktop or mobile). Fold shows a slider of posts, a quote banner and "Devamini Oku" links. No "hire / contact / free consultation" action. The only conversion element is a WhatsApp bubble. |
| Medium | Floating WhatsApp button (fixed bottom-left, ~50px) overlaps content on mobile: it covers the start of the post title on the homepage and the last intro line on the post. |
| Medium | Homepage hero slider cards show small centered illustrations on flat teal. Thumbnails are 390x220 jpgs of ~2-3KB, so they are low-information and the same teal block repeats. Post hero (muvera) is a small graphic on a teal block, with wasted space. |
| Low | Quote banner ("SEO, yapboz parcalarindan...") takes prime fold space with no link or action. |
| Low | Mobile nav is fine (hamburger, search, dark-mode toggle all visible). H1 is visible on the post above the fold. Body text is large and readable. No horizontal scroll seen. |
| Info | Tap targets: header icons and the WhatsApp button are about 44-50 CSS px, which is acceptable. The slider pagination dots are small (about 6-8px), so they fail the 48px guideline. |

## Image findings
| Sev | Finding |
|---|---|
| High | Homepage OG image is cropped-anilcagliyan-favikon-1.png, a 512x512 PNG favicon (2.6KB). It is square, tiny, and shows as a poor social card. Declared 512x512. Fix: use a 1200x630 branded image. |
| High | No twitter:image tag, and no twitter:card image meta found (only twitter:card, label and data are present). |
| Medium | Zero WebP/AVIF in HTML. All images are JPG/PNG. Sizes are small, so the byte savings are modest, but the "next-gen formats" check fails. |
| Medium | Alt text gaps. Homepage: 17 imgs, 2 with empty alt (ssl-hatasi-nedir, muvera-algoritmasi-nedir), so about 88% coverage. Post: hero image (1200x787) alt is empty, and the in-body MUVERA3_Recall.png alt is empty. The "Hemen Teklif Al" CTA image has alt text but no width/height. Alt text on the Googleda... thumbnail has an unescaped `&#039;` entity. |
| Medium | Lazy loading: homepage imgs have no loading="lazy", so all 17 load eagerly, including below-fold ones. The post page lazy-loads the below-fold related thumbs correctly. The post hero uses fetchpriority=high, which is good. The homepage LCP image has no fetchpriority hint. |
| Low | CLS: width/height attributes are present on nearly all images, so risk is low. The exception is hemen-teklif-al.png (81KB, no dimensions), which is a CLS risk and also oversized for a button banner. |
| Low | No srcset/sizes found on post hero or thumbs in homepage; thumbnails are fixed 390x220 and 220x150 crops. Mobile gets the same files (acceptable at these byte sizes). |
| Low | Weight is good. Hero 19KB, in-body PNG 63KB (could be WebP, about 60% smaller), logo 3.4KB, author photo unnamed.jpg 25KB (generic filename), thumbs 2-3KB. |
| Info | Author photo uses a descriptive alt. The file name "unnamed.jpg" is non-descriptive. |

## Score rationale
Start 100. OG/social image -12, no twitter:image -4, no next-gen formats -6, alt gaps -6, homepage lazy loading -4, missing dimensions on one image -2. Total 66.

## Priorities
1. Create a 1200x630 OG image for the homepage (and twitter:image).
2. Add a visible CTA (contact/quote) in the header or hero.
3. Fix alt for the 2 empty homepage thumbs and the post hero and in-body image.
4. Move the WhatsApp bubble clear of the content, or shrink it.
5. Serve WebP (plugin or CDN), add loading=lazy below the fold on the homepage, add dimensions to the CTA image.
