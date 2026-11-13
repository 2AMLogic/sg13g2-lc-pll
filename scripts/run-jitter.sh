#!/usr/bin/env bash
# Spec row 8 jitter bench, method L (spec section 4): runs the linear phase-domain model (sim/loop-model) at the
# design point and across the Kvco range, and writes a dated append-only record that carries every section 4
# method field next to the number. No ngspice, no PDK: method L is arithmetic. The method T transient-noise
# cross-check is NOT run here and the record says why. Row 8 is NOT graded.
#
#   scripts/run-jitter.sh
#
# Environment: PYTHON (default python3; needs numpy), RECORD_DIR (default sim/jitter/records),
#   LOOP_FILTER (default sim/loop-model/loop-filter.json; a different file is recorded by path and sha256).
# Exit 0 if the model ran and the record was written; non-zero if numpy is missing or the model failed.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { echo "run-jitter: error: $*" >&2; exit 1; }
source "${ROOT}/scripts/lib-record.sh"
PY="${PYTHON:-python3}"
"${PY}" -c 'import numpy' 2>/dev/null || die "${PY} has no numpy (the method-L model needs it): use a venv, e.g. python3 -m venv .venv && .venv/bin/pip install numpy, then PYTHON=.venv/bin/python scripts/run-jitter.sh"
command -v jq >/dev/null || die "jq is required"
LOOP_FILTER="${LOOP_FILTER:-${ROOT}/sim/loop-model/loop-filter.json}"
[ -f "${LOOP_FILTER}" ] || die "${LOOP_FILTER} not found"
REC_DIR="${RECORD_DIR:-${ROOT}/sim/jitter/records}"; mkdir -p "${REC_DIR}"
WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT
set +e
"${PY}" -I "${ROOT}/sim/loop-model/loop_model.py" --filter "${LOOP_FILTER}" --out "${WORK}/lm.json" > "${WORK}/lm.txt" 2>&1
RC=$?
set -e
[ -s "${WORK}/lm.json" ] || { cat "${WORK}/lm.txt" >&2; die "the model produced no result"; }
record_stamp sim scripts
ID="$(date -u +%Y%m%d-%H%M%S)-${COMMIT}${DIRTY}"
REC="${REC_DIR}/${ID}.md"
[ ! -e "${REC}" ] || die "${REC} exists; records are append-only"
cp "${WORK}/lm.txt" "${REC_DIR}/${ID}-model.txt"
P='.points[] | select(.kvco_hz_per_v==480000000 and .icp_a==0.0002)'
JIT_PS="$(jq -r "${P} | .jitter_rms_s*1e12*1000|round/1000" "${WORK}/lm.json")"
SP="$(jq -r "${P} | .sigma_phi_sq_rad2_by_term | add | sqrt*1000*100|round/100" "${WORK}/lm.json")"
FC="$(jq -r "${P} | .f_c_hz/1e6*1000|round/1000" "${WORK}/lm.json")"
PM="$(jq -r "${P} | .pm_deg*10|round/10" "${WORK}/lm.json")"
{
  echo "# jitter run ${ID}"
  echo
  GATE=""; [ "${RC}" = 0 ] || GATE="MODEL GATE FAILED (exit ${RC}: a design-range point is outside f_c 0.5-2 MHz or PM < 45 deg; this filter does not meet spec row 5). "
  echo "**${GATE}Result (method L, PARTIAL, simulated by a model, not measured; row 8 NOT graded): ${JIT_PS} ps rms integrated 10 kHz-10 MHz at the design point (Kvco 480 MHz/V, I_cp 200 uA, N = 100); sigma_phi = ${SP} mrad; f_c ${FC} MHz, PM ${PM} deg.** The number covers only two terms (the VCO's *target* 1/f^2 line and R1 thermal noise). The reference, PFD/CP and divider/prescaler terms are **zero placeholders**, not zero noise, so this is a floor, not an estimate of the loop's jitter. Spec row 8 is <= 1.0 ps."
  echo
  echo "- **Method (spec section 4, primary)**: L, the linear phase-domain model of a type-II third-order charge-pump PLL, L(s) = I_cp Kvco Z(s)/(N s), Z = (R1-C1 || C2) then the unloaded R3-C3 pole. First-order: no in-loop peaking beyond L(s), no sampling-time effects, no charge-pump nonlinearity, no supply or substrate coupling into the tank."
  echo "- **Inputs, each with its source**: N = 100, f_ref = 50 MHz, f_out = 5.0 GHz (spec rows 1-3); loop filter \`${LOOP_FILTER#"${ROOT}/"}\` sha256 \`$(sha256sum "${LOOP_FILTER}" | cut -d' ' -f1)\`; I_cp = 200 uA (row 6); Kvco = 480 MHz/V (section 3 geometric mid); VCO phase noise = the 1/f^2 line through -105 dBc/Hz at 1 MHz, a **target** from \`sg13g2-vco\` row 4 whose method is open there, **not measured**; R1 thermal noise 4kT R1 at 300.15 K."
  echo "- **Estimator**: integrate L(f) over 10 kHz-10 MHz on a log grid, 30 points per decade, trapezoid on log f; sigma_phi^2 = 2 integral L(f) df; sigma_t = sigma_phi/(2 pi f_out). Deterministic given its inputs: no run length, no window, no variance."
  echo "- **Method T cross-check (window >= 100 us, >= 8 windows): NOT RUN.** Reason: it needs a locked 5 GHz loop with noise sources. The closed-loop bench (\`sim/loop-tran\`) uses a noiseless behavioural VCO and divider, and an ngspice transient-noise run of >= 800 us of a 5 GHz loop is gate G6 (unresolved). Measurement of the in-band terms by ngspice \`.noise\` (method N) is owed and not run."
  echo "- **Corners**: the design point only; the C-grid is graded later through \`klt sim\`. The Kvco range is covered in the table below at I_cp = 200 uA."
  echo "- **Model**: \`sim/loop-model/loop_model.py\` sha256 \`$(sha256sum "${ROOT}/sim/loop-model/loop_model.py" | cut -d' ' -f1)\`, run with Python $("${PY}" -c 'import sys;print(sys.version.split()[0])') and numpy $("${PY}" -c 'import numpy;print(numpy.__version__)'); exit status ${RC} (non-zero means the model's own f_c / PM gate flagged a design-range point; full output in [\`${ID}-model.txt\`](${ID}-model.txt))."
  echo "- **Commit**: \`${COMMIT}${DIRTY}\` of this repository"
  echo "- **Host**: $(hostname), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "| Kvco (MHz/V) | I_cp (uA) | f_c (MHz) | PM (deg) | jitter, method L partial (ps rms) |"
  echo "|---|---|---|---|---|"
  jq -r '.points[] | select(.icp_a==0.0002) | "| \(.kvco_hz_per_v/1e6) | \(.icp_a*1e6) | \(.f_c_hz/1e6*1000|round/1000) | \(.pm_deg*10|round/10) | \(.jitter_rms_s*1e12*1000|round/1000) |"' "${WORK}/lm.json"
  echo
  echo "Per-term sigma_phi^2 at the design point (rad^2): $(jq -r "${P} | .sigma_phi_sq_rad2_by_term | to_entries | map(\"\(.key) = \(.value)\") | join(\"; \")" "${WORK}/lm.json")"
} > "${REC}"
echo "record: ${REC#"${ROOT}/"}"
echo "jitter (method L, partial): ${JIT_PS} ps"
