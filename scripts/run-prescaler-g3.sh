#!/usr/bin/env bash
# Prescaler /4/5-stage evidence (spec row 4, gate G3): two local ngspice runs in sequence, nominal corner only.
#   chain : the whole prescaler in both modulus states (MC = 0 -> /8 total, MC = 3.3 V -> /10 total), swept over
#           the VCO-side input frequency, so the /4/5 stage sees half of it.
#   pairs : the HBT latch pair of the /4/5 stage against the same CML topology on 3.3 V thick-oxide NMOS
#           (sg13_hv_nmos, three widths), same clock, same tail current, same load resistors.
# Writes a dated append-only record under sim/prescaler-g3/records/. Not a corner grid (`klt sim` does those).
#
#   scripts/run-prescaler-g3.sh
#
# Environment: PDK_ROOT, NGSPICE as in scripts/run-cp-dc.sh; PRESC_NETLIST / MOS_NETLIST override the committed
# netlists (recorded by path and sha256; used by the negative control); RECORD_DIR (default sim/prescaler-g3/records);
# G3_CHAIN_FLIST / G3_PAIR_FLIST: sweep frequencies, Hz.
# Exit 0 if both runs completed and the record was written (the verdict is in the record).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { echo "run-prescaler-g3: error: $*" >&2; exit 1; }
source "${ROOT}/scripts/lib-pdk.sh"

PRESC_NETLIST="${PRESC_NETLIST:-${ROOT}/design/netlist/prescaler.spice}"
MOS_NETLIST="${MOS_NETLIST:-${ROOT}/design/netlist/mos_latch.spice}"
[ -f "${PRESC_NETLIST}" ] && [ -f "${MOS_NETLIST}" ] || die "netlist not found (${PRESC_NETLIST}, ${MOS_NETLIST})"
if [ "${PRESC_NETLIST}" = "${ROOT}/design/netlist/prescaler.spice" ] && [ "${MOS_NETLIST}" = "${ROOT}/design/netlist/mos_latch.spice" ]; then
  "${ROOT}/design/netlist.sh" --check prescaler mos_latch >/dev/null 2>&1 || die "design/netlist/{prescaler,mos_latch}.spice is stale against its schematic (run design/netlist.sh)"
fi
REC_DIR="${RECORD_DIR:-${ROOT}/sim/prescaler-g3/records}"; mkdir -p "${REC_DIR}"
WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT

AMP=0.1; CCM=2.3; CAMP=0.15
CHAIN_FLIST="${G3_CHAIN_FLIST:-5e9 5.5e9 6e9 7e9 8e9 9e9 10e9 12e9}"
PAIR_FLIST="${G3_PAIR_FLIST:-1e9 1.5e9 2e9 2.5e9 2.75e9 3e9 3.5e9 4e9 5e9 6e9}"
CHAIN_STOP=30n; CHAIN_T0=15e-9; PAIR_STOP=12n; PAIR_T0=4e-9
W1=12u; W2=24u; W3=48u
# MOS width variants: same committed netlist, subckt renamed, the 12u device width replaced.
mkvar() { sed -e "s/^\.subckt mos_latch /.subckt mos_latch_$1 /" -e "s/ w=12u / w=$2 /g" "${MOS_NETLIST}" > "${WORK}/mos_$1.spice"; }
mkvar w1 "${W1}"; mkvar w2 "${W2}"; mkvar w3 "${W3}"
grep -q "w=${W2}" "${WORK}/mos_w2.spice" || die "MOS width variant did not apply (is the committed width still 12u?)"
printf 'set ngbehavior=hsa\n' > "${WORK}/.spiceinit"
render() { # template out [extra sed args...]
  local t="$1" o="$2"; shift 2
  sed -e "s|@@MODELS_DIR@@|${MODELS}|g" -e "s|@@PRESC_NETLIST@@|${PRESC_NETLIST}|g" -e "s|@@OUT_DIR@@|${WORK}|g" \
      -e "s|@@AMP@@|${AMP}|g" -e "s|@@CCM@@|${CCM}|g" -e "s|@@CAMP@@|${CAMP}|g" -e "s|@@OSDI_PSP@@|${OSDI_PSP}|g" \
      -e "s|@@MOS_NETLIST1@@|${WORK}/mos_w1.spice|g" -e "s|@@MOS_NETLIST2@@|${WORK}/mos_w2.spice|g" -e "s|@@MOS_NETLIST3@@|${WORK}/mos_w3.spice|g" \
      -e "s|@@MOSW1@@|${W1}|g" -e "s|@@MOSW2@@|${W2}|g" -e "s|@@MOSW3@@|${W3}|g" "$@" "${ROOT}/sim/prescaler-g3/$t" > "${WORK}/$o"
  if grep -vE '^[[:space:]]*\*' "${WORK}/$o" | grep -q '@@'; then die "unsubstituted placeholder left in $o"; fi
}
render g3_chain.spice.tmpl chain.spice -e "s|@@FIN@@|5e9|g" -e "s|@@FLIST@@|${CHAIN_FLIST}|g" -e "s|@@TRAN_STOP@@|${CHAIN_STOP}|g"
render g3_pairs.spice.tmpl pairs.spice -e "s|@@FLIST@@|${PAIR_FLIST}|g" -e "s|@@TRAN_STOP@@|${PAIR_STOP}|g"

COMMIT="$(git -C "${ROOT}" rev-parse --short=7 HEAD)"
DIRTY=""; [ -z "$(git -C "${ROOT}" status --porcelain -- design sim scripts reuse.lock.json ':(exclude)sim/*/records/*' ':(exclude)sim/*/negative-control-*' 2>/dev/null)" ] || DIRTY="-dirty"
ID="$(date -u +%Y%m%d-%H%M%S)-${COMMIT}${DIRTY}"
REC="${REC_DIR}/${ID}.md"
[ ! -e "${REC}" ] || die "${REC} exists; records are append-only"

set +e
( cd "${WORK}" && HOME="${WORK}" "${NGSPICE}" -b chain.spice ) > "${WORK}/chain.log" 2>&1; RC_CH=$?
( cd "${WORK}" && HOME="${WORK}" "${NGSPICE}" -b pairs.spice ) > "${WORK}/pairs.log" 2>&1; RC_PA=$?
set -e
cat "${WORK}/chain.log" > "${REC_DIR}/${ID}-ngspice.txt"; { echo; echo "===== pairs run ====="; cat "${WORK}/pairs.log"; } >> "${REC_DIR}/${ID}-ngspice.txt"
ls "${WORK}"/mc0_* >/dev/null 2>&1 && ls "${WORK}"/pair_* >/dev/null 2>&1 || { echo "run-prescaler-g3: ngspice produced no data (rc=${RC_CH}/${RC_PA}); see ${REC_DIR}/${ID}-ngspice.txt" >&2; exit 1; }

# analyse FILE COL T0 FEXPECT -> "f_out crossings pkpk ok" (rising zero crossings after T0; ok = f_out within 2 % of
# FEXPECT and pk-pk >= 0.2 V, so a latched DC state or a collapsed swing cannot pass)
analyse() { awk -v col="$2" -v t0="$3" -v fe="$4" '$1>=t0 { v=$col; if (v>mx||!h) mx=v; if (v<mn||!h) mn=v; h=1
    if (n && pv<0 && v>=0) { c++; if(!fi) fi=$1; la=$1 } n=1; pv=v }
  END { fo=(c>1)?(c-1)/(la-fi):0; ok=(fo>0.98*fe && fo<1.02*fe && (mx-mn)>=0.2); printf "%.6e %d %.3f %s\n", fo, c, mx-mn, ok?"pass":"FAIL" }' "$1"; }

# lim FLAGVAR... helpers: a mode's limit is the last pass before the first fail (contiguous from the lowest frequency)
CHAINROWS=""; LIM0=""; LIM1=""; FF0=""; FF1=""
for f in ${CHAIN_FLIST}; do
  read -r fo0 c0 pp0 ok0 < <(analyse "${WORK}/mc0_${f}" 2 "${CHAIN_T0}" "$(awk -v f="$f" 'BEGIN{print f/8}')")
  read -r fo1 c1 pp1 ok1 < <(analyse "${WORK}/mc1_${f}" 2 "${CHAIN_T0}" "$(awk -v f="$f" 'BEGIN{print f/10}')")
  CHAINROWS+="$(awk -v f="$f" -v a="$fo0" -v pa="$pp0" -v oa="$ok0" -v b="$fo1" -v pb="$pp1" -v ob="$ok1" \
    'BEGIN{printf "| %.2f | %.3f | %.1f | %.2f | %.3f | %s | %.1f | %.2f | %.3f | %s |\n", f/1e9, f/2e9, a/1e6, (a>0)?f/a:0, pa, oa, b/1e6, (b>0)?f/b:0, pb, ob}')"$'\n'
  if [ "$ok0" = pass ]; then [ -n "$FF0" ] || LIM0="$f"; else [ -n "$FF0" ] || FF0="$f"; fi
  if [ "$ok1" = pass ]; then [ -n "$FF1" ] || LIM1="$f"; else [ -n "$FF1" ] || FF1="$f"; fi
done

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
CH_OK=no; awk -v a="${LIM0:-0}" -v b="${LIM1:-0}" 'BEGIN{exit !(a>=5.5e9 && b>=5.5e9)}' && CH_OK=yes
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
  echo "**Result (simulated, nominal corner only, not measured): whole prescaler divides by 8 (MC = 0) up to $(ghz "${LIM0}") and by 10 (MC = 3.3 V) up to $(ghz "${LIM1}") at the VCO-side input, i.e. the /4/5 stage divides by 4 and by 5 at the 2.5 and 2.75 GHz stage clocks: ${CH_OK}; bare HBT latch-pair /2 limit: $(lim_txt "${LIMP[0]}" "${FFP[0]}"); HV-MOS at the same tail current and load: $(lim_txt "${LIMP[1]}" "${FFP[1]}") (12u), $(lim_txt "${LIMP[2]}" "${FFP[2]}") (24u), $(lim_txt "${LIMP[3]}" "${FFP[3]}") (48u). G3 evidence points to: ${CHOICE}**"
  echo
  echo "- **Scope**: nominal only: \`hbt_typ\` / \`mos_tt\`, 27 C, 3.3 V. No corner grid, no Monte Carlo. The decision in \`spec/decision-records/\` rests on this one corner plus the margin shown; it is not a corner-bounded result."
  echo "- **Netlists**: \`${PRESC_NETLIST#"${ROOT}/"}\` sha256 \`${NLSHA}\`$(ovr "${PRESC_NETLIST}" "${ROOT}/design/netlist/prescaler.spice"); \`${MOS_NETLIST#"${ROOT}/"}\` sha256 \`${MOSSHA}\`$(ovr "${MOS_NETLIST}" "${ROOT}/design/netlist/mos_latch.spice") (the 24u and 48u variants are this file with the subcircuit renamed and the 12u width replaced by sed)"
  echo "- **Decks**: \`sim/prescaler-g3/g3_chain.spice.tmpl\` sha256 \`$(sha256sum "${ROOT}/sim/prescaler-g3/g3_chain.spice.tmpl" | cut -d' ' -f1)\`, \`sim/prescaler-g3/g3_pairs.spice.tmpl\` sha256 \`$(sha256sum "${ROOT}/sim/prescaler-g3/g3_pairs.spice.tmpl" | cut -d' ' -f1)\`, placeholder substitution only"
  echo "- **PDK**: IHP-Open-PDK $(jq -r .pdk.release_tag "${PINS}") (model libraries hash-checked against \`sim/pins.json\`); PDK_ROOT \`${PDK_ROOT}\`; PSP103 OSDI \`psp103.osdi\` sha256 \`$(jq -r .psp103.osdi_sha256 "${PINS}")\` (pinned); HBT \`npn13G2v\` (VBIC)"
  echo "- **Simulator**: \`${NG_VER}\` (\`${NGSPICE}\`), two local \`ngspice -b\` runs in sequence (chain exit status ${RC_CH}, pairs ${RC_PA}); scratch \`.spiceinit\` = \`set ngbehavior=hsa\`"
  echo "- **Pin check**: ${NG_PIN_STATUS}"
  echo "- **Commit**: \`${COMMIT}${DIRTY}\` of this repository"
  echo "- **Chain method**: one transient (${CHAIN_STOP}) per input frequency and modulus state; stimulus as in sim/prescaler-g1 (0.4 Vpp differential, common mode 3.3 V); ideal IREF = 50 uA; the differential output v(OUTP)-v(OUTN) is analysed after $(awk -v t="${CHAIN_T0}" 'BEGIN{printf "%.0f ns", t*1e9}'): rising zero crossings give the output frequency; a point passes when the output frequency is within 2 % of f_in/8 (MC = 0) or f_in/10 (MC = 3.3 V) **and** the output is at least 0.2 V pk-pk. The /4/5 stage sees f_in/2."
  echo "- **Pairs method**: one transient (${PAIR_STOP}) per clock frequency; bare two-latch /2 circuits (no input buffer) driven by one ideal differential clock, common mode ${CCM} V, amplitude ${CAMP} V per side antiphase; same IREF = 50 uA (tail = 2 x IREF = 100 uA for both flavours), same 2.4 kohm loads. The MOS circuits are NOT optimised (fixed L = 0.45 um, W swept over three values, no inductive peaking); the HBT circuit is the committed one. Pass rule as above (f/2 within 2 %, >= 0.2 V pk-pk), after $(awk -v t="${PAIR_T0}" 'BEGIN{printf "%.0f ns", t*1e9}'). The flattering simplification for MOS is the ideal clock (no source follower)."
  echo "- **Chain limits**: MC = 0: $(lim_txt "${LIM0}" "${FF0}"); MC = 3.3 V: $(lim_txt "${LIM1}" "${FF1}"). Required: both pass at 5.0 and 5.5 GHz (the /4/5 stage at 2.5 and 2.75 GHz): **${CH_OK}**."
  echo "- **Not covered**: other corners, supply or temperature; the modulus control timing against a real divider; noise; layout parasitics. Resistors are ideal. The /4/5 stage's input swing here is whatever the /2 stage delivers, not a separate input specification."
  echo "- **Host**: $(hostname), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "## Chain: whole prescaler, both modulus states"
  echo
  echo "| f_in (GHz) | /4/5 stage clock (GHz) | MC=0 f_out (MHz) | ratio | pk-pk (V) | /8 | MC=1 f_out (MHz) | ratio | pk-pk (V) | /10 |"
  echo "|---|---|---|---|---|---|---|---|---|---|"
  printf '%s' "${CHAINROWS}"
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
echo "chain: MC=0 $(lim_txt "${LIM0}" "${FF0}"); MC=1 $(lim_txt "${LIM1}" "${FF1}") (both >= 5.5 GHz: ${CH_OK})"
echo "pairs: HBT $(lim_txt "${LIMP[0]}" "${FFP[0]}"); MOS12u $(lim_txt "${LIMP[1]}" "${FFP[1]}"); MOS24u $(lim_txt "${LIMP[2]}" "${FFP[2]}"); MOS48u $(lim_txt "${LIMP[3]}" "${FFP[3]}")"
echo "choice: ${CHOICE}"
