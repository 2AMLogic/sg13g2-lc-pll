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
pass=0; bad=0
expect() { # <name> <want: ok|refuse> <cmd...>
  local name="$1" want="$2"; shift 2
  "$@" >"${T}/out" 2>&1; local rc=$?
  if { [ "${want}" = ok ] && [ "${rc}" = 0 ]; } || { [ "${want}" = refuse ] && [ "${rc}" != 0 ]; }; then
    echo "PASS ${name} (rc=${rc})"; pass=$((pass+1))
  else echo "FAIL ${name} (rc=${rc})"; sed 's/^/    /' "${T}/out"; bad=$((bad+1)); fi
}

F="${T}/scripts/${WRAP}"
cp "${ROOT}/reuse.lock.json" "${T}/reuse.lock.json"
expect "fetch pinned files"            ok     "${F}"
expect "verify clean tree"             ok     "${F}" --verify

# Tamper: flip one byte of a fetched file.
f="${T}/.fetched/${REPO#*/}/${TAMPER}"
printf 'X' | dd of="${f}" bs=1 seek=10 conv=notrunc 2>/dev/null
expect "tampered file (--verify)"      refuse "${F}" --verify
expect "re-fetch repairs tamper"       ok     "${F}"

# Lock edits.
lock() { jq --arg r "${REPO}" "(.imports[] | select(.from == \$r)) |= ($1)" "${ROOT}/reuse.lock.json" > "${T}/reuse.lock.json"; }
lock '.commit = "17e49a8"'
expect "short commit refused"          refuse "${F}"
lock '.commit = "main"'
expect "ref instead of SHA refused"    refuse "${F}"
lock '.mode = "vendored"'
expect "non-fetched mode refused"      refuse "${F}"
lock '.files[0].sha256 = ("0" * 64)'
expect "wrong sha256 refused"          refuse "${F}"
lock '.files[0].upstream = "design/no-such-file.spice"'
expect "missing file at commit refused" refuse "${F}"
cp "${ROOT}/reuse.lock.json" "${T}/reuse.lock.json"
FETCH_VCO_REPO=2AMLogic/not-in-lock FETCH_PLL_REPO=2AMLogic/not-in-lock \
  expect "import absent from lock refused" refuse "${F}"

echo "${pass} passed, ${bad} failed"
[ "${bad}" = 0 ]
