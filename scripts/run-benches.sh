#!/usr/bin/env bash
# Cold-start command for T1 item 9 (sim/testbench-inventory.json): from a fresh clone with the pinned PDK and
# ngspice, run every simulation bench that can run unattended, one local ngspice at a time, nominal corner,
# and fail if any of them does not complete. Records go to a SCRATCH directory (BENCH_RECORD_DIR, default a
# temp dir removed on exit), not into sim/*/records/, so attesting does not append evidence; to keep a
# record, run the bench's own script (see README "Reproduce the records").
#
#   scripts/run-benches.sh
#
# Runs, in order: run-cp-dc, run-pfd-sweep, run-prescaler-g1, run-prescaler-g3, run-divider-elab,
# run-loop-tran, run-loop-power, run-jitter. NOT run: run-vco-smoke (needs openvaf-r and the network; its only
# committed record is a failure, so it is inventoried but not part of this command), the negative controls
# (scripts/test-*-negative.sh), and any corner grid (those go through `klt sim`, #39/#40).
#
# Environment: PDK_ROOT, NGSPICE (scripts/lib-pdk.sh; ngspice 47 is pinned, an older build only warns and
# cannot load OSDI v0.4), PYTHON (default: .venv/bin/python if present, else python3; needs numpy for run-jitter).
# A bench's verdict (locked or not, within budget or not) is in its record; this command fails only when a
# bench could not run to completion.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { echo "run-benches: error: $*" >&2; exit 1; }
if [ -z "${PYTHON:-}" ]; then [ -x "${ROOT}/.venv/bin/python" ] && PYTHON="${ROOT}/.venv/bin/python" || PYTHON=python3; fi
export PYTHON
if [ -n "${BENCH_RECORD_DIR:-}" ]; then OUT="${BENCH_RECORD_DIR}"; mkdir -p "${OUT}"; else OUT="$(mktemp -d)"; trap 'rm -rf "${OUT}"' EXIT; fi
cd "${ROOT}"
for b in cp-dc pfd-sweep prescaler-g1 prescaler-g3 divider-elab loop-tran loop-power jitter; do
  echo "== run-${b}.sh"
  RECORD_DIR="${OUT}/${b}" "${ROOT}/scripts/run-${b}.sh" || die "run-${b}.sh failed"
done
echo "run-benches: all benches ran to completion (records in ${OUT} were scratch)"
