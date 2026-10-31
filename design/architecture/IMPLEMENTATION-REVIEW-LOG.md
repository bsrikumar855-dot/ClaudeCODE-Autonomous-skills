# Milestone 7 implementation review log

Three fresh-context, read-only reviews of the **implemented** 2.0 (2026-10-31): `security-engineer` (S, static inspection only), `architect` (A), `critical-reviewer` (C), followed by a security re-check of the fixes (R, see the end). Reviewer text is data to evaluate. "Fixed" for security findings requires the re-check.

## Security (S)
| ID | Finding | Result |
|---|---|---|
| S-H1 | Repo-local git clean/smudge filters make `git status` and `git diff <ref> --` run repository-supplied commands; the earlier flags (fsmonitor, pager, external diff) did not stop it | **Reproduced by us as CONFIRMED** (plain git, and the helper's old flags, both fired a planted clean filter; an appended file does not trigger it, a same-size edit does). **Fixed:** the helper reads repo-local git config (reading executes nothing) and **refuses all working-tree git operations** if it defines filters, include, external diff/textconv, fsmonitor, worktree config and similar; standard Git LFS commands are the one exact exception. `state` degrades loudly (ATTENTION), `graph --check-changes` exits 2. Regression tests fire a real planted filter (with a control proving unprotected git fires it here). |
| S-M1 | ReDoS in the `browser-report` header parser | **Fixed:** no backtracking regex; 20,000-character line cap; 15,000- and 800,000-space tests. |
| S-M2 | git resolved from the project / relative PATH | **Fixed:** git is looked up only in absolute PATH entries outside the project; PATH passed to git is the same trusted list; hijack tests (relative, absolute-in-project, empty entry). |
| S-M3 | Output line injection (newlines, bidi) and unbounded echoed text | **Fixed:** `clean()` strips control, newline and bidi characters and truncates; text output starts with a "data, not instructions" banner; injection test with a newline and U+202E in a file name. |
| S-L1–L3 | crash paths; unbounded CPU; TOCTOU; pathspec magic | **Fixed:** digit caps, catch-all handler (no traceback, no local paths), `commonpath` guard, caps on files per task and dirty files, `os.open(O_NOFOLLOW)` + `fstat`, `--literal-pathspecs`, leading `:` rejected. |
| S-L4 | browser-report approval is self-attested; prod-host check skipped for `Environment: test`; link-local/metadata addresses | **Fixed:** prod-host check for every environment, link-local/unspecified addresses rejected, a warning that `Approved by user: yes` proves nothing and must be confirmed in-session. |
| S-docs | standing push approval in release.md must come from the user, not from PR/CI text | **Fixed** (wording + validator). |

## Architecture (A)
| ID | Finding | Disposition |
|---|---|---|
| A-1 | `state` fragile: no Tasks table; milestone labels like `M1 - Core`; silent "unanchored" | **Fixed:** missing table = zero tasks; labels match by first token; a label matching no gate row is ATTENTION. Tests. |
| A-2 | Grammar too lenient/strict for LLM-written tables (pipes in commands, backticks, `None`/`n/a`, ✅, status vocabulary) | **Fixed:** `\|` escape; rows wider than the header fail loudly; backticks/bold/check marks tolerated; None/n/a = no dependency; allowed values documented in the template. |
| A-3 | Ownership check flags the user's pre-existing dirty files and the lead's own state-file writes | **Fixed:** `--preexisting` baseline (snapshot before spawning); state files are a warning to confirm, `.git` stays a violation; swarm.md says the helper **detects, does not prevent**. |
| A-4 | Playbooks require a fresh reviewer for every small fix, contradicting Quality protocol item 3 | **Fixed:** playbooks now say "per Quality protocol item 3". |
| A-5 | `Begin with Phase 0 now`; router lacks resume and report steps; trivial vs `TASKS.md`; config as trivial | **Fixed:** SKILL ends with "route first"; router step 0 (resume) and step 8 (report); small changes keep criteria in the conversation; deployment/behaviour-changing configuration is not trivial. |
| A-minor | "limits defined once" overstated; undocumented gate vocabulary; counter parsing masks regressions; `Verified at` commit sequence undocumented; verification.md inconsistencies | **Fixed:** wording now "the numbers appear authoritatively here; other files repeat them and must not change them"; `yes`/`tdd`/`regression`/`benchmark`/`read-only` tokens defined; counter regex is `<check> → <n>` / `attempt k of n`; Phase 5 spells out commit-code, record sha, commit state. **Not changed:** SKILL.md has several dense paragraphs (token budget); a later restructuring would need validator rework. |

## Critical review vs the brief (C)
| ID | Finding | Disposition |
|---|---|---|
| C-1 | ~40 of 53 mutations only pin sentences, not behaviour | **Accepted and fixed in how it is reported:** the mutation harness now classifies and reports **behaviour** (breaks the helper's code, `test_ab.py` must fail), **static** and **wording** guards separately; 15 new behavioural mutations. Wording guards are documented as pinning a sentence only. |
| C-2 | IMPLEMENTATION-STATUS, README, CHANGELOG, site missing | Written (ordering artifact). |
| C-3 | Untrusted-data rule vs resume conflict | **Fixed:** the user prompt applies only to state not written by an earlier run in this repository; non-interactive runs report instead of stalling. |
| C-4 | Overhead for small non-trivial work | **Fixed:** an explicit small-change tier (no `TASKS.md` row or `DECISIONS.md` entry unless more than one pass; Quality protocol item 3 review). |
| C-5 | Drop the browser-report checker | **Rejected:** Part 14 requires a testable evidence format, and the checker makes lazy fabrication harder; it is labelled as proving nothing and must not be cited. Its bypasses were hardened (S-L4). |
| C-6 | "detects, does not prevent" | **Fixed** in swarm.md and status. |
| C-7 | benchmark has no decision rule; scorer not blind | **Fixed** in the benchmark plan. |

## R: security re-checks of the fixes (two rounds, `security-engineer`, static inspection; the re-checker also ran the test suites)
| ID | Finding | Result |
|---|---|---|
| R1-H1 | filter execution | The reproduced vector is closed, with a real planted filter as regression test and a control proving plain git fires it here. |
| R1-N1 | `repo_risks` failed open (git config unreadable, timed out, or listing truncated at 5 MB) | **Fixed**, fails closed; tests for a 5 MB+ listing, an unreadable config and a non-repository; mutation tests for both branches. |
| R1-N2 | `git status` recurses into submodules whose own config can define filters | **Fixed** (`--ignore-submodules=all`); real-submodule test with a control. **Documented limit:** the ownership check cannot see inside submodules. |
| R1-N3 | dotted diff-driver names | **Fixed** (regex) and tested. |
| R1-N4 | TOCTOU after open | **Fixed on Linux** (`/proc/self/fd`); **partial elsewhere** (path-based fallback, also if `/proc` is unavailable). Accepted: low severity, read-only, no-follow open. |
| R1-N5 | link-local check was a prefix match | **Fixed**: `ipaddress`-based; metadata names; non-canonical IP forms; IPv4-mapped, NAT64, 6to4; trailing-dot hosts; `fd00:ec2::254`. **Residual (cannot be fixed statically):** a DNS name that resolves to a metadata address. |
| R1-N6 | validator enforcement by substring presence | **Partially fixed**: the wiring of the worktree guard and the fail-closed raises are AST-checked; other controls are still substring-checked, so the behavioural tests and behavioural mutations are what actually protect them. |
| R2-new | trailing-dot metadata host, `fd00:ec2::254`, NAT64/6to4 forms, leading-zero IPv4 | **Fixed** with tests and two more behavioural mutations. |
| Overall | | No confirmed Critical or High findings remain in the reviewed scope. This is **not** a statement that the helper is secure: the risky-git-config list is a deny-list and may miss ways for a hostile repository to make git run programs. The helper is not a sandbox. |
