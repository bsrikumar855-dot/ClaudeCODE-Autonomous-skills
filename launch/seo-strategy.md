# SEO strategy

## Honest framing
- No search-volume or ranking data was available when this was written, so keyword priorities below are based on **search intent and the competitive landscape**, not volumes. Don't quote volumes you haven't measured; validate in Search Console after the site is indexed.
- A new GitHub Pages site under a `github.io` project path has no authority yet. Realistic expectation: it can rank for its own name and very specific phrases first; broad terms ("Claude Code skills") are dominated by Anthropic's docs, large curated lists and established repositories.
- Landscape (observed in a web search on 2026-10-30): GitHub topic pages and "awesome" lists for `agent-skills`, `claude-skills`, `subagents` list hundreds to 1,000+ repositories. Differentiate with specifics rather than volume.

## Keyword map
| Keyword | Intent | Where it is used (naturally) |
|---|---|---|
| Claude Code skills | Informational / navigational: find or learn skills | README H1 area, home page, installation page title and h1, GitHub topics |
| Claude Code subagents | Informational: how to structure subagents | Features and Architecture titles/h1/h2, agent table |
| Claude Code autonomous agent | Commercial-investigation: autonomous workflows in Claude Code | Home title, README intro, announcement |
| Autonomous coding agent | Informational/broad | Home title and README H1, FAQ |
| Goal-driven coding agent | Informational/long-tail | Usage page title, home h1 ("Goal-driven autonomous development") |
| Autonomous AI development | Informational/broad | Home h1/description, features lead |
| AI software development workflow | Informational: process, not tool | Home "What is" paragraph, Architecture, DEV article |

Secondary long-tail ideas to target with tutorials/articles, not forced into existing pages: "claude code plan before implementing workflow", "claude code subagent least privilege tools", "claude code skill disable-model-invocation", "install claude code skill project vs personal".

## On-page implementation (done)
- Unique `<title>` (≤60 chars) and meta description (70–160 chars) per page, enforced by `site/check.py`.
- One `<h1>` per page; descriptive `h2`s; anchored sections for deep links.
- Canonical URLs, Open Graph and Twitter/X cards, JSON-LD (`SoftwareSourceCode`, `WebSite`, `WebPage`/`FAQPage`, `BreadcrumbList`), `sitemap.xml`, `robots.txt`.
- Descriptive internal links ("installation guide", "known limitations"), mobile-first responsive layout, semantic landmarks, skip link, no render-blocking third-party scripts, no external fonts, system fonts only.
- Every claim on the site is derived from or checked against the repo; agents and lifecycle phases are generated from source files.

## Limitations to be aware of
1. **robots.txt location:** crawlers read `robots.txt` only at the host root. This project site lives at `/ClaudeCODE-Autonomous-skills/`, so `docs/robots.txt` is served at `.../ClaudeCODE-Autonomous-skills/robots.txt` and is **not** honoured as the host's robots file. It is harmless and documents the sitemap, but the sitemap must be submitted in Search Console. A custom domain or a `bsrikumar855-dot.github.io` user-site repository would allow a root robots.txt.
2. **FAQ rich results:** FAQPage markup is valid, but Google restricts FAQ rich results to well-known authoritative government and health sites, so don't expect expandable FAQ snippets.
3. **Indexing is not guaranteed or instant.** Do not claim the site is indexed until Search Console shows it.
4. **Backlinks must be earned.** Don't buy, trade or fabricate them. Legitimate sources: your own posts, the launch drafts here, relevant "awesome" lists that accept submissions (read their contribution rules first), and documentation that genuinely cites it.
5. **Domain authority:** `github.io` subpaths share the host with millions of projects; a custom domain would help long-term (optional).
6. **Crowded niche:** see the landscape note above.

## Measure
Search Console (queries, pages, indexing), GitHub traffic (Insights → Traffic, shows 14 days of referrers), clones, stars as a soft signal only.
