#!/usr/bin/env bash
# Method T cost ladder (spec section 4, gate G6): transient-noise wall time and estimator variance versus run
# length on the closed-loop stand-in bench (sim/jitter/jitter_t.spice.tmpl). NOT a jitter result.
#
#   scripts/run-jitter-t-cost.sh --smoke       ONE short local ngspice (debug probe; prints wall time, edge count)
#   scripts/run-jitter-t-cost.sh               render the ladder, submit ONE `klt sim` deck-list request to the
#                                              Spot batch fleet (KLT_SIM_BACKEND=batch), write the record
#   scripts/run-jitter-t-cost.sh --dry-run     render + `klt sim --dry-run` only
#
# The ladder is a set of runs: it is never hand-looped on this host. A failed batch submit is reported and
# the script exits non-zero; it does NOT fall back to a local grid.
# Environment: PDK_ROOT NGSPICE (scripts/lib-pdk.sh); LADDER_US (default "20 50 100 200", stop times in us; longer
#   rungs would exceed the fleet whole-job ceiling, see the record); TMAX (200p); NOISE_NT (1n); SEED (1); SETTLE_US (15); RECORD_DIR (sim/jitter/records);
#   RUNNER_PDK_ROOT (default /opt/pdk: where the fleet image keeps ihp-sg13g2; forwarded as models.pdk_root);
#   UNIT_TIMEOUT_S (default 3400: one unit per fleet job, under the 3600 s ceiling); OUTDIR (default a scratch dir).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { echo "run-jitter-t-cost: error: $*" >&2; exit 1; }
MODE=ladder
case "${1:-}" in --smoke) MODE=smoke ;; --dry-run) MODE=dry ;; "") ;; *) die "unknown argument $1" ;; esac
source "${ROOT}/scripts/lib-pdk.sh"
"${ROOT}/scripts/fetch-pll.sh" --verify >/dev/null 2>&1 || die "the pinned sg13g2-pll files are missing or altered (run scripts/fetch-pll.sh)"
command -v jq >/dev/null || die "jq is required"
PFD_NETLIST="${ROOT}/.fetched/sg13g2-pll/design/netlist/pfd.spice"
CP_NETLIST="${ROOT}/design/netlist/cp.spice"; LF_NETLIST="${ROOT}/design/netlist/loopfilter.spice"
for f in "${PFD_NETLIST}" "${CP_NETLIST}" "${LF_NETLIST}"; do [ -f "${f}" ] || die "${f} not found"; done
"${ROOT}/design/netlist.sh" --check cp loopfilter >/dev/null 2>&1 || die "design/netlist/{cp,loopfilter}.spice is stale against the schematics (run design/netlist.sh)"
LADDER_US="${LADDER_US:-20 50 100 200}"; TMAX="${TMAX:-200p}"; NOISE_NT="${NOISE_NT:-1n}"; SEED="${SEED:-1}"
SETTLE_US="${SETTLE_US:-15}"; RUNNER_PDK_ROOT="${RUNNER_PDK_ROOT:-/opt/pdk}"; UNIT_TIMEOUT_S="${UNIT_TIMEOUT_S:-3400}"
NDIV=100; F0=5.0e9; VC0=2.475; KV=480e6; VSTART=1.65; PHI0=0.25
# Noise level: white frequency noise whose phase noise is the section 3 target line, L(1 MHz) = -105 dBc/Hz,
# L(f) = L1 (1 MHz/f)^2. Single-sided S_df = 2 L1 (1e6)^2 Hz^2/Hz at the VCO; /N^2 at the FB clock; a sampled
# source of NA amps rms per NT seconds has single-sided PSD 2 NA^2 NT, so NA = sqrt(S_df/(N^2 2 NT)).
NT_S="$(printf '%s' "${NOISE_NT}" | sed -e 's/n$/e-9/' -e 's/p$/e-12/' -e 's/u$/e-6/')"
NOISE_NA="$(awk -v nt="${NT_S}" -v n="${NDIV}" 'BEGIN{l1=10^(-105/10); s=2*l1*1e12; printf "%.6g", sqrt(s/(n*n*2*nt))}')"
# Ladder decks include the three netlists by relative name (a deck-list request cannot stage absolute includes),
# so render() takes the include directory prefix: "" for decks/ (copies sit beside the deck), absolute for --smoke.
render() { # render STOP_US OUT_DECK DATA_NAME [INCLUDE_PREFIX]
  local pre="${4:-}" models="${MODELS}" opsp="${OSDI_PSP}" or3="${OSDI_R3}"
  if [ -n "${pre}" ] || [ "${MODE}" != smoke ]; then # ladder: PDK files are the RUNNER's, same layout under its PDK root
    models="${RUNNER_PDK_ROOT}/ihp-sg13g2/libs.tech/ngspice/models"
    opsp="${RUNNER_PDK_ROOT}/ihp-sg13g2/$(jq -r .psp103.osdi "${PINS}")"; or3="${RUNNER_PDK_ROOT}/ihp-sg13g2/$(jq -r .r3_cmc.osdi "${PINS}")"
  fi
  sed -e "s|@@MODELS_DIR@@|${models}|g" -e "s|@@OSDI_PSP@@|${opsp}|g" -e "s|@@OSDI_R3@@|${or3}|g" \
      -e "s|@@PFD_NETLIST@@|${pre}pfd.spice|g" -e "s|@@CP_NETLIST@@|${pre}cp.spice|g" -e "s|@@LF_NETLIST@@|${pre}loopfilter.spice|g" \
      -e "s|@@NDIV@@|${NDIV}|g" -e "s|@@VC0@@|${VC0}|g" -e "s|@@KV_SIGNED@@|${KV}|g" -e "s|@@PHI0@@|${PHI0}|g" \
      -e "s|@@VSTART@@|${VSTART}|g" -e "s|@@TSTOP@@|${1}u|g" -e "s|@@TMAX@@|${TMAX}|g" -e "s|@@DATA_OUT@@|${3}|g" \
      -e "s|@@NOISE_NA@@|${NOISE_NA}|g" -e "s|@@NOISE_NT@@|${NOISE_NT}|g" -e "s|@@SEED@@|${SEED}|g" \
      "${ROOT}/sim/jitter/jitter_t.spice.tmpl" > "${2}"
  if grep -vE '^[[:space:]]*\*' "${2}" | grep -q '@@'; then die "unsubstituted placeholder left in the deck"; fi
}
WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT
T_REF=20e-9; SETTLE_S="$(awk -v u="${SETTLE_US}" 'BEGIN{print u*1e-6}')"

if [ "${MODE}" = smoke ]; then
  STOP="${SMOKE_US:-2}"
  cp "${PFD_NETLIST}" "${CP_NETLIST}" "${LF_NETLIST}" "${WORK}/"
  render "${STOP}" "${WORK}/deck.spice" fb.data
  printf 'set ngbehavior=hsa\n' > "${WORK}/.spiceinit"
  T0="$(date +%s.%N)"
  ( cd "${WORK}" && HOME="${WORK}" "${NGSPICE}" -b deck.spice ) > "${WORK}/ng.log" 2>&1 || { tail -20 "${WORK}/ng.log" >&2; die "ngspice failed"; }
  WALL="$(awk -v a="${T0}" -v b="$(date +%s.%N)" 'BEGIN{printf "%.1f", b-a}')"
  python3 -I "${ROOT}/scripts/jitter_t_analyze.py" "${WORK}/fb.data" "${T_REF}" 0.5e-6 1e-6 | jq -c .
  echo "smoke: ${STOP} us transient-noise run, wall ${WALL} s, noise NA=${NOISE_NA} A NT=${NOISE_NT}"
  exit 0
fi

OUTDIR="${OUTDIR:-${WORK}/out}"; mkdir -p "${WORK}/decks"; cp "${PFD_NETLIST}" "${CP_NETLIST}" "${LF_NETLIST}" "${WORK}/decks/"
printf 'set ngbehavior=hsa\n' > "${WORK}/decks/spiceinit"   # shipped as the unit's .spiceinit (the PDK's compatibility mode)
DECKS="[]"
for L in ${LADDER_US}; do
  render "${L}" "${WORK}/decks/t${L}us.spice" fb.data
  DECKS="$(jq -c --arg id "t${L}us" --arg d "decks/t${L}us.spice" --argjson to "${UNIT_TIMEOUT_S}" '. + [{id:$id, deck:$d, inputs:[{path:"decks/spiceinit", name:".spiceinit"}], outputs:["fb.data"], timeout_s:$to}]' <<<"${DECKS}")"
done
jq -n --argjson decks "${DECKS}" --argjson to "${UNIT_TIMEOUT_S}" --arg pr "${RUNNER_PDK_ROOT}" \
  '{backend:"batch", engine:"ngspice", models:{pdk:"sg13g2", pdk_root:$pr}, decks:$decks, options:{timeout_s:$to}, batch:{job_ceiling_check:"split"}}' > "${WORK}/request.json"
if [ "${MODE}" = dry ]; then
  klt sim --dry-run --backend batch -o "${OUTDIR}" "${WORK}/request.json"; exit $?
fi
set +e
klt sim --backend batch --wait-for-capacity "${CAPACITY_WAIT_S:-1800}" --format json --report-out "${WORK}/report.json" -o "${OUTDIR}" "${WORK}/request.json" > "${WORK}/klt.out" 2> "${WORK}/klt.err"
KLT_RC=$?
set -e
[ -s "${WORK}/report.json" ] || { cat "${WORK}/klt.err" "${WORK}/klt.out" >&2; die "the batch submit failed (rc=${KLT_RC}); not falling back to a local grid"; }
REC_DIR="${RECORD_DIR:-${ROOT}/sim/jitter/records}"; mkdir -p "${REC_DIR}"
COMMIT="$(git -C "${ROOT}" rev-parse --short=7 HEAD)"
DIRTY=""; [ -z "$(git -C "${ROOT}" status --porcelain -- design sim scripts reuse.lock.json ':(exclude)sim/*/records/*' ':(exclude)sim/*/negative-control-*' 2>/dev/null)" ] || DIRTY="-dirty"
ID="$(date -u +%Y%m%d-%H%M%S)-${COMMIT}${DIRTY}-tcost"
REC="${REC_DIR}/${ID}.md"; [ ! -e "${REC}" ] || die "${REC} exists; records are append-only"
cp "${WORK}/report.json" "${REC_DIR}/${ID}-report.json"
WIN="5e-6 12.5e-6 25e-6 100e-6"
{
  echo "# jitter method-T cost ladder ${ID}"
  echo
  echo "**Result (simulated, not measured; cost and estimator variance only, NO jitter or phase-noise number is claimed): see the table.** Bench: closed-loop stand-in, DIVIDED-DOWN (FB, 50 MHz) output, one nominal corner, one noise seed."
  echo
  echo "- **Method (spec section 4, method T)**: ngspice transient noise (\`trnoise\` current source on the behavioural phase accumulator of \`sim/jitter/jitter_t.spice.tmpl\`, sha256 \`$(sha256sum "${ROOT}/sim/jitter/jitter_t.spice.tmpl" | cut -d' ' -f1)\`). Noise: white frequency noise equal to the 1/f^2 target line (-105 dBc/Hz @ 1 MHz) at the VCO, NA = ${NOISE_NA} A rms per NT = ${NOISE_NT}, seed ${SEED}. A cost placeholder, not a noise model: no R1, reference, PFD/CP or divider noise."
  echo "- **Run lengths**: ${LADDER_US} us; \`tran 100p <stop> 0 ${TMAX}\`, reltol 1e-3; first ${SETTLE_US} us discarded as lock transient."
  echo "- **Estimator** (\`scripts/jitter_t_analyze.py\`): FB rising 1.65 V edges; per non-overlapping window of W, edge times against edge index with the least-squares line removed; sigma_W = rms residual; mean over K windows, relative standard error = std/mean/sqrt(K). Windows W = 5, 12.5, 25 and 100 us; the spec window (100 us, >= 8 windows) is out of reach at these lengths and rows are blank where K < 2."
  echo "- **Backend**: Spot batch fleet via one \`klt sim\` deck-list request, one unit per job (\`job_ceiling_check: split\`), unit timeout ${UNIT_TIMEOUT_S} s; klt exit ${KLT_RC}; fleet job ids in the report (\`${ID}-report.json\`)."
  echo "- **Simulator**: $(grep -a -o -m1 'ngspice-[0-9.]*' "${OUTDIR}"/t*us/stdout.bin 2>/dev/null | head -1 | cut -d: -f2 | grep . || echo "version not reported by the fleet runner (report engine_version is null)") on the fleet against the pin $(jq -r '.ngspice.version // "47"' "${PINS}" 2>/dev/null) (\`sim/pins.json\`); local smoke on this host: ${NG_VER}. PDK: IHP-Open-PDK $(jq -r .pdk.release_tag "${PINS}")."
  echo "- **Commit**: \`${COMMIT}${DIRTY}\`; host $(hostname), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "| stop (us) | unit status | fleet wall (s) | wall / simulated us (s) | samples | FB edges | W (us) | K | sigma_W mean (ps) | rel. std. err. |"
  echo "|---|---|---|---|---|---|---|---|---|---|"
  for L in ${LADDER_US}; do
    U="t${L}us"
    ST="$(jq -r --arg u "${U}" '.units[] | select(.id==$u) | .status' "${WORK}/report.json")"
    DUR="$(jq -r --arg u "${U}" '.units[] | select(.id==$u) | .duration_s' "${WORK}/report.json")"
    DATA="${OUTDIR}/${U}/fb.data"
    if [ "${ST}" = pass ] && [ -s "${DATA}" ]; then
      python3 -I "${ROOT}/scripts/jitter_t_analyze.py" "${DATA}" "${T_REF}" "${SETTLE_S}" ${WIN//e-6/e-6} > "${WORK}/a-${U}.json" || true
      jq -r --arg l "${L}" --arg st "${ST}" --arg d "${DUR}" '. as $a | .windows[] | "| \($l) | \($st) | \($d|tonumber|.*10|round/10) | \(($d|tonumber)/($l|tonumber)*100|round/100) | \($a.samples) | \($a.fb_edges) | \(.window_s*1e6) | \(.windows_used) | \(if .sigma_mean_s then (.sigma_mean_s*1e12*100|round/100) else "" end) | \(if .rel_std_err then (.rel_std_err*1000|round/1000) else "" end) |"' "${WORK}/a-${U}.json"
    else
      echo "| ${L} | ${ST} | ${DUR} | | | | | | | |"
    fi
  done
  echo
  echo "klt stderr tail: \`$(tail -c 300 "${WORK}/klt.err" | tr '\n' ' ')\`"
} > "${REC}"
echo "record: ${REC#"${ROOT}/"}"
