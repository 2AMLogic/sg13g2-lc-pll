#!/usr/bin/env bash
# Layout scaffold check: the generated top cell holds the pinned VCO unmodified, and the
# keep-out / guard-ring checks both pass and can fail. Needs .fetched/ (scripts/fetch-vco.sh),
# klt, jq and a python with `klayout` (default .venv/bin/python; override with LAYOUT_PY).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${LAYOUT_PY:-${ROOT}/.venv/bin/python}"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
# expect()/expect_summary and the pass/bad tally, including when `refuse:<ERE>` is required
# over a bare `refuse`: see the contract in scripts/lib-expect.sh.
# shellcheck source=lib-expect.sh
source "${ROOT}/scripts/lib-expect.sh"
VCO="${ROOT}/.fetched/sg13g2-vco/layout/vco.gds"
G="${T}/top.gds"
FORB="${T}/forbidden.json"
RING='[-331.13,-132.03,331.13,316.26]'   # ring outer edge = vco bbox + 20 (keep-out) + 5 + 1
# layout/gen_top.py's refusal on a VCO stream whose sha256 differs from reuse.lock.json.
REFUSAL='gen_top: .* sha256 [0-9a-f]{64} != pinned [0-9a-f]{64}; refusing'

expect "fetched VCO files verify"   ok "${ROOT}/scripts/fetch-vco.sh" --verify
expect "generate top cell"          ok "${PY}" "${ROOT}/layout/gen_top.py" --out "${G}" --forbidden-json "${FORB}"
klt clip "${G}" --cell vco -o "${T}/vco_placed.gds" >/dev/null 2>&1
klt clip "${VCO}" --cell vco -o "${T}/vco_pinned.gds" >/dev/null 2>&1
expect "placed VCO subtree == pinned stream" ok klt diff "${T}/vco_placed.gds" "${T}/vco_pinned.gds"
expect "keepout-check clean"        ok klt keepout-check "${G}" --forbidden "${FORB}" --margin 20 --cells vco
expect "ring-check closed annulus"  ok klt ring-check "${G}" --layers '[[1,0]]' --region "${RING}" --ignore-enclosed

# Negative controls.
"${PY}" -I - "${G}" "${T}" <<'PYEOF'
import sys, klayout.db as db
g, t = sys.argv[1], sys.argv[2]
def load(): ly = db.Layout(); ly.read(g); return ly
ly = load()   # 1: a shape inside the VCO cell
ly.cell("vco").shapes(ly.layer(8, 0)).insert(db.Box(0, 0, 1000, 1000)); ly.write(t + "/vco_edited.gds")
ly = load()   # 2: Metal1 intruder inside the keep-out margin, outside the VCO
ly.cell("lc_pll_top").shapes(ly.layer(8, 0)).insert(db.Box(-320000, 100000, -315000, 105000)); ly.write(t + "/intruder.gds")
ly = load()   # 3: cut the guard ring (Activ) on its left side
ly.cell("lc_pll_top").shapes(ly.layer(1, 0)).insert(db.Box(-332000, 100000, -330000, 102000))
r = db.Region(ly.cell("lc_pll_top").shapes(ly.layer(1, 0))); cut = db.Region(db.Box(-332000, 100000, -330000, 102000))
s = ly.cell("lc_pll_top").shapes(ly.layer(1, 0)); s.clear(); s.insert(r - cut); ly.write(t + "/cut_ring.gds")
PYEOF
klt clip "${T}/vco_edited.gds" --cell vco -o "${T}/vco_edited_clip.gds" >/dev/null 2>&1
expect "NEG edited VCO cell detected"   refuse klt diff "${T}/vco_edited_clip.gds" "${T}/vco_pinned.gds"
expect "NEG keep-out intruder detected" refuse klt keepout-check "${T}/intruder.gds" --forbidden "${FORB}" --margin 20 --cells vco
expect "NEG cut guard ring detected"    refuse klt ring-check "${T}/cut_ring.gds" --layers '[[1,0]]' --region "${RING}" --ignore-enclosed

# Tamper with the fetched stream (scratch copy of the lock + stream): verify and generator refuse.
mkdir -p "${T}/s/scripts" "${T}/s/.fetched/sg13g2-vco/layout"
cp "${ROOT}/scripts/fetch-vco.sh" "${T}/s/scripts/"; cp "${ROOT}/reuse.lock.json" "${T}/s/"
cp "${VCO}" "${T}/s/.fetched/sg13g2-vco/layout/vco.gds"
printf 'X' | dd of="${T}/s/.fetched/sg13g2-vco/layout/vco.gds" bs=1 seek=100 conv=notrunc 2>/dev/null
expect "NEG tampered stream: fetch-vco --verify" refuse "${T}/s/scripts/fetch-vco.sh" --verify
# Must carry gen_top.py's own sha256 refusal, not merely exit non-zero: see scripts/lib-expect.sh.
expect "NEG tampered stream: generator refuses"  "refuse:${REFUSAL}" \
  "${PY}" "${ROOT}/layout/gen_top.py" --vco "${T}/s/.fetched/sg13g2-vco/layout/vco.gds" --out "${T}/x.gds"

expect_summary || exit 1
