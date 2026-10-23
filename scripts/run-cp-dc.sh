#!/usr/bin/env bash
# Charge-pump static current bench: ONE local ngspice, ONE .dc sweep of V_out 1.0 -> 3.3 V
# at the typical corner and nominal supply; UP and DN each forced on in their own copy.
# Writes a dated append-only record under sim/cp-dc/records/. Not a corner grid (that goes
# through `klt sim`), and row 7 is NOT graded here.
#
#   scripts/run-cp-dc.sh
#
# Environment:
#   PDK_ROOT     parent of ihp-sg13g2/ (default: first of ~/share/pdk, /usr/share/pdk, /usr/local/share/pdk)
#   NGSPICE      ngspice binary (default: ngspice on PATH)
#   CP_NETLIST   cp netlist to simulate (default design/netlist/cp.spice); a different file is
#                recorded by path and sha256 (used by scripts/test-cp-dc-negative.sh)
#   RECORD_DIR   record directory (default sim/cp-dc/records)
#
# Exit 0 if the run completed and the record was written (the verdict is in the record);
# non-zero if the PDK is not the pinned one, ngspice failed, or the sweep is incomplete.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { echo "run-cp-dc: error: $*" >&2; exit 1; }
source "${ROOT}/scripts/lib-pdk.sh"

CP_NETLIST="${CP_NETLIST:-${ROOT}/design/netlist/cp.spice}"
[ -f "${CP_NETLIST}" ] || die "${CP_NETLIST} not found"
"${ROOT}/design/netlist.sh" --check >/dev/null 2>&1 || {
  [ "${CP_NETLIST}" != "${ROOT}/design/netlist/cp.spice" ] || die "design/netlist/cp.spice is stale against design/cp.sch (run design/netlist.sh)"
}
REC_DIR="${RECORD_DIR:-${ROOT}/sim/cp-dc/records}"; mkdir -p "${REC_DIR}"
WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT

sed -e "s|@@MODELS_DIR@@|${MODELS}|g" -e "s|@@OSDI_PSP@@|${OSDI_PSP}|g" \
    -e "s|@@CP_NETLIST@@|${CP_NETLIST}|g" -e "s|@@DATA_OUT@@|${WORK}/cp_dc.data|g" \
    "${ROOT}/sim/cp-dc/cp_dc.spice.tmpl" > "${WORK}/cp_dc.spice"
if grep -vE '^[[:space:]]*\*' "${WORK}/cp_dc.spice" | grep -q '@@'; then die "unsubstituted placeholder left in the deck"; fi
printf 'set ngbehavior=hsa\n' > "${WORK}/.spiceinit"

COMMIT="$(git -C "${ROOT}" rev-parse --short=7 HEAD)"
DIRTY=""; [ -z "$(git -C "${ROOT}" status --porcelain -- design sim scripts reuse.lock.json ':(exclude)sim/*/records/*' ':(exclude)sim/*/negative-control-*' 2>/dev/null)" ] || DIRTY="-dirty"
ID="$(date -u +%Y%m%d-%H%M%S)-${COMMIT}${DIRTY}"
REC="${REC_DIR}/${ID}.md"
[ ! -e "${REC}" ] || die "${REC} exists; records are append-only"

set +e
( cd "${WORK}" && HOME="${WORK}" "${NGSPICE}" -b cp_dc.spice ) > "${WORK}/ngspice.log" 2>&1
NG_RC=$?
set -e
cp "${WORK}/ngspice.log" "${REC_DIR}/${ID}-ngspice.txt"
[ -s "${WORK}/cp_dc.data" ] || { echo "run-cp-dc: ngspice produced no data (rc=${NG_RC}); see ${REC_DIR}/${ID}-ngspice.txt" >&2; exit 1; }

ICP_NOM=200e-6; TOL=2.0
# cols: V, i(VA), V, i(VMB).  mismatch % = |I_up - I_dn| / I_cp,nom * 100
TABLE="$(awk -v icp="${ICP_NOM}" '{ iu=$2; id=$4; printf "%.2f %.3f %.3f %.3f\n", $1, iu*1e6, id*1e6, (iu>id?iu-id:id-iu)/icp*100 }' "${WORK}/cp_dc.data")"
NPTS="$(printf '%s\n' "${TABLE}" | wc -l)"
[ "${NPTS}" = 47 ] || { echo "run-cp-dc: expected 47 sweep points, got ${NPTS}" >&2; exit 1; }
# Window: the contiguous run of points with mismatch <= TOL that contains 1.65 V, extended both ways.
read -r V_LO V_TOP IN165 < <(printf '%s\n' "${TABLE}" | awk -v tol="${TOL}" '
  { v[NR]=$1; m[NR]=$4; if ($1 > 1.649 && $1 < 1.651) k=NR }
  END { if (!k || m[k] > tol) { print "NA NA 0"; exit }
        lo=k; while (lo>1 && m[lo-1] <= tol) lo--
        hi=k; while (hi<NR && m[hi+1] <= tol) hi++
        printf "%.2f %.2f 1\n", v[lo], v[hi] }')
MAXM_165_TOP="$(printf '%s\n' "${TABLE}" | awk -v lo=1.65 -v hi="${V_TOP}" 'hi!="NA" && $1>=lo-1e-6 && $1<=hi+1e-6 && $4>mx {mx=$4} END{printf "%.3f", mx}')"
MIS_AT() { printf '%s\n' "${TABLE}" | awk -v x="$1" '$1>x-1e-6 && $1<x+1e-6 {print $4}'; }

CPSHA="$(sha256sum "${CP_NETLIST}" | cut -d' ' -f1)"
{
  echo "# cp-dc run ${ID}"
  echo
  if [ "${IN165}" = 1 ]; then
    echo "**Result: measured mismatch <= ${TOL} % window = ${V_LO} V to ${V_TOP} V** (contiguous around 1.65 V; mismatch at 1.65 V = $(MIS_AT 1.65) %). **Spec row 7 is NOT graded here.**"
  else
    echo "**Result: mismatch at 1.65 V exceeds ${TOL} % ($(MIS_AT 1.65) %); no window around 1.65 V.** **Spec row 7 is NOT graded here.**"
  fi
  echo
  echo "- **Scope**: typical corner (\`mos_tt\`) only, 27 C, nominal 3.3 V supply, one nominal I_cp = 200 uA. No corner grid, no Monte Carlo. **Spec row 7 is not graded:** its upper bound V_hi,req needs the VCO's graded f(Vctrl) curve (gate G4), which does not exist yet. This record lists only the measured window. The numbers are **simulated, not measured**."
  echo "- **Netlist**: \`${CP_NETLIST#"${ROOT}/"}\` sha256 \`${CPSHA}\`$([ "${CP_NETLIST}" = "${ROOT}/design/netlist/cp.spice" ] && echo ', checked against design/cp.sch with design/netlist.sh --check' || echo ' (NOT the committed netlist: an override, see CP_NETLIST)')"
  echo "- **Deck**: \`sim/cp-dc/cp_dc.spice.tmpl\` sha256 \`$(sha256sum "${ROOT}/sim/cp-dc/cp_dc.spice.tmpl" | cut -d' ' -f1)\`, placeholder substitution only"
  echo "- **PDK**: IHP-Open-PDK $(jq -r .pdk.release_tag "${PINS}") (model libraries hash-checked against \`sim/pins.json\`); PDK_ROOT \`${PDK_ROOT}\`; PSP103 OSDI \`psp103.osdi\` sha256 \`$(jq -r .psp103.osdi_sha256 "${PINS}")\` (pinned)"
  echo "- **Simulator**: \`${NG_VER}\` (\`${NGSPICE}\`), one local \`ngspice -b\`, exit status ${NG_RC}; scratch \`.spiceinit\` = \`set ngbehavior=hsa\`"
  echo "- **Commit**: \`${COMMIT}${DIRTY}\` of this repository"
  echo "- **Method**: one \`.dc\` sweep of V_out, 1.0 V to 3.3 V in 0.05 V steps (${NPTS} points). Two copies of \`cp\` in the same deck: copy A has UP=1, DN=0 (I_up = current it sources into the output node); copy B has UP=0, DN=1 (I_dn = current it sinks), its output tied to copy A's by a unity VCVS. IREF = 20 uA into each copy (I_cp = ~10 x IREF; 100-400 uA is IREF 10-40 uA, not exercised here)."
  echo "- **Mismatch definition**: mismatch (%) = |I_up - I_dn| / I_cp,nom x 100, with I_cp,nom = 200 uA (spec row 6 typical), at the same V_out. It is a static DC quantity: no switching, no charge sharing, no pulse-width effect."
  echo "- **Window definition**: the contiguous run of sweep points with mismatch <= ${TOL} % that contains 1.65 V, extended up and down; V_top is its upper end. Endpoints are not clipped: points outside compliance are reported as measured."
  echo "- **Host**: $(hostname), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "| V_out (V) | I_up (uA) | I_dn (uA) | mismatch (% of I_cp,nom) |"
  echo "|---|---|---|---|"
  printf '%s\n' "${TABLE}" | awk '{ printf "| %s | %s | %s | %s |\n", $1, $2, $3, $4 }'
  echo
  echo "ngspice log: [\`${ID}-ngspice.txt\`](${ID}-ngspice.txt)"
} > "${REC}"

echo "record: ${REC#"${ROOT}/"}"
echo "window(<=${TOL}%): ${V_LO} V .. ${V_TOP} V (contains 1.65 V: ${IN165}); max mismatch within 1.65..V_top = ${MAXM_165_TOP} %"
