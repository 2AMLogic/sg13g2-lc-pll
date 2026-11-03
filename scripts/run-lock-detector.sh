#!/usr/bin/env bash
# Lock-detector 50 MHz re-grade (spec section 7, gate G5): the pinned sg13g2-pll PFD drives the
# pinned, unmodified lock_detector at REF = 50 MHz, 3.3 V. Writes a dated append-only record under
# sim/lock-detector/records/.
#
#   scripts/run-lock-detector.sh nominal        ONE local ngspice transient (mos_tt/cap_typ/res_typ, 27 C, 3.3 V)
#   scripts/run-lock-detector.sh closed PHI_PS V0 TSTOP_US
#                                               ONE closed-loop transient (nothing held): fixed phase error PHI_PS,
#                                               VWIN starting at V0 (.ic on xld.vwin, uic); spot check of the held-VWIN model
#   scripts/run-lock-detector.sh grid1|grid2    write the klt sim C-grid request (stage 1: 45 points at 3.3 V;
#                                               stage 2: 18 supply sub-corners) and submit it with
#                                               `klt sim --backend batch`. A failed submit is reported and
#                                               exits non-zero: it is NEVER run locally.
#   scripts/run-lock-detector.sh grid1 --dry-run   validate the request only
#
# Environment: PDK_ROOT, NGSPICE as for scripts/run-cp-dc.sh; RECORD_DIR (default sim/lock-detector/records).
# Method (the same words go in every record): sim/lock-detector/README.md.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { echo "run-lock-detector: error: $*" >&2; exit 1; }
MODE="${1:-}"; shift || true
case "${MODE}" in nominal|closed|grid1|grid2|report) ;; *) die "usage: $0 nominal|grid1|grid2 [--dry-run]" ;; esac
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1

PDK_NEED_R3CMC=1
source "${ROOT}/scripts/lib-pdk.sh"
"${ROOT}/scripts/fetch-pll.sh" >/dev/null || die "fetch/verify of the pinned sg13g2-pll files failed"
REC_DIR="${RECORD_DIR:-${ROOT}/sim/lock-detector/records}"; mkdir -p "${REC_DIR}"
WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT
TOOL=(python3 -I "${ROOT}/scripts/ld_tool.py")
TSTOP_PS="$("${TOOL[@]}" body "${WORK}/body.spice" "${WORK}/meas.txt" "${WORK}/meas.json")"

COMMIT="$(git -C "${ROOT}" rev-parse --short=7 HEAD)"
DIRTY=""; [ -z "$(git -C "${ROOT}" status --porcelain -- design sim scripts reuse.lock.json ':(exclude)sim/*/records/*' ':(exclude)sim/*/negative-control-*' 2>/dev/null)" ] || DIRTY="-dirty"
ID="$(date -u +%Y%m%d-%H%M%S)-${COMMIT}${DIRTY}"
PLL_PIN="$(jq -r '.imports[] | select(.from=="2AMLogic/sg13g2-pll") | .commit' "${ROOT}/reuse.lock.json")"
LD_SHA="$(sha256sum "${ROOT}/.fetched/sg13g2-pll/design/netlist/lock_detector.spice" | cut -d' ' -f1)"
PFD_SHA="$(sha256sum "${ROOT}/.fetched/sg13g2-pll/design/netlist/pfd.spice" | cut -d' ' -f1)"

if [ "${MODE}" = closed ]; then
  PHI="${1:?PHI_PS}"; V0="${2:?V0}"; TUS="${3:?TSTOP_US}"
  REC="${REC_DIR}/${ID}-closed-phi${PHI}-v0${V0}.md"; [ ! -e "${REC}" ] || die "${REC} exists"
  {
    echo ".lib ${MODELS}/cornerMOShv.lib mos_tt"; echo ".lib ${MODELS}/cornerCAP.lib cap_typ"; echo ".lib ${MODELS}/cornerRES.lib res_typ"
    echo ".option scale=1 temp=27"; echo ".global sub!"; echo "VSUB sub! 0 0"; echo "VDD vdd 0 3.3"
    echo "VREF ref 0 PULSE(0 3.3 20n 100p 100p 4.9n 20n)"
    echo "VFB fb 0 PULSE(0 3.3 $((20000+PHI))p 100p 100p 4.9n 20n)"
    echo ".include ${ROOT}/.fetched/sg13g2-pll/design/netlist/pfd.spice"; echo ".include ${ROOT}/.fetched/sg13g2-pll/design/netlist/lock_detector.spice"
    echo "XPFD ref fb up dn vdd 0 pfd"; echo "XLD up dn lock vdd 0 lock_detector"
    echo ".options reltol=1e-3 abstol=1e-10 vntol=1e-5 chgtol=1e-14"
    echo ".ic v(xld.vwin)=${V0}"
    echo ".control"; echo "pre_osdi ${OSDI_PSP}"; echo "pre_osdi ${OSDI_R3CMC}"
    echo "tran 100p ${TUS}u 0 100p uic"
    echo "let n = 1"
    echo "while n <= 10"
    echo "  let tt = n * ${TUS}u / 10"
    echo "  meas tran vw FIND v(xld.vwin) AT=\$&tt"
    echo "  meas tran lk FIND v(lock) AT=\$&tt"
    echo "  let n = n + 1"
    echo "end"
    echo ".endc"; echo ".end"
  } > "${WORK}/closed.spice"
  printf 'set ngbehavior=hsa\n' > "${WORK}/.spiceinit"
  START="$(date +%s)"; set +e
  ( cd "${WORK}" && HOME="${WORK}" nice "${NGSPICE}" -b closed.spice ) > "${WORK}/closed.log" 2>&1
  NG_RC=$?; set -e; ELAPSED=$(( $(date +%s) - START ))
  cp "${WORK}/closed.log" "${REC_DIR}/${ID}-closed-phi${PHI}-v0${V0}-ngspice.txt"
  {
    echo "# lock-detector closed-loop spot check: phi = ${PHI} ps, VWIN(0) = ${V0} V, ${TUS} us: run ${ID}"
    echo
    echo "**Simulated, not measured.** Nominal corner (mos_tt/cap_typ/res_typ, 27 C, 3.3 V). Nothing is held: the pinned PFD drives the pinned unmodified lock_detector (sg13g2-pll@${PLL_PIN}, lock_detector.spice sha256 \`${LD_SHA}\`) with a fixed phase error; \`.ic v(xld.vwin)=${V0}\`, \`tran 100p ${TUS}u 0 100p uic\`. VWIN and LOCK are sampled by \`meas FIND ... AT\` at 10 evenly spaced times (t = TSTOP/10 ... TSTOP; AT=0 is out of the measure interval). ${NG_VER}, exit ${NG_RC}, ${ELAPSED} s wall, commit \`${COMMIT}${DIRTY}\`, host $(hostname)."
    echo
    echo "| t (us) | VWIN (V) | LOCK (V) |"; echo "|---|---|---|"
    grep -E '^(vw|lk) +=' "${WORK}/closed.log" | awk '{v=$3} /^vw/ {w=v; i++; next} /^lk/ {printf "| %.2f | %s | %s |\n", i*'"${TUS}"'/10, w, v}'
    echo
    echo "ngspice log: [\`${ID}-closed-phi${PHI}-v0${V0}-ngspice.txt\`](${ID}-closed-phi${PHI}-v0${V0}-ngspice.txt)"
  } > "${REC}"
  echo "record: ${REC#"${ROOT}/"}"; sed -n '/^| t/,$p' "${REC}"
  exit 0
fi

if [ "${MODE}" = nominal ]; then
  REC="${REC_DIR}/${ID}-nominal.md"; [ ! -e "${REC}" ] || die "${REC} exists; records are append-only"
  {
    echo ".lib ${MODELS}/cornerMOShv.lib mos_tt"
    echo ".lib ${MODELS}/cornerCAP.lib cap_typ"
    echo ".lib ${MODELS}/cornerRES.lib res_typ"
    echo ".option scale=1 temp=27"
    sed -e "s|^\.include \.fetched/|.include ${ROOT}/.fetched/|" "${WORK}/body.spice"
    cat "${WORK}/meas.txt"
    echo ".control"
    echo "pre_osdi ${OSDI_PSP}"
    echo "pre_osdi ${OSDI_R3CMC}"
    echo "tran 50p ${TSTOP_PS}p 0 50p"
    echo ".endc"
    echo ".end"
  } > "${WORK}/ld.spice"
  printf 'set ngbehavior=hsa\n' > "${WORK}/.spiceinit"
  START="$(date +%s)"; set +e
  ( cd "${WORK}" && HOME="${WORK}" nice "${NGSPICE}" -b ld.spice ) > "${WORK}/ngspice.log" 2>&1
  NG_RC=$?; set -e
  ELAPSED=$(( $(date +%s) - START ))
  cp "${WORK}/ngspice.log" "${REC_DIR}/${ID}-nominal-ngspice.txt"
  # .meas results: "name = value" lines
  awk '/^[a-z_0-9]+ += +[-+0-9.eE]+/ { v[$1]=$3 } END { printf "{"; n=0; for (k in v) { printf "%s\"%s\": %s", (n++?",":""), k, v[k] } printf "}\n" }' "${WORK}/ngspice.log" > "${WORK}/values.json"
  [ "$(jq 'length' "${WORK}/values.json")" -gt 100 ] || die "ngspice produced too few measurements (rc=${NG_RC}); see ${REC_DIR}/${ID}-nominal-ngspice.txt"
  "${TOOL[@]}" analyze "${WORK}/values.json" "${WORK}/tables.md" "${WORK}/summary.json"
  {
    echo "# lock-detector 50 MHz re-grade, nominal corner: run ${ID}"
    echo
    echo "**Simulated, not measured.** One corner (\`mos_tt\`/\`cap_typ\`/\`res_typ\`, 27 C, 3.3 V), held-VWIN method (below); the C-grid is separate."
    echo
    echo "- **Cells**: \`2AMLogic/sg13g2-pll@${PLL_PIN}\` \`design/netlist/pfd.spice\` sha256 \`${PFD_SHA}\` and \`design/netlist/lock_detector.spice\` sha256 \`${LD_SHA}\`, fetched and sha256-verified by \`scripts/fetch-pll.sh\`, simulated unmodified"
    echo "- **PDK**: IHP-Open-PDK $(jq -r .pdk.release_tag "${PINS}") (model libraries hash-checked against \`sim/pins.json\`); PSP103 and r3_cmc OSDI hash-checked; resistor corner \`res_typ\` / capacitor corner \`cap_typ\` / MOS \`mos_tt\`"
    echo "- **Simulator**: \`${NG_VER}\`, one local \`ngspice -b\` (OMP_NUM_THREADS=${OMP_NUM_THREADS}), exit ${NG_RC}, ${ELAPSED} s wall; \`.tran 50p ${TSTOP_PS}p 0 50p\`; ${NG_PIN_STATUS}"
    echo "- **Commit**: \`${COMMIT}${DIRTY}\`; generator \`scripts/ld_tool.py\` sha256 \`$(sha256sum "${ROOT}/scripts/ld_tool.py" | cut -d' ' -f1)\`"
    echo "- **Host**: $(hostname), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo
    cat "${ROOT}/sim/lock-detector/method.md"
    echo
    cat "${WORK}/tables.md"
    echo
    echo "ngspice log: [\`${ID}-nominal-ngspice.txt\`](${ID}-nominal-ngspice.txt)"
  } > "${REC}"
  echo "record: ${REC#"${ROOT}/"}"; cat "${WORK}/summary.json"; echo
  exit 0
fi

write_grid_record() { # <grid dir>: the record from request.json + report.json (also: `report <grid dir>`)
  local D="$1" STG="$2" REC_ID TOT
  REC_ID="$(basename "${D}")"
  jq -e '.status == "pass"' "${D}/report.json" >/dev/null || die "${D}/report.json is not a complete passing report"
  "${TOOL[@]}" summary "${D}/report.json" "${WORK}/grid.md"
  {
    echo "# lock-detector 50 MHz re-grade, C-grid stage ${STG}: run ${REC_ID#*-}"
    echo
    echo "**Simulated, not measured.** $(jq -r .corner_count "${D}/report.json") corners through \`klt sim --backend batch\` ($(jq -r '.environment.remote.job_id // "sharded batch jobs, see report.json"' "${D}/report.json" 2>/dev/null)); request \`${REC_ID}/request.json\`, report \`${REC_ID}/report.json\`. Stage 1 = MOS {tt,ss,ff,sf,fs} x MIM {typ,bcs,wcs} x T {-40,27,125} at 3.3 V; stage 2 = {2.97, 3.63} V x {SLOW,TYP,FAST} x T (spec Corner set). The HBT axis is omitted: the lock_detector and PFD contain no HBT, so it cannot move any number here. The poly-resistor (rhigh) corner is paired by name with the MIM corner (res_typ/cap_typ, res_bcs/cap_bcs, res_wcs/cap_wcs); the spec does not define a resistor axis, and the unpaired crossings (e.g. fast R with slow C) are not run."
    echo
    echo "- **Cells**: \`2AMLogic/sg13g2-pll@${PLL_PIN}\` pfd.spice sha256 \`${PFD_SHA}\`, lock_detector.spice sha256 \`${LD_SHA}\`, unmodified. Commit \`${COMMIT}${DIRTY}\`; generator \`scripts/ld_tool.py\` sha256 \`$(sha256sum "${ROOT}/scripts/ld_tool.py" | cut -d' ' -f1)\`. klt $(klt --version 2>&1 | head -1), $(jq -r .environment.engine_version "${D}/report.json" | sed 's/^/ngspice-/'). Host $(hostname), $(date -u +%Y-%m-%dT%H:%M:%SZ)."
    if [ -f "${D}/report-first-attempt.json.gz" ]; then
      echo "- **Run history**: the first submission returned $(zcat "${D}/report-first-attempt.json.gz" | jq -r .passed) of $(zcat "${D}/report-first-attempt.json.gz" | jq -r .corner_count) corners (the rest \`lost_shard\`: shard jobs submitted but never launched, a klt/fleet capacity effect); the same request was completed with \`klt sim --backend batch --resume\` on the same outdir. Nothing was run locally. \`report.json\` is the merged complete report, \`report-first-attempt.json\` the partial one."
    else echo "- **Run history**: complete on the first submission (no partial report)."; fi
    echo
    cat "${ROOT}/sim/lock-detector/method.md"
    echo
    echo "## Results (per corner; phase columns are |phi| where the net current at the named VWIN trip is zero)"
    echo
    cat "${WORK}/grid.md"
  } > "${D}.md"
  echo "record: ${D#"${ROOT}/"}.md"
}
if [ "${MODE}" = report ]; then
  RD="$(cd "${1:?grid dir}" && pwd)"; write_grid_record "${RD}" "$(basename "${RD}" | sed 's/.*grid//')"; exit 0
fi

# ---- C-grid through klt sim (batch). Never falls back to local.
STAGE="${MODE#grid}"
REQDIR="${REC_DIR}/${ID}-grid${STAGE}"; mkdir -p "${REQDIR}"
cp "${WORK}/body.spice" "${REQDIR}/body.spice"
sed -i -e 's|^\.include \.fetched/|.include ../../../../.fetched/|' "${REQDIR}/body.spice"
"${TOOL[@]}" request --stage "${STAGE}" --body body.spice "${REQDIR}/request.json"
export PDK_ROOT
if [ "${DRY}" = 1 ]; then klt sim "${REQDIR}/request.json" --dry-run; exit $?; fi
set +e
klt sim "${REQDIR}/request.json" --backend batch --format json --report-out "${REQDIR}/report.json" -o "${REQDIR}/out" > /dev/null 2> "${REQDIR}/klt-stderr.txt"
RC=$?; set -e
echo "klt sim exit ${RC}; request and report under ${REQDIR#"${ROOT}/"}"
[ "${RC}" = 0 ] || { echo "run-lock-detector: batch submit/run failed (rc=${RC}); NOT falling back to local. See ${REQDIR#"${ROOT}/"}/klt-stderr.txt; if it reports shards never launched, rerun with: klt sim ${REQDIR#"${ROOT}/"}/request.json --backend batch --resume -o ${REQDIR#"${ROOT}/"}/out, then: $0 report ${REQDIR#"${ROOT}/"}" >&2; exit "${RC}"; }
write_grid_record "${REQDIR}" "${STAGE}"
