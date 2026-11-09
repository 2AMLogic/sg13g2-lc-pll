#!/usr/bin/env bash
# Divider elaboration (five N codes, one .op), a relaxed-clock count check (two codes, one transient) and a SPEED check
# at the prescaler output rates 625 / 687.5 MHz (issue #61; N = 100 plus A = 0 / A = 7 at M = 12): FIVE local ngspice runs, run one after another, nominal corner only (issue #155: the real chains and the ideal-clock control counters are separate decks, as they get no common operating point). Writes an append-only record under sim/divider-elab/records/.
# The count check shows the counter LOGIC divides as N = 8M + A (P = 8/9) at a 100 MHz clock; the speed check exits nonzero
# (after writing the record) if FB does not divide as expected at 625 or 687.5 MHz.
#   scripts/run-divider-elab.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { echo "run-divider-elab: error: $*" >&2; exit 1; }
source "${ROOT}/scripts/lib-pdk.sh"
source "${ROOT}/scripts/lib-record.sh"
"${ROOT}/design/netlist.sh" --check divider >/dev/null 2>&1 || die "design/netlist/divider.spice is stale (run design/netlist.sh)"
REC_DIR="${RECORD_DIR:-${ROOT}/sim/divider-elab/records}"; mkdir -p "${REC_DIR}"
WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT
write_spiceinit "${WORK}"
NET="${ROOT}/design/netlist/divider.spice"
for k in elab tran speed speedC speedA; do
  sed -e "s|@@MODELS_DIR@@|${MODELS}|g" -e "s|@@DIV_NETLIST@@|${NET}|g" -e "s|@@OSDI_PSP@@|${OSDI_PSP}|g" -e "s|@@OSDI_PSP_NQS@@|${OSDI_PSP_NQS}|g" -e "s|@@OUT_DIR@@|${WORK}|g" \
    "${ROOT}/sim/divider-elab/divider_${k}.spice.tmpl" > "${WORK}/divider_${k}.spice"
  check_deck_placeholders "${WORK}/divider_${k}.spice"
done
record_stamp
ID="$(date -u +%Y%m%d-%H%M%S)-${COMMIT}${DIRTY}"; REC="${REC_DIR}/${ID}.md"
[ ! -e "${REC}" ] || die "${REC} exists; records are append-only"
RUNTIMES=""
run_deck() {   # run_deck NAME DIE-MESSAGE: one local ngspice -b, sequential; appends the wall time to RUNTIMES
  local t0 t1; t0="$(date +%s)"
  ( cd "${WORK}" && HOME="${WORK}" "${NGSPICE}" -b "divider_$1.spice" ) > "${WORK}/$1.log" 2>&1 || die "$2; see ${WORK}/$1.log"
  t1="$(date +%s)"; RUNTIMES="${RUNTIMES}${RUNTIMES:+, }\`divider_$1\` $((t1 - t0)) s"
}
run_deck elab "elaboration run failed"
grep -q '^ELAB_OK' "${WORK}/elab.log" || die "elaboration did not complete"
run_deck tran "transient run failed"
[ -s "${WORK}/div.data" ] || die "no transient data"
run_deck speed "speed run failed"
[ -s "${WORK}/speed.data" ] || die "no speed data"
run_deck speedC "ideal-clock control speed run failed"
[ -s "${WORK}/speedC.data" ] || die "no ideal-clock control speed data"
run_deck speedA "A-code speed run failed"
[ -s "${WORK}/speedA.data" ] || die "no A-code speed data"
SPEED_RC=0; SPEED="$(python3 -I "${ROOT}/scripts/divider_speed_counts.py" "${WORK}/speed.data" "${WORK}/speedC.data")" || SPEED_RC=$?
[ -n "${SPEED}" ] || die "speed check produced no output"
SPEEDA_RC=0; SPEEDA="$(python3 -I "${ROOT}/scripts/divider_speed_counts.py" "${WORK}/speedA.data" A)" || SPEEDA_RC=$?
[ -n "${SPEEDA}" ] || die "A-code speed check produced no output"
[ "${SPEEDA_RC}" -eq 0 ] || SPEED_RC=1
COUNTS="$(python3 -I "${ROOT}/scripts/divider_counts.py" "${WORK}/div.data")"
grep -vE 'Reference value' "${WORK}/tran.log" > "${REC_DIR}/${ID}-ngspice.txt"
{
  echo "# divider elaboration and count check ${ID}"
  echo
  echo "- **Netlist**: \`design/netlist/divider.spice\` sha256 \`$(sha256sum "${NET}" | cut -d' ' -f1)\`, checked fresh against \`design/divider.sch\` before the run"
  echo "- **Simulator**: \`${NG_VER}\`, five local \`ngspice -b\` runs, one at a time; PDK model libraries hash-checked against \`sim/pins.json\`; corners \`hbt_typ\`, \`mos_tt\`, \`cap_typ\`, 27 C, 3.3 V. **Nominal only: no corner grid.**"
  echo "- **Run time** (wall clock, per deck, shared host): ${RUNTIMES}."
  echo "- **Elaboration** (30 ns transient, one deck, five codes tied): N = 100 (M=12, A=4), 90 (11,2), 110 (13,6), and A = 0 and A = 7 at M = 12 all parse and run. Elaboration only."
  echo "- **Count check method** (transient 640 ns, 100 MHz clock, ideal sources): input 0.4 Vpp differential at 3.18 V common mode; the clock is the converter output \`xd100.ck\`. A window is the interval between consecutive rising \`FB\` edges; clocks are rising \`CK\` edges in it, MC-high clocks are those where MC was high 0.3 ns before the edge; N = 8 x clocks + MC-high (prescaler P = 8/9, issue #158)."
  echo
  echo "| code | FB window (ns) | CK cycles | MC-high cycles | N |"
  echo "|---|---|---|---|---|"
  echo "${COUNTS}" | awk '{printf "| %s | %s | %s | %s | %s |\n",$1,$2,$3,$4,$5}'
  echo
  echo "- **Speed check method** (transient 150 ns, nominal corner, ngspice, N = 100): the real chain (\`cml2cmos\` + counters) fed by an ideal 0.4 Vpp differential sine at 3.18 V common mode (deck \`divider_speed\`), and, as a bisect control in its own deck (\`divider_speedC\`, issue #155; the two halves get no common operating point, issue #153), the same counters fed by an ideal 0..3.3 V clock (converter bypassed), each at 625 MHz (5.0 GHz / 8) and 687.5 MHz (5.5 GHz / 8); plus the real chain at M = 12 with A = 0 (expect N = 96) and A = 7 (expect N = 103) at both rates. Pass = at least 3 rising \`FB\` edges and N = 8 x clocks + MC-high = the expected N on every full window."
  echo
  echo "| case | FB rising edges | CK cycles (last window) | MC-high cycles | N | expected N |"
  echo "|---|---|---|---|---|---|"
  { echo "${SPEED}"; echo "${SPEEDA}"; } | awk '{printf "| %s | %s | %s | %s | %s | %s |\n",$1,$2,$3,$4,$5,$6}'
  echo
  if [ "${SPEED_RC}" -eq 0 ]; then echo "- **Speed verdict**: PASS (simulated, nominal corner)."; else echo "- **Speed verdict**: FAIL, the divider does not divide as expected at the prescaler output rate (simulated, nominal corner, not measured). The bench exited nonzero."; fi
  echo "- **Not covered**: the real prescaler driving the converter, other codes' behaviour (only 100 and 90 are counted; the code-to-N map for all of 90-110 is checked at netlist level by sim/prescaler-div89/test_divider_code.py, arithmetic on the tie, not a simulation), any corner other than nominal (including at speed), noise. Simulated, not measured."
} > "${REC}"
echo "wrote ${REC#"${ROOT}/"}"
[ "${SPEED_RC}" -eq 0 ] || { echo "run-divider-elab: SPEED CHECK FAILED (see ${REC#"${ROOT}/"})" >&2; exit 1; }
