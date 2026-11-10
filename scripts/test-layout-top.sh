#!/usr/bin/env bash
# Integrated layout check (#35): committed layout/top.gds reproduces, holds the pinned VCO unmodified,
# keep-out intrusions are exactly the recorded VCTRL pin-access ones, and the checks can fail.
# Needs .fetched/ (scripts/fetch-vco.sh), klt, a python with `klayout` (default .venv/bin/python; LAYOUT_PY).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${LAYOUT_PY:-${ROOT}/.venv/bin/python}"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
pass=0; bad=0
expect() { local name="$1" want="$2"; shift 2
  "$@" >"${T}/out" 2>&1; local rc=$?
  if { [ "${want}" = ok ] && [ "${rc}" = 0 ]; } || { [ "${want}" = refuse ] && [ "${rc}" != 0 ]; }; then
    echo "PASS ${name} (rc=${rc})"; pass=$((pass+1))
  else echo "FAIL ${name} (rc=${rc})"; sed 's/^/    /' "${T}/out"; bad=$((bad+1)); fi; }
VCO="${ROOT}/.fetched/sg13g2-vco/layout/vco.gds"; G="${ROOT}/layout/top.gds"

expect "fetched VCO files verify" ok "${ROOT}/scripts/fetch-vco.sh" --verify
expect "regenerated geometry == committed provenance" ok "${PY}" "${ROOT}/layout/gen_integrated.py" --check
klt clip "${G}" --cell vco -o "${T}/placed.gds" >/dev/null 2>&1
klt clip "${VCO}" --cell vco -o "${T}/pinned.gds" >/dev/null 2>&1
expect "placed VCO subtree == pinned stream" ok klt diff "${T}/placed.gds" "${T}/pinned.gds"
expect "committed stream sha256 == provenance" ok bash -c \
  "[ \"\$(sha256sum '${G}' | cut -d' ' -f1)\" = \"\$(jq -r .output.sha256 '${ROOT}/layout/provenance.json')\" ]"
expect "attestation envelope passes" ok jq -e '.status=="pass" and .t1_item==2' "${ROOT}/manifests/layout.attest.json"

# keep-out: the only intrusions are the VCTRL pin-access stack (3 shapes, Metal3/4/5), recorded in layout/README.md
"${PY}" "${ROOT}/layout/gen_top.py" --out "${T}/b.gds" --forbidden-json "${T}/f.json" >/dev/null 2>&1
klt keepout-check "${G}" --forbidden "${T}/f.json" --margin 20 --cells vco --format json >"${T}/ko.json" 2>/dev/null
n="$(jq '[.. | objects | select(has("kind"))] | length' "${T}/ko.json" 2>/dev/null)"
[ -n "${n}" ] && [ "${n}" = 3 ] && { echo "PASS keep-out: 3 recorded VCTRL intrusions"; pass=$((pass+1)); } \
  || { echo "FAIL keep-out intrusions = '${n}', expected the 3 recorded VCTRL ones"; bad=$((bad+1)); }

# negative controls
"${PY}" -I - "${G}" "${T}" <<'PYEOF'
import sys, klayout.db as db
g, t = sys.argv[1], sys.argv[2]
ly = db.Layout(); ly.read(g)
ly.cell("vco").shapes(ly.layer(8, 0)).insert(db.Box(0, 0, 1000, 1000)); ly.write(t + "/edited.gds")
ly = db.Layout(); ly.read(g)
ly.cell("lc_pll_top").shapes(ly.layer(8, 0)).insert(db.Box(-320000, 100000, -315000, 105000)); ly.write(t + "/intr.gds")
PYEOF
klt clip "${T}/edited.gds" --cell vco -o "${T}/edited_clip.gds" >/dev/null 2>&1
expect "NEG edited VCO cell detected" refuse klt diff "${T}/edited_clip.gds" "${T}/pinned.gds"
klt keepout-check "${T}/intr.gds" --forbidden "${T}/f.json" --margin 20 --cells vco --format json >"${T}/ko2.json" 2>/dev/null
n2="$(jq '[.. | objects | select(has("kind"))] | length' "${T}/ko2.json" 2>/dev/null)"
[ "${n2}" = 4 ] && { echo "PASS NEG extra keep-out intruder detected (4)"; pass=$((pass+1)); } || { echo "FAIL NEG intruder count '${n2}'"; bad=$((bad+1)); }
mkdir -p "${T}/s/.fetched/sg13g2-vco/layout"; cp "${VCO}" "${T}/s/.fetched/sg13g2-vco/layout/vco.gds"
printf 'X' | dd of="${T}/s/.fetched/sg13g2-vco/layout/vco.gds" bs=1 seek=100 conv=notrunc 2>/dev/null
expect "NEG tampered stream: generator refuses" refuse "${PY}" "${ROOT}/layout/gen_integrated.py" --vco "${T}/s/.fetched/sg13g2-vco/layout/vco.gds" --check
echo "${pass} passed, ${bad} failed"; [ "${bad}" = 0 ]
