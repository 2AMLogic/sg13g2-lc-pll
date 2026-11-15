#!/usr/bin/env bash
# PDK-free unit test for scripts/lib-record.sh, in a scratch git repo.
#   scripts/test-lib-record.sh
set -uo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
ROOT="${T}/r"; mkdir -p "${ROOT}/design" "${ROOT}/sim/x/records" "${ROOT}/scripts"
die() { echo "die: $*" >&2; return 1; }
git -C "${ROOT}" init -q; git -C "${ROOT}" config user.email t@t; git -C "${ROOT}" config user.name t
touch "${ROOT}/design/a" "${ROOT}/sim/x/records/r0" "${ROOT}/scripts/s" "${ROOT}/reuse.lock.json"
git -C "${ROOT}" add -A; git -C "${ROOT}" commit -qm init
# shellcheck source=lib-record.sh
source "${SRC}/scripts/lib-record.sh"
bad=0
want() { # <name> <expected DIRTY> [pathspec...]
  local name="$1" exp="$2"; shift 2
  unset ID                       # record_stamp must set it, not inherit the previous call's
  record_stamp "$@"
  if [ "${DIRTY}" != "${exp}" ] || [ "${#COMMIT}" != 7 ]; then
    echo "FAIL ${name}: DIRTY='${DIRTY}' want '${exp}'"; bad=1; return
  fi
  # record_stamp owns the record ID (date-COMMITDIRTY), the filename stem of every
  # sim/*/records/<ID>.md and its sibling logs, so assert the format and the stamp it carries.
  if ! [[ "${ID:-}" =~ ^[0-9]{8}-[0-9]{6}-[0-9a-f]{7}(-dirty)?$ ]]; then
    echo "FAIL ${name}: ID='${ID:-<unset>}' does not match ^[0-9]{8}-[0-9]{6}-[0-9a-f]{7}(-dirty)?\$"; bad=1; return
  fi
  if [[ "${ID}" != *"${COMMIT}${DIRTY}" ]]; then
    echo "FAIL ${name}: ID='${ID}' does not end in COMMIT+DIRTY '${COMMIT}${DIRTY}'"; bad=1; return
  fi
  echo "ok   ${name}"
}
want "clean tree" ""
echo x > "${ROOT}/sim/x/records/r1"; want "new record only" ""
echo x > "${ROOT}/sim/x/negative-control-y"; want "negative-control only" ""
want "narrow pathspec, no change" "" sim scripts
echo x >> "${ROOT}/design/a"; want "design edit" "-dirty"
want "narrow pathspec ignores design edit" "" sim scripts
git -C "${ROOT}" checkout -q design/a
echo x >> "${ROOT}/reuse.lock.json"; want "lock edit" "-dirty"
git -C "${ROOT}" checkout -q reuse.lock.json
echo x > "${ROOT}/scripts/new"; want "untracked script" "-dirty"
rm "${ROOT}/scripts/new"; want "back to clean" ""
printf '* @@C@@ comment\nR1 a b 1\n' > "${T}/ok.spice"
printf 'R1 a b @@R@@\n' > "${T}/bad.spice"
if ( check_deck_placeholders "${T}/ok.spice" ) 2>/dev/null; then echo "ok   placeholder in comment passes"; else echo "FAIL comment placeholder rejected"; bad=1; fi
if ( check_deck_placeholders "${T}/bad.spice" ) 2>/dev/null; then echo "FAIL placeholder accepted"; bad=1; else echo "ok   placeholder in deck refused"; fi
write_spiceinit "${T}"; [ "$(cat "${T}/.spiceinit")" = "set ngbehavior=hsa" ] && echo "ok   spiceinit" || { echo "FAIL spiceinit"; bad=1; }
rec_dir zz; [ "${REC_DIR}" = "${ROOT}/sim/zz/records" ] && [ -d "${REC_DIR}" ] \
  && echo "ok   rec_dir default" || { echo "FAIL rec_dir default: REC_DIR='${REC_DIR}'"; bad=1; }
( RECORD_DIR="${T}/override" ; rec_dir zz; [ "${REC_DIR}" = "${T}/override" ] && [ -d "${REC_DIR}" ] ) \
  && echo "ok   rec_dir honours RECORD_DIR" || { echo "FAIL rec_dir ignored RECORD_DIR"; bad=1; }
exit "${bad}"
