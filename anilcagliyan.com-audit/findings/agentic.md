# Agent-readiness: https://www.anilcagliyan.com (checked 2026-10-08)

Agent-readiness score (analyst composite, not a Lighthouse figure): 80/100
Agent-UX heuristic (separate): 100/100, status complete (1023 a11y nodes, 97 interactive, 0 unnamed, 7 landmarks)
Lighthouse Agentic Browsing: unavailable. PSI returned HTTP 429 (keyless daily quota) for mobile and desktop. No X/N reported. Rerun with a Google API key.

## Access policy (robots.txt, 10 groups)
- Training (GPTBot, ClaudeBot): allowed, no named group, falls to default; no Content-Signal
- Search (OAI-SearchBot, Claude-SearchBot): allowed
- User-triggered (ChatGPT-User, Claude-User, Perplexity-User): not blocked. Vendors differ on honouring robots.txt (Claude-User honours; ChatGPT-User may not apply; Perplexity-User generally ignores).
- Blocked: archive.org_bot, ia_archiver, AhrefsBot, SiteAuditBot, SemrushBot variants, SplitSignalBot.
- WAF treatment of agent UAs: NOT tested. UA matrix needs the site owner's authorization, which was not confirmed.

## Findings
- P3 / info: No Content-Signal line. Optional, e.g. `Content-Signal: search=yes, ai-input=yes, ai-train=no`. A preference only; Google does not act on it (checked 2026-09-23).
- P3 / info: No named AI groups in robots.txt. Add them only if policy differs by purpose.
- P3 / opportunity: /llms.txt returns 404 (and llms-full.txt). Lighthouse drops the audit from the fraction; a valid file (H1, `>` summary, Markdown links) would add a counted pass. Google Search ignores it.
- P3 / opportunity: No Markdown delivery (Accept: text/markdown returns HTML, no rel=alternate, /index.md 404).
- P3 / opportunity: WebMCP absent (0 registerTool call sites). 3 forms, none annotated. W3C Community Group draft, WebKit opposes (checked 2026-09-23). Annotate only forms that are safe for an agent to submit.
- N/A: ai-catalog.json (404; draft ARD spec), API catalog, OAuth metadata, A2A agent card, UCP all 404. Only needed if the matching service exists.
- P3: 4 inputs lack ARIA attributes (labels are present, 0 unlabeled). Minor.

## Passes
- Server-rendered: 740 words without JS
- robots.txt reachable (200), Sitemap declared
- Real 404s (no soft-404)
- 135 real anchors, 4 real buttons, no div-onclick widgets

## Fix priority
No P0/P1/P2 defects. All gaps are opportunities. No ranking, citation or traffic effect is promised.
