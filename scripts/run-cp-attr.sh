#!/usr/bin/env bash
# Charge-pump mismatch attribution per device group (issue #78): one Monte Carlo per group with mismatch ON in that
# group only (mm_ok=0 on every other MOS instance), plus all-on and a mismatch-off control. Batch fleet only.
#
#   scripts/run-cp-attr.sh --dry-run   build + validate the requests, submit nothing
#   scripts/run-cp-attr.sh             run, write sim/cp-mc/records/<id>-attribution.md
# Environment: CP_ATTR_N (samples per corner, default 100), CP_MC_SEED (default 20261103), CP_ATTR_NETLIST (default design/netlist/cp.spice),
#   CP_MC_UNITS_PER_JOB (default 696), CP_MC_JOBS (default 3), CP_MC_WORK (keep scratch), CP_MC_RESUME, CP_MC_WAIT, RECORD_DIR.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { echo "run-cp-attr: error: $*" >&2; exit 1; }
PDK_SKIP_OSDI_PINS=0
source "${ROOT}/scripts/lib-pdk.sh"
source "${ROOT}/scripts/lib-record.sh"
export PDK_ROOT
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1
N="${CP_ATTR_N:-100}"; SEED="${CP_MC_SEED:-20261103}"; NET="${CP_ATTR_NETLIST:-${ROOT}/design/netlist/cp.spice}"
REC_DIR="${RECORD_DIR:-${ROOT}/sim/cp-mc/records}"; mkdir -p "${REC_DIR}"
"${ROOT}/design/netlist.sh" --check cp >/dev/null 2>&1 || die "design/netlist/cp.spice is stale against design/cp.sch (run design/netlist.sh cp)"
python3 "${ROOT}/sim/cp-mc/attribute.py" groups "${NET}" >/dev/null
if [ -n "${CP_MC_WORK:-}" ]; then WORK="${CP_MC_WORK}"; mkdir -p "${WORK}"; else WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT; fi
GROUPS_RUN="all bn_ref bn_xbn2 bn_xbns bn_casc bp_ref bp_copy bp_casc leg_p leg_n switches none"
for g in ${GROUPS_RUN}; do
  n="${N}"; [ "${g}" = none ] && n=10
  python3 "${ROOT}/sim/cp-mc/attribute.py" netlist "${g}" "${NET}" "${WORK}/cp_${g}.spice"
  python3 "${ROOT}/sim/cp-mc/make_request.py" --cp-netlist "${WORK}/cp_${g}.spice" --outdir "${WORK}/${g}" --n "${n}" --seed "${SEED}" \
    --corner-set attr --label "attribution group ${g}:" >/dev/null
  klt sim "${WORK}/${g}/request.json" --dry-run --format json >/dev/null || die "${g} request failed klt sim --dry-run"
done
[ "${DRY}" = 1 ] && { echo "run-cp-attr: all requests validate (dry run, nothing submitted)"; exit 0; }
record_stamp
ID="$(date -u +%Y%m%d-%H%M%S)-${COMMIT}${DIRTY}"
REC="${REC_DIR}/${ID}-attribution.md"; [ ! -e "${REC}" ] || die "${REC} exists; records are append-only"
ARGS=()
for g in ${GROUPS_RUN}; do
  rc=0
  klt sim "${WORK}/${g}/request.json" --backend batch ${CP_MC_RESUME:+--resume} ${CP_MC_WAIT:+--wait-for-capacity "${CP_MC_WAIT}"} \
    --max-units-per-job "${CP_MC_UNITS_PER_JOB:-696}" --max-concurrent-jobs "${CP_MC_JOBS:-3}" --format json -o "${WORK}/${g}/out" \
    > "${WORK}/${g}/report.json" 2> "${WORK}/${g}/stderr.txt" || rc=$?
  cp "${WORK}/${g}/stderr.txt" "${REC_DIR}/${ID}-attr-${g}-klt-sim-stderr.txt"
  if [ "${rc}" != 0 ] && [ "${rc}" != 3 ]; then
    echo "run-cp-attr: BATCH SUBMIT/RUN FAILED for ${g} (klt sim exit ${rc}); not falling back to a local grid. stderr:" >&2
    tail -20 "${WORK}/${g}/stderr.txt" >&2; exit 1
  fi
  ARGS+=("${g}=${WORK}/${g}/report.json")
done
{
  echo "# cp-mc attribution ${ID}"
  echo
  echo "**Simulated, not measured.** Method: \`klt sim\` Monte Carlo (vary: mismatch, seed ${SEED}, n = ${N} per corner, none-control n = 10) on 9 corners (MOS tt/ss/ff x T -40/27/125 C at 3.3 V), one cp instance per sample, static op (UP on / DN on at each V_out). Each run leaves mismatch on in one device group (\`mm_ok=0\` on every other MOS instance, sim/cp-mc/attribute.py); \`all\` is every instance on; \`none\` (mismatch off everywhere, n = 10) measures the deterministic P/N offset, which adds in quadrature and is subtracted. Groups add in mean-square if independent; the table's last columns test that. Values are rms of mm = |I_up - I_dn| / 200 uA x 100 over all samples and corners pooled (mean of the square, so the sign drops out); the percentage is the group's share of the all-on mean-square. Groups: $(python3 "${ROOT}/sim/cp-mc/attribute.py" groups "${NET}")."
  echo
  python3 "${ROOT}/sim/cp-mc/attribute.py" report "${ARGS[@]}"
  echo
  echo "Commit \`${COMMIT}${DIRTY}\`, host $(hostname), $(klt --version 2>&1 | head -1)."
} > "${REC}"
echo "record: ${REC#"${ROOT}/"}"
