# shellcheck shell=bash
# Sourced by scripts/run-cp-dc.sh and scripts/run-pfd-sweep.sh: locate the PDK, refuse one
# whose model libraries (or PSP103 OSDI) do not hash to sim/pins.json, find ngspice.
# Sets: PDK_ROOT PDK_DIR MODELS OSDI_PSP NGSPICE NG_VER PINS. Expects ROOT and die().
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
OSDI_PSP="${PDK_DIR}/$(jq -r .psp103.osdi "${PINS}")"
got="$(sha256sum "${OSDI_PSP}" 2>/dev/null | cut -d' ' -f1)"
[ "${got}" = "$(jq -r .psp103.osdi_sha256 "${PINS}")" ] || die "${OSDI_PSP} is ${got:-missing}, not the pinned psp103.osdi"
NGSPICE="${NGSPICE:-$(command -v ngspice || true)}"
[ -x "${NGSPICE}" ] || die "ngspice not found; set NGSPICE"
NG_VER="$("${NGSPICE}" --version 2>&1 | grep -o 'ngspice-[0-9.]*' | head -1)"
# Shared 8-core host: ngspice's OpenMP threads default to every core. Keep to 2 (host rule).
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}"
[ "${OMP_NUM_THREADS}" -le 2 ] || die "OMP_NUM_THREADS=${OMP_NUM_THREADS}: keep ngspice to <= 2 threads on the shared host"
