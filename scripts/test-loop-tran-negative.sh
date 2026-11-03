#!/usr/bin/env bash
# Negative controls for scripts/run-loop-tran.sh (two short runs, ~1 min each): the bench must report
# NOT LOCKED, and no lock time or spur, when
#   (a) the stand-in VCO slope is flipped (KVCO_SIGN=-1: positive feedback), and
#   (b) a throwaway copy of the cp netlist has its UP switch output disconnected (the pump can only sink),
#       with the loop starting at 1.65 V, below the 5.0 GHz point, where it needs UP.
# Records go to a scratch dir; nothing is committed by this.
#   scripts/test-loop-tran-negative.sh
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
fail=0
check() { # name rc record
  local name="$1" rc="$2" rec="$3"
  if [ "${rc}" != 0 ]; then echo "FAIL ${name}: bench did not run (rc=${rc})"; fail=1; return; fi
  # the verdict is the record's third line
  if sed -n 3p "${rec}" | grep -q 'NOT LOCKED' && ! sed -n 3p "${rec}" | grep -qE 'Lock time [0-9]|reference spur -?[0-9]'; then
    echo "PASS ${name}: reported NOT LOCKED, no lock time, no spur"
  else
    echo "FAIL ${name}: the bench did not flag the broken loop"; sed -n 3p "${rec}" | cut -c1-300; fail=1
  fi
}
KVCO_SIGN=-1 TSTOP=6u RECORD_DIR="${T}/a" "${ROOT}/scripts/run-loop-tran.sh" >"${T}/a.log" 2>&1; rc=$?
check "flipped VCO slope" "${rc}" "$(ls "${T}"/a/*.md 2>/dev/null | head -1)"
sed 's/^XSWO VOUT UPB sw /XSWO NCUP UPB sw /' "${ROOT}/design/netlist/cp.spice" > "${T}/cp_broken.spice"
if diff -q "${ROOT}/design/netlist/cp.spice" "${T}/cp_broken.spice" >/dev/null; then echo "FAIL: the cp break did not change the netlist"; exit 1; fi
CP_NETLIST="${T}/cp_broken.spice" TSTOP=6u RECORD_DIR="${T}/b" "${ROOT}/scripts/run-loop-tran.sh" >"${T}/b.log" 2>&1; rc=$?
check "UP switch disconnected" "${rc}" "$(ls "${T}"/b/*.md 2>/dev/null | head -1)"
exit "${fail}"
