#!/usr/bin/env bash
# Negative controls for scripts/fetch-vco.sh. Runs in a scratch copy of the
# repo's lock + script; needs network for the fetch-path cases (the missing
# file case), none for --verify cases once .fetched/ exists.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
mkdir -p "${T}/scripts"
cp "${ROOT}/scripts/fetch-vco.sh" "${T}/scripts/"
pass=0; bad=0
expect() { # <name> <want: ok|refuse> <cmd...>
  local name="$1" want="$2"; shift 2
  "$@" >"${T}/out" 2>&1; local rc=$?
  if { [ "${want}" = ok ] && [ "${rc}" = 0 ]; } || { [ "${want}" = refuse ] && [ "${rc}" != 0 ]; }; then
    echo "PASS ${name} (rc=${rc})"; pass=$((pass+1))
  else echo "FAIL ${name} (rc=${rc})"; sed 's/^/    /' "${T}/out"; bad=$((bad+1)); fi
}

cp "${ROOT}/reuse.lock.json" "${T}/reuse.lock.json"
expect "fetch pinned files"            ok     "${T}/scripts/fetch-vco.sh"
expect "verify clean tree"             ok     "${T}/scripts/fetch-vco.sh" --verify

# Tamper: flip one byte of a fetched file.
f="${T}/.fetched/sg13g2-vco/design/vco.spice"
printf 'X' | dd of="${f}" bs=1 seek=10 conv=notrunc 2>/dev/null
expect "tampered file (--verify)"      refuse "${T}/scripts/fetch-vco.sh" --verify
expect "re-fetch repairs tamper"       ok     "${T}/scripts/fetch-vco.sh"

# Lock edits.
lock() { jq "$1" "${ROOT}/reuse.lock.json" > "${T}/reuse.lock.json"; }
lock '.imports[0].commit = "17e49a8"'
expect "short commit refused"          refuse "${T}/scripts/fetch-vco.sh"
lock '.imports[0].commit = "main"'
expect "ref instead of SHA refused"    refuse "${T}/scripts/fetch-vco.sh"
lock '.imports[0].mode = "vendored"'
expect "non-fetched mode refused"      refuse "${T}/scripts/fetch-vco.sh"
lock '.imports[0].files[0].sha256 = ("0" * 64)'
expect "wrong sha256 refused"          refuse "${T}/scripts/fetch-vco.sh"
lock '.imports[0].files[0].upstream = "design/no-such-file.spice"'
expect "missing file at commit refused" refuse "${T}/scripts/fetch-vco.sh"

echo "${pass} passed, ${bad} failed"
[ "${bad}" = 0 ]
