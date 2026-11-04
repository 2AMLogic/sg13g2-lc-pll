#!/usr/bin/env bash
# Closed-loop transient: lock time (spec row 10) and reference spur (row 9) of the REAL PFD / charge pump /
# loop filter with a BEHAVIOURAL VCO+divider stand-in (see sim/loop-tran/README.md). ONE local ngspice,
# nominal corner, nominal supply; writes a dated append-only record under sim/loop-tran/records/.
# Not a corner grid (that goes through `klt sim`, #39), and rows 9 and 10 are NOT graded here.
#
#   scripts/run-loop-tran.sh
#
# Environment:
#   PDK_ROOT, NGSPICE   as in scripts/lib-pdk.sh
#   TSTOP (default 12u) run length; TMAX (default 200p) maximum time step
#   KVCO_SIGN (default 1) -1 flips the stand-in VCO slope (positive feedback): the negative control
#   CP_NETLIST, LF_NETLIST   override the committed netlists (recorded by path and sha256)
#   RECORD_DIR (default sim/loop-tran/records)
# Exit 0 if the run completed and the record was written (the verdict is in the record); non-zero if the
# PDK is not the pinned one, ngspice failed, or the data could not be analysed.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { echo "run-loop-tran: error: $*" >&2; exit 1; }
source "${ROOT}/scripts/lib-pdk.sh"
"${ROOT}/scripts/fetch-pll.sh" --verify >/dev/null 2>&1 || die "the pinned sg13g2-pll files are missing or altered (run scripts/fetch-pll.sh)"

PFD_NETLIST="${ROOT}/.fetched/sg13g2-pll/design/netlist/pfd.spice"
CP_NETLIST="${CP_NETLIST:-${ROOT}/design/netlist/cp.spice}"
LF_NETLIST="${LF_NETLIST:-${ROOT}/design/netlist/loopfilter.spice}"
for f in "${PFD_NETLIST}" "${CP_NETLIST}" "${LF_NETLIST}"; do [ -f "${f}" ] || die "${f} not found"; done
if [ "${CP_NETLIST}" = "${ROOT}/design/netlist/cp.spice" ] && [ "${LF_NETLIST}" = "${ROOT}/design/netlist/loopfilter.spice" ]; then
  "${ROOT}/design/netlist.sh" --check cp loopfilter >/dev/null 2>&1 || die "design/netlist/{cp,loopfilter}.spice is stale against the schematics (run design/netlist.sh)"
fi
TSTOP="${TSTOP:-12u}"; TMAX="${TMAX:-200p}"; KVCO_SIGN="${KVCO_SIGN:-1}"
case "${KVCO_SIGN}" in 1|-1) ;; *) die "KVCO_SIGN must be 1 or -1" ;; esac
NDIV=100; F0=5.0e9; VC0=2.475; KV=480e6; FREF=50e6; VSTART=1.65; PHI0=0.25
REC_DIR="${RECORD_DIR:-${ROOT}/sim/loop-tran/records}"; mkdir -p "${REC_DIR}"
WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT

sed -e "s|@@MODELS_DIR@@|${MODELS}|g" -e "s|@@OSDI_PSP@@|${OSDI_PSP}|g" -e "s|@@OSDI_R3@@|${OSDI_R3}|g" \
    -e "s|@@PFD_NETLIST@@|${PFD_NETLIST}|g" -e "s|@@CP_NETLIST@@|${CP_NETLIST}|g" -e "s|@@LF_NETLIST@@|${LF_NETLIST}|g" \
    -e "s|@@NDIV@@|${NDIV}|g" -e "s|@@VC0@@|${VC0}|g" -e "s|@@KV_SIGNED@@|$([ "${KVCO_SIGN}" = 1 ] && echo "${KV}" || echo "-${KV}")|g" \
    -e "s|@@PHI0@@|${PHI0}|g" -e "s|@@VSTART@@|${VSTART}|g" -e "s|@@TSTOP@@|${TSTOP}|g" -e "s|@@TMAX@@|${TMAX}|g" \
    -e "s|@@DATA_OUT@@|${WORK}/loop_tran.data|g" \
    "${ROOT}/sim/loop-tran/loop_tran.spice.tmpl" > "${WORK}/loop_tran.spice"
if grep -vE '^[[:space:]]*\*' "${WORK}/loop_tran.spice" | grep -q '@@'; then die "unsubstituted placeholder left in the deck"; fi
printf 'set ngbehavior=hsa\n' > "${WORK}/.spiceinit"

COMMIT="$(git -C "${ROOT}" rev-parse --short=7 HEAD)"
DIRTY=""; [ -z "$(git -C "${ROOT}" status --porcelain -- design sim scripts reuse.lock.json ':(exclude)sim/*/records/*' ':(exclude)sim/*/negative-control-*' 2>/dev/null)" ] || DIRTY="-dirty"
ID="$(date -u +%Y%m%d-%H%M%S)-${COMMIT}${DIRTY}"
REC="${REC_DIR}/${ID}.md"
[ ! -e "${REC}" ] || die "${REC} exists; records are append-only"

T_START="$(date +%s)"
set +e
( cd "${WORK}" && HOME="${WORK}" "${NGSPICE}" -b loop_tran.spice ) > "${WORK}/ngspice.log" 2>&1
NG_RC=$?
set -e
WALL=$(( $(date +%s) - T_START ))
cp "${WORK}/ngspice.log" "${REC_DIR}/${ID}-ngspice.txt"
[ -s "${WORK}/loop_tran.data" ] || { echo "run-loop-tran: ngspice produced no data (rc=${NG_RC}); see ${REC_DIR}/${ID}-ngspice.txt" >&2; exit 1; }
python3 -I "${ROOT}/scripts/loop_tran_analyze.py" "${WORK}/loop_tran.data" "${NDIV}" "${F0}" "${VC0}" "$([ "${KVCO_SIGN}" = 1 ] && echo "${KV}" || echo "-${KV}")" "${FREF}" > "${WORK}/res.json" \
  || { cat "${WORK}/res.json" >&2; die "analysis failed; see ${REC_DIR}/${ID}-ngspice.txt"; }

J() { jq -r "$1" "${WORK}/res.json"; }
LOCKED="$(J .locked)"
US() { awk -v x="$1" 'BEGIN{printf "%.2f", x*1e6}'; }
CPSHA="$(sha256sum "${CP_NETLIST}" | cut -d' ' -f1)"; LFSHA="$(sha256sum "${LF_NETLIST}" | cut -d' ' -f1)"
{
  echo "# loop-tran run ${ID}"
  echo
  if [ "${LOCKED}" = true ]; then
    echo "**Result (simulated, stand-in VCO, nominal corner only; NOT graded against rows 9 or 10): LOCKED. Lock time $(US "$(J .lock_time_or_s)") us (strict: frequency OR phase criterion) / $(US "$(J .lock_time_and_s)") us (row 10 wording: frequency AND phase) from Vctrl = ${VSTART} V; reference spur $(J '.spur.spur_dbc|.*10|round/10') dBc (V_r = $(J '.spur.vr_peak_v*1e3|.*1000|round/1000') mV peak at f_ref, method T on v(Vctrl)).**"
  else
    echo "**Result (simulated, stand-in VCO, nominal corner only): NOT LOCKED within ${TSTOP} s (no 40 reference periods after the last violation). No lock time and no spur are reported.**"
  fi
  echo
  echo "- **Scope**: typical corner (\`mos_tt\`, \`cap_typ\`, \`res_typ\`), 27 C, 3.3 V, I_cp = 200 uA (IREF 20 uA), f_ref = 50 MHz, N = ${NDIV}. One run. No corner grid, no Monte Carlo, no noise. Rows 9 and 10 are **not graded**: they are graded over the C-grid with the real VCO, prescaler and counters in the loop. Numbers are **simulated, not measured**."
  echo "- **REAL in the loop**: the pinned sg13g2-pll PFD (\`.fetched/sg13g2-pll/design/netlist/pfd.spice\` sha256 \`$(sha256sum "${PFD_NETLIST}" | cut -d' ' -f1)\`, \`reuse.lock.json\`), \`${CP_NETLIST#"${ROOT}/"}\` sha256 \`${CPSHA}\`, \`${LF_NETLIST#"${ROOT}/"}\` sha256 \`${LFSHA}\` (third-order filter from \`sim/loop-model/loop-filter.json\`)."
  echo "- **STAND-IN, not the design**: the VCO, the CML prescaler and the M/A counters are replaced by ONE behavioural block: a phase accumulator (B-source into a 1 F capacitor, V = cycles of the FB clock) integrating f_out(Vctrl)/N, with f_out(Vctrl) = 5.0 GHz + K_VCO (Vctrl - ${VC0} V), K_VCO = $([ "${KVCO_SIGN}" = 1 ] && echo "+" || echo "-")480 MHz/V (the spec section 3 geometric mid), and FB = 1.65 + 1.65 tanh(25 sin(2 pi phase)) V. The line, its centre (the window centre, so 5.0 GHz at ${VC0} V) and its positive sign are **assumptions**: the VCO's graded f(Vctrl) curve is gate G4 and does not exist, and the pinned VCO did not oscillate in the only smoke record. Prescaler delay, counter delay, VCO swing and loading are therefore **not** in these numbers (the prescaler load on the tank is gate G2)."
  echo "- **Deck**: \`sim/loop-tran/loop_tran.spice.tmpl\` sha256 \`$(sha256sum "${ROOT}/sim/loop-tran/loop_tran.spice.tmpl" | cut -d' ' -f1)\`, placeholder substitution only. Initial state: Vctrl, the CP output and the R1-C1 node at ${VSTART} V (the window edge farthest from the 5.0 GHz point at ${VC0} V is equally 1.65 V or 3.30 V; the CP cannot reach 3.30 V, so 1.65 V is used); initial FB phase ${PHI0} cycle; REF starts at t = 0 (PFD enabled at t = 0)."
  echo "- **PDK**: IHP-Open-PDK $(jq -r .pdk.release_tag "${PINS}") (model libraries hash-checked against \`sim/pins.json\`); PSP103 OSDI \`psp103.osdi\` sha256 \`$(jq -r .psp103.osdi_sha256 "${PINS}")\` and r3_cmc OSDI (loop-filter rppd) sha256 \`$(jq -r .r3_cmc.osdi_sha256 "${PINS}")\` (both pinned)"
  echo "- **Simulator**: \`${NG_VER}\` (\`${NGSPICE}\`), one local \`ngspice -b\`, exit status ${NG_RC}, wall ${WALL} s, OMP_NUM_THREADS ${OMP_NUM_THREADS}; \`tran 100p ${TSTOP} 0 ${TMAX}\`, reltol 1e-3; scratch \`.spiceinit\` = \`set ngbehavior=hsa\`"
  echo "- **Pin check**: ${NG_PIN_STATUS}"
  echo "- **Commit**: \`${COMMIT}${DIRTY}\` of this repository"
  echo "- **Run length**: ${TSTOP} s = $(J .ref_edges) reference edges; samples $(J .samples)."
  echo "- **Estimators** (from \`scripts/loop_tran_analyze.py\`): edges are rising 1.65 V crossings, linearly interpolated. Phase error = t_FB - t_REF to the nearest FB rising edge at each REF edge, wrapped to +-T_ref/2. Frequency error per reference period = K_VCO x (mean Vctrl over that period - ${VC0} V), i.e. the stand-in line, so it carries no edge-timing noise. Lock time = first REF edge after the last period that violates the criterion; strict reading: |f error| > 1 MHz (0.02 % of 5.0 GHz) **or** |phase error| > 5 % T_ref (1 ns); row 10's wording: **and**. No cycle-slip count is claimed."
  echo "- **Spur method T** (spec row 9): Vctrl over the last 40 reference periods of the run, resampled to 20 ps, linear trend removed, coherent Fourier component at f_ref (peak V_r); spur = 20 log10(K_VCO V_r / (2 f_ref)) (small-index FM). The VCO-output cross-check is **not run**: the stand-in has no 5 GHz output spectrum. No noise sources; the spur is deterministic CP/PFD/filter ripple only."
  if [ "${LOCKED}" = true ]; then
    echo "- **Locked state**: Vctrl mean $(J '.spur.vctrl_mean_v*1000|round/1000') V, ripple $(J '.spur.vctrl_pp_v*1e6|round/1000') mV pk-pk over the spur window; static phase error $(J '.phase_err_final_ps|.*10|round/10') ps; delta-f peak $(J '.spur.delta_f_peak_hz/1e3|round') kHz."
    echo "- **Supply current of PFD + CP + bias (row 11 part, same window)**: $(J '.supply.i_vdd_mean_a*-1e6|.*10|round/10') uA mean from the 3.3 V rail = $(J '.supply.p_w*1e6|.*10|round/10') uW (the 20 uA IREF is an ideal source from the rail; the lock detector is not in this deck)."
  fi
  echo "- **Host**: $(hostname), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "| t (us) | Vctrl (V) | phase error (ps) | f error (MHz) |"
  echo "|---|---|---|---|"
  jq -r '.trace[] | "| \(.t_us) | \(.vctrl_v) | \(.phase_err_ps) | \(.f_err_mhz) |"' "${WORK}/res.json"
  echo
  echo "ngspice log: [\`${ID}-ngspice.txt\`](${ID}-ngspice.txt)"
} > "${REC}"

echo "record: ${REC#"${ROOT}/"}"
echo "locked: ${LOCKED}"
