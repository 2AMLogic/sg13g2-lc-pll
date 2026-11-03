#!/usr/bin/env bash
# Divider elaboration (five N codes, one .op), a relaxed-clock count check (two codes, one transient) and a SPEED check
# at the prescaler output rates 625 / 687.5 MHz (issue #61): THREE local ngspice runs, nominal corner only. Writes an append-only record under sim/divider-elab/records/.
# The count check shows the counter LOGIC divides as N = 8M + 2A at a 100 MHz clock; the speed check exits nonzero
# (after writing the record) if FB does not divide N = 100 at 625 or 687.5 MHz.
#   scripts/run-divider-elab.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { echo "run-divider-elab: error: $*" >&2; exit 1; }
source "${ROOT}/scripts/lib-pdk.sh"
"${ROOT}/design/netlist.sh" --check divider >/dev/null 2>&1 || die "design/netlist/divider.spice is stale (run design/netlist.sh)"
REC_DIR="${RECORD_DIR:-${ROOT}/sim/divider-elab/records}"; mkdir -p "${REC_DIR}"
WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT
printf 'set ngbehavior=hsa\n' > "${WORK}/.spiceinit"
NET="${ROOT}/design/netlist/divider.spice"
for k in elab tran speed; do
  sed -e "s|@@MODELS_DIR@@|${MODELS}|g" -e "s|@@DIV_NETLIST@@|${NET}|g" -e "s|@@OSDI_PSP@@|${OSDI_PSP}|g" -e "s|@@OUT_DIR@@|${WORK}|g" \
    "${ROOT}/sim/divider-elab/divider_${k}.spice.tmpl" > "${WORK}/divider_${k}.spice"
  grep -vE '^[[:space:]]*\*' "${WORK}/divider_${k}.spice" | grep -q '@@' && die "unsubstituted placeholder in divider_${k}"
done
COMMIT="$(git -C "${ROOT}" rev-parse --short=7 HEAD)"
ID="$(date -u +%Y%m%d-%H%M%S)-${COMMIT}"; REC="${REC_DIR}/${ID}.md"
[ ! -e "${REC}" ] || die "${REC} exists; records are append-only"
( cd "${WORK}" && HOME="${WORK}" "${NGSPICE}" -b divider_elab.spice ) > "${WORK}/elab.log" 2>&1 || die "elaboration run failed; see ${WORK}/elab.log"
grep -q '^ELAB_OK' "${WORK}/elab.log" || die "elaboration did not complete"
( cd "${WORK}" && HOME="${WORK}" "${NGSPICE}" -b divider_tran.spice ) > "${WORK}/tran.log" 2>&1 || die "transient run failed"
[ -s "${WORK}/div.data" ] || die "no transient data"
( cd "${WORK}" && HOME="${WORK}" "${NGSPICE}" -b divider_speed.spice ) > "${WORK}/speed.log" 2>&1 || die "speed run failed; see ${WORK}/speed.log"
[ -s "${WORK}/speed.data" ] || die "no speed data"
SPEED_RC=0; SPEED="$(python3 -I "${ROOT}/scripts/divider_speed_counts.py" "${WORK}/speed.data")" || SPEED_RC=$?
[ -n "${SPEED}" ] || die "speed check produced no output"
COUNTS="$(python3 -I "${ROOT}/scripts/divider_counts.py" "${WORK}/div.data")"
grep -vE 'Reference value' "${WORK}/tran.log" > "${REC_DIR}/${ID}-ngspice.txt"
{
  echo "# divider elaboration and count check ${ID}"
  echo
  echo "- **Netlist**: \`design/netlist/divider.spice\` sha256 \`$(sha256sum "${NET}" | cut -d' ' -f1)\`, checked fresh against \`design/divider.sch\` before the run"
  echo "- **Simulator**: \`${NG_VER}\`, three local \`ngspice -b\` runs; PDK model libraries hash-checked against \`sim/pins.json\`; corners \`hbt_typ\`, \`mos_tt\`, \`cap_typ\`, 27 C, 3.3 V. **Nominal only: no corner grid.**"
  echo "- **Elaboration** (30 ns transient, one deck, five codes tied): N = 100 (M=12, A=2), 90 (11,1), 110 (13,3), and A = 0 and A = 3 at M = 12 all parse and run. Elaboration only."
  echo "- **Count check method** (transient 640 ns, 100 MHz clock, ideal sources): input 0.4 Vpp differential at 3.18 V common mode; the clock is the converter output \`xd100.ck\`. A window is the interval between consecutive rising \`FB\` edges; clocks are rising \`CK\` edges in it, MC-high clocks are those where MC was high 0.3 ns before the edge; N = 8 x clocks + 2 x MC-high (prescaler P = 8/10, issue #43)."
  echo
  echo "| code | FB window (ns) | CK cycles | MC-high cycles | N |"
  echo "|---|---|---|---|---|"
  echo "${COUNTS}" | awk '{printf "| %s | %s | %s | %s | %s |\n",$1,$2,$3,$4,$5}'
  echo
  echo "- **Speed check method** (transient 150 ns, nominal corner, ngspice, N = 100): the real chain (\`cml2cmos\` + counters) fed by an ideal 0.4 Vpp differential sine at 3.18 V common mode, and, as a bisect control, the same counters fed by an ideal 0..3.3 V clock (converter bypassed), each at 625 MHz (5.0 GHz / 8) and 687.5 MHz (5.5 GHz / 8). Pass = at least 3 rising \`FB\` edges and N = 8 x clocks + 2 x MC-high = 100 on every full window."
  echo
  echo "| case | FB rising edges | CK cycles (last window) | MC-high cycles | N |"
  echo "|---|---|---|---|---|"
  echo "${SPEED}" | awk '{printf "| %s | %s | %s | %s | %s |\n",$1,$2,$3,$4,$5}'
  echo
  if [ "${SPEED_RC}" -eq 0 ]; then echo "- **Speed verdict**: PASS (simulated, nominal corner)."; else echo "- **Speed verdict**: FAIL, the divider does not divide N = 100 at the prescaler output rate (simulated, nominal corner, not measured). The bench exited nonzero."; fi
  echo "- **Not covered**: the real prescaler driving the converter, other codes' behaviour (only 100 and 90 are counted), any corner other than nominal (including at speed), noise. Simulated, not measured."
} > "${REC}"
echo "wrote ${REC#"${ROOT}/"}"
[ "${SPEED_RC}" -eq 0 ] || { echo "run-divider-elab: SPEED CHECK FAILED (see ${REC#"${ROOT}/"})" >&2; exit 1; }
