#!/usr/bin/env bash
# Run every check the CI runs; exit non-zero if any fails. Use as a commit gate.
set -u
cd "$(dirname -- "${BASH_SOURCE[0]}")/.."
fail=0
run() { printf '%-52s' "$*"; out="$("$@" 2>&1)"; rc=$?; printf '%s\n' "$(printf '%s' "$out" | tail -1)"; [ $rc -eq 0 ] || { fail=1; printf '%s\n' "$out" | tail -15 | sed 's/^/    /'; }; }
run python3 -I tests/validate.py
run python3 -I tests/test_mutations.py
run python3 -I tests/test_ab.py
run bash tests/test-install.sh
python3 -I site/build.py >/dev/null 2>&1
printf '%-52s' "docs/ in sync with site/ (git diff)"; if git diff --quiet -- docs/ ':!docs/assets/og-image.png'; then echo "yes"; else echo "NO (uncommitted regenerated docs; commit them)"; fi
run python3 -I site/check.py
rm -rf site/__pycache__ tests/__pycache__
[ $fail -eq 0 ] && echo "ALL CHECKS PASSED" || echo "SOME CHECKS FAILED"
exit $fail
