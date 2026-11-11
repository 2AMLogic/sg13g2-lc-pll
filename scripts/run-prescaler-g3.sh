#!/usr/bin/env bash
# Gate G3 device-flavour evidence (spec row 4): one local ngspice run, nominal corner only.
#   pairs : the HBT latch pair (cml_latch) against the same CML topology on 3.3 V thick-oxide NMOS
#           (sg13_hv_nmos, three widths), same clock, same tail current, same load resistors. Resistors are
#           the PDK rppd/rhigh instances (cornerRES.lib res_typ, r3_cmc.osdi), as in the committed netlists.
# The former "chain" half (whole /8-/10 prescaler) is retired (DR-006): sim/prescaler-div89 is its successor.
# Writes a dated append-only record under sim/prescaler-g3/records/. Not a corner grid (`klt sim` does those).
#
#   scripts/run-prescaler-g3.sh
#
# Environment: PDK_ROOT, NGSPICE as in scripts/run-cp-dc.sh; PRESC_NETLIST / MOS_NETLIST override the committed
# netlists (recorded by path and sha256); RECORD_DIR (default sim/prescaler-g3/records);
# G3_PAIR_FLIST: sweep frequencies, Hz.
# Exit 0 if the run completed and the record was written (the verdict is in the record).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { echo "run-prescaler-g3: error: $*" >&2; exit 1; }
source "${ROOT}/scripts/lib-pdk.sh"
source "${ROOT}/scripts/lib-record.sh"

PRESC_NETLIST="${PRESC_NETLIST:-${ROOT}/design/netlist/prescaler.spice}"
MOS_NETLIST="${MOS_NETLIST:-${ROOT}/design/netlist/mos_latch.spice}"
[ -f "${PRESC_NETLIST}" ] && [ -f "${MOS_NETLIST}" ] || die "netlist not found (${PRESC_NETLIST}, ${MOS_NETLIST})"
if [ "${PRESC_NETLIST}" = "${ROOT}/design/netlist/prescaler.spice" ] && [ "${MOS_NETLIST}" = "${ROOT}/design/netlist/mos_latch.spice" ]; then
  "${ROOT}/design/netlist.sh" --check prescaler mos_latch >/dev/null 2>&1 || die "design/netlist/{prescaler,mos_latch}.spice is stale against its schematic (run design/netlist.sh)"
fi
grep -q 'rppd\|rhigh' "${MOS_NETLIST}" || echo "run-prescaler-g3: warning: ${MOS_NETLIST} has no PDK resistor instance; cornerRES is loaded anyway" >&2
REC_DIR="${RECORD_DIR:-${ROOT}/sim/prescaler-g3/records}"; mkdir -p "${REC_DIR}"
WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT

AMP=0.1; CCM=2.3; CAMP=0.15
PAIR_FLIST="${G3_PAIR_FLIST:-1e9 1.5e9 2e9 2.5e9 2.75e9 3e9 3.5e9 4e9 5e9 6e9}"
PAIR_STOP=12n; PAIR_T0=4e-9
W1=12u; W2=24u; W3=48u
# MOS width variants: same committed netlist, subckt renamed, the 12u device width replaced.
mkvar() { sed -e "s/^\.subckt mos_latch /.subckt mos_latch_$1 /" -e "s/ w=12u / w=$2 /g" "${MOS_NETLIST}" > "${WORK}/mos_$1.spice"; }
mkvar w1 "${W1}"; mkvar w2 "${W2}"; mkvar w3 "${W3}"
grep -q "w=${W2}" "${WORK}/mos_w2.spice" || die "MOS width variant did not apply (is the committed width still 12u?)"
write_spiceinit "${WORK}"
render() { # template out [extra sed args...]
  local t="$1" o="$2"; shift 2
  sed -e "s|@@MODELS_DIR@@|${MODELS}|g" -e "s|@@PRESC_NETLIST@@|${PRESC_NETLIST}|g" -e "s|@@OUT_DIR@@|${WORK}|g" \
      -e "s|@@AMP@@|${AMP}|g" -e "s|@@CCM@@|${CCM}|g" -e "s|@@CAMP@@|${CAMP}|g" -e "s|@@OSDI_PSP@@|${OSDI_PSP}|g" -e "s|@@OSDI_R3@@|${OSDI_R3}|g" \
      -e "s|@@MOS_NETLIST1@@|${WORK}/mos_w1.spice|g" -e "s|@@MOS_NETLIST2@@|${WORK}/mos_w2.spice|g" -e "s|@@MOS_NETLIST3@@|${WORK}/mos_w3.spice|g" \
      -e "s|@@MOSW1@@|${W1}|g" -e "s|@@MOSW2@@|${W2}|g" -e "s|@@MOSW3@@|${W3}|g" "$@" "${ROOT}/sim/prescaler-g3/$t" > "${WORK}/$o"
  check_deck_placeholders "${WORK}/$o"
}
render g3_pairs.spice.tmpl pairs.spice -e "s|@@FLIST@@|${PAIR_FLIST}|g" -e "s|@@TRAN_STOP@@|${PAIR_STOP}|g"

record_stamp
ID="$(date -u +%Y%m%d-%H%M%S)-${COMMIT}${DIRTY}"
REC="${REC_DIR}/${ID}.md"
[ ! -e "${REC}" ] || die "${REC} exists; records are append-only"

set +e
( cd "${WORK}" && HOME="${WORK}" "${NGSPICE}" -b pairs.spice ) > "${WORK}/pairs.log" 2>&1; RC_PA=$?
set -e
cat "${WORK}/pairs.log" > "${REC_DIR}/${ID}-ngspice.txt"
ls "${WORK}"/pair_* >/dev/null 2>&1 || { echo "run-prescaler-g3: ngspice produced no data (rc=${RC_PA}); see ${REC_DIR}/${ID}-ngspice.txt" >&2; exit 1; }

# analyse FILE COL T0 FEXPECT -> "f_out crossings pkpk ok" (rising zero crossings after T0; ok = f_out within 2 % of
# FEXPECT and pk-pk >= 0.2 V, so a latched DC state or a collapsed swing cannot pass)
analyse() { awk -v col="$2" -v t0="$3" -v fe="$4" '$1>=t0 { v=$col; if (v>mx||!h) mx=v; if (v<mn||!h) mn=v; h=1
    if (n && pv<0 && v>=0) { c++; if(!fi) fi=$1; la=$1 } n=1; pv=v }
  END { fo=(c>1)?(c-1)/(la-fi):0; ok=(fo>0.98*fe && fo<1.02*fe && (mx-mn)>=0.2); printf "%.6e %d %.3f %s\n", fo, c, mx-mn, ok?"pass":"FAIL" }' "$1"; }

# a flavour's limit is the last pass before the first fail (contiguous from the lowest frequency)
PAIRROWS=""; LIMP=("" "" "" ""); FFP=("" "" "" "")
for f in ${PAIR_FLIST}; do
  fe="$(awk -v f="$f" 'BEGIN{print f/2}')"; row="| $(awk -v f="$f" 'BEGIN{printf "%.2f", f/1e9}')"
  for k in 0 1 2 3; do
    read -r fo c pp ok < <(analyse "${WORK}/pair_${f}" "$((2 + 2 * k))" "${PAIR_T0}" "${fe}")
    row+=" | $(awk -v a="$fo" -v pp="$pp" -v ok="$ok" 'BEGIN{printf "%.3f GHz, %.2f V, %s", a/1e9, pp, ok}')"
    if [ "$ok" = pass ]; then [ -n "${FFP[$k]}" ] || LIMP[$k]="$f"; else [ -n "${FFP[$k]}" ] || FFP[$k]="$f"; fi
  done
  PAIRROWS+="${row} |"$'\n'
done
ghz() { [ -n "$1" ] && awk -v a="$1" 'BEGIN{printf "%.2f GHz", a/1e9}' || echo "none"; }
lim_txt() { # lastpass firstfail
  if [ -z "$1" ]; then echo "does not divide at the lowest swept frequency"
  elif [ -n "$2" ]; then echo "last pass $(ghz "$1"), first fail $(ghz "$2")"
  else echo "passes at every swept frequency up to $(ghz "$1")"; fi; }

# Verdicts
HBT_OK=no; awk -v a="${LIMP[0]:-0}" 'BEGIN{exit !(a>=2.75e9)}' && HBT_OK=yes
MOS_BEST="${LIMP[1]:-0}"; for k in 2 3; do awk -v a="${LIMP[$k]:-0}" -v b="${MOS_BEST}" 'BEGIN{exit !(a>b)}' && MOS_BEST="${LIMP[$k]}"; done
MOS_OK=no; awk -v a="${LIMP[1]:-0}" -v b="${LIMP[2]:-0}" -v c="${LIMP[3]:-0}" 'BEGIN{m=a; if(b>m)m=b; if(c>m)m=c; exit !(m>=2.75e9)}' && MOS_OK=yes
case "${HBT_OK}/${MOS_OK}" in
  yes/no) CHOICE="HBT: the HBT latch pair divides up to the 2.75 GHz stage-2 clock (spec row 4 range 2.5-2.75 GHz), no tested HV-MOS width does at the same tail current and load." ;;
  yes/yes) CHOICE="NOT DECIDED by this run: both flavours reach 2.75 GHz at the same tail current and load, so the choice rests on other grounds (area, input load, corners), none of which this nominal bench covers." ;;
  *) CHOICE="NOT DECIDED: the HBT pair itself does not reach 2.75 GHz in this run." ;;
esac

NLSHA="$(sha256sum "${PRESC_NETLIST}" | cut -d' ' -f1)"; MOSSHA="$(sha256sum "${MOS_NETLIST}" | cut -d' ' -f1)"
ovr() { [ "$1" = "$2" ] && echo ", checked against its schematic with design/netlist.sh --check" || echo " (NOT the committed netlist: an override)"; }
{
  echo "# prescaler-g3 run ${ID}"
  echo
  echo "**Result (simulated, nominal corner only, not measured): bare HBT latch-pair /2 limit: $(lim_txt "${LIMP[0]}" "${FFP[0]}"); HV-MOS at the same tail current and load: $(lim_txt "${LIMP[1]}" "${FFP[1]}") (12u), $(lim_txt "${LIMP[2]}" "${FFP[2]}") (24u), $(lim_txt "${LIMP[3]}" "${FFP[3]}") (48u). G3 evidence points to: ${CHOICE}**"
  echo
  echo "- **Scope**: nominal only: \`hbt_typ\` / \`mos_tt\` / \`res_typ\`, 27 C, 3.3 V. No corner grid, no Monte Carlo. The decision in \`spec/decision-records/\` rests on this one corner plus the margin shown; it is not a corner-bounded result."
  echo "- **Netlists**: \`${PRESC_NETLIST#"${ROOT}/"}\` sha256 \`${NLSHA}\`$(ovr "${PRESC_NETLIST}" "${ROOT}/design/netlist/prescaler.spice"); \`${MOS_NETLIST#"${ROOT}/"}\` sha256 \`${MOSSHA}\`$(ovr "${MOS_NETLIST}" "${ROOT}/design/netlist/mos_latch.spice") (the 24u and 48u variants are this file with the subcircuit renamed and the 12u width replaced by sed)"
  echo "- **Decks**: \`sim/prescaler-g3/g3_pairs.spice.tmpl\` sha256 \`$(sha256sum "${ROOT}/sim/prescaler-g3/g3_pairs.spice.tmpl" | cut -d' ' -f1)\`, placeholder substitution only"
  echo "- **PDK**: IHP-Open-PDK $(jq -r .pdk.release_tag "${PINS}") (model libraries hash-checked against \`sim/pins.json\`); PDK_ROOT \`${PDK_ROOT}\`; PSP103 OSDI \`psp103.osdi\` sha256 \`$(jq -r .psp103.osdi_sha256 "${PINS}")\` (pinned); HBT \`npn13G2v\` (VBIC)"
  echo "- **Simulator**: \`${NG_VER}\` (\`${NGSPICE}\`), one local \`ngspice -b\` run (exit status ${RC_PA}); scratch \`.spiceinit\` = \`set ngbehavior=hsa\`"
  echo "- **Pin check**: ${NG_PIN_STATUS}"
  echo "- **Commit**: \`${COMMIT}${DIRTY}\` of this repository"
  echo "- **Pairs method**: one transient (${PAIR_STOP}) per clock frequency; bare two-latch /2 circuits (no input buffer) driven by one ideal differential clock, common mode ${CCM} V, amplitude ${CAMP} V per side antiphase; same IREF = 50 uA (tail = 2 x IREF = 100 uA for both flavours), same 2.4 kohm loads. The MOS circuits are NOT optimised (fixed L = 0.45 um, W swept over three values, no inductive peaking); the HBT circuit is the committed one. Pass rule as above (f/2 within 2 %, >= 0.2 V pk-pk), after $(awk -v t="${PAIR_T0}" 'BEGIN{printf "%.0f ns", t*1e9}'). The flattering simplification for MOS is the ideal clock (no source follower)."
  echo "- **Not covered**: other corners, supply or temperature; the modulus control timing against a real divider; noise; layout parasitics. Resistors are PDK \`rppd\`/\`rhigh\` (\`res_typ\`); this record supersedes the ideal-R record 20261103-034036 (retained, append-only) for the same circuit. The whole-prescaler divide check is not here: it is \`sim/prescaler-div89\` (DR-006). "
  echo "- **Host**: $(hostname), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "## Pairs: bare /2 at the /4/5 stage current (cells: f_out, pk-pk, verdict)"
  echo
  echo "| clock (GHz) | HBT cml_latch pair | MOS 12u | MOS 24u | MOS 48u |"
  echo "|---|---|---|---|---|"
  printf '%s' "${PAIRROWS}"
  echo
  echo "ngspice logs: [\`${ID}-ngspice.txt\`](${ID}-ngspice.txt)"
} > "${REC}"

echo "record: ${REC#"${ROOT}/"}"
echo "pairs: HBT $(lim_txt "${LIMP[0]}" "${FFP[0]}"); MOS12u $(lim_txt "${LIMP[1]}" "${FFP[1]}"); MOS24u $(lim_txt "${LIMP[2]}" "${FFP[2]}"); MOS48u $(lim_txt "${LIMP[3]}" "${FFP[3]}")"
echo "choice: ${CHOICE}"
