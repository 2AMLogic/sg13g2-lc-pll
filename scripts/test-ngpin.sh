#!/usr/bin/env bash
# Negative control for the ngspice pin check (scripts/lib-ngpin.sh): with a stubbed NGSPICE
# whose --version differs from sim/pins.json, a real run-cp-dc.sh record must carry the
# mismatch line and the run must still complete; a stub at the pinned version must say
# "matches pin"; a stub with no ngspice-N string must not crash the check under set -e.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
REAL="${NGSPICE:-$(command -v ngspice)}"
PIN="$(jq -r .ngspice.version "${ROOT}/sim/pins.json")"
stub() { # stub <version-output> -> path; every other invocation runs the real ngspice
  printf '#!/usr/bin/env bash\n[ "${1:-}" = "--version" ] && { echo %q; exit 0; }\nexec %q "$@"\n' "$1" "${REAL}" > "${T}/ng-$2"
  chmod +x "${T}/ng-$2"; echo "${T}/ng-$2"; }
fail=0
check() { # check <label> <version-output> <expected-substring>
  local ng; ng="$(stub "$2" "$1")"
  local st; st="$(PINS="${ROOT}/sim/pins.json" NGSPICE="${ng}" bash -c 'set -euo pipefail
    NG_VER="$("${NGSPICE}" --version 2>&1 | grep -o "ngspice-[0-9.]*" | head -1 || true)"
    source "$1"; echo "${NG_PIN_STATUS}"' _ "${ROOT}/scripts/lib-ngpin.sh" 2>/dev/null)" \
    || { echo "FAIL ($1): the pin check crashed"; fail=1; return; }
  case "${st}" in *"$3"*) echo "PASS ($1): ${st}";; *) echo "FAIL ($1): got '${st}', want '*$3*'"; fail=1;; esac; }
check match "ngspice-${PIN}" "matches pin"
check mismatch "ngspice-99" "Pin check: ngspice-99 != pinned ${PIN} (mismatch)"
check nostring "no version here" "Pin check: ngspice-unknown != pinned ${PIN} (mismatch)"
# End to end through the real lib-pdk.sh: the run still completes and the record carries the line.
e2e() { # e2e <label> <version-output> <expected-record-text>
  local ng out rc rec; ng="$(stub "$2" "e2e-$1")"
  out="$(NGSPICE="${ng}" RECORD_DIR="${T}/rec-$1" "${ROOT}/scripts/run-cp-dc.sh" 2>&1)"; rc=$?
  [ "${rc}" = 0 ] || { echo "${out}"; echo "FAIL (e2e $1): bench did not run (rc=${rc})"; fail=1; return; }
  rec="$(ls "${T}"/rec-"$1"/*.md | head -1)"
  if grep -qF "**Pin check**: $3" "${rec}"; then echo "PASS (e2e $1): record carries '$3'"
  else echo "FAIL (e2e $1): record lacks '$3'"; fail=1; fi; }
e2e mismatch "ngspice-99" "Pin check: ngspice-99 != pinned ${PIN} (mismatch)"
e2e nostring "no version here" "Pin check: ngspice-unknown != pinned ${PIN} (mismatch)"
exit "${fail}"
