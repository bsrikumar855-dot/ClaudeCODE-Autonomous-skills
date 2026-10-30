# Merge and publication checklist

State when written (2026-10-30), verified from git and the GitHub API:
- `feat/auto-builder` was merged on GitHub as PR #1 (merge commit `7b9d42d`); `origin/main` already contains the AUTO-BUILDER skill, 8 agents, installers, hooks and tests, and its tree is identical to `feat/auto-builder`.
- `feat/launch-seo` is based on `56ce411` (the head of PR #1, an ancestor of `main`). **It has no commits of its own: all launch work is uncommitted in the working tree.** The launch changes apply cleanly to `origin/main` (checked with `git apply --check`; `main` has no changes to the four modified files).
- The repository has no description, homepage or topics, and GitHub Pages is **not enabled** (`has_pages: false`).
- The CI workflow ran and passed on GitHub for PR #1 and for the merge to `main` (original two-step version).

## A. Merge the launch work (you)
- [ ] Review `git diff origin/main` plus the untracked files (`site/`, `docs/`, `launch/`, `SECURITY.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`).
- [ ] Commit on `feat/launch-seo` (not yet done). Note: `git config user.name/email` are set repo-locally to your GitHub handle/email.
- [ ] Update local `main`: it is 2 commits behind (`git switch main && git pull --ff-only`), then optionally `git rebase origin/main feat/launch-seo`. A rebase is not required; there are no conflicts.
- [ ] Push `feat/launch-seo` and open a PR **into `main`** (not into `feat/auto-builder`, which is already merged).
- [ ] Wait for CI on the PR. The two new steps (site up-to-date check, site checks) run on GitHub for the first time here; they passed in a clean local emulation.
- [ ] Merge the PR.

## B. Enable and verify GitHub Pages (you, after A)
- [ ] Settings → Pages → Deploy from a branch → `main` → `/docs` (or the `gh api` command in [github-metadata.md](github-metadata.md)).
- [ ] Open `https://bsrikumar855-dot.github.io/ClaudeCODE-Autonomous-skills/` and click through all six pages and the 404 page. **Verify the exact-case URL serves 200**: the repo name is mixed-case and I could not verify Pages' path-case behaviour. If it does not, canonical URLs and the sitemap must be changed.
- [ ] Check that CSS, favicon and the social image load, and view a page in a phone-width window.
- [ ] Confirm the canonical, `og:url` and sitemap URLs match the URL that actually serves.

## C. Repository settings (you)
- [ ] Description, website, topics ([github-metadata.md](github-metadata.md)).
- [ ] Upload the social preview (`docs/assets/og-image.png`, Settings → General → Social preview).
- [ ] Security → enable *Private vulnerability reporting* (SECURITY.md assumes it).
- [ ] Optional: enable Discussions.

## D. Search Console (you, after B)
- [ ] Follow [search-console.md](search-console.md): add a URL-prefix property, verify (HTML tag or file), submit `sitemap.xml`.
- [ ] Do not state the site is indexed until Search Console shows it.

## E. Before any public announcement (you)
- [ ] Run `/auto-builder` on a small throwaway project in real Claude Code; note what breaks. This is the main unverified area.
- [ ] If possible, run `install.ps1` on Windows.
- [ ] Decide the version (see below) and, if it changes, edit `CHANGELOG.md` and `metadata.version` in `SKILL.md`, then run `python3 -I site/build.py`.
- [ ] Create the release only with your approval, e.g. `gh release create v0.1.0 --prerelease --title "AUTO-BUILDER v0.1.0" --notes-file launch/release-notes-v1.0.0.md` after editing the notes' title/version (**not run**).
- [ ] Post community drafts one at a time ([community-posts.md](community-posts.md)), after reading each community's current rules.

## Version recommendation: **v0.1.0 (preview / pre-release)**
Evidence for stability is limited to: static validation, installer and hook tests, website checks, three CI runs, and an independent multi-agent review. There is **no** live end-to-end run of the skill, no executed Windows installer, no external users. That supports a clearly-labelled preview, not 1.0.0. Mark the GitHub release as a pre-release. Reconsider 1.0.0 after real sessions and at least one external try-out.

## Known follow-ups (not blockers)
- `SKILL.md` documents declining the *branch* but not declining commits. The docs now say only "no branch"; consider one sentence in `SKILL.md` Phase 5 (a skill change, so do it deliberately and re-validate).
- Optional CI hardening: pin `actions/checkout` to a commit SHA and add `timeout-minutes`.
- The fact-check pass over the launch copy was done by me directly (a delegated reviewer was stopped before reporting); a second human read of `launch/` is advised.
- Tutorial step uses the project-install path for `init-artifacts.sh`; personal installs have it under `~/.claude/skills/auto-builder/scripts/`.
