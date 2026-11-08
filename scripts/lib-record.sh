# shellcheck shell=bash
# Sourced by the run-* bench drivers that write an append-only record under sim/*/records/: the one
# definition of the record's commit stamp, the unsubstituted-placeholder scan and the scratch .spiceinit.
# Consumers: `git grep -ln 'source.*lib-record.sh' -- scripts`. Expects ROOT and die() (as lib-pdk.sh does).
#
# "-dirty" means: the commit hash in a record does not describe the inputs, because tracked or untracked
# files under the stamp pathspec differ from HEAD. Records and negative-control outputs are excluded, so
# writing a record (or leaving a negative-control file) never marks the next one dirty.
#
# Stamp pathspec: every bench stamps RECORD_STAMP_PATHS (design sim scripts reuse.lock.json) except where it
# passes its own list, which must say why in the caller. Known differences:
#   run-jitter.sh        sim scripts only: method L reads sim/loop-model and the loop-filter json, no design/ file
#                        and no VCO pin (loop_model.py imports argparse/json/math/sys/pathlib/numpy only).
#   run-vco-smoke.sh     no repo stamp: its record ID is the pinned VCO commit from reuse.lock.json, not HEAD.
#   run-vco-prescaler-load.sh  keeps its own `git diff --quiet HEAD -- .` whole-tree stamp (stricter than the
#                        default, and it does not exclude records); not moved here to leave its IDs unchanged.

RECORD_STAMP_PATHS=(design sim scripts reuse.lock.json)

# record_stamp [pathspec...]  -> sets COMMIT (7-char HEAD) and DIRTY ("" or "-dirty"); ID is date-COMMITDIRTY.
# shellcheck disable=SC2034  # COMMIT and DIRTY are read by the sourcing driver
record_stamp() {
  local -a paths=("$@")
  [ "${#paths[@]}" -gt 0 ] || paths=("${RECORD_STAMP_PATHS[@]}")
  COMMIT="$(git -C "${ROOT}" rev-parse --short=7 HEAD)"
  DIRTY=""
  [ -z "$(git -C "${ROOT}" status --porcelain -- "${paths[@]}" ':(exclude)sim/*/records/*' ':(exclude)sim/*/negative-control-*' 2>/dev/null)" ] || DIRTY="-dirty"
}

# check_deck_placeholders <file>...  -> die() if any non-comment line still holds an @@PLACEHOLDER@@.
check_deck_placeholders() {
  local f
  for f in "$@"; do
    if grep -vE '^[[:space:]]*\*' "${f}" | grep -q '@@'; then die "unsubstituted placeholder left in $(basename "${f}")"; fi
  done
}

# write_spiceinit <dir>  -> the scratch .spiceinit every bench runs ngspice with.
write_spiceinit() { printf 'set ngbehavior=hsa\n' > "$1/.spiceinit"; }
