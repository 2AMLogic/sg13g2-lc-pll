#!/usr/bin/env bash
# PDK-free test for `scripts/run-lock-detector.sh report <grid dir>`: the replay of a completed
# batch grid must rebuild the stage record from the saved request.json + report.json ALONE (no
# PDK, ngspice, klt, fetch or network: the replay runs with a PATH that has none of them and
# PDK_ROOT pointed at an absent directory), must describe the simulation from the saved report
# (netlist hashes as recorded, unrecorded fields marked), must refuse a non-passing report, and
# must refuse to overwrite an existing record (sim/*/records is append-only). The committed grid
# directories are the fixtures; every replay and comparison runs on scratch copies.
#   scripts/test-lock-detector-report.sh
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
fail=0

# A PATH with none of the simulation tools: the replay must not invoke any of them.
BIN="${T}/bin"; mkdir -p "${BIN}"
for c in bash sh env python3 jq basename dirname sed date hostname mktemp sha256sum cat cut head grep awk cp mkdir rm zcat gzip uname readlink; do
  p="$(command -v "${c}" 2>/dev/null)" && ln -s "${p}" "${BIN}/${c}"
done

replay() { # <grid dir> -> runs `report` with no simulation tooling available; rc in REPLAY_RC
  env PATH="${BIN}" PDK_ROOT="${T}/no-such-pdk" NGSPICE="${T}/no-such-ngspice" \
    bash "${ROOT}/scripts/run-lock-detector.sh" report "$1" >"${T}/replay.log" 2>&1
  REPLAY_RC=$?
}

# Fixture selection: one complete archived grid per stage, by name. A `grid1 --dry-run` leaves a
# request-only ${ID}-grid1 directory (request.json but no report.json/record) in the records dir,
# and records are append-only, so more than one complete archive per stage can exist; a raw glob
# would feed the first into the loop and make the second multi-source `cp -r` fail. (Both found
# live on a scratch fixture tree by the reviewer.)
sel_grid() { # <stage> -> GRID_SEL = newest complete archive for that stage
  GRID_SEL=""
  local g
  for g in "${ROOT}/sim/lock-detector/records/"*-"$1"; do
    if [ -d "${g}" ] && [ -f "${g}/report.json" ] && [ -f "${g}.md" ]; then
      GRID_SEL="${g}"   # append-only records: the last match is the newest archive
    fi
  done
  [ -n "${GRID_SEL}" ] || { echo "test-lock-detector-report: no complete ${1} archive under sim/lock-detector/records" >&2; exit 1; }
}
sel_grid grid1; GRID1="${GRID_SEL}"
sel_grid grid2; GRID2="${GRID_SEL}"

for GRID in "${GRID1}" "${GRID2}"; do
  NAME="$(basename "${GRID}")"
  D="${T}/${NAME}"; cp -r "${GRID}" "${D}"
  ARCHIVED="${GRID}.md"
  SCRATCH_MD="${D}.md"
  cp "${ARCHIVED}" "${SCRATCH_MD}"

  # Append-only: replaying onto a grid whose record already exists must refuse and leave it alone.
  replay "${D}"
  if [ "${REPLAY_RC}" != 0 ] && cmp -s "${ARCHIVED}" "${SCRATCH_MD}" && grep -q "append-only" "${T}/replay.log"; then
    echo "ok   ${NAME}: replay refused an existing record (append-only), record untouched"
  else
    echo "FAIL ${NAME}: replay did not refuse an existing record (rc=${REPLAY_RC})"; sed -n '1,5p' "${T}/replay.log"; fail=1
  fi

  # The replay itself, with the record moved out of the way.
  rm "${SCRATCH_MD}"
  replay "${D}"
  if [ "${REPLAY_RC}" != 0 ] || [ ! -f "${SCRATCH_MD}" ]; then
    echo "FAIL ${NAME}: replay without simulation tooling failed (rc=${REPLAY_RC})"; sed -n '1,10p' "${T}/replay.log"; fail=1
    continue
  fi
  echo "ok   ${NAME}: replay succeeded with no PDK, ngspice, klt, fetch or network"

  # Everything downstream of the provenance line is derived from the saved artifacts: the results
  # section must be byte-identical to the archived record, and the run-history numbers must be the
  # archived ones. (The run-history sentence's tail wording differs from the archived records by a
  # pre-existing dirty-stamp drift -- the records were written by an uncommitted variant -- so the
  # comparison there is on the numbers, not the bytes.)
  NUMS="$(grep -o 'returned [0-9]* of [0-9]* corners' "${ARCHIVED}")"
  if grep -Fqx "$(grep -F '**Simulated, not measured.**' "${ARCHIVED}")" "${SCRATCH_MD}" \
    && diff <(sed -n '/^## Results/,$p' "${ARCHIVED}") <(sed -n '/^## Results/,$p' "${SCRATCH_MD}") >/dev/null \
    && { [ -z "${NUMS}" ] || grep -qF "${NUMS}" "${SCRATCH_MD}"; }; then
    echo "ok   ${NAME}: lead paragraph, run-history numbers and results identical to the archived record"
  else
    echo "FAIL ${NAME}: replayed record diverges from the archived one below the provenance line"; diff "${ARCHIVED}" "${SCRATCH_MD}" | head -20; fail=1
  fi

  # Simulation provenance comes from the saved report: the recorded netlist hashes are quoted, the
  # fields the report does not record are marked unrecorded, and no fresh-run stamp leaks in.
  PFD_SHA="$(jq -r '[.environment.netlist_closure[]? | select((.path // "") | endswith("/pfd.spice"))][0].sha256' "${D}/report.json")"
  LD_SHA="$(jq -r '[.environment.netlist_closure[]? | select((.path // "") | endswith("/lock_detector.spice"))][0].sha256' "${D}/report.json")"
  if grep -q "pfd.spice sha256 \`${PFD_SHA}\`" "${SCRATCH_MD}" && grep -q "lock_detector.spice sha256 \`${LD_SHA}\`" "${SCRATCH_MD}" \
    && grep -q "not recorded in the saved report" "${SCRATCH_MD}" && ! grep -Eq 'Commit .[0-9a-f]{7}' "${SCRATCH_MD}"; then
    echo "ok   ${NAME}: provenance from report.json (netlist hashes recorded, pin/commit unrecorded)"
  else
    echo "FAIL ${NAME}: provenance line does not follow the saved report"; grep -n '\*\*Cells\*\*' "${SCRATCH_MD}"; fail=1
  fi
done

# A non-passing report must still fail, and write nothing.
FAILDIR="${T}/failing-grid"; cp -r "${GRID1}" "${FAILDIR}"
jq '.status = "fail"' "${FAILDIR}/report.json" > "${FAILDIR}/report.json.new" && mv "${FAILDIR}/report.json.new" "${FAILDIR}/report.json"
replay "${FAILDIR}"
if [ "${REPLAY_RC}" != 0 ] && [ ! -e "${FAILDIR}.md" ] && grep -q "not a complete passing report" "${T}/replay.log"; then
  echo "ok   non-passing report refused, no record written"
else
  echo "FAIL non-passing report was accepted or clobbered something (rc=${REPLAY_RC})"; sed -n '1,5p' "${T}/replay.log"; fail=1
fi

# A grid directory without a report must fail too.
mkdir -p "${T}/empty-grid"; replay "${T}/empty-grid"
if [ "${REPLAY_RC}" != 0 ] && [ ! -e "${T}/empty-grid.md" ]; then
  echo "ok   missing report.json refused, no record written"
else
  echo "FAIL missing report.json accepted (rc=${REPLAY_RC})"; fail=1
fi

# Partial metadata: a saved report stripped of its environment blocks (remote.fleet,
# engine_version, netlist_closure) but carrying .provenance.klt_version must still replay from
# the saved artifacts alone: klt quoted from .provenance, the stripped fields marked unrecorded
# (never ngspice-null), and the cell digests reported without an "unmodified" claim the saved
# evidence cannot verify against the upstream pin.
PGRID="${T}/partial-metadata-grid"; cp -r "${GRID1}" "${PGRID}"
jq 'del(.environment.remote.fleet, .environment.engine_version, .environment.netlist_closure)' \
  "${PGRID}/report.json" > "${PGRID}/report.json.new" && mv "${PGRID}/report.json.new" "${PGRID}/report.json"
replay "${PGRID}"
PKLT="$(jq -r '.provenance.klt_version // ""' "${PGRID}/report.json")"
if [ "${REPLAY_RC}" = 0 ] && [ -f "${PGRID}.md" ] \
  && grep -q "klt ${PKLT}," "${PGRID}.md" \
  && ! grep -q "ngspice-null" "${PGRID}.md" \
  && grep -q "pfd.spice sha256 \`unrecorded\`" "${PGRID}.md" \
  && ! grep '\*\*Cells\*\*' "${PGRID}.md" | grep -q "unmodified" \
  && diff <(sed -n '/^## Results/,$p' "${GRID1}.md") <(sed -n '/^## Results/,$p' "${PGRID}.md") >/dev/null; then
  echo "ok   partial-metadata report: klt from .provenance, stripped fields unrecorded, no unverifiable match claim"
else
  echo "FAIL partial-metadata report mis-rendered (rc=${REPLAY_RC})"; grep -n '\*\*Cells\*\*' "${PGRID}.md" 2>/dev/null; sed -n '1,5p' "${T}/replay.log"; fail=1
fi

exit "${fail}"
