#!/usr/bin/env bash
# Negative controls for scripts/fetch-vco.sh and its pointed wrappers. Runs in a scratch
# copy of the repo's lock + scripts; needs network for the fetch-path cases (the missing
# file case), none for --verify cases once .fetched/ exists, and none for the stubbed
# transient-retry cases (#348).
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
# fetch-vco.sh:81 -- the on-disk hash differs from the lock (no network in --verify).
expect "tampered file (--verify)" \
  "refuse:fetch-vco: MISMATCH .fetched/.*/${TAMPER}: lock [0-9a-f]{64}, on disk [0-9a-f]{64}" \
  "${F}" --verify
expect "re-fetch repairs tamper"       ok     "${F}"

# Lock edits.
lock() { jq --arg r "${REPO}" "(.imports[] | select(.from == \$r)) |= ($1)" "${ROOT}/reuse.lock.json" > "${T}/reuse.lock.json"; }
lock '.commit = "17e49a8"'
# fetch-vco.sh:33 -- the same refusal for a short SHA and for a ref.
expect "short commit refused" \
  "refuse:fetch-vco: error: commit '17e49a8' is not a full 40-hex SHA" "${F}"
lock '.commit = "main"'
expect "ref instead of SHA refused" \
  "refuse:fetch-vco: error: commit 'main' is not a full 40-hex SHA" "${F}"
lock '.mode = "vendored"'
# fetch-vco.sh:34
expect "non-fetched mode refused" \
  "refuse:fetch-vco: error: mode is 'vendored', expected 'fetched'" "${F}"
lock '.files[0].sha256 = ("0" * 64)'
# fetch-vco.sh:74 -- caught on the fetched bytes, before anything is installed.
expect "wrong sha256 refused" \
  "refuse:fetch-vco: MISMATCH .*: lock 0{64}, fetched [0-9a-f]{64}" "${F}"
lock '.files[0].upstream = "design/no-such-file.spice"'
# fetch-vco.sh:71
expect "missing file at commit refused" \
  "refuse:fetch-vco: design/no-such-file.spice missing or unreachable at [0-9a-f]{40}" "${F}"
cp "${ROOT}/reuse.lock.json" "${T}/reuse.lock.json"
FETCH_VCO_REPO=2AMLogic/not-in-lock FETCH_PLL_REPO=2AMLogic/not-in-lock \
  expect "import absent from lock refused" \
    "refuse:fetch-vco: error: .* must have exactly one import from 2AMLogic/not-in-lock \\(found 0\\)" \
    "${F}"

# Transient transport failure (#348): one blob blipping mid-fetch must not fail the
# deterministic gate. curl and gh are stubbed on PATH -- the stub curl dies with a
# transport error on its first call, then serves the blob -- so the case is offline,
# deterministic, and cannot pass without fetch_one's retry loop.
stub="${T}/stub-bin"; mkdir -p "${stub}"
printf '0' > "${stub}/count"
printf 'transient-retry stub blob\n' > "${stub}/blob"
cat > "${stub}/curl" <<'STUB'
#!/usr/bin/env bash
# Test stub, not a real fetch: fail once with a transport error, then serve the blob.
set -u
self="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
n="$(( $(cat "${self}/count" 2>/dev/null || echo 0) + 1 ))"; echo "${n}" > "${self}/count"
[ -f "${self}/always-fail" ] && n=1
if [ -f "${self}/always-404" ]; then
  echo "curl: (22) The requested URL returned error: 404" >&2
  exit 22
fi
dest=""
while [ $# -gt 0 ]; do
  case "$1" in -o) dest="$2"; shift 2 ;; *) shift ;; esac
done
if [ "${n}" = 1 ]; then
  echo "curl: (56) Recv failure: Connection reset by peer" >&2
  exit 56
fi
cp "${self}/blob" "${dest}"
STUB
cat > "${stub}/gh" <<'STUB'
#!/usr/bin/env bash
# Test stub: the gh leg must neither succeed nor touch the network.
if [ -f "$(dirname "${BASH_SOURCE[0]}")/always-404" ]; then echo "gh: Not Found (HTTP 404)" >&2; exit 1; fi
echo "gh: stub failure (HTTP 403)" >&2
exit 1
STUB
chmod +x "${stub}/curl" "${stub}/gh"
stub_sha="$(sha256sum "${stub}/blob" | cut -d' ' -f1)"
jq -n --arg sha "${stub_sha}" '{schema: 1, imports: [{from: "2AMLogic/stub-repo",
  commit: "4444444444444444444444444444444444444444", mode: "fetched",
  files: [{upstream: "stub.txt", local: ".fetched/stub-repo/stub.txt", sha256: $sha}]}],
  in_tree: []}' > "${T}/reuse.lock.json"
PATH="${stub}:${PATH}" FETCH_VCO_REPO=2AMLogic/stub-repo FETCH_PLL_REPO=2AMLogic/stub-repo \
  expect "transient transport failure retried ok" ok "${F}"
# Permanent failure: every attempt fails, so the bounded retries run out; the refusal
# keeps the "missing or unreachable at <commit>" form and names the last error (#348).
printf '0' > "${stub}/count"; : > "${stub}/always-fail"
PATH="${stub}:${PATH}" FETCH_VCO_REPO=2AMLogic/stub-repo FETCH_PLL_REPO=2AMLogic/stub-repo \
  expect "permanent failure names the last error" \
    "refuse:fetch-vco: stub\\.txt missing or unreachable at [0-9a-f]{40} \\(last error: curl: \\(56\\) Recv failure: Connection reset by peer" \
    "${F}"
rm -f "${stub}/always-fail"
# Permanent 404 (a bad pin) must not burn the retry loop: one curl call, no backoff sleep.
printf '0' > "${stub}/count"; : > "${stub}/always-404"
s0=${SECONDS}
PATH="${stub}:${PATH}" FETCH_VCO_REPO=2AMLogic/stub-repo FETCH_PLL_REPO=2AMLogic/stub-repo \
  expect "permanent 404 fails fast" \
    "refuse:fetch-vco: stub\\.txt missing or unreachable at [0-9a-f]{40} \\(last error: curl: \\(22\\) The requested URL returned error: 404" \
    "${F}"
if [ "$(cat "${stub}/count")" = 1 ] && [ $((SECONDS - s0)) -lt 2 ]; then
  echo "PASS 404 not retried (1 attempt)"; pass=$((pass+1))
else echo "FAIL 404 retried (attempts=$(cat "${stub}/count"), $((SECONDS - s0))s)"; bad=$((bad+1)); fi
rm -f "${stub}/always-404"

expect_summary || exit 1
