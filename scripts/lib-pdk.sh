# shellcheck shell=bash
# Sourced by the run-*.sh bench drivers (`git grep -ln 'source.*lib-pdk.sh' -- scripts`): locate
# the PDK, refuse one whose model libraries (or the three OSDI libraries) do not hash to
# sim/pins.json, find ngspice, cap its threads.
# Set PDK_SKIP_OSDI_PINS=1 before sourcing to skip ALL THREE OSDI pin checks below (the VCO
# benches compile mosvar.va instead and use none of the three); OSDI_PSP, OSDI_PSP_NQS and
# OSDI_R3 are then all unset. There is no per-library skip: a bench needing any one of them
# leaves the flag unset and gets all three pinned.
# Sets: PDK_ROOT PDK_DIR MODELS OSDI_PSP OSDI_PSP_NQS OSDI_R3 NGSPICE NG_VER NG_PIN_STATUS PINS. Expects ROOT and die().
PINS="${ROOT}/sim/pins.json"
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
# The three OSDI libraries the decks pre_osdi, pinned identically and skipped together. Why each
# is pinned (a deck that loads none of them simply ignores its variable):
#   psp103      the HV MOS models in cornerMOShv.lib are PSP103.
#   psp103_nqs  the RF HV MOS variants (sg13g2_hv_*mos_psp_rf, pspnqs103va) need the NQS build of
#               PSP103; the divider decks load it explicitly (pre_osdi) so no host ngspice startup
#               file is relied on.
#   r3_cmc      the loop-filter poly resistor (rppd) and the lock-detector rhigh pull-up are
#               r3_cmc OSDI models (sim/loop-tran, scripts/run-lock-detector.sh).
if [ "${PDK_SKIP_OSDI_PINS:-0}" != 1 ]; then
  while IFS=$'\t' read -r key var; do
    osdi="${PDK_DIR}/$(jq -r ".${key}.osdi" "${PINS}")"
    got="$(sha256sum "${osdi}" 2>/dev/null | cut -d' ' -f1)"
    [ "${got}" = "$(jq -r ".${key}.osdi_sha256" "${PINS}")" ] || die "${osdi} is ${got:-missing}, not the pinned ${key}.osdi"
    declare -g "${var}=${osdi}"
  done < <(printf '%s\t%s\n' psp103 OSDI_PSP psp103_nqs OSDI_PSP_NQS r3_cmc OSDI_R3)
  unset key var osdi
fi
NGSPICE="${NGSPICE:-$(command -v ngspice || true)}"
[ -x "${NGSPICE}" ] || die "ngspice not found; set NGSPICE"
NG_VER="$("${NGSPICE}" --version 2>&1 | grep -o 'ngspice-[0-9.]*' | head -1 || true)"
source "$(dirname "${BASH_SOURCE[0]}")/lib-ngpin.sh"
# Shared 8-core host: ngspice's OpenMP threads default to every core. Keep to 2 (host rule).
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}"
[ "${OMP_NUM_THREADS}" -le 2 ] || die "OMP_NUM_THREADS=${OMP_NUM_THREADS}: keep ngspice to <= 2 threads on the shared host"
