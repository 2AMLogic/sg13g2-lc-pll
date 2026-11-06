#!/usr/bin/env bash
# Charge-pump up/down mismatch Monte Carlo (spec rows 7 and 9, mismatch contribution only), T1 item 6.
# The whole grid goes to the Spot batch fleet through `klt sim --backend batch`; nothing is hand-launched
# locally, and a failed submit is reported, never retried locally.
#
#   scripts/run-cp-mc.sh                # nominal campaign + negative control + klt yield; writes a dated record
#   scripts/run-cp-mc.sh --dry-run      # build and validate both requests (klt sim --dry-run), submit nothing
#
# Environment: PDK_ROOT (pinned PDK, scripts/lib-pdk.sh), CP_MC_N (samples per corner, default 200),
#   CP_MC_N_CONTROL (default 20), CP_MC_UNITS_PER_JOB (default 696 = floor((3600-120)/options.timeout_s 5); a batch job is killed whole at 3600 s and a single 6600-unit job at the default OpenMP thread count timed out entirely, which options.threads_per_worker=1 now prevents), CP_MC_JOBS (concurrent jobs, default 3), CP_MC_SEED (default 20261103), RECORD_DIR (default sim/cp-mc/records),
#   CP_MC_WORK (keep the scratch dir there, for resuming), CP_MC_ATTACH_NOM / CP_MC_ATTACH_NEG (re-attach to an
#   already-submitted batch job id of the same request instead of submitting again; the fleet cannot cancel a job),
#   CP_MC_RESUME=1 (with the same CP_MC_WORK: launch shards the fleet had no capacity for and reuse the finished ones),
#   CP_MC_WAIT=SECONDS (klt sim --wait-for-capacity: retry a launch the fleet refused for capacity),
#   YIELD_PY (python with klt + klt_yield_native; default .venv/bin/python, see sim/cp-mc/README.md).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { echo "run-cp-mc: error: $*" >&2; exit 1; }
PDK_SKIP_PSP103=0
source "${ROOT}/scripts/lib-pdk.sh"
source "${ROOT}/scripts/lib-record.sh"
export PDK_ROOT
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1
N="${CP_MC_N:-200}"; NC="${CP_MC_N_CONTROL:-20}"; SEED="${CP_MC_SEED:-20261103}"
REC_DIR="${RECORD_DIR:-${ROOT}/sim/cp-mc/records}"; mkdir -p "${REC_DIR}"
YPY="${YIELD_PY:-${ROOT}/.venv/bin/python}"
"${ROOT}/design/netlist.sh" --check cp >/dev/null 2>&1 || die "design/netlist/cp.spice is stale against design/cp.sch (run design/netlist.sh)"
if [ -n "${CP_MC_WORK:-}" ]; then WORK="${CP_MC_WORK}"; mkdir -p "${WORK}"; else WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT; fi

# Negative control: the same deterministic skew as scripts/test-cp-dc-negative.sh (up-leg mirror + cascode 3.8u -> 4.6u, ~ +20 % I_up).
awk '/^\.subckt cp_leg_p/ {p=1} /^\.ends/ {p=0} p && /^XM[12] / { sub(/w=3\.8u/, "w=4.6u") } {print}' \
  "${ROOT}/design/netlist/cp.spice" > "${WORK}/cp_skewed.spice"
diff -q "${ROOT}/design/netlist/cp.spice" "${WORK}/cp_skewed.spice" >/dev/null && die "the negative-control skew did not change the netlist"

python3 "${ROOT}/sim/cp-mc/make_request.py" --cp-netlist "${ROOT}/design/netlist/cp.spice" --outdir "${WORK}/nom" --n "${N}" --seed "${SEED}"
python3 "${ROOT}/sim/cp-mc/make_request.py" --cp-netlist "${WORK}/cp_skewed.spice" --outdir "${WORK}/neg" --n "${NC}" --seed "${SEED}"
for d in nom neg; do klt sim "${WORK}/${d}/request.json" --dry-run --format json >/dev/null || die "${d} request failed klt sim --dry-run"; done
[ "${DRY}" = 1 ] && { echo "run-cp-mc: both requests validate (dry run, nothing submitted)"; exit 0; }
[ -x "${YPY}" ] && "${YPY}" -c 'import klt_yield_native' 2>/dev/null || die "no python with klt_yield_native at ${YPY}; see sim/cp-mc/README.md (build it in a venv in the worktree, never host-wide)"
KLTY="$(dirname "${YPY}")/klt"

record_stamp
ID="$(date -u +%Y%m%d-%H%M%S)-${COMMIT}${DIRTY}"
REC="${REC_DIR}/${ID}.md"; [ ! -e "${REC}" ] || die "${REC} exists; records are append-only"

# klt sim exits 3 when any sample fails a limit (expected, informative); 4+ and 1 are real errors.
run_sim() { # name
  local rc=0 att=""
  case "$1" in nom) att="${CP_MC_ATTACH_NOM:-}";; neg) att="${CP_MC_ATTACH_NEG:-}";; esac
  klt sim "${WORK}/$1/request.json" --backend batch ${att:+--attach "${att}"} ${CP_MC_RESUME:+--resume} ${CP_MC_WAIT:+--wait-for-capacity "${CP_MC_WAIT}"} --max-units-per-job "${CP_MC_UNITS_PER_JOB:-696}" --max-concurrent-jobs "${CP_MC_JOBS:-3}" --format json -o "${WORK}/$1/out" > "${WORK}/$1/report.json" 2> "${WORK}/$1/stderr.txt" || rc=$?
  cp "${WORK}/$1/stderr.txt" "${REC_DIR}/${ID}-$1-klt-sim-stderr.txt"
  if [ "${rc}" != 0 ] && [ "${rc}" != 3 ]; then
    echo "run-cp-mc: BATCH SUBMIT/RUN FAILED for $1 (klt sim exit ${rc}); not falling back to a local grid. stderr:" >&2
    tail -20 "${WORK}/$1/stderr.txt" >&2; exit 1
  fi
}
run_sim nom; run_sim neg

"${KLTY}" yield-samples "${WORK}/nom/report.json" --negative-control "${WORK}/neg/report.json" \
  --description "up-leg mirror+cascode widened 3.8u->4.6u (~+20 % I_up), same seed and grid" --format json > "${WORK}/samples.json"
yrc=0; "${KLTY}" yield "${WORK}/samples.json" --limits "${ROOT}/sim/cp-mc/limits-target.json" --format json > "${WORK}/yield-target.json" 2> "${WORK}/yield-target.err" || yrc=$?
"${KLTY}" yield "${WORK}/samples.json" --limits "${ROOT}/sim/cp-mc/limits-fallback.json" --format json > "${WORK}/yield-fallback.json" 2> "${WORK}/yield-fallback.err" || true
"${KLTY}" yield "${WORK}/samples.json" --limits "${ROOT}/sim/cp-mc/limits-target.json" > "${WORK}/yield-target.txt" 2>&1 || true
cp "${WORK}/nom/request.json" "${REC_DIR}/${ID}-request.json"
cp "${WORK}/neg/request.json" "${REC_DIR}/${ID}-request-negative-control.json"
cp "${WORK}/yield-target.json" "${REC_DIR}/${ID}-yield-target.json"
cp "${WORK}/yield-fallback.json" "${REC_DIR}/${ID}-yield-fallback.json"
cp "${WORK}/yield-target.txt" "${REC_DIR}/${ID}-yield-target.txt"
python3 "${ROOT}/sim/cp-mc/summarize.py" "${WORK}/nom/report.json" "${WORK}/neg/report.json" "${REC_DIR}/${ID}-yield-target.json" \
  "${REC_DIR}/${ID}-yield-fallback.json" --id "${ID}" --commit "${COMMIT}${DIRTY}" --n "${N}" --n-control "${NC}" --seed "${SEED}" \
  --pdk-tag "$(jq -r .pdk.release_tag "${PINS}")" --host "$(hostname)" --klt "$(klt --version 2>&1 | head -1)" > "${REC}"
echo "record: ${REC#"${ROOT}/"} (klt yield target-limits exit ${yrc})"
