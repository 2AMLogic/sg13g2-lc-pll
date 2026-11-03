#!/usr/bin/env bash
# Spec row 11 (loop power, excluding the VCO core), the part that exists as circuits: the CML prescaler and
# the M/A divider at N = 100, driven by an ideal 5.0 GHz differential source; plus the PFD + charge pump
# supply current from the newest locked sim/loop-tran record when there is one. ONE local ngspice, nominal
# corner, 27 C, 3.3 V. Writes a dated append-only record under sim/loop-power/records/. Not a corner grid.
#
#   scripts/run-loop-power.sh
#
# Environment: PDK_ROOT, NGSPICE (as in scripts/lib-pdk.sh); RECORD_DIR (default sim/loop-power/records);
#   TSTOP (default 120n), W0 (default 40n): the supply current is averaged over [W0, TSTOP].
# Exit 0 if the run completed and the record was written (the verdict is in the record); non-zero if the
# PDK is not the pinned one, a netlist is stale, ngspice failed, or the data is incomplete.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { echo "run-loop-power: error: $*" >&2; exit 1; }
source "${ROOT}/scripts/lib-pdk.sh"
"${ROOT}/design/netlist.sh" --check prescaler divider >/dev/null 2>&1 || die "design/netlist/{prescaler,divider}.spice is stale against the schematics (run design/netlist.sh)"
PRESC_NETLIST="${ROOT}/design/netlist/prescaler.spice"; DIV_NETLIST="${ROOT}/design/netlist/divider.spice"
TSTOP="${TSTOP:-120n}"; W0="${W0:-40n}"
REC_DIR="${RECORD_DIR:-${ROOT}/sim/loop-power/records}"; mkdir -p "${REC_DIR}"
WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT
sed -e "s|@@MODELS_DIR@@|${MODELS}|g" -e "s|@@OSDI_PSP@@|${OSDI_PSP}|g" -e "s|@@PRESC_NETLIST@@|${PRESC_NETLIST}|g" \
    -e "s|@@DIV_NETLIST@@|${DIV_NETLIST}|g" -e "s|@@TSTOP@@|${TSTOP}|g" -e "s|@@W0@@|${W0}|g" -e "s|@@OUT_DIR@@|${WORK}|g" \
    "${ROOT}/sim/loop-power/loop_power.spice.tmpl" > "${WORK}/loop_power.spice"
if grep -vE '^[[:space:]]*\*' "${WORK}/loop_power.spice" | grep -q '@@'; then die "unsubstituted placeholder left in the deck"; fi
printf 'set ngbehavior=hsa\n' > "${WORK}/.spiceinit"

COMMIT="$(git -C "${ROOT}" rev-parse --short=7 HEAD)"
DIRTY=""; [ -z "$(git -C "${ROOT}" status --porcelain -- design sim scripts reuse.lock.json ':(exclude)sim/*/records/*' ':(exclude)sim/*/negative-control-*' 2>/dev/null)" ] || DIRTY="-dirty"
ID="$(date -u +%Y%m%d-%H%M%S)-${COMMIT}${DIRTY}"
REC="${REC_DIR}/${ID}.md"
[ ! -e "${REC}" ] || die "${REC} exists; records are append-only"
T_START="$(date +%s)"
set +e
( cd "${WORK}" && HOME="${WORK}" "${NGSPICE}" -b loop_power.spice ) > "${WORK}/ngspice.log" 2>&1
NG_RC=$?
set -e
WALL=$(( $(date +%s) - T_START ))
cp "${WORK}/ngspice.log" "${REC_DIR}/${ID}-ngspice.txt"
grep -q '^ipavg' "${WORK}/ngspice.log" && grep -q '^idavg' "${WORK}/ngspice.log" && [ -s "${WORK}/fb.data" ] \
  || { echo "run-loop-power: ngspice produced no measurements (rc=${NG_RC}); see ${REC_DIR}/${ID}-ngspice.txt" >&2; exit 1; }
M() { awk -v k="$1" '$1==k {print $3}' "${WORK}/ngspice.log" | head -1; }
IP="$(M ipavg)"; ID_="$(M idavg)"; OP_P="$(M OP_IDDP)"; OP_D="$(M OP_IDDD)"
[ -n "${IP}" ] && [ -n "${ID_}" ] || die "could not read the averaged currents"
# FB: rising 1.65 V crossings in [W0, TSTOP]
W0S="$(awk -v x="${W0}" 'BEGIN{ s=x; m=1; if (s ~ /n$/) {m=1e-9; sub(/n$/,"",s)} printf "%.6g", s*m }')"
FB="$(awk -v w0="${W0S}" 'NR>1 && p<1.65 && $2>=1.65 && $1>=w0 { n++; te=pt+(1.65-p)*($1-pt)/($2-p); if (n>1) { s+=te-last; k++ } last=te; if(n==1) first=te } { p=$2; pt=$1 } END { printf "%d %.4g %.4g", n, (k?s/k:0), first }' "${WORK}/fb.data")"
read -r FB_N FB_T FB_FIRST <<<"${FB}"
FB_MHZ="$(awk -v t="${FB_T}" 'BEGIN{ if (t>0) printf "%.2f", 1e-6/t; else print "NA" }')"
IPUA="$(awk -v i="${IP}" 'BEGIN{printf "%.1f", -i*1e6}')"; IDUA="$(awk -v i="${ID_}" 'BEGIN{printf "%.1f", -i*1e6}')"
PP="$(awk -v i="${IP}" 'BEGIN{printf "%.2f", -i*3.3*1e3}')"; PD="$(awk -v i="${ID_}" 'BEGIN{printf "%.2f", -i*3.3*1e3}')"
DIV_OK="$(awk -v t="${FB_T}" -v n="${FB_N}" 'BEGIN{ print (n>=3 && t>19.5e-9 && t<20.5e-9) ? "yes" : "no" }')"
# newest locked loop-tran record: PFD + CP + bias power
LT="$(ls -1 "${ROOT}"/sim/loop-tran/records/*.md 2>/dev/null | tail -1 || true)"
LT_P=""; if [ -n "${LT}" ]; then LT_P="$(grep -o 'bias (row 11 part, same window)\*\*: [0-9.]* uA mean from the 3.3 V rail = [0-9.]* uW' "${LT}" | grep -o '= [0-9.]* uW' | grep -o '[0-9.]*' || true)"; fi
LT_MW="$(awk -v u="${LT_P:-0}" 'BEGIN{printf "%.2f", u/1000}')"
TOT="$(awk -v a="${PP}" -v b="${PD}" -v c="${LT_MW}" 'BEGIN{printf "%.2f", a+b+c}')"
{
  echo "# loop-power run ${ID}"
  echo
  if [ "${DIV_OK}" = yes ]; then
    echo "**Result (simulated, nominal corner only, not measured; row 11 NOT graded): prescaler ${PP} mW + M/A divider ${PD} mW at 5.0 GHz in, N = 100 divide confirmed (FB ${FB_MHZ} MHz, ${FB_N} edges in window)$([ -n "${LT_P}" ] && echo "; with PFD + CP + bias ${LT_MW} mW from \`$(basename "${LT}")\`: ${TOT} mW of the 20 mW budget, for the circuits that exist")."'**'
  else
    echo "**Result: the divide chain did NOT reach FB = 50 MHz in the window (FB ${FB_MHZ} MHz, ${FB_N} edges). The currents below are for a chain that is not dividing by 100 and are not a row 11 number.**"
  fi
  echo
  echo "- **Scope**: nominal only: \`hbt_typ\`, \`mos_tt\`, \`cap_typ\`, 27 C, 3.3 V. No corner grid. Spec row 11 is **not graded**: it is a C-grid row and its sum needs the lock detector, reference and clock buffering, which are **not in this design** (no schematic exists for them: listed as owed, not as zero). Row 11 allocates prescaler <= 10 mW, CP + PFD + bias <= 2 mW, post-prescaler counters + lock detector <= 4 mW, reference and clock buffering <= 4 mW."
  echo "- **Netlists**: \`design/netlist/prescaler.spice\` sha256 \`$(sha256sum "${PRESC_NETLIST}" | cut -d' ' -f1)\`, \`design/netlist/divider.spice\` sha256 \`$(sha256sum "${DIV_NETLIST}" | cut -d' ' -f1)\`, both checked fresh against their schematics with \`design/netlist.sh --check\` before the run."
  echo "- **Deck**: \`sim/loop-power/loop_power.spice.tmpl\` sha256 \`$(sha256sum "${ROOT}/sim/loop-power/loop_power.spice.tmpl" | cut -d' ' -f1)\`, placeholder substitution only."
  echo "- **Stimulus**: ideal differential sine, 5.0 GHz, 0.4 Vpp differential (0.1 V amplitude per side, antiphase), common mode 3.3 V, zero source impedance (the VCO core is excluded by the row's definition). Division code N = 100 (M = 12, A = 2; P = 8/10, DR-002). Ideal 50 uA reference current into the shared IREF node, as in \`design/pll_top.sch\` (its source is **not** in the design: that bias generation is not counted and is not an owed zero either)."
  echo "- **Method (DC/transient average, not an op-point alone)**: \`tran 4p ${TSTOP} 0 4p\`; supply current of each rail averaged over ${W0}-${TSTOP} (\`meas ... avg\`), power = 3.3 V x |I|. The prescaler rail also carries the 50 uA reference. FB rising edges at 1.65 V counted in the same window to confirm the division (${FB_N} edges, mean period $(awk -v t="${FB_T}" 'BEGIN{printf "%.2f", t*1e9}') ns). Window ${W0}-${TSTOP} is $(awk -v a="${FB_T}" 'BEGIN{ if (a>0) printf "%.1f", (120e-9-40e-9)/a; else print "NA"}') FB periods (default window); the divide-by-2, /4/5 and counter chain is fully dynamic, so the average depends on the clock being present."
  echo "- **DC operating point (no clock)**: prescaler rail $(awk -v i="${OP_P}" 'BEGIN{printf "%.1f", i*1e6}') uA, divider rail $(awk -v i="${OP_D}" 'BEGIN{printf "%.1f", i*1e6}') uA."
  echo "- **PFD + CP + bias**: $([ -n "${LT_P}" ] && echo "${LT_MW} mW taken from \`sim/loop-tran/records/$(basename "${LT}")\` (locked-state mean supply current of the real PFD/CP, 50 MHz, 200 uA I_cp, IREF 20 uA ideal), not re-simulated here." || echo "no locked loop-tran record found; not included.")"
  echo "- **PDK**: IHP-Open-PDK $(jq -r .pdk.release_tag "${PINS}") (model libraries hash-checked against \`sim/pins.json\`); PSP103 OSDI \`psp103.osdi\` sha256 \`$(jq -r .psp103.osdi_sha256 "${PINS}")\` (pinned)"
  echo "- **Simulator**: \`${NG_VER}\` (\`${NGSPICE}\`), one local \`ngspice -b\`, exit status ${NG_RC}, wall ${WALL} s, OMP_NUM_THREADS ${OMP_NUM_THREADS}; scratch \`.spiceinit\` = \`set ngbehavior=hsa\`"
  echo "- **Pin check**: ${NG_PIN_STATUS}"
  echo "- **Commit**: \`${COMMIT}${DIRTY}\` of this repository"
  echo "- **Host**: $(hostname), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "| block | supply current (uA) | power at 3.3 V (mW) | row 11 allocation (mW) |"
  echo "|---|---|---|---|"
  echo "| prescaler (+ 50 uA reference) | ${IPUA} | ${PP} | <= 10 |"
  echo "| M/A divider (CML-to-CMOS, M and A counters, FB flop) | ${IDUA} | ${PD} | <= 4 with the lock detector |"
  echo "| PFD + CP + bias | $([ -n "${LT_P}" ] && echo "-" || echo NA) | ${LT_MW} | <= 2 |"
  echo "| lock detector, reference and clock buffering | not simulated: no schematic | not counted | <= 4 + share of <= 4 |"
  echo "| **sum of the above** | | ${TOT} | <= 20 |"
  echo
  echo "ngspice log: [\`${ID}-ngspice.txt\`](${ID}-ngspice.txt)"
} > "${REC}"
echo "record: ${REC#"${ROOT}/"}"
echo "divide_ok: ${DIV_OK}  prescaler ${PP} mW  divider ${PD} mW"
