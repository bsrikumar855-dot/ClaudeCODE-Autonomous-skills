# Google Search Console setup

Do this only after the site is live (merged to `main` and Pages enabled). Do not state the site is indexed until Search Console confirms it.

1. Open <https://search.google.com/search-console> and sign in with the Google account that should own the property.
2. **Add property → URL prefix** and enter exactly:
   `https://bsrikumar855-dot.github.io/ClaudeCODE-Autonomous-skills/`
   (Domain properties require DNS control, which you don't have for `github.io`.)
3. **Verify ownership** with the *HTML tag* method: Search Console gives a `<meta name="google-site-verification" content="…">` tag. Add it inside `<head>` of the home page by putting it in `site/build.py`'s template (or ask me to add it), rebuild with `python3 -I site/build.py`, commit, and deploy. Click **Verify**. (The *HTML file* method also works: place the provided file in `docs/`.) Don't share the token publicly beyond the page itself.
4. **Submit the sitemap:** Sitemaps → enter `sitemap.xml` → Submit. Expected status "Success" and 6 discovered URLs (home, features, installation, usage, architecture, faq).
5. **Request indexing (optional):** URL Inspection → paste the home page URL → *Request indexing*. Repeat for key pages. This is a request, not a guarantee.
6. **Check** after a few days: Pages → indexed vs not indexed (reasons are listed), Performance → queries. Mobile usability and Core Web Vitals reports appear once there is enough data.
7. Optionally add the same URL in **Bing Webmaster Tools** (it can import from Search Console).

Troubleshooting: "Discovered – currently not indexed" is common for new sites and usually resolves with time and internal/external links; don't resubmit repeatedly.
