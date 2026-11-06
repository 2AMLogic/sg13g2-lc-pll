#!/usr/bin/env bash
# Gate G2 bench: the pinned sg13g2-vco (unmodified) with and without the prescaler input on the tank.
# Two local ngspice runs (unloaded, loaded), NOMINAL corner only, 3 Vctrl points each. Not a corner grid:
# the C-grid needs the mosvar OSDI varactor, which `klt sim` cannot express (klayout-tools#2511).
#
#   scripts/run-vco-prescaler-load.sh
#
# Environment: PDK_ROOT, NGSPICE, OPENVAF_R, OPENVAF_LD_LIBRARY_PATH (see scripts/run-vco-smoke.sh).
# Writes sim/vco-prescaler-load/records/<id>.md (append-only) and prints its path.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FETCHED="${ROOT}/.fetched"
die() { echo "run-vco-prescaler-load: error: $*" >&2; exit 1; }

"${ROOT}/scripts/fetch-vco.sh" >/dev/null
PDK_SKIP_PSP103=1
source "${ROOT}/scripts/lib-pdk.sh"
source "${ROOT}/scripts/lib-record.sh"

PRESC="${ROOT}/design/netlist/prescaler.spice"
"${ROOT}/design/netlist.sh" --check prescaler >/dev/null 2>&1 || die "design/netlist/prescaler.spice is stale against design/prescaler.sch"

# OSDI: compile the PDK's own mosvar.va (same steps as run-vco-smoke.sh)
VA_DIR="${PDK_DIR}/libs.tech/verilog-a/mosvar"
va_sha="$(sha256sum "${VA_DIR}/mosvar.va" | cut -d' ' -f1)"
[ "${va_sha}" = "$(jq -r .osdi.verilog_a_sha256 "${PINS}")" ] || die "mosvar.va is not the pinned one"
OSDI="${FETCHED}/osdi/mosvar.osdi"; mkdir -p "${FETCHED}/osdi"
OVAF="${OPENVAF_R:-$(command -v openvaf-r || true)}"
[ -n "${OVAF}" ] || die "openvaf-r not found; set OPENVAF_R"
rm -f "${OSDI}"
LD_LIBRARY_PATH="${OPENVAF_LD_LIBRARY_PATH:+${OPENVAF_LD_LIBRARY_PATH}:}${LD_LIBRARY_PATH:-}" \
  "${OVAF}" -I "${VA_DIR}" -o "${OSDI}" "${VA_DIR}/mosvar.va" >/dev/null 2>&1 || die "openvaf-r failed on mosvar.va"
osdi_sha="$(sha256sum "${OSDI}" | cut -d' ' -f1)"

TMPL="${FETCHED}/sg13g2-vco/design/vco.spice"
IND="${FETCHED}/sg13g2-vco/sim/inductor-model/sg13g2_inductor_em.spice"
BTMPL="${ROOT}/sim/vco-prescaler-load/load.spice.tmpl"
WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT
write_spiceinit "${WORK}"

LOAD_BLOCK=".include ${PRESC}
IRF vdd iref dc 50u
VMC mc 0 dc 0
X1 outp outn mc iref pdp pdn vdd 0 prescaler
.ic v(x1.hp)=3.2 v(x1.hn)=3.0 v(x1.x2.mp)=3.0 v(x1.x2.mn)=3.2"

for tag in unloaded loaded; do
  load=""; [ "${tag}" = loaded ] && load="${LOAD_BLOCK}"
  {
    # the fetched deck up to (not including) its own .control block, placeholders substituted only
    sed -e "s|@@MODELS_DIR@@|${MODELS}|g" -e "s|@@IND_MODEL@@|${IND}|g" -e "s|@@OSDI_MOSVAR@@|${OSDI}|g" "${TMPL}" | sed '/^\.control/,$d'
    sed -e "s|@@OSDI@@|${OSDI}|g" -e "s|@@OUT@@|${WORK}|g" -e "s|@@TAG@@|${tag}|g" "${BTMPL}" | awk -v ld="${load}" '{ if ($0 == "@@LOAD@@") print ld; else print }'
  } > "${WORK}/${tag}.spice"
  check_deck_placeholders "${WORK}/${tag}.spice"
  ( cd "${WORK}" && HOME="${WORK}" "${NGSPICE}" -b "${tag}.spice" ) > "${WORK}/${tag}.log" 2>&1 || echo "warning: ngspice exit status non-zero for ${tag}" >&2
done

COMMIT="$(jq -r '.imports[] | select(.from=="2AMLogic/sg13g2-vco") | .commit' "${ROOT}/reuse.lock.json")"
SHA="$(git -C "${ROOT}" rev-parse --short HEAD)$(git -C "${ROOT}" diff --quiet HEAD -- . 2>/dev/null || echo -dirty)"
ID="$(date -u +%Y%m%d-%H%M%S)-${SHA}"
REC_DIR="${ROOT}/sim/vco-prescaler-load/records"; mkdir -p "${REC_DIR}"
REC="${REC_DIR}/${ID}.md"; [ ! -e "${REC}" ] || die "${REC} exists; records are append-only"
cat "${WORK}/unloaded.log" > "${REC_DIR}/${ID}-ngspice-unloaded.txt"
cat "${WORK}/loaded.log" > "${REC_DIR}/${ID}-ngspice-loaded.txt"
JSON="${WORK}/result.json"
python3 -I "${ROOT}/sim/vco-prescaler-load/analyze.py" "${WORK}" > "${JSON}"

g1="$(ls "${ROOT}"/sim/prescaler-g1/records/*-24cdbb1-dirty.md 2>/dev/null | tail -1 || true)"
{
  echo "# vco-prescaler-load run ${ID}"
  echo
  jq -r '
    def f(x): if x == null then "NA" else (x * 1000 | round / 1000 | tostring) end;
    . as $r |
    "**Result (simulated, nominal corner only, not measured)**: see the table; verdicts below are against spec rows 1, 6 (proxy), 7.",
    "",
    "| Vctrl (V) | case | f_osc (GHz) | Vpp diff (V) | t90 (ns) | cycles in 10-20 ns |",
    "|---|---|---|---|---|---|",
    (["0","1.65","3.3"][] as $v | ["unloaded","loaded"][] as $t | $r[$t]["tran_"+$v] as $m |
      "| \($v) | \($t) | \(if $m then f($m.f_ghz) else "NA" end) | \(if $m then f($m.vpp) else "NA" end) | \(if $m then f($m.t90_ns) else "NA" end) | \(if $m then $m.cycles else 0 end) |"),
    "",
    "Small-signal tank probe at the unstable symmetric operating point (differential 1 A current probe, 3-6 GHz; reported as the pull of the load on the resonance only, no loss or gain is read from it):",
    "",
    "| case | f at max abs(Z) (GHz) | abs(Z) peak (ohm) |",
    "|---|---|---|",
    (["unloaded","loaded"][] as $t | $r[$t].ac as $a |
      "| \($t) | \(if $a then f($a.f_res_ghz) else "NA" end) | \(if $a then f($a.z_peak_ohm) else "NA" end) |")
  ' "${JSON}"
  jq -r '
    def band(t): [("0","1.65","3.3") as $v | .[t]["tran_"+$v].f_ghz | select(. != null and . >= 4.5 and . <= 5.5)] | length;
    def minvpp(t): [("0","1.65","3.3") as $v | .[t]["tran_"+$v].vpp | select(. != null)] | min;
    def osc(t): [("0","1.65","3.3") as $v | .[t]["tran_"+$v] | select(. != null and .cycles > 5)] | length;
    "",
    "**Verdicts (nominal corner only; the C-grid is open)**",
    "",
    "- Oscillation: unloaded \(osc("unloaded"))/3, loaded \(osc("loaded"))/3 Vctrl points oscillate (more than 5 cycles in 10-20 ns).",
    "- Row 7 swing >= 0.40 Vpp differential: minimum over Vctrl unloaded \(minvpp("unloaded") * 1000 | round / 1000) V, loaded \(minvpp("loaded") * 1000 | round / 1000) V: \(if minvpp("loaded") >= 0.40 then "PASS" else "FAIL" end) with the load.",
    "- Row 1 band 4.5-5.5 GHz: Vctrl points inside the band, unloaded \(band("unloaded"))/3, loaded \(band("loaded"))/3: \(if band("loaded") > 0 then "at least one point in band" else "FAIL, and not caused by the load: the unloaded VCO is already outside the band at all three points in this flow" end). 5.0 GHz is not reached in either case.",
    "- Row 1/2 shift from the load at Vctrl 1.65 V: \(((.loaded["tran_1.65"].f_ghz - .unloaded["tran_1.65"].f_ghz) * 1000 | round)) MHz (\((((.loaded["tran_1.65"].f_ghz / .unloaded["tran_1.65"].f_ghz - 1) * 10000 | round) / 100)) %).",
    "- Row 6 startup: all loaded points start from the 10 mV kick; t90 loaded vs unloaded is in the table. The g_m / G_loss >= 3.0 ratio is not evaluated."
  ' "${JSON}"
  echo
  echo "- **Load presented** (the prescaler input, \`design/netlist/prescaler.spice\` sha256 \`$(sha256sum "${PRESC}" | cut -d' ' -f1)\`, instance \`X1\` on OUTP/OUTN, MC=0, ideal IREF 50 uA): the G1 device-level figure, 1.373 fF differential and -29.3 uS at 5.0 GHz, nominal corner (\`$(basename "${g1:-none}")\`). Routing capacitance is not included (budget 2.1 fF device plus routing). Here the actual input is attached, so the effect is simulated directly rather than inferred from that number."
  echo "- **VCO**: \`2AMLogic/sg13g2-vco@${COMMIT}\` unmodified; deck = fetched \`design/vco.spice\` (sha256 \`$(sha256sum "${TMPL}" | cut -d' ' -f1)\`) up to its \`.control\` block, placeholders substituted; this bench appends only the load and its own \`.control\`. Inductor model sha256 \`$(sha256sum "${IND}" | cut -d' ' -f1)\`."
  echo "- **Method**: per case one \`ngspice -b\`: \`op\`, a 3-6 GHz \`ac\` current-probe sweep, then \`tran 1p 20n 0 2p\` at Vctrl = 0, 1.65, 3.3 V from the deck's 10 mV differential \`.ic\` kick. f_osc, Vpp: mean-crossing count and peak-to-peak over 10-20 ns; t90: first half-cycle peak-to-peak at 90 % of final Vpp (see \`sim/vco-prescaler-load/analyze.py\`). Startup margin row 6 is the ratio g_m / tank loss >= 3.0; it is **not** extracted here. The t90 loaded against unloaded is the only startup evidence."
  echo "- **Corner**: typical only (\`hbt_typ\`, \`mos_tt\`, \`cap_typ\`), 27 C, 3.3 V. The C-grid (135 + 18) was **not** run: the varactor is an OSDI model and \`klt sim\` cannot express an OSDI deck (klayout-tools#2511); hand-launching a local grid is not allowed on this host. Gate G2 therefore stays open for the C-grid."
  echo "- **Simulator**: \`${NG_VER}\` (\`${NGSPICE}\`); ${NG_PIN_STATUS}. OSDI \`mosvar.osdi\` from the PDK's \`mosvar.va\` (sha256 \`${va_sha}\`), output sha256 \`${osdi_sha}\`. PDK IHP-Open-PDK $(jq -r .pdk.release_tag "${PINS}")."
  echo "- **Commit**: \`${SHA}\`. Host: $(hostname), $(date -u +%Y-%m-%dT%H:%M:%SZ). ngspice logs: \`${ID}-ngspice-unloaded.txt\`, \`${ID}-ngspice-loaded.txt\`."
} > "${REC}"
echo "record: ${REC#"${ROOT}/"}"
sed -n '1,25p' "${REC}"
