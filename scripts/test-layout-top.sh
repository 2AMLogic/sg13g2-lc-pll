#!/usr/bin/env bash
# Integrated layout check (#35): committed layout/top.gds reproduces, holds the pinned VCO unmodified,
# keep-out intrusions are exactly the recorded VCTRL pin-access ones, and the checks can fail.
# Needs .fetched/ (scripts/fetch-vco.sh), klt, a python with `klayout` (default .venv/bin/python; LAYOUT_PY).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${LAYOUT_PY:-${ROOT}/.venv/bin/python}"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
pass=0; bad=0
# want: ok | refuse | refuse:<ERE>. Plain `refuse` passes on any non-zero exit, so it cannot
# tell a detected fault from a crash (a SyntaxError, a missing klayout); `refuse:<ERE>` also
# requires the checker's own refusal text in the output, which is what makes a negative
# control discriminating (#234).
expect() { local name="$1" want="$2"; shift 2
  "$@" >"${T}/out" 2>&1; local rc=$?
  local ok=0
  case "${want}" in
    ok) [ "${rc}" = 0 ] && ok=1 ;;
    refuse) [ "${rc}" != 0 ] && ok=1 ;;
    refuse:*) [ "${rc}" != 0 ] && grep -qE "${want#refuse:}" "${T}/out" && ok=1 ;;
    *) echo "FAIL ${name}: unknown expectation '${want}'"; bad=$((bad+1)); return ;;
  esac
  if [ "${ok}" = 1 ]; then
    echo "PASS ${name} (rc=${rc})"; pass=$((pass+1))
  else echo "FAIL ${name} (rc=${rc})"; sed 's/^/    /' "${T}/out"; bad=$((bad+1)); fi; }
VCO="${ROOT}/.fetched/sg13g2-vco/layout/vco.gds"; G="${ROOT}/layout/top.gds"
# layout/gen_top.py's refusal on a VCO stream whose sha256 differs from reuse.lock.json.
REFUSAL='gen_top: .* sha256 [0-9a-f]{64} != pinned [0-9a-f]{64}; refusing'

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
# Must carry gen_top.py's own sha256 refusal (reached through gen_integrated's build_base
# subprocess), not merely exit non-zero: see the expect() note above.
expect "NEG tampered stream: generator refuses" "refuse:${REFUSAL}" \
  "${PY}" "${ROOT}/layout/gen_integrated.py" --vco "${T}/s/.fetched/sg13g2-vco/layout/vco.gds" --check
# Metal1 pad-trim guard (#245). Drives gen_integrated.trim_pad over synthetic Metal1 so the guard
# is exercised in BOTH directions: it must stay quiet on a pad whose via survives the trim, and must
# report a pad cut back past its own Via1. A check that cannot fail is not a check (same reasoning as
# the refuse:<ERE> note above). Foreign Metal1 is placed NOT touching the pad, because metal that
# touches it is the pad's own landing polygon and trim_pad excludes it by construction.
cat >"${T}/trimguard.py" <<'TRIMEOF'
import sys
sys.path.insert(0, sys.argv[1] + "/layout")
import klayout.db as db
import gen_integrated as g

dbu = 0.001
PAD, VIA, SP = g.PAD_UM[0], g.VIA_UM[0], g.M1B_SP_UM
pad = g.box(dbu, 0, 0, PAD, PAD)
edge = PAD / 2


def run(foreign_boxes, sp_um):
    base = db.Region(pad)
    for b in foreign_boxes:
        base.insert(b)
    base = base.merged()
    keep, trimmed, unc = g.trim_pad(dbu, pad, base, round(sp_um / dbu))
    return trimmed, not unc.is_empty()


# a 1 um square whose near edge sits `gap` outside the pad, on the +x side
def near(gap):
    return g.box(dbu, edge + gap + 0.5, 0, 1.0, 1.0)


# (name, foreign shapes, spacing um, expect_trimmed, expect_below_via)
cases = [
    ("no foreign metal",        [],                      SP,   False, False),
    ("foreign clear of M1.b",   [near(SP + 0.02)],       SP,   False, False),
    ("worst-case 1 nm gap",     [near(0.001)],           SP,   True,  False),
    ("foreign both sides",      [near(0.001),
                                 g.box(dbu, -(edge + 0.501), 0, 1.0, 1.0)], SP, True, False),
    # The guard must arm if the pad/via/spacing relationship ever regresses. At the shipped constants
    # the trim reaches edge-SP = %.3f um from centre, clear of the via's %.4f um half-width; widening
    # the spacing past %.3f um takes it past the via and MUST be reported.
    ("wider spacing cuts via",  [near(0.001)],           0.30, True,  True),
    ("wider spacing, 2 sides",  [near(0.001),
                                 g.box(dbu, -(edge + 0.501), 0, 1.0, 1.0)], 0.40, True, True),
]

print("  pad=%.2fum via=%.2fum M1.b=%.2fum -> trim reaches %.3fum from centre, via half-width %.4fum"
      % (PAD, VIA, SP, edge - SP, VIA / 2))
bad = 0
for name, foreign, sp_um, want_trim, want_below in cases:
    trimmed, below = run(foreign, sp_um)
    if (trimmed, below) != (want_trim, want_below):
        print("  FAIL %-24s sp=%.2f trimmed=%s below_via=%s, want %s/%s"
              % (name, sp_um, trimmed, below, want_trim, want_below))
        bad += 1
    else:
        print("  ok   %-24s sp=%.2f trimmed=%-5s below_via=%s" % (name, sp_um, trimmed, below))
sys.exit(1 if bad else 0)
TRIMEOF
expect "pad-trim guard discriminates" ok "${PY}" -I "${T}/trimguard.py" "${ROOT}"

# The committed layout must carry the trim record and have no pad cut below its via (#245).
expect "committed layout records the pad trim" ok jq -e \
  '.metal1_pad_trim | .pads_total >= 1 and .pads_trimmed_below_via == 0
   and (.below_via | length) == 0 and .via_cover_margin_um > 0' \
  "${ROOT}/layout/provenance.json"

echo "${pass} passed, ${bad} failed"; [ "${bad}" = 0 ]
