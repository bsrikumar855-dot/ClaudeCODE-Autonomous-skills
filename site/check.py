#!/usr/bin/env python3
"""Validate the generated site in docs/ (standard library only).

Run:  python3 -I site/build.py && python3 -I site/check.py
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS = os.path.join(ROOT, "docs")
sys.path.insert(0, os.path.dirname(__file__))
import build  # noqa: E402

BASE, GH = build.BASE, build.GH
errors, warnings, checks = [], [], 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        errors.append(msg)
    return cond


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""; self._in_title = False
        self.meta = {}; self.prop = {}; self.links = []; self.canon = []
        self.ids = set(); self.hrefs = []; self.srcs = []; self.h = []; self._h = None
        self.ld = []; self._ld = False; self.lang = None; self.robots = None
        self.base = None; self.imgs_no_alt = 0

    def handle_starttag(self, tag, a):
        a = dict(a)
        if "id" in a: self.ids.add(a["id"])
        if tag == "html": self.lang = a.get("lang")
        elif tag == "title": self._in_title = True
        elif tag == "meta":
            if "name" in a: self.meta[a["name"]] = a.get("content", "")
            if "property" in a: self.prop[a["property"]] = a.get("content", "")
        elif tag == "base": self.base = a.get("href")
        elif tag == "link":
            if a.get("rel") == "canonical": self.canon.append(a.get("href"))
            self.links.append(a.get("href"))
        elif tag == "a" and "href" in a: self.hrefs.append(a["href"])
        elif tag in ("img", "script") and "src" in a: self.srcs.append(a["src"])
        elif tag in ("h1", "h2", "h3"): self._h = tag; self.h.append([tag, ""])
        elif tag == "script" and a.get("type") == "application/ld+json": self._ld = True
        if tag == "img" and a.get("alt") is None: self.imgs_no_alt += 1
        if tag == "script" and a.get("type") == "application/ld+json": self._ld = True; self.ld.append("")

    def handle_endtag(self, tag):
        if tag == "title": self._in_title = False
        if tag in ("h1", "h2", "h3"): self._h = None
        if tag == "script": self._ld = False

    def handle_data(self, d):
        if self._in_title: self.title += d
        if self._h: self.h[-1][1] += d
        if self._ld and self.ld: self.ld[-1] += d


def parse(path):
    p = Page(); p.feed(open(path, encoding="utf-8").read()); return p


def local_target(page_dir, ref):
    ref = ref.split("#")[0].split("?")[0]
    if ref in ("", "./"): return os.path.join(DOCS, "index.html")
    path = os.path.normpath(os.path.join(page_dir, ref))
    return os.path.join(path, "index.html") if os.path.isdir(path) else path


def main():
    titles, canonicals, parsed = {}, {}, {}
    for slug, (title, desc, _, _) in build.PAGES.items():
        fn = os.path.join(DOCS, "index.html" if slug == "index" else slug + ".html")
        if not ok(os.path.isfile(fn), f"missing {fn}"): continue
        p = parsed[slug] = parse(fn)
        want = build.url(slug)
        ok(p.lang == "en", f"{slug}: html lang")
        ok(p.title == title, f"{slug}: title mismatch")
        ok(len(p.title) <= 60, f"{slug}: title {len(p.title)} chars (>60)")
        ok(70 <= len(p.meta.get("description", "")) <= 160, f"{slug}: description length {len(p.meta.get('description',''))}")
        ok("width=device-width" in p.meta.get("viewport", ""), f"{slug}: viewport")
        ok(p.canon == [want], f"{slug}: canonical {p.canon} != {want}")
        ok(p.prop.get("og:url") == want, f"{slug}: og:url")
        for k in ("og:title", "og:description", "og:image", "og:type", "og:site_name"):
            ok(bool(p.prop.get(k)), f"{slug}: missing {k}")
        ok(p.prop.get("og:title") == p.title, f"{slug}: og:title != title")
        ok(p.meta.get("twitter:card") == "summary_large_image", f"{slug}: twitter:card")
        for k in ("twitter:title", "twitter:description", "twitter:image"):
            ok(bool(p.meta.get(k)), f"{slug}: missing {k}")
        ok(p.prop.get("og:image") == build.OG_IMAGE, f"{slug}: og:image url")
        ok(p.meta.get("robots") is None, f"{slug}: must be indexable")
        ok(sum(1 for t, _ in p.h if t == "h1") == 1, f"{slug}: need exactly one h1")
        ok(p.title not in titles, f"{slug}: duplicate title with {titles.get(p.title)}"); titles[p.title] = slug
        ok(want not in canonicals, f"{slug}: duplicate canonical"); canonicals[want] = slug
        ok(len(p.ld) == 1, f"{slug}: expected one JSON-LD block")
        try:
            data = json.loads(p.ld[0]); ok(data.get("@context") == "https://schema.org", f"{slug}: JSON-LD context")
            types = [n["@type"] for n in data["@graph"]]
            ok("SoftwareSourceCode" in types, f"{slug}: JSON-LD SoftwareSourceCode")
            if slug == "faq":
                ok("FAQPage" in types, "faq: FAQPage JSON-LD")
                q = [n for n in data["@graph"] if n["@type"] == "FAQPage"][0]["mainEntity"]
                ok(len(q) >= 8 and all(x["acceptedAnswer"]["text"] for x in q), "faq: JSON-LD questions/answers")
                ok(len(q) == open(fn, encoding="utf-8").read().count("<details"), "faq: JSON-LD question count != visible questions")
        except Exception as e:
            ok(False, f"{slug}: JSON-LD invalid: {e}")

    # links / anchors / assets
    allpages = {s: p for s, p in parsed.items()}
    for slug, p in allpages.items():
        pdir = DOCS
        for ref in p.hrefs + p.srcs + [l for l in p.links if l and not l.startswith("http")]:
            if re.match(r"^(mailto:|javascript:)", ref): continue
            if ref.startswith(GH):
                rest = ref[len(GH):].split("#")[0]
                m = re.match(r"^/(blob|tree)/main/(.+)$", rest)
                if m: ok(os.path.exists(os.path.join(ROOT, m.group(2))), f"{slug}: GitHub link to missing repo path {m.group(2)}")
                continue
            if ref.startswith("http"):
                ok(ref.startswith("https://"), f"{slug}: non-https link {ref}")
                if ref.startswith(BASE): ok(ref in canonicals or ref.startswith(BASE + "assets/"), f"{slug}: unknown site URL {ref}")
                continue
            if ref.startswith("#"):
                ok(ref[1:] in p.ids, f"{slug}: anchor {ref} missing"); continue
            t = local_target(pdir, ref)
            if ok(os.path.exists(t), f"{slug}: broken link {ref}") and "#" in ref and t.endswith(".html"):
                frag = ref.split("#", 1)[1]
                ok(frag in parse(t).ids, f"{slug}: anchor {ref} missing in target")
        ok(p.imgs_no_alt == 0, f"{slug}: image without alt")
    for rel in ("assets/style.css", "assets/site.js", "assets/favicon.svg", "assets/og-image.png"):
        ok(os.path.isfile(os.path.join(DOCS, rel)), f"missing {rel}")

    # sitemap
    try:
        tree = ET.parse(os.path.join(DOCS, "sitemap.xml"))
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [e.text for e in tree.getroot().findall("s:url/s:loc", ns)]
        ok(sorted(locs) == sorted(canonicals), f"sitemap URLs differ from canonicals: {set(locs) ^ set(canonicals)}")
        ok(len(locs) == len(set(locs)), "sitemap duplicates")
        ok(all(l.startswith(BASE) and not l.endswith("404.html") for l in locs), "sitemap bad URL")
    except Exception as e:
        ok(False, f"sitemap invalid: {e}")
    robots = open(os.path.join(DOCS, "robots.txt")).read()
    ok(f"Sitemap: {BASE}sitemap.xml" in robots, "robots.txt must reference the sitemap")
    ok("Disallow: /" not in re.sub(r"Disallow:\s*\n", "", robots) or "Disallow: /\n" not in robots, "robots.txt blocks the site")
    p404 = parse(os.path.join(DOCS, "404.html"))
    ok(p404.meta.get("robots") == "noindex" and not p404.canon, "404: noindex and no canonical")
    ok(os.path.exists(os.path.join(DOCS, ".nojekyll")), "missing .nojekyll")

    # no stale claims / placeholders across generated pages
    for fn in os.listdir(DOCS):
        if fn.endswith(".html"):
            t = open(os.path.join(DOCS, fn), encoding="utf-8").read()
            ok("{{" not in t and "TODO" not in t, f"{fn}: unresolved placeholder")
            ok("http://" not in re.sub(r"http://www\.sitemaps\.org|http://www\.w3\.org", "", t), f"{fn}: insecure http link")
    # every shipped state-file template is documented on the architecture page
    arch = open(os.path.join(DOCS, "architecture.html"), encoding="utf-8").read()
    tdir = os.path.join(ROOT, ".claude", "skills", "auto-builder", "templates")
    for t in sorted(os.listdir(tdir)):
        ok(t in arch, f"architecture.html does not mention template {t}")
    # image size
    try:
        from PIL import Image
        ok(Image.open(os.path.join(DOCS, "assets/og-image.png")).size == (1280, 640), "og-image must be 1280x640")
    except ImportError:
        warnings.append("Pillow not installed: og-image size not checked")

    for w in warnings: print("WARN:", w)
    if errors:
        print(f"FAILED: {len(errors)} problem(s) in {checks} checks")
        for e in errors: print("  -", e)
        return 1
    print(f"OK: {checks} site checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
