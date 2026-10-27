#!/usr/bin/env bash
# Prescaler first-stage bench (spec row 4, gate G1): ONE local ngspice, nominal corner only.
# Reports, at 5.0 GHz, the differential input capacitance (fF) and shunt conductance (S) of the
# prescaler input (small-signal AC at the DC operating point, cross-checked by the fundamental of the
# input current in a large-signal transient), and the highest input frequency at which the /2 output
# still toggles at f/2 (one transient per input frequency). Writes a dated append-only record under
# sim/prescaler-g1/records/. Not a corner grid (that goes through `klt sim`).
#
#   scripts/run-prescaler-g1.sh
#
# Environment:
#   PDK_ROOT         parent of ihp-sg13g2/ (default: first of ~/share/pdk, /usr/share/pdk, /usr/local/share/pdk)
#   NGSPICE          ngspice binary (default: ngspice on PATH)
#   PRESC_NETLIST    prescaler netlist to simulate (default design/netlist/prescaler.spice); a different file
#                    is recorded by path and sha256 (used by scripts/test-prescaler-g1-negative.sh)
#   RECORD_DIR       record directory (default sim/prescaler-g1/records)
#   G1_FLIST         input frequencies of the toggle sweep, Hz (default 6e9 ... 26e9, 2 GHz steps)
#
# Exit 0 if the run completed and the record was written (the verdict is in the record, not the exit
# status); non-zero if the PDK is not the pinned one, the netlist is stale, ngspice failed, or the
# data is incomplete.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { echo "run-prescaler-g1: error: $*" >&2; exit 1; }
PDK_SKIP_PSP103=1
source "${ROOT}/scripts/lib-pdk.sh"

PRESC_NETLIST="${PRESC_NETLIST:-${ROOT}/design/netlist/prescaler.spice}"
[ -f "${PRESC_NETLIST}" ] || die "${PRESC_NETLIST} not found"
if [ "${PRESC_NETLIST}" = "${ROOT}/design/netlist/prescaler.spice" ]; then
  "${ROOT}/design/netlist.sh" --check prescaler >/dev/null 2>&1 || die "design/netlist/prescaler.spice is stale against design/prescaler.sch (run design/netlist.sh)"
fi
REC_DIR="${RECORD_DIR:-${ROOT}/sim/prescaler-g1/records}"; mkdir -p "${REC_DIR}"
WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT

FIN=5.0e9; AMP=0.1; CBUDGET_FF=2.1; FBAND_TOP=5.5e9
FLIST="${G1_FLIST:-6e9 8e9 10e9 12e9 14e9 16e9 18e9 20e9 22e9 24e9 26e9}"
TRAN_STOP=20n; TOG_STOP=12n; TOG_T0=4e-9
sed -e "s|@@MODELS_DIR@@|${MODELS}|g" -e "s|@@PRESC_NETLIST@@|${PRESC_NETLIST}|g" -e "s|@@OUT_DIR@@|${WORK}|g" \
    -e "s|@@FIN@@|${FIN}|g" -e "s|@@AMP@@|${AMP}|g" -e "s|@@FLIST@@|${FLIST}|g" \
    -e "s|@@TRAN_STOP@@|${TRAN_STOP}|g" -e "s|@@TOG_STOP@@|${TOG_STOP}|g" \
    "${ROOT}/sim/prescaler-g1/prescaler_g1.spice.tmpl" > "${WORK}/prescaler_g1.spice"
if grep -vE '^[[:space:]]*\*' "${WORK}/prescaler_g1.spice" | grep -q '@@'; then die "unsubstituted placeholder left in the deck"; fi
printf 'set ngbehavior=hsa\n' > "${WORK}/.spiceinit"

COMMIT="$(git -C "${ROOT}" rev-parse --short=7 HEAD)"
DIRTY=""; [ -z "$(git -C "${ROOT}" status --porcelain -- design sim scripts reuse.lock.json ':(exclude)sim/*/records/*' ':(exclude)sim/*/negative-control-*' 2>/dev/null)" ] || DIRTY="-dirty"
ID="$(date -u +%Y%m%d-%H%M%S)-${COMMIT}${DIRTY}"
REC="${REC_DIR}/${ID}.md"
[ ! -e "${REC}" ] || die "${REC} exists; records are append-only"

set +e
( cd "${WORK}" && HOME="${WORK}" "${NGSPICE}" -b prescaler_g1.spice ) > "${WORK}/ngspice.log" 2>&1
NG_RC=$?
set -e
cp "${WORK}/ngspice.log" "${REC_DIR}/${ID}-ngspice.txt"
AC_LINE="$(grep -E '^AC_RESULT ' "${WORK}/ngspice.log" | tail -1 || true)"
[ -n "${AC_LINE}" ] && [ -s "${WORK}/tran5g" ] || { echo "run-prescaler-g1: ngspice produced no AC/transient data (rc=${NG_RC}); see ${REC_DIR}/${ID}-ngspice.txt" >&2; exit 1; }
read -r _ C_AC G_AC <<<"${AC_LINE}"
IDD_MA="$(grep -E '^OP_IDD ' "${WORK}/ngspice.log" | tail -1 | awk '{printf "%.3f", $2*1e3}')"

# Fundamental of the input current and of the differential input voltage over an integer number of
# periods (last 10 ns = 50 cycles): Y = I1 / V1; C = Im(Y)/w; G = Re(Y).
# tran5g columns: t, -i(vip), t, vdiff_in, t, vdiv2, t, vout.
read -r C_TR G_TR VPP_IN < <(awk -v f="${FIN}" -v t0=10e-9 -v t1=20e-9 '
  BEGIN { w=2*3.14159265358979*f }
  NR>1 && $1>=t0-1e-15 && $1<=t1+1e-15 {
    if (have) { dt=$1-pt
      c=cos(w*$1); s=sin(w*$1); pc=cos(w*pt); ps=sin(w*pt)
      ic+=0.5*dt*($2*c+pi*pc); is+=0.5*dt*($2*s+pi*ps)
      vc+=0.5*dt*($4*c+pv*pc); vs+=0.5*dt*($4*s+pv*ps)
      if ($4>vmx||!hv) vmx=$4; if ($4<vmn||!hv) vmn=$4; hv=1 }
    pt=$1; pi=$2; pv=$4; have=1 }
  END { T=t1-t0; Ir=2/T*ic; Ii=-2/T*is; Vr=2/T*vc; Vi=-2/T*vs   # X = (2/T) int x e^{-jwt}
        d=Vr*Vr+Vi*Vi; yr=(Ir*Vr+Ii*Vi)/d; yi=(Ii*Vr-Ir*Vi)/d
        printf "%.4e %.4e %.4f\n", yi/w, yr, vmx-vmn }' "${WORK}/tran5g")
# /8 output at 5.0 GHz (MC = 0): rising crossings of the differential output after 8 ns
read -r NX_OUT F_OUT PP_OUT < <(awk -v t0=8e-9 'NR>1 && $1>=t0 { v=$8; if (v>mx||!h) mx=v; if (v<mn||!h) mn=v; h=1
  if (n && pv<0 && v>=0) { c++; if(!f) f=$1; l=$1 } n=1; pv=v }
  END { printf "%d %.4e %.3f\n", c, (c>1)?(c-1)/(l-f):0, mx-mn }' "${WORK}/tran5g")

# Toggle sweep: /2 output = v(x1.hp)-v(x1.hn). Pass: rising crossings after TOG_T0 match f/2 within
# 2 % AND peak-to-peak >= 0.2 V (so a latched DC state or a collapsed swing cannot pass).
TOGROWS=""; LASTPASS=""; FIRSTFAIL=""
for f in ${FLIST}; do
  fn="${WORK}/tog_${f}"
  [ -s "${fn}" ] || { TOGROWS+="| $(awk -v f="${f}" 'BEGIN{printf "%.1f", f/1e9}') | no data | | | FAIL |"$'\n'; [ -n "${FIRSTFAIL}" ] || FIRSTFAIL="${f}"; continue; }
  row="$(awk -v f="${f}" -v t0="${TOG_T0}" '$1>=t0 { v=$2; if (v>mx||!h) mx=v; if (v<mn||!h) mn=v; h=1
      if (n && pv<0 && v>=0) { c++; if(!fi) fi=$1; la=$1 } n=1; pv=v }
    END { fo=(c>1)?(c-1)/(la-fi):0; ok=(fo>0.98*f/2 && fo<1.02*f/2 && (mx-mn)>=0.2)
          printf "| %.1f | %.4f | %d | %.3f | %s |\n", f/1e9, fo/1e9, c, mx-mn, ok?"pass":"FAIL" }' "${fn}")"
  TOGROWS+="${row}"$'\n'
  if [[ "${row}" == *"| pass |" ]]; then
    [ -n "${FIRSTFAIL}" ] || LASTPASS="${f}"
  else
    [ -n "${FIRSTFAIL}" ] || FIRSTFAIL="${f}"
  fi
done

C_AC_FF="$(awk -v c="${C_AC}" 'BEGIN{printf "%.3f", c*1e15}')"
C_TR_FF="$(awk -v c="${C_TR}" 'BEGIN{printf "%.3f", c*1e15}')"
CVERD="$(awk -v c="${C_AC_FF}" -v b="${CBUDGET_FF}" 'BEGIN{print (c<=b)?"WITHIN":"EXCEEDS"}')"
TVERD="FAIL"
if [ -n "${LASTPASS}" ] && awk -v f="${LASTPASS}" -v b="${FBAND_TOP}" 'BEGIN{exit !(f>=b)}'; then TVERD="PASS"; fi
FMAX_TXT="none of the swept frequencies toggled"
if [ -n "${LASTPASS}" ]; then
  if [ -n "${FIRSTFAIL}" ]; then FMAX_TXT="between $(awk -v a="${LASTPASS}" -v b="${FIRSTFAIL}" 'BEGIN{printf "%.0f GHz (last pass) and %.0f GHz (first fail)", a/1e9, b/1e9}')"
  else FMAX_TXT="at least $(awk -v a="${LASTPASS}" 'BEGIN{printf "%.0f", a/1e9}') GHz (every swept frequency passed; the limit is above the sweep)"; fi
fi
REQ_BAND="$(awk -v b="${FBAND_TOP}" 'BEGIN{printf "%.1f", b/1e9}')"
RIN_TXT="$(awk -v g="${G_AC}" 'BEGIN{ if (g==0) print "infinite"; else printf "%.0f ohm%s", 1/g, (g<0)?" (NEGATIVE: the input presents a negative resistance, i.e. no added loss at the operating point)":"" }')"

NLSHA="$(sha256sum "${PRESC_NETLIST}" | cut -d' ' -f1)"
{
  echo "# prescaler-g1 run ${ID}"
  echo
  echo "**Result (simulated, nominal corner only, not measured): differential input capacitance ${C_AC_FF} fF ${CVERD} the ${CBUDGET_FF} fF budget (AC small-signal at 5.0 GHz; large-signal cross-check ${C_TR_FF} fF); shunt conductance ${G_AC} S; /2 toggle limit ${FMAX_TXT} against the ${REQ_BAND} GHz band top: ${TVERD}.**"
  echo
  echo "- **Scope**: nominal only: model corner \`hbt_typ\`, 27 C, supply 3.3 V. No corner grid, no Monte Carlo, no routing parasitics. The budget (spec section 1: <= 2.1 fF differential, device plus routing, graded over C-grid) is therefore **not graded**: this is the device-level number at one corner. A pass here does not close G1 for the C-grid; a fail would stand."
  echo "- **Netlist**: \`${PRESC_NETLIST#"${ROOT}/"}\` sha256 \`${NLSHA}\`$([ "${PRESC_NETLIST}" = "${ROOT}/design/netlist/prescaler.spice" ] && echo ', checked against design/prescaler.sch with design/netlist.sh --check' || echo ' (NOT the committed netlist: an override, see PRESC_NETLIST)')"
  echo "- **Deck**: \`sim/prescaler-g1/prescaler_g1.spice.tmpl\` sha256 \`$(sha256sum "${ROOT}/sim/prescaler-g1/prescaler_g1.spice.tmpl" | cut -d' ' -f1)\`, placeholder substitution only"
  echo "- **PDK**: IHP-Open-PDK $(jq -r .pdk.release_tag "${PINS}") (model libraries hash-checked against \`sim/pins.json\`); PDK_ROOT \`${PDK_ROOT}\`; HBT model \`npn13G2v\` (VBIC), \`cornerHBT.lib hbt_typ\`"
  echo "- **Simulator**: \`${NG_VER}\` (\`${NGSPICE}\`), one local \`ngspice -b\`, exit status ${NG_RC}; scratch \`.spiceinit\` = \`set ngbehavior=hsa\`"
  echo "- **Pin check**: ${NG_PIN_STATUS}"
  echo "- **Commit**: \`${COMMIT}${DIRTY}\` of this repository"
  echo "- **Stimulus**: differential sine on INP/INN, amplitude ${AMP} V per side in antiphase (= 0.4 Vpp differential, the VCO row 7 swing), common mode 3.3 V (the tank inductors return to VDD), zero source impedance; supply 3.3 V; ideal reference current IREF = 50 uA into the prescaler (every tail is k x IREF); MC = 0 (/4 mode) for these runs; ideal resistors (no PDK resistor model, no resistor parasitics)."
  echo "- **Capacitance and conductance, method 1 (headline)**: \`ac\` at 5.0 GHz around the DC operating point. 1 V differential drive (+0.5 V / -0.5 V); Y = -i(VIP) / v_diff; C_diff = Im(Y)/(2 pi f) (the capacitance that, connected across the two input nodes, draws the same current), G_diff = Re(Y). The operating point is the unclocked symmetric state of the dividers."
  echo "- **Method 2 (cross-check, large signal)**: transient with the 5.0 GHz stimulus, fundamental (Fourier integral, trapezoid) of the current into INP and of v(INP)-v(INN) over 10-20 ns (50 whole periods, after the dividers settle); Y = I1 / V1. Differential amplitude seen: ${VPP_IN} V pk-pk. C = ${C_TR_FF} fF, G = ${G_TR} S."
  echo "- **Equivalent parallel resistance** (1 / G_diff, method 1): ${RIN_TXT}."
  echo "- **Compared with the budget**: ${C_AC_FF} fF vs ${CBUDGET_FF} fF: **${CVERD}**. The load on the tank is also a conductance: for scale, the tank's own loss at 5.0 GHz is 1 / 3.418 kohm = 293 uS (spec section 1, I6)."
  echo "- **Max toggle frequency, method**: one transient per input frequency (${FLIST// / , } Hz), same 0.4 Vpp swing, ${TOG_STOP} each; the /2 output is v(x1.hp)-v(x1.hn); rising zero crossings counted after $(awk -v t="${TOG_T0}" 'BEGIN{printf "%.0f ns", t*1e9}'); a frequency passes when the output frequency is within 2 % of f/2 **and** its peak-to-peak is at least 0.2 V (a latched DC state or collapsed swing cannot pass). The limit is bracketed by the sweep grid, not interpolated."
  echo "- **Max toggle frequency**: ${FMAX_TXT}. Required: >= ${REQ_BAND} GHz (VCO row 1 band top); verdict **${TVERD}** (nominal corner only)."
  echo "- **Whole-prescaler check at 5.0 GHz, MC = 0**: output ${F_OUT} Hz (expected 6.25e8 = f/8), ${NX_OUT} rising crossings after 8 ns, ${PP_OUT} V pk-pk differential."
  echo "- **Supply current at the DC operating point** (all of prescaler plus the 50 uA reference): ${IDD_MA} mA = $(awk -v i="${IDD_MA}" 'BEGIN{printf "%.1f", i*3.3}') mW at 3.3 V (spec row 11 allocates <= 10 mW to the prescaler)."
  echo "- **Not covered**: routing/pad capacitance between the tank nodes and the first emitter followers; any corner other than \`hbt_typ\`/27 C/3.3 V; the VCO loaded by this input (gate G2); noise."
  echo "- **Host**: $(hostname), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "| f_in (GHz) | f_out (GHz) | rising crossings | pk-pk (V) | /2 toggles at f/2 |"
  echo "|---|---|---|---|---|"
  printf '%s' "${TOGROWS}"
  echo
  echo "ngspice log: [\`${ID}-ngspice.txt\`](${ID}-ngspice.txt)"
} > "${REC}"

echo "record: ${REC#"${ROOT}/"}"
echo "C_diff(AC, 5.0 GHz) = ${C_AC_FF} fF (budget ${CBUDGET_FF} fF: ${CVERD}); transient cross-check ${C_TR_FF} fF; G_diff = ${G_AC} S"
echo "toggle limit: ${FMAX_TXT}; required >= ${REQ_BAND} GHz: ${TVERD}"
