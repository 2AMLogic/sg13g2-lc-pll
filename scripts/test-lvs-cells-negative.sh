#!/usr/bin/env bash
# Per-cell LVS negative control (#343): `klt lvs` reads `status: match` for the routed
# lcpll_loopfilter and lcpll_cp cells against their own .subckt references. A compare that
# cannot fail would not be evidence, so this control corrupts a scratch copy of each
# reference -- ONE device card gets one of its nets swapped for another net of the same
# subckt (a single-line edit; swapping two net NAMES token-for-token is not a control at
# all: it renames both sides of every connection and the comparer, which pairs top-level
# pins positionally, still matches) -- and the same request must flip to `mismatch`. The
# scratch copy lives in a mktemp dir and is never committed: nothing in design/netlist/ is
# touched, and the committed envelopes re-hash the uncorrupted files (klt lvs --check).
#
#   scripts/test-lvs-cells-negative.sh
#
# Needs klt carrying the per-cell subckt-call compare (klayout-tools#6960's diagnostics)
# and the repo's layout present. Like scripts/test-layout-cells.sh this does not run in
# .github/workflows/harness.yml (no PDK there); run it locally.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
pass=0; bad=0
ok()   { echo "PASS $1"; pass=$((pass+1)); }
fail() { echo "FAIL $1"; bad=$((bad+1)); }

negative() {  # <cell> <request (repo-relative)> <netlist (repo-relative)> <sed expr> <what>
  local cell="$1" request="$2" netlist="$3" expr="$4" what="$5"
  local swapped="${T}/${cell}.swap.spice" req="${T}/${cell}.negative.json" out="${T}/${cell}.negative.lvs.json"
  sed "${expr}" "${ROOT}/${netlist}" > "${swapped}"
  local changed
  changed="$(diff "${ROOT}/${netlist}" "${swapped}" | grep -c '^[<>]')"
  if [ "${changed}" = 0 ]; then
    fail "${cell}: '${expr}' changed nothing in ${netlist} (pattern drifted?)"
    return
  fi
  if [ "${changed}" != 2 ]; then   # one line replaced = one < and one > line
    fail "${cell}: '${expr}' rewrote $((changed / 2)) line(s) of ${netlist}, want exactly 1"
    return
  fi
  python3 - "${ROOT}/${request}" "${swapped}" "${req}" <<'PY'
import json, os, sys
req, netlist, out = sys.argv[1:4]
d = os.path.dirname(req)
r = json.load(open(req))
# a scratch request outside the cell directory must carry absolute input paths: the
# committed request's relative layout path resolves against the request file's location
r["reference"]["netlist"] = netlist   # scratch absolute path: this envelope is never committed
lf = r["layout"]["file"]
if not os.path.isabs(lf):
    r["layout"]["file"] = os.path.abspath(os.path.join(d, lf))
json.dump(r, open(out, "w"), indent=2)
PY
  klt lvs "${req}" --format json > "${out}" 2> "${T}/${cell}.err"
  local status
  status="$(python3 -c "import json; print(json.load(open('${out}'))['status'])" 2>/dev/null || echo no-envelope)"
  case "${status}" in
    mismatch) ok "${cell}: ${what} -> mismatch (the match can flip)" ;;
    *)        fail "${cell}: ${what} -> ${status} (want mismatch)" ;;
  esac
}

# XC2 from VIN to VCTRL: one capacitor of the input shunt moves onto the output net.
negative lcpll_loopfilter layout/lvs/cells/lcpll_loopfilter/request.json \
  design/netlist/loopfilter.spice \
  's/^XC2 VIN VSS/XC2 VCTRL VSS/' \
  "XC2's VIN node moved to VCTRL"
# XIUP_N's gate from UP to DN: the UP leg's input nfet now follows the DN input.
negative lcpll_cp layout/lvs/cells/lcpll_cp/request.json \
  design/netlist/cp.spice \
  's/^XIUP_N UPB UP /XIUP_N UPB DN /' \
  "XIUP_N's gate moved from UP to DN"

if [ "${bad}" = 0 ]; then echo "lvs cell negative controls: ${pass} passed, ${bad} failed"; fi
exit $((bad > 0))
