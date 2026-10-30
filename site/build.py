#!/usr/bin/env python3
"""Static site generator for the AUTO-BUILDER landing site (standard library only).

Reads page fragments from site/pages/, facts from the repository itself
(agent frontmatter, SKILL.md version and phase headings) and writes docs/ for
GitHub Pages (Settings -> Pages -> Deploy from branch -> /docs).

Run:  python3 -I site/build.py
"""
import html
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "docs")
PAGES_DIR = os.path.join(ROOT, "site", "pages")
AGENTS_DIR = os.path.join(ROOT, ".claude", "agents")
SKILL = os.path.join(ROOT, ".claude", "skills", "auto-builder", "SKILL.md")

GH = "https://github.com/bsrikumar855-dot/ClaudeCODE-Autonomous-skills"
BASE = "https://bsrikumar855-dot.github.io/ClaudeCODE-Autonomous-skills/"
LASTMOD = "2026-10-30"
SITE_NAME = "AUTO-BUILDER"
OG_IMAGE = BASE + "assets/og-image.png"

# slug -> (title, description, nav label, priority)
PAGES = {
    "index": (
        "AUTO-BUILDER: Autonomous Coding Agent Skill for Claude Code",
        "Open-source Claude Code skill with eight subagents: turn a goal into a planned, built, tested and independently reviewed project, with approval checkpoints.",
        "Home", "1.0"),
    "features": (
        "Features: Claude Code Subagents & Autonomous Workflow",
        "Nine-step autonomous development lifecycle, eight Claude Code subagents, independent review, approval checkpoints, safe installers and optional hooks.",
        "Features", "0.8"),
    "installation": (
        "Install AUTO-BUILDER: Claude Code Skill Setup Guide",
        "Install the AUTO-BUILDER Claude Code skill and subagents for one project or all projects on Linux, macOS, WSL or Windows. Dry-run and update supported.",
        "Installation", "0.9"),
    "usage": (
        "Use AUTO-BUILDER: Goal-Driven Coding Agent Tutorial",
        "How to run /auto-builder: write a goal, approve the plan, follow the lifecycle, and read the delivery report. Includes example goals and a first-run tutorial.",
        "Usage", "0.8"),
    "architecture": (
        "Architecture: Claude Code Subagents & Dev Lifecycle",
        "How AUTO-BUILDER works: the lead agent, eight specialist subagents, state files, parallel-work rules, approval policy and the verify-and-review loop.",
        "Architecture", "0.7"),
    "faq": (
        "AUTO-BUILDER FAQ: Autonomous Claude Code Questions",
        "Answers about AUTO-BUILDER: what it is, whether it is official, safety, cost, Windows support, limitations, licensing and how it differs from plain prompting.",
        "FAQ", "0.6"),
}


def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    fm = text.split("\n---\n", 1)[0].lstrip("-\n")
    out = {}
    for line in fm.split("\n"):
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip('"')
    return out


def repo_facts():
    agents = []
    for f in sorted(os.listdir(AGENTS_DIR)):
        if f.endswith(".md"):
            fm = frontmatter(os.path.join(AGENTS_DIR, f))
            tools = [t.strip() for t in fm.get("tools", "").split(",") if t.strip()]
            agents.append({
                "name": fm["name"], "description": fm["description"], "tools": tools,
                "can_edit": "Edit" in tools or "Write" in tools,
            })
    text = open(SKILL, encoding="utf-8").read()
    version = re.search(r'version:\s*"([^"]+)"', text).group(1)
    phases = re.findall(r"^### Phase (\d) — (.+)$", text, flags=re.M)
    return agents, version, phases


ROLE_ORDER = ["product-manager", "researcher", "architect", "frontend-engineer",
              "backend-engineer", "ai-engineer", "qa-engineer", "critical-reviewer"]

PHASE_SUMMARY = {
    "0": "Inspect the repository, git state, conventions and the commands that build, test and lint it.",
    "1": "Frame the real problem and users, research where facts matter, compare approaches, recommend one.",
    "2": "Write testable requirements, user journeys and acceptance criteria.",
    "3": "Choose the stack, design components, data and APIs, and record trade-offs.",
    "4": "Define measurable acceptance criteria and milestones with verification gates in a persistent task file, with a per-milestone iteration budget.",
    "5": "Build one milestone at a time as vertical slices on a work branch; the lead commits only after the milestone passes its gate.",
    "6": "Run the milestone gate: tests, linters and regression checks, real user flows, then an independent review at meaningful checkpoints.",
    "7": "Repeat plan, build, test, review, fix per milestone, with root-cause analysis of failures, until the completion standard is met or a blocker needs you.",
    "8": "Report what was built and, per criterion, what is verified, partially verified or untested, whether review was independent, and what you must do next.",
}


def agent_table(agents):
    by = {a["name"]: a for a in agents}
    rows = []
    for n in ROLE_ORDER:
        a = by[n]
        edit = "Yes (assigned files)" if a["can_edit"] else "No edit tools"
        rows.append(
            f"<tr><th scope=\"row\"><code>{html.escape(n)}</code></th>"
            f"<td>{html.escape(a['description'])}</td>"
            f"<td>{html.escape(', '.join(a['tools']))}</td><td>{edit}</td></tr>")
    return ('<div class="table-wrap"><table><caption>The eight AUTO-BUILDER subagents (generated from '
            '<code>.claude/agents/</code>)</caption><thead><tr><th scope="col">Agent</th>'
            '<th scope="col">Responsibility</th><th scope="col">Tools</th>'
            '<th scope="col">Can edit files</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")


def phase_list(phases):
    items = "".join(
        f"<li><strong>Phase {n}: {html.escape(t)}.</strong> {html.escape(PHASE_SUMMARY[n])}</li>"
        for n, t in phases)
    return f'<ol class="phases" start="0">{items}</ol>'


def phase_short(phases):
    return " &rarr; ".join(html.escape(t) for _, t in phases)


def url(slug):
    return BASE if slug == "index" else f"{BASE}{slug}.html"


def href(slug):
    return "./" if slug == "index" else f"{slug}.html"


def json_ld(slug, title, desc, version, faq):
    graph = [{
        "@type": "SoftwareSourceCode",
        "@id": BASE + "#software",
        "name": SITE_NAME,
        "description": "Claude Code skill and subagents for goal-driven, autonomous software development with approval checkpoints.",
        "codeRepository": GH,
        "programmingLanguage": ["Markdown", "Bash", "PowerShell", "Python"],
        "license": "https://www.apache.org/licenses/LICENSE-2.0",
        "version": version,
        "url": BASE,
    }, {
        "@type": "WebSite", "@id": BASE + "#website", "name": SITE_NAME, "url": BASE,
    }]
    page_type = "FAQPage" if slug == "faq" else "WebPage"
    page = {"@type": page_type, "@id": url(slug) + "#page", "url": url(slug), "name": title,
            "description": desc, "isPartOf": {"@id": BASE + "#website"}, "about": {"@id": BASE + "#software"}}
    if slug == "faq":
        page["mainEntity"] = [{"@type": "Question", "name": q,
                               "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]
    graph.append(page)
    if slug != "index":
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE},
            {"@type": "ListItem", "position": 2, "name": PAGES[slug][2], "item": url(slug)}]})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=2, ensure_ascii=False)


def extract_faq(fragment):
    pairs = re.findall(r"<details[^>]*>\s*<summary>(.*?)</summary>\s*(.*?)</details>", fragment, flags=re.S)
    return [(re.sub(r"<[^>]+>", "", q).strip(),
             html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", a))).strip()) for q, a in pairs]


def render(slug, fragment, agents, version, phases):
    title, desc, _, _ = PAGES[slug]
    canonical = url(slug)
    nav = "".join(
        f'<li><a href="{href(s)}"{" aria-current=\"page\"" if s == slug else ""}>{PAGES[s][2]}</a></li>'
        for s in PAGES)
    faq = extract_faq(fragment) if slug == "faq" else []
    ld = json_ld(slug, title, desc, version, faq)
    body = (fragment.replace("{{AGENT_TABLE}}", agent_table(agents))
            .replace("{{PHASE_LIST}}", phase_list(phases))
            .replace("{{PHASE_SHORT}}", phase_short(phases))
            .replace("{{VERSION}}", html.escape(version))
            .replace("{{GH}}", GH).replace("{{BASE}}", BASE))
    et, ed = html.escape(title, quote=True), html.escape(desc, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{et}</title>
<meta name="description" content="{ed}">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#0b5fff">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/style.css">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{et}">
<meta property="og:description" content="{ed}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{OG_IMAGE}">
<meta property="og:image:width" content="1280">
<meta property="og:image:height" content="640">
<meta property="og:image:alt" content="AUTO-BUILDER: goal-driven autonomous development for Claude Code">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{et}">
<meta name="twitter:description" content="{ed}">
<meta name="twitter:image" content="{OG_IMAGE}">
<script type="application/ld+json">
{ld}
</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap bar">
    <a class="brand" href="./" aria-label="AUTO-BUILDER home"><span class="logo" aria-hidden="true">AB</span> AUTO-BUILDER</a>
    <nav aria-label="Main"><ul>{nav}<li><a class="gh" href="{GH}">GitHub</a></li></ul></nav>
  </div>
</header>
<main id="main" class="wrap">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <p><strong>AUTO-BUILDER</strong> v{html.escape(version)}: an independent, open-source Claude Code skill released under the
    <a href="{GH}/blob/main/LICENSE">Apache-2.0 license</a>. Not affiliated with or endorsed by Anthropic.</p>
    <p><a href="{GH}">Source on GitHub</a> &middot; <a href="{GH}/blob/main/CHANGELOG.md">Changelog</a> &middot;
    <a href="{GH}/blob/main/CONTRIBUTING.md">Contributing</a> &middot; <a href="{GH}/issues">Issues</a></p>
  </div>
</footer>
<script src="assets/site.js" defer></script>
</body>
</html>
"""


def main():
    agents, version, phases = repo_facts()
    assert len(agents) == 8 and len(phases) == 9, (len(agents), len(phases))
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    for slug in PAGES:
        frag = open(os.path.join(PAGES_DIR, slug + ".html"), encoding="utf-8").read()
        out = os.path.join(OUT, "index.html" if slug == "index" else slug + ".html")
        open(out, "w", encoding="utf-8").write(render(slug, frag, agents, version, phases))
    # 404: noindex, no canonical
    frag = open(os.path.join(PAGES_DIR, "404.html"), encoding="utf-8").read()
    page = render("index", frag, agents, version, phases)
    page = re.sub(r'<link rel="canonical"[^>]*>\n', "", page)
    page = re.sub(r'<meta property="og:url"[^>]*>\n', "", page)
    page = re.sub(r"<title>.*?</title>", "<title>Page not found | AUTO-BUILDER</title>", page)
    page = re.sub(r'<script type="application/ld\+json">.*?</script>\n', "", page, flags=re.S)
    page = page.replace('<meta charset="utf-8">', f'<meta charset="utf-8">\n<meta name="robots" content="noindex">\n<base href="{BASE}">')
    open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(page)

    urls = "".join(
        f"  <url>\n    <loc>{url(s)}</loc>\n    <lastmod>{LASTMOD}</lastmod>\n    <priority>{PAGES[s][3]}</priority>\n  </url>\n"
        for s in PAGES)
    open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")
    open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(
        f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n")
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    print(f"built {len(PAGES)} pages + 404, sitemap.xml, robots.txt into docs/ (v{version})")


if __name__ == "__main__":
    main()
