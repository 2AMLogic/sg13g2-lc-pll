#!/usr/bin/env bash
# Negative controls for scripts/fetch-pll.sh (the sg13g2-pll PFD pin). Runs in a scratch
# copy of the repo's lock + scripts; needs network for the fetch-path cases.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
mkdir -p "${T}/scripts"
cp "${ROOT}/scripts/fetch-vco.sh" "${ROOT}/scripts/fetch-pll.sh" "${T}/scripts/"
pass=0; bad=0
expect() { # <name> <want: ok|refuse> <cmd...>
  local name="$1" want="$2"; shift 2
  "$@" >"${T}/out" 2>&1; local rc=$?
  if { [ "${want}" = ok ] && [ "${rc}" = 0 ]; } || { [ "${want}" = refuse ] && [ "${rc}" != 0 ]; }; then
    echo "PASS ${name} (rc=${rc})"; pass=$((pass+1))
  else echo "FAIL ${name} (rc=${rc})"; sed 's/^/    /' "${T}/out"; bad=$((bad+1)); fi
}
F="${T}/scripts/fetch-pll.sh"
cp "${ROOT}/reuse.lock.json" "${T}/reuse.lock.json"
expect "fetch pinned files"            ok     "${F}"
expect "verify clean tree"             ok     "${F}" --verify

# Tamper: flip one byte of the fetched PFD schematic.
f="${T}/.fetched/sg13g2-pll/design/pfd.sch"
printf 'X' | dd of="${f}" bs=1 seek=10 conv=notrunc 2>/dev/null
expect "tampered file (--verify)"      refuse "${F}" --verify
expect "re-fetch repairs tamper"       ok     "${F}"

# Lock edits (index of the sg13g2-pll import, not assumed to be 0).
lock() { jq --arg r 2AMLogic/sg13g2-pll "(.imports[] | select(.from == \$r)) |= ($1)" "${ROOT}/reuse.lock.json" > "${T}/reuse.lock.json"; }
lock '.commit = "83e59fe"'
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
FETCH_PLL_REPO=2AMLogic/not-in-lock expect "import absent from lock refused" refuse "${F}"

echo "${pass} passed, ${bad} failed"
[ "${bad}" = 0 ]
