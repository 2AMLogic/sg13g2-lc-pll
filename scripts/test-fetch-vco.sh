#!/usr/bin/env bash
# Negative controls for scripts/fetch-vco.sh and its pointed wrappers. Runs in a scratch
# copy of the repo's lock + scripts; needs network for the fetch-path cases (the missing
# file case), none for --verify cases once .fetched/ exists.
#
#   scripts/test-fetch-vco.sh                                              # the VCO pin
#   scripts/test-fetch-vco.sh 2AMLogic/sg13g2-pll fetch-pll.sh design/pfd.sch   # the PFD pin
#
# Arguments: <import repo as named in reuse.lock.json .from> <wrapper script under
# scripts/> <a fetched file, relative to .fetched/<repo name>/, to tamper with>.
# The lock entry is selected by `.from`, never by position.
set -uo pipefail
REPO="${1:-2AMLogic/sg13g2-vco}"
WRAP="${2:-fetch-vco.sh}"
TAMPER="${3:-design/vco.spice}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
mkdir -p "${T}/scripts"
cp "${ROOT}/scripts/fetch-vco.sh" "${T}/scripts/"
[ "${WRAP}" = fetch-vco.sh ] || cp "${ROOT}/scripts/${WRAP}" "${T}/scripts/"
# expect()/expect_summary and the pass/bad tally: see the contract in scripts/lib-expect.sh.
# Every negative control below is `refuse:<ERE>`, matching fetch-vco.sh's own refusal line for
# that case. A bare `refuse` would also pass on a missing jq, a wrapper copied without its +x
# bit or a parse error in fetch-vco.sh, i.e. while measuring nothing (#234) -- and this is the
# script scripts/ci-harness.sh runs, twice, over the pinned-reuse boundary.
# shellcheck source=lib-expect.sh
source "${ROOT}/scripts/lib-expect.sh"

F="${T}/scripts/${WRAP}"
cp "${ROOT}/reuse.lock.json" "${T}/reuse.lock.json"
expect "fetch pinned files"            ok     "${F}"
expect "verify clean tree"             ok     "${F}" --verify

# Tamper: flip one byte of a fetched file.
f="${T}/.fetched/${REPO#*/}/${TAMPER}"
printf 'X' | dd of="${f}" bs=1 seek=10 conv=notrunc 2>/dev/null
# fetch-vco.sh:66 -- the on-disk hash differs from the lock (no network in --verify).
expect "tampered file (--verify)" \
  "refuse:fetch-vco: MISMATCH .fetched/.*/${TAMPER}: lock [0-9a-f]{64}, on disk [0-9a-f]{64}" \
  "${F}" --verify
expect "re-fetch repairs tamper"       ok     "${F}"

# Lock edits.
lock() { jq --arg r "${REPO}" "(.imports[] | select(.from == \$r)) |= ($1)" "${ROOT}/reuse.lock.json" > "${T}/reuse.lock.json"; }
lock '.commit = "17e49a8"'
# fetch-vco.sh:30 -- the same refusal for a short SHA and for a ref.
expect "short commit refused" \
  "refuse:fetch-vco: error: commit '17e49a8' is not a full 40-hex SHA" "${F}"
lock '.commit = "main"'
expect "ref instead of SHA refused" \
  "refuse:fetch-vco: error: commit 'main' is not a full 40-hex SHA" "${F}"
lock '.mode = "vendored"'
# fetch-vco.sh:31
expect "non-fetched mode refused" \
  "refuse:fetch-vco: error: mode is 'vendored', expected 'fetched'" "${F}"
lock '.files[0].sha256 = ("0" * 64)'
# fetch-vco.sh:59 -- caught on the fetched bytes, before anything is installed.
expect "wrong sha256 refused" \
  "refuse:fetch-vco: MISMATCH .*: lock 0{64}, fetched [0-9a-f]{64}" "${F}"
lock '.files[0].upstream = "design/no-such-file.spice"'
# fetch-vco.sh:56
expect "missing file at commit refused" \
  "refuse:fetch-vco: design/no-such-file.spice missing or unreachable at [0-9a-f]{40}" "${F}"
cp "${ROOT}/reuse.lock.json" "${T}/reuse.lock.json"
FETCH_VCO_REPO=2AMLogic/not-in-lock FETCH_PLL_REPO=2AMLogic/not-in-lock \
  expect "import absent from lock refused" \
    "refuse:fetch-vco: error: .* must have exactly one import from 2AMLogic/not-in-lock \\(found 0\\)" \
    "${F}"

expect_summary || exit 1
