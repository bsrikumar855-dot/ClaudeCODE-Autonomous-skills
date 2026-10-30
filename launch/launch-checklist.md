# Launch and SEO checklist

## Before launch (you)
- [ ] Review the diff on branch `feat/launch-seo` (and `feat/auto-builder` if not yet merged); merge to `main`.
- [ ] Decide the first version number (see [release-notes-v1.0.0.md](release-notes-v1.0.0.md)).
- [ ] **Run `/auto-builder` yourself on a small throwaway project** and fix what you find; update the "not validated" wording only if it becomes untrue.
- [ ] If possible, run `install.ps1` on Windows (or ask a Windows user) and update the docs accordingly.
- [ ] Confirm CI is green on the launch PR and on `main` (CI already passed for PR #1 and the `main` merge; the new site steps run for the first time on the launch PR).
- [ ] Enable GitHub Pages (`main` + `/docs`) and open the site; click through every page.
- [ ] Set description, website, topics, social preview ([github-metadata.md](github-metadata.md)).
- [ ] Enable private vulnerability reporting.

## SEO checklist
- [x] Unique titles (≤60) and meta descriptions per page (checked by `site/check.py`)
- [x] Canonical URLs consistent with the GitHub Pages URL
- [x] Open Graph + Twitter/X cards with 1280×640 image
- [x] JSON-LD (SoftwareSourceCode, WebSite, WebPage/FAQPage, BreadcrumbList)
- [x] sitemap.xml with canonical URLs; robots.txt (note root-path limitation)
- [x] Semantic HTML, single h1, descriptive internal links, skip link, responsive
- [ ] Search Console property + sitemap submitted ([search-console.md](search-console.md))
- [ ] Verify indexing in Search Console before claiming it
- [ ] Add the site to the repo "Website" field and README (README already links it)
- [ ] Publish the DEV tutorial with `canonical_url` pointing at the site's usage page

## Release (you, after approval)
- [ ] Tag and create the GitHub release from the notes draft: `gh release create vX.Y.Z --title "AUTO-BUILDER vX.Y.Z" --notes-file launch/release-notes-v1.0.0.md` (**not run**)
- [ ] Post community drafts one at a time ([community-posts.md](community-posts.md)); be present to reply.

## After
- [ ] Triage issues using the templates; update the FAQ with recurring questions.
- [ ] Review Search Console queries after 2–4 weeks and adjust headings/content to real queries.
