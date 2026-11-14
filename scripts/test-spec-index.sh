#!/usr/bin/env bash
# Every decision record tracked in the tree must be named in spec/README.md's index (#268).
# The index is hand-maintained and is the only place that reads out which DR numbers are
# taken, so a record added without an index line is invisible to the next record author --
# which is exactly how DR-005 stayed unindexed across all seven of its commits.
#
#   scripts/test-spec-index.sh
#
# One-directional on purpose: a DR-NNN named in the index with no file in the tree is NOT a
# failure. The index legitimately refers to numbers claimed by open PRs (DR-004 lives only
# in PR #46), and those must not break the check.
#
# Untracked drafts under spec/decision-records/ are ignored (git ls-files, tracked only).
# Ends with a negative control: the same comparison against a scratch copy of the index with
# one DR mention stripped must report that record missing. The copy lives under mktemp -d;
# nothing is written into the tree. PDK-free. Needs bash, git, grep, sed.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
INDEX="spec/README.md"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT

# DR numbers of the tracked records, e.g. "DR-001".
records() {
  git ls-files 'spec/decision-records/DR-*.md' \
    | sed -nE 's#^spec/decision-records/(DR-[0-9]+)-.*\.md$#\1#p'
}

# compare <index-file> <label> -> 0 if every tracked record is mentioned, 1 otherwise.
compare() {
  local index="$1" label="$2" dr missing=0 n=0
  while read -r dr; do
    n=$((n + 1))
    if grep -q "${dr}" "${index}"; then
      echo "ok   ${label}${dr} in ${INDEX}"
    else
      echo "FAIL ${label}${dr} is tracked under spec/decision-records/ but not named in ${INDEX}"
      missing=$((missing + 1))
    fi
  done < <(records)
  echo "spec-index: ${label:-}${n} tracked records, ${missing} unindexed"
  [ "${n}" -gt 0 ] || { echo "FAIL ${label}no tracked decision records found -- check is vacuous"; return 1; }
  [ "${missing}" -eq 0 ]
}

bad=0
compare "${INDEX}" "" || bad=1

# Negative control: strip the first record's mentions from a scratch copy; the same
# comparison must then fail and name that record.
VICTIM="$(records | head -1)"
if [ -z "${VICTIM}" ]; then
  echo "FAIL negative control: no record to strip"
  bad=1
else
  sed "s/${VICTIM}//g" "${INDEX}" > "${T}/README.md"
  if out="$(compare "${T}/README.md" "negative control: " 2>&1)"; then
    echo "FAIL negative control: stripping ${VICTIM} from a copy of ${INDEX} still passed"
    bad=1
  elif printf '%s\n' "${out}" | grep -q "FAIL negative control: ${VICTIM} is tracked"; then
    echo "ok   negative control: stripping ${VICTIM} is caught"
  else
    echo "FAIL negative control: failed, but not for the stripped ${VICTIM}:"
    printf '%s\n' "${out}"
    bad=1
  fi
fi

exit "${bad}"
