#!/usr/bin/env bash
# PDK-free unit test for the OSDI pin block in scripts/lib-pdk.sh, run against a fabricated
# ihp-sg13g2 tree and sim/pins.json (no PDK install; NGSPICE is a stub that only answers
# --version). Asserts what the collapsed loop must keep true (issue #285):
#
#   - all three OSDI libraries (psp103, psp103_nqs, r3_cmc) are still hash-checked
#     independently, and a mismatch dies naming that library's own sim/pins.json key;
#   - a clean tree sets all three OSDI_* variables;
#   - PDK_SKIP_OSDI_PINS=1 skips all three checks and leaves all three variables unset;
#   - the retired spelling PDK_SKIP_PSP103=1 skips nothing. A stale flag name must fail
#     safe, towards more pin checking, never less;
#   - the model-library loop above the OSDI block is untouched.
#
# Every case asserts behaviour that predates the collapse except the two flag cases, which pin
# the renamed escape hatch and the fail-safe on its retired spelling.
#
#   scripts/test-lib-pdk.sh
set -uo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
ROOT="${T}/r"; PDK="${T}/pdk/ihp-sg13g2"
OSDI_DIR="${PDK}/libs.tech/ngspice/osdi"; MODELS_DIR="${PDK}/libs.tech/ngspice/models"
mkdir -p "${ROOT}/sim" "${MODELS_DIR}" "${OSDI_DIR}"
printf '#!/usr/bin/env bash\necho ngspice-47\n' > "${T}/ng"; chmod +x "${T}/ng"
h() { sha256sum "$1" | cut -d' ' -f1; }

# A fabricated PDK whose contents hash to a fabricated sim/pins.json. Written once; the
# cases below corrupt a file, assert, then restore it with fixture().
fixture() {
  printf 'cornerMOSlv\n' > "${MODELS_DIR}/cornerMOSlv.lib"
  local k; for k in psp103 psp103_nqs r3_cmc; do printf 'osdi-%s\n' "${k}" > "${OSDI_DIR}/${k}.osdi"; done
}
fixture
cat > "${ROOT}/sim/pins.json" <<EOF
{
  "pdk": { "release_tag": "v0-test",
           "model_libs_sha256": { "cornerMOSlv.lib": "$(h "${MODELS_DIR}/cornerMOSlv.lib")" } },
  "psp103":     { "osdi": "libs.tech/ngspice/osdi/psp103.osdi",
                  "osdi_sha256": "$(h "${OSDI_DIR}/psp103.osdi")" },
  "psp103_nqs": { "osdi": "libs.tech/ngspice/osdi/psp103_nqs.osdi",
                  "osdi_sha256": "$(h "${OSDI_DIR}/psp103_nqs.osdi")" },
  "r3_cmc":     { "osdi": "libs.tech/ngspice/osdi/r3_cmc.osdi",
                  "osdi_sha256": "$(h "${OSDI_DIR}/r3_cmc.osdi")" },
  "ngspice": { "version": "47" }
}
EOF

fail=0
# source lib-pdk.sh the way a bench driver does (set -euo pipefail, a die() that exits 1),
# then print the three variables it is documented to set. Extra args are env assignments.
# shellcheck disable=SC2016  # the bash -c body is deliberately single-quoted: it must expand
#                              in that subshell, against the env assignments, not out here.
run() { OUT="$(env ROOT="${ROOT}" PDK_ROOT="${T}/pdk" NGSPICE="${T}/ng" OMP_NUM_THREADS=2 \
    LIBPDK="${SRC}/scripts/lib-pdk.sh" "$@" bash -c '
      set -euo pipefail
      die() { echo "die: $*" >&2; exit 1; }
      # shellcheck disable=SC1090
      source "${LIBPDK}"
      echo "PSP=${OSDI_PSP:-unset} NQS=${OSDI_PSP_NQS:-unset} R3=${OSDI_R3:-unset}"' 2>&1)"
  RC=$?; }
ok() {   # ok <label> <expected-PSP=... line>
  if [ "${RC}" = 0 ] && printf '%s' "${OUT}" | grep -qxF "$2"; then echo "ok   $1"
  else echo "FAIL $1: rc=${RC}, want a line '$2', got:"; printf '%s\n' "${OUT}" | sed 's/^/       /'; fail=1; fi; }
dies() { # dies <label> <expected-substring>
  if [ "${RC}" != 0 ] && printf '%s' "${OUT}" | grep -qF "$2"; then echo "ok   $1"
  else echo "FAIL $1: rc=${RC}, want a die containing '$2', got:"; printf '%s\n' "${OUT}" | sed 's/^/       /'; fail=1; fi; }

SET_ALL="PSP=${OSDI_DIR}/psp103.osdi NQS=${OSDI_DIR}/psp103_nqs.osdi R3=${OSDI_DIR}/r3_cmc.osdi"

run; ok "clean tree sets all three OSDI_* variables" "${SET_ALL}"

# Each library is pinned on its own: corrupting one must die naming that one's pins.json key.
for k in psp103 psp103_nqs r3_cmc; do
  printf 'tampered\n' > "${OSDI_DIR}/${k}.osdi"
  run; dies "${k} mismatch is refused" "not the pinned ${k}.osdi"
  fixture
done

# A missing library is refused too. Only the non-zero exit is asserted, not a message: under
# the `set -euo pipefail` every driver sets, the failing sha256sum aborts the shell at the
# assignment, so the block's own "is missing" die text is unreachable. Pre-existing and left
# alone here (#285 is the duplication); tracked separately.
rm -f "${OSDI_DIR}/r3_cmc.osdi"
run
if [ "${RC}" != 0 ]; then echo "ok   a missing OSDI library is refused"
else echo "FAIL a missing OSDI library is refused: rc=0, output: ${OUT}"; fail=1; fi
fixture

# The escape hatch gates all three, and says so in its name.
for k in psp103 psp103_nqs r3_cmc; do printf 'tampered\n' > "${OSDI_DIR}/${k}.osdi"; done
run PDK_SKIP_OSDI_PINS=1; ok "PDK_SKIP_OSDI_PINS=1 skips all three and unsets all three" "PSP=unset NQS=unset R3=unset"
# Fail-safe: the retired spelling must not silently switch the pin checks off.
run PDK_SKIP_PSP103=1; dies "retired PDK_SKIP_PSP103=1 skips nothing" "not the pinned psp103.osdi"
fixture

# The model-library loop ahead of the OSDI block still refuses an unpinned PDK.
printf 'tampered\n' > "${MODELS_DIR}/cornerMOSlv.lib"
run; dies "an unpinned model library is refused" "not the pinned PDK"
fixture

exit "${fail}"
