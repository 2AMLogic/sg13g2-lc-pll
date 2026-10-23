#!/usr/bin/env bash
# PFD phase-error sweep at 50 MHz: ONE local ngspice transient (typical corner, nominal
# supply) with the phase error stepped inside the single deck; the adopted sg13g2-pll PFD
# drives this repo's charge pump held at 2.0 V. Reports per-cycle CP charge vs phase error,
# dead-zone width and monotonicity in a dated append-only record under sim/pfd/records/.
# This is the 50 MHz re-grade spec section 7 asks of the adopted PFD (dead zone and charge
# vs phase only; nothing else about the PFD is re-graded).
#
#   scripts/run-pfd-sweep.sh
#
# Environment: PDK_ROOT, NGSPICE as for scripts/run-cp-dc.sh; RECORD_DIR (default sim/pfd/records).
#   PFD_VARIANT  adopted (default): the pinned PFD, unmodified. reset-fix: DIAGNOSTIC ONLY, a
#                scratch copy whose reset path has one inverter instead of two (XI2 removed),
#                to show what the adopted PFD's failure is; the record says so in its first line.
# Exit 0 if the run completed and the record was written (the verdict is in the record).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
die() { echo "run-pfd-sweep: error: $*" >&2; exit 1; }
source "${ROOT}/scripts/lib-pdk.sh"

"${ROOT}/scripts/fetch-pll.sh" >/dev/null || die "fetch/verify of the pinned sg13g2-pll PFD failed"
PFD_ADOPTED="${ROOT}/.fetched/sg13g2-pll/design/netlist/pfd.spice"
PFD_NETLIST="${PFD_ADOPTED}"
PFD_VARIANT="${PFD_VARIANT:-adopted}"
CP_NETLIST="${CP_NETLIST:-${ROOT}/design/netlist/cp.spice}"
"${ROOT}/design/netlist.sh" --check >/dev/null 2>&1 || die "design/netlist/cp.spice is stale against design/cp.sch (run design/netlist.sh)"
REC_DIR="${RECORD_DIR:-${ROOT}/sim/pfd/records}"; mkdir -p "${REC_DIR}"
WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT
case "${PFD_VARIANT}" in
  adopted) ;;
  reset-fix)
    sed -e 's/^XI1 reset_raw reset_d1 VDD VSS inv_hv$/XI1 reset_raw reset VDD VSS inv_hv/' -e '/^XI2 reset_d1 reset VDD VSS inv2x_hv$/d' \
      "${PFD_ADOPTED}" > "${WORK}/pfd_variant.spice"
    cmp -s "${PFD_ADOPTED}" "${WORK}/pfd_variant.spice" && die "reset-fix edit did not apply to the pinned pfd.spice"
    PFD_NETLIST="${WORK}/pfd_variant.spice" ;;
  *) die "PFD_VARIANT must be adopted or reset-fix" ;;
esac

T_PS=20000          # T_ref = 20 ns (50 MHz)
IREF_UA=20; ICP_NOM_UA=200

# ---- phase schedule (ps): 4 warm-up cycles at +1 ns, then the swept cycles, in increasing phi
awk -v T="${T_PS}" 'BEGIN{ k=0
  for(i=0;i<4;i++) phi[k++]=1000
  for(p=-10000;p<=-3000;p+=250) phi[k++]=p
  for(p=-2950;p<=-1000;p+=50) phi[k++]=p
  for(p=-990;p<=990;p+=10) phi[k++]=p
  for(p=1000;p<=3000;p+=50) phi[k++]=p
  for(p=3250;p<=10000;p+=250) phi[k++]=p
  for(i=0;i<k;i++) printf "%d %d %d %d\n", i, phi[i], 20000+i*T, 20000+i*T+phi[i] }' > "${WORK}/sched.txt"
NCYC="$(wc -l < "${WORK}/sched.txt")"
TSTOP_PS=$(( 20000 + NCYC*T_PS + 20000 ))
awk 'BEGIN{ printf "VFB fb 0 PWL(0 0\n" }
     { printf "+ %dp 0 %dp 3.3 %dp 3.3 %dp 0\n", $4, $4+100, $4+4900+100, $4+5000+100 }
     END{ printf "+ )\n" }' "${WORK}/sched.txt" > "${WORK}/fb.inc"

sed -e "s|@@MODELS_DIR@@|${MODELS}|g" -e "s|@@OSDI_PSP@@|${OSDI_PSP}|g" -e "s|@@PFD_NETLIST@@|${PFD_NETLIST}|g" \
    -e "s|@@CP_NETLIST@@|${CP_NETLIST}|g" -e "s|@@FB_FILE@@|${WORK}/fb.inc|g" -e "s|@@TSTOP@@|${TSTOP_PS}p|g" \
    -e "s|@@DATA_OUT@@|${WORK}/pfd.data|g" "${ROOT}/sim/pfd/pfd_sweep.spice.tmpl" > "${WORK}/pfd_sweep.spice"
if grep -vE '^[[:space:]]*\*' "${WORK}/pfd_sweep.spice" | grep -q '@@'; then die "unsubstituted placeholder left in the deck"; fi
printf 'set ngbehavior=hsa\n' > "${WORK}/.spiceinit"

COMMIT="$(git -C "${ROOT}" rev-parse --short=7 HEAD)"
DIRTY=""; [ -z "$(git -C "${ROOT}" status --porcelain -- design sim scripts reuse.lock.json ':(exclude)sim/*/records/*' ':(exclude)sim/*/negative-control-*' 2>/dev/null)" ] || DIRTY="-dirty"
ID="$(date -u +%Y%m%d-%H%M%S)-${COMMIT}${DIRTY}"
REC="${REC_DIR}/${ID}.md"
[ ! -e "${REC}" ] || die "${REC} exists; records are append-only"

START="$(date +%s)"
set +e
( cd "${WORK}" && HOME="${WORK}" "${NGSPICE}" -b pfd_sweep.spice ) > "${WORK}/ngspice.log" 2>&1
NG_RC=$?
set -e
ELAPSED=$(( $(date +%s) - START ))
cp "${WORK}/ngspice.log" "${REC_DIR}/${ID}-ngspice.txt"
[ -s "${WORK}/pfd.data" ] || { echo "run-pfd-sweep: ngspice produced no data (rc=${NG_RC}); see ${REC_DIR}/${ID}-ngspice.txt" >&2; exit 1; }
NPTS_T="$(wc -l < "${WORK}/pfd.data")"

# ---- estimator: per-cycle charge = trapezoid integral of i(VO) over that cycle's window.
# Window k = [min(t_ref,t_fb)_k - 1 ns, same for k+1): it holds every pulse of cycle k and
# none of cycle k-1 (its tail ends <= 11.5 ns after its first edge, the next window opens ~19 ns after);
# the last window ends T_ref after its own start, so REF pulses after the schedule are not counted.
awk -v T="${T_PS}" -v tstop="${TSTOP_PS}" '
  NR==FNR { k=$1; phi[k]=$2; m=($3<$4?$3:$4)-1000; w[k]=m*1e-12; n=k+1; next }
  BEGIN { j=0 }
  { t=$1; i=$2
    if (have) { while (j+1<n && pt>=w[j+1]) j++
                wend = (j+1<n) ? w[j+1] : w[j]+T*1e-12
                if (pt>=w[0] && pt<wend) q[j]+=0.5*(i+pi)*(t-pt) }
    pt=t; pi=i; have=1 }
  END { for (k=4;k<n;k++) printf "%d %.1f %.4f\n", phi[k], q[k]*1e15, q[k]*1e15*1e-15/(T*1e-12)*1e6 }
' "${WORK}/sched.txt" "${WORK}/pfd.data" > "${WORK}/curve.txt"   # phi_ps  Q_fC  Iavg_uA
NSW="$(wc -l < "${WORK}/curve.txt")"
[ "${NSW}" -gt 300 ] || die "analysis produced ${NSW} points"

# ---- metrics (all in awk over curve.txt)
# slope/intercept: least squares over phi 3..8 ns (the linear region); zero crossing
#   phi0 = -intercept/slope (the static phase offset of the PFD + CP pair).
# dead zone: the longest run of consecutive swept steps whose local slope dQ/dphi is below
#   10 % of the fitted slope, width = phi span of that run; no such step -> 0 ps (resolution
#   = the step, 10 ps near zero). Only meaningful if the function check passes.
# monotonic: dQ between consecutive phase points; pass if no step is below -TOL_FC.
TOL_FC=0.5
FLAT_FRAC=0.1
METRICS="$(awk -v tol="${TOL_FC}" -v ff="${FLAT_FRAC}" '
  { p[NR]=$1; q[NR]=$2 }
  END { n=NR; worst=1e9; wi=2
        for (i=2;i<=n;i++) { d=q[i]-q[i-1]; if (d<worst) { worst=d; wi=i } }
        sx=sy=sxx=sxy=c=0
        for (i=1;i<=n;i++) if (p[i]>=3000 && p[i]<=8000) { sx+=p[i]; sy+=q[i]; sxx+=p[i]*p[i]; sxy+=p[i]*q[i]; c++ }
        slope=(c*sxy-sx*sy)/(c*sxx-sx*sx); icept=(sy-slope*sx)/c
        best=0; bs=0; be=0; rs=0
        for (i=2;i<=n;i++) {
          s=(q[i]-q[i-1])/(p[i]-p[i-1])
          if (slope>0 && s < ff*slope) { if (!rs) rs=i-1; if (p[i]-p[rs] > best) { best=p[i]-p[rs]; bs=p[rs]; be=p[i] } }
          else rs=0 }
        phi0 = (slope>0) ? -icept/slope : 0
        printf "%.3f %d %d %d %d %d %d %.4f %.3f %.1f\n", worst, p[wi-1], p[wi], (worst>=-tol), best, bs, be, slope, icept, phi0 }
' "${WORK}/curve.txt")"
read -r WORST P_A P_B MONO DZ_SPAN DZ_LO DZ_HI SLOPE ICEPT PHI0 <<<"${METRICS}"
Q_MIN="$(awk 'NR==1||$2<m{m=$2} END{printf "%.1f", m}' "${WORK}/curve.txt")"
Q_MAX="$(awk 'NR==1||$2>m{m=$2} END{printf "%.1f", m}' "${WORK}/curve.txt")"
Q_AT0="$(awk '$1==0{print $2}' "${WORK}/curve.txt")"
SLOPE_UA="$(awk -v s="${SLOPE}" 'BEGIN{printf "%.1f", s*1e-15/1e-12*1e6}')"   # fC/ps -> uA
# (dead-zone text is set after the function check below)
[ "${MONO}" = 1 ] && MONO_TXT="PASS: no step of the curve decreases by more than ${TOL_FC} fC (worst step ${WORST} fC between phi = ${P_A} ps and ${P_B} ps)" \
                  || MONO_TXT="FAIL: worst non-monotone step ${WORST} fC between phi = ${P_A} ps and ${P_B} ps (tolerance ${TOL_FC} fC)"
# Function check: a tri-state PFD makes Q = I_cp x phi, so the 3-8 ns slope must be ~I_cp.
if awk -v s="${SLOPE_UA}" -v n="${ICP_NOM_UA}" 'BEGIN{exit !(s>=0.8*n && s<=1.2*n)}'; then
  FUNC_TXT="PASS: charge is proportional to phase (linear-region slope ${SLOPE_UA} uA vs I_cp,nom ${ICP_NOM_UA} uA, within +-20 %)"
else
  FUNC_TXT="FAIL: charge is not proportional to phase (linear-region slope ${SLOPE_UA} uA vs I_cp,nom ${ICP_NOM_UA} uA, outside +-20 %): this PFD does not act as a tri-state phase detector in this bench; the dead-zone and monotonicity lines below are not meaningful as a PFD grade"
fi
if [ "${FUNC_TXT%%:*}" != PASS ]; then
  DZ_TXT="not graded: the function check failed, so there is no charge-vs-phase curve to read a dead zone from"
  DZ_HEAD="dead zone not graded"
elif [ "${DZ_SPAN}" -gt 0 ]; then
  DZ_TXT="${DZ_SPAN} ps (flat from phi = ${DZ_LO} ps to ${DZ_HI} ps, local slope < ${FLAT_FRAC} x the fitted slope); phase step 10 ps for |phi| <= 1 ns, 50 ps to 3 ns, 250 ps beyond"
  DZ_HEAD="dead zone ${DZ_SPAN} ps"
else
  DZ_TXT="0 ps: no step of the swept curve has a local slope below ${FLAT_FRAC} x the fitted slope; resolution = the 10 ps phase step near the zero crossing (zero crossing at phi = ${PHI0} ps)"
  DZ_HEAD="dead zone 0 ps (step 10 ps)"
fi
[ "${MONO}" = 1 ] && MONO_HEAD="monotonic" || MONO_HEAD="NOT monotonic"

{
  echo "# pfd-sweep run ${ID}"
  echo
  [ "${PFD_VARIANT}" = adopted ] || echo "**DIAGNOSTIC RUN, NOT THE ADOPTED PFD**: \`PFD_VARIANT=${PFD_VARIANT}\` edits a scratch copy of the pinned \`pfd.spice\` (the second reset inverter \`XI2\` removed, \`XI1\` drives \`reset\` directly). Nothing here grades the adopted PFD; it shows what its failure is. Not a design."
  [ "${PFD_VARIANT}" = adopted ] || echo
  echo "**PFD function check: ${FUNC_TXT}**"
  echo
  echo "**Result: ${DZ_HEAD}; charge-vs-phase ${MONO_HEAD}** over phi = -10 ns to +10 ns (T_ref/2 = 10 ns) at 50 MHz. Typical corner only; simulated, not measured."
  echo
  echo "- **Scope**: this is the 50 MHz re-grade of the adopted PFD that spec section 7 conditions its adoption on (gate G5), for dead zone and charge vs phase only. Typical corner (\`mos_tt\`), 27 C, nominal 3.3 V supply, one run. No corner grid, no jitter, no noise number, no spec row 7 grading."
  echo "- **PFD**: \`2AMLogic/sg13g2-pll@$(jq -r '.imports[] | select(.from=="2AMLogic/sg13g2-pll") | .commit' "${ROOT}/reuse.lock.json")\` \`design/netlist/pfd.spice\` (fetched mode, sha256-verified by \`scripts/fetch-pll.sh\`), sha256 \`$(sha256sum "${PFD_ADOPTED}" | cut -d' ' -f1)\`$([ "${PFD_VARIANT}" = adopted ] && echo ', simulated unmodified' || echo "; simulated with variant ${PFD_VARIANT} (sha256 \`$(sha256sum "${PFD_NETLIST}" | cut -d' ' -f1)\`)")"
  echo "- **CP load**: \`${CP_NETLIST#"${ROOT}/"}\` sha256 \`$(sha256sum "${CP_NETLIST}" | cut -d' ' -f1)\` (checked against design/cp.sch), IREF = ${IREF_UA} uA, output held at 2.0 V by an ideal source"
  echo "- **Deck**: \`sim/pfd/pfd_sweep.spice.tmpl\` sha256 \`$(sha256sum "${ROOT}/sim/pfd/pfd_sweep.spice.tmpl" | cut -d' ' -f1)\`, placeholder substitution plus the generated FB source (${NCYC} cycles)"
  echo "- **PDK**: IHP-Open-PDK $(jq -r .pdk.release_tag "${PINS}") (model libraries hash-checked against \`sim/pins.json\`); PDK_ROOT \`${PDK_ROOT}\`; PSP103 OSDI sha256 \`$(jq -r .psp103.osdi_sha256 "${PINS}")\` (pinned)"
  echo "- **Simulator**: \`${NG_VER}\` (\`${NGSPICE}\`), one local \`ngspice -b\`, exit status ${NG_RC}, ${ELAPSED} s wall, ${NPTS_T} accepted time points; \`.tran 25p ${TSTOP_PS}p 0 25p\`; scratch \`.spiceinit\` = \`set ngbehavior=hsa\`"
  echo "- **Commit**: \`${COMMIT}${DIRTY}\` of this repository"
  echo "- **Method**: REF is a fixed 50 MHz clock (T_ref = 20 ns, 100 ps edges). FB is a PWL source whose rising edge in cycle k is delayed by phi_k relative to REF's rising edge (phi > 0: FB lags, PFD pulses UP). The phase is stepped inside the one transient: 10 ps steps for |phi| <= 1 ns, 50 ps steps for 1-3 ns, 250 ps steps for 3 ns to 10 ns; ${NSW} swept cycles after 4 warm-up cycles at +1 ns (excluded). Inputs are never run at different frequencies, so the PFD never sees a cycle slip."
  echo "- **Estimator**: the CP output is held at 2.0 V; Q_k = integral of the current sourced into that node (trapezoid on ngspice's own time points) over cycle k's window, [first input edge of cycle k - 1 ns, the same for cycle k+1). Averaged CP current = Q_k / T_ref. The ideal sign is Q = +I_cp x phi (UP sources)."
  echo "- **Dead zone**: the longest run of consecutive swept steps whose local slope dQ/dphi is below ${FLAT_FRAC} x the fitted linear-region slope; width = the phi span of that run, 0 ps if no step qualifies. The phase step is 10 ps for |phi| <= 1 ns, so a dead zone narrower than 10 ps reads 0 ps. Result: ${DZ_TXT}."
  echo "- **Monotonicity**: Q_k compared with Q_(k-1) in increasing phi. ${MONO_TXT}."
  echo "- **Linear region** (phi 3 to 8 ns, least squares): slope ${SLOPE} fC/ps = ${SLOPE_UA} uA (the nominal I_cp is 200 uA), intercept ${ICEPT} fC, zero crossing phi0 = ${PHI0} ps (static phase offset of this PFD + CP pair, meaningful only when the function check passes). Charge range over the sweep: ${Q_MIN} fC to ${Q_MAX} fC; Q at phi = 0: ${Q_AT0} fC."
  echo "- **Host**: $(hostname), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "| phi (ps) | Q (fC) | averaged I (uA) |"
  echo "|---|---|---|"
  awk '{ printf "| %s | %s | %s |\n", $1, $2, $3 }' "${WORK}/curve.txt"
  echo
  echo "ngspice log: [\`${ID}-ngspice.txt\`](${ID}-ngspice.txt)"
} > "${REC}"
echo "record: ${REC#"${ROOT}/"}"
echo "function check: ${FUNC_TXT%%:*}; ${DZ_HEAD}; ${MONO_HEAD} (worst step ${WORST} fC between ${P_A} and ${P_B} ps); slope ${SLOPE_UA} uA; ${ELAPSED}s"
