#!/usr/bin/env bash
# One-command smoke bench: fetch + verify the pinned sg13g2-vco, render its
# netlist template against the installed PDK, run ONE local ngspice at the
# typical corner and nominal supply (a toolchain/pin check, not a corner grid
# and not a loop result), and write a dated append-only record.
#
#   scripts/run-vco-smoke.sh
#
# Environment:
#   PDK_ROOT       parent of ihp-sg13g2/ (default: first of ~/share/pdk, /usr/share/pdk, /usr/local/share/pdk)
#   NGSPICE        ngspice binary (default: ngspice on PATH); must load OSDI v0.4 (>= 46)
#   OPENVAF_R      openvaf-r binary used to compile mosvar.va (default: openvaf-r on PATH)
#   OPENVAF_LD_LIBRARY_PATH   dir holding libLLVM.so.21 for openvaf-r, if not system-installed
#   SMOKE_CPUSET   optional `taskset -c` list to keep ngspice off other jobs' cores
#
# Exit 0 only if the VCO oscillates (f > 1 GHz, Vpp(diff) > 0.1 V at Vctrl = 1.65 V).
# A failed run still writes its record: failures are evidence too.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PINS="${ROOT}/sim/pins.json"
FETCHED="${ROOT}/.fetched"
die() { echo "run-vco-smoke: error: $*" >&2; exit 1; }

"${ROOT}/scripts/fetch-vco.sh"

# ---- PDK: locate and check against the pinned model-library hashes ----------
if [ -z "${PDK_ROOT:-}" ]; then
  for c in "${HOME}/share/pdk" /usr/share/pdk /usr/local/share/pdk; do
    [ -d "${c}/ihp-sg13g2/libs.tech/ngspice/models" ] && { PDK_ROOT="${c}"; break; }
  done
fi
[ -n "${PDK_ROOT:-}" ] || die "no ihp-sg13g2 install found; set PDK_ROOT to the parent of ihp-sg13g2/ (IHP-Open-PDK $(jq -r .pdk.release_tag "${PINS}"))"
PDK_DIR="${PDK_ROOT}/ihp-sg13g2"
MODELS="${PDK_DIR}/libs.tech/ngspice/models"
while IFS=$'\t' read -r name want; do
  got="$(sha256sum "${MODELS}/${name}" 2>/dev/null | cut -d' ' -f1)"
  [ "${got}" = "${want}" ] || die "${MODELS}/${name} is ${got:-missing}, pinned ${want}: not the pinned PDK (IHP-Open-PDK $(jq -r .pdk.release_tag "${PINS}"))"
done < <(jq -r '.pdk.model_libs_sha256 | to_entries[] | [.key, .value] | @tsv' "${PINS}")

# ---- OSDI: compile the PDK's own mosvar.va (never trust a prebuilt binary blindly)
VA_DIR="${PDK_DIR}/libs.tech/verilog-a/mosvar"
va_sha="$(sha256sum "${VA_DIR}/mosvar.va" | cut -d' ' -f1)"
[ "${va_sha}" = "$(jq -r .osdi.verilog_a_sha256 "${PINS}")" ] || die "mosvar.va hash ${va_sha} is not the pinned one"
OSDI="${FETCHED}/osdi/mosvar.osdi"
mkdir -p "${FETCHED}/osdi"
OVAF="${OPENVAF_R:-$(command -v openvaf-r || true)}"
[ -n "${OVAF}" ] || die "openvaf-r not found; set OPENVAF_R (pinned: $(jq -r .osdi.compiler "${PINS}"))"
export LD_LIBRARY_PATH="${OPENVAF_LD_LIBRARY_PATH:+${OPENVAF_LD_LIBRARY_PATH}:}${LD_LIBRARY_PATH:-}"
OVAF_VER="$("${OVAF}" --version 2>&1 | head -1)"
rm -f "${OSDI}"
"${OVAF}" -I "${VA_DIR}" -o "${OSDI}" "${VA_DIR}/mosvar.va" >/dev/null 2>&1 || die "openvaf-r failed on mosvar.va"
unset LD_LIBRARY_PATH
osdi_sha="$(sha256sum "${OSDI}" | cut -d' ' -f1)"

# ---- render the deck: placeholder substitution only --------------------------
NGSPICE="${NGSPICE:-$(command -v ngspice || true)}"
[ -x "${NGSPICE}" ] || die "ngspice not found; set NGSPICE"
NG_VER="$("${NGSPICE}" --version 2>&1 | grep -o 'ngspice-[0-9.]*' | head -1)"
IND="${FETCHED}/sg13g2-vco/sim/inductor-model/sg13g2_inductor_em.spice"
TMPL="${FETCHED}/sg13g2-vco/design/vco.spice"
WORK="$(mktemp -d)"; trap 'rm -rf "${WORK}"' EXIT
sed -e "s|@@MODELS_DIR@@|${MODELS}|g" -e "s|@@IND_MODEL@@|${IND}|g" -e "s|@@OSDI_MOSVAR@@|${OSDI}|g" \
  "${TMPL}" > "${WORK}/vco_elab.spice"
if grep -vE '^[[:space:]]*\*' "${WORK}/vco_elab.spice" | grep -q '@@'; then die "unsubstituted placeholder left in the rendered deck"; fi
printf 'set ngbehavior=hsa\n' > "${WORK}/.spiceinit"

# ---- the one run ---------------------------------------------------------------
COMMIT="$(jq -r '.imports[] | select(.from=="2AMLogic/sg13g2-vco") | .commit' "${ROOT}/reuse.lock.json")"
ID="$(date -u +%Y%m%d-%H%M%S)-${COMMIT:0:7}"
REC_DIR="${ROOT}/sim/vco-smoke/records"; mkdir -p "${REC_DIR}"
REC="${REC_DIR}/${ID}.md"
[ ! -e "${REC}" ] || die "${REC} exists; records are append-only"
RUN=("${NGSPICE}" -b vco_elab.spice)
[ -z "${SMOKE_CPUSET:-}" ] || RUN=(taskset -c "${SMOKE_CPUSET}" "${RUN[@]}")
set +e
( cd "${WORK}" && HOME="${WORK}" "${RUN[@]}" ) > "${WORK}/ngspice.log" 2>&1
NG_RC=$?
set -e

# ---- extract: rising mean-crossings of vdiff over the 10-20 ns window ---------
measure() { # <wrdata file> -> "f_GHz vpp_V cycles" or "NA NA 0"
  [ -s "$1" ] || { echo "NA NA 0"; return; }
  awk '$1 >= 10e-9 && $1 <= 20e-9 { t[++n]=$1; v[n]=$2; s+=$2; if(n==1||$2<lo)lo=$2; if(n==1||$2>hi)hi=$2 }
       END { if (n < 10) { print "NA NA 0"; exit }
             m = s/n; c = 0
             for (i = 2; i <= n; i++) if (v[i-1] < m && v[i] >= m) { x = t[i-1] + (m-v[i-1])*(t[i]-t[i-1])/(v[i]-v[i-1]); if (!c) t0 = x; t1 = x; c++ }
             if (c < 2) { printf "NA %.4f %d\n", hi-lo, c; exit }
             printf "%.4f %.4f %d\n", (c-1)/(t1-t0)/1e9, hi-lo, c-1 }' "$1"
}
ROWS=""; OSC=0
for v in 0 1.65 3.3; do
  read -r f vpp cyc < <(measure "${WORK}/vco_tran_${v}.data")
  ROWS="${ROWS}| ${v} | ${f} | ${vpp} | ${cyc} |"$'\n'
  if [ "${v}" = 1.65 ] && [ "${f}" != NA ] && awk -v f="${f}" -v p="${vpp}" 'BEGIN{exit !(f>1 && p>0.1)}'; then OSC=1; fi
done
cp "${WORK}/ngspice.log" "${REC_DIR}/${ID}-ngspice.txt"

{
  echo "# sg13g2-vco smoke run ${ID}"
  echo
  echo "**Result: $([ "${OSC}" = 1 ] && echo 'OSCILLATES' || echo 'DOES NOT OSCILLATE / run failed')** (toolchain and pin check; not a loop result, not a re-grade of the VCO, and not a noise result)."
  echo
  echo "- **VCO**: \`2AMLogic/sg13g2-vco@${COMMIT}\` (\`reuse.lock.json\`, fetched mode, every file sha256-verified before use)"
  echo "- **Deck**: fetched \`design/vco.spice\` sha256 \`$(sha256sum "${TMPL}" | cut -d' ' -f1)\`, placeholder substitution only (\`@@MODELS_DIR@@\`, \`@@IND_MODEL@@\`, \`@@OSDI_MOSVAR@@\`); inductor model \`sim/inductor-model/sg13g2_inductor_em.spice\` sha256 \`$(sha256sum "${IND}" | cut -d' ' -f1)\`"
  echo "- **PDK**: IHP-Open-PDK $(jq -r .pdk.release_tag "${PINS}") (model libraries hash-checked against \`sim/pins.json\`); PDK_ROOT \`${PDK_ROOT}\`"
  echo "- **OSDI**: \`mosvar.osdi\` compiled from the PDK's \`mosvar.va\` (sha256 \`${va_sha}\`) with \`${OVAF_VER}\` (${OVAF}), output sha256 \`${osdi_sha}\`"
  echo "- **Simulator**: \`${NG_VER}\` (\`${NGSPICE}\`), single local \`ngspice -b\`, exit status ${NG_RC}; scratch \`.spiceinit\` = \`set ngbehavior=hsa\`"
  echo "- **Corner**: typical (\`hbt_typ\`, \`mos_tt\`, \`cap_typ\`), 27 C (ngspice default TEMP), VDD 3.3 V, 10 mV differential \`.ic\` kick from the deck"
  echo "- **Method**: the deck's own \`.control\` block: \`tran 1p 20n 0 2p\` at Vctrl = 0, 1.65, 3.3 V. Frequency = (rising mean-crossings of v(OUTP)-v(OUTN) - 1) / span between first and last crossing, 10-20 ns window; amplitude = peak-to-peak of the same differential voltage over the same window. ngspice \`.tran\`, no noise, single run each."
  echo "- **Host**: $(hostname), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "| Vctrl (V) | f_osc (GHz) | Vpp diff (V) | cycles |"
  echo "|---|---|---|---|"
  printf '%s' "${ROWS}"
  echo
  echo "ngspice log: [\`${ID}-ngspice.txt\`](${ID}-ngspice.txt)"
} > "${REC}"

echo "record: ${REC#"${ROOT}/"}"
printf '%s' "${ROWS}"
[ "${OSC}" = 1 ] || { echo "run-vco-smoke: the pinned VCO did NOT oscillate in this flow (see the record)" >&2; exit 1; }
