#!/usr/bin/env bash
# Integrated layout check (#35): committed layout/top.gds reproduces, still matches the stream hash
# manifests/layout.attest.json pins (#257), every committed LVS envelope under layout/lvs/ pins the
# shipped stream too (#413), holds the pinned VCO unmodified, keep-out intrusions are
# exactly the recorded VCTRL pin-access ones, top metal keeps clear of the VCO's inductor exclusion
# markers (#361), and the checks can fail.
# Needs .fetched/ (scripts/fetch-vco.sh), klt, a python with `klayout` (default .venv/bin/python; LAYOUT_PY).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${LAYOUT_PY:-${ROOT}/.venv/bin/python}"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
# expect()/expect_summary and the pass/bad tally, including when `refuse:<ERE>` is required
# over a bare `refuse`: see the contract in scripts/lib-expect.sh.
# shellcheck source=lib-expect.sh
source "${ROOT}/scripts/lib-expect.sh"
VCO="${ROOT}/.fetched/sg13g2-vco/layout/vco.gds"; G="${ROOT}/layout/top.gds"
# layout/gen_top.py's refusal on a VCO stream whose sha256 differs from reuse.lock.json.
REFUSAL='gen_top: .* sha256 [0-9a-f]{64} != pinned [0-9a-f]{64}; refusing'

# Preflight: the fixture heredocs and generators below run under `${PY} -I`, which excludes user
# site-packages, so a LAYOUT_PY that cannot import klayout there must fail here, naming itself,
# before it can degrade the negative controls (#282).
expect "klayout importable under ${PY} -I" ok "${PY}" -I -c 'import klayout.db'
expect "fetched VCO files verify" ok "${ROOT}/scripts/fetch-vco.sh" --verify
expect "regenerated geometry == committed provenance" ok "${PY}" "${ROOT}/layout/gen_integrated.py" --check
klt clip "${G}" --cell vco -o "${T}/placed.gds" >/dev/null 2>&1
klt clip "${VCO}" --cell vco -o "${T}/pinned.gds" >/dev/null 2>&1
expect "placed VCO subtree == pinned stream" ok klt diff "${T}/placed.gds" "${T}/pinned.gds"
expect "committed stream sha256 == provenance" ok bash -c \
  "[ \"\$(sha256sum '${G}' | cut -d' ' -f1)\" = \"\$(jq -r .output.sha256 '${ROOT}/layout/provenance.json')\" ]"
expect "attestation envelope passes" ok jq -e '.status=="pass" and .t1_item==2' "${ROOT}/manifests/layout.attest.json"

# T1 item 2's envelope pins the stream BYTES, not the geometry digest, so a timestamp-only rewrite
# of layout/top.gds invalidates the attestation while --check keeps passing (#257). Compare the
# stream on disk against the hash the envelope pins -- the file is what is attested.
PIN="$(jq -r '.provenance.input.content_hash' "${ROOT}/manifests/layout.attest.json" | sed 's/^sha256://')"
pin_check() { local f="$1" h
  [ -n "${PIN}" ] && [ "${PIN}" != "null" ] || { echo "pin-check: manifests/layout.attest.json has no provenance.input.content_hash; refusing"; return 1; }
  h="$(sha256sum "${f}" | cut -d' ' -f1)"
  [ "${h}" = "${PIN}" ] || { echo "pin-check: ${f} sha256 ${h} != attested ${PIN}; refusing"; return 1; }
  echo "pin-check: ${f} matches the attested stream ${PIN}"; }
expect "committed stream == attestation pin" ok pin_check "${G}"
expect "attestation pin == provenance output.sha256" ok bash -c \
  "[ \"${PIN}\" = \"\$(jq -r .output.sha256 '${ROOT}/layout/provenance.json')\" ]"

# #413: a stream bump (c1e1155) left every committed LVS envelope pinning the previous
# layout/top.gds, so `klt lvs --check` -- the input-freshness signal layout/lvs/README.md
# documents -- reported `drifted` on all four and stopped distinguishing "describes the shipped
# stream" from "describes an older one". The same rule the attestation pin check above states for
# manifests/layout.attest.json, stated for the LVS evidence tree: discover every committed
# *.lvs.json under layout/lvs/ whose recorded layout input IS the integrated GDS -- klt has
# recorded that input in both forms, a report-relative string ("../top.gds") and
# {"scope":"repo","path":"layout/top.gds"} -- and compare the report's
# environment.layout_sha256 with one digest of the actual file, naming file and both hashes on a
# drift. Discovery is by glob over the tree, so a newly committed report for the same input is
# covered the moment it lands. Nothing here re-runs a compare or touches the PDK: the check
# needs only the report bytes and the stream bytes (`klt lvs --check` stays the fuller probe).
LVS_STREAM_SHA="$(sha256sum "${G}" | cut -d' ' -f1)"
lvs_fresh_check() { local root="$1" stream="$2" f t rel pin found=0
  while IFS= read -r -d '' f; do
    # #419: the || continue on the .layout probe below also swallowed unparseable envelopes (jq
    # exits non-zero on malformed JSON), so the gate covered fewer files than were committed and
    # still reported success. Parse each envelope up front: an empty or not-JSON file is refused
    # naming it, while a parsed document that is not a report of a recognised shape (array root,
    # object without .layout) stays skipped -- jq empty exits 0 on 0-byte input, hence [ -s ].
    [ -s "${f}" ] || { echo "lvs-fresh: ${f} is empty; refusing"; return 1; }
    jq empty "${f}" 2>/dev/null || { echo "lvs-fresh: ${f} is not valid JSON; refusing"; return 1; }
    t="$(jq -r '.layout | type' "${f}" 2>/dev/null)" || continue
    case "${t}" in
      string) rel="$(realpath -m --canonicalize-missing --relative-to="${root}" \
        "${f%/*}/$(jq -r '.layout' "${f}")")" ;;
      object) rel=""; [ "$(jq -r '.layout.scope // ""' "${f}")" = repo ] \
        && rel="$(jq -r '.layout.path // ""' "${f}")" ;;
      *) continue ;;
    esac
    [ "${rel}" = layout/top.gds ] || continue
    found=$((found+1))
    pin="$(jq -r '.environment.layout_sha256 // ""' "${f}")"
    [ -n "${pin}" ] || { echo "lvs-fresh: ${f} records no environment.layout_sha256; refusing"; return 1; }
    [ "${pin}" = "${stream}" ] || { echo "lvs-fresh: ${f} pins layout sha256 ${pin} != stream ${stream}; refusing"; return 1; }
  done < <(find "${root}/layout/lvs" -name '*.lvs.json' -print0 | sort -z)
  [ "${found}" -gt 0 ] || { echo "lvs-fresh: no *.lvs.json under ${root}/layout/lvs names the integrated GDS; refusing"; return 1; }
  echo "lvs-fresh: ${found} committed report(s) pin the shipped stream ${stream}"; }
expect "committed LVS envelopes pin the shipped stream" ok lvs_fresh_check "${ROOT}" "${LVS_STREAM_SHA}"

# layout/gen_integrated.py's digest() is billed as writer-independent, so a KLayout read->write->read
# of the committed stream -- a clip, a merge, a DRC-prep step, an exported sub-cell -- must digest to
# the recorded value. It did not before #263: digest() hashed per-layer records in ly.layer_indexes()
# order, which a re-save permutes, so comparing layout/top.gds against any re-saved copy reported a
# geometry mismatch that was not one. Three guards keep the case from passing vacuously: the round
# trip must actually permute the enumeration order, the committed stream must itself digest to the
# recorded value, and an inserted shape must still move the digest.
expect "geometry digest survives a KLayout round trip" ok \
  "${PY}" "${ROOT}/scripts/rt_test.py" "${ROOT}" "${G}" "${T}"

# The churn this guards against is the GDS timestamp fields and nothing else, so the fixture for it
# is a byte-level edit of the seconds in every BGNLIB/BGNSTR record -- same size, same geometry,
# different sha256. Re-saving the stream through KLayout is still NOT an equivalent fixture: it
# rewrites the whole stream (record layout, cell order, layer-index order), so it isolates nothing.
# What it no longer does is move the geometry digest -- since #263 digest() hashes layers in sorted
# (layer, datatype) order, and the round-trip case above is what holds that property.
expect "timestamp-churn fixture builds" ok "${PY}" -I "${ROOT}/scripts/gds_restamp.py" "${G}" "${T}/restamped.gds"

# --write must keep the attested bytes when the geometry is unchanged and replace them when it is
# not. Exercises layout/gen_integrated.py's publish_stream() on copies under ${T}; nothing in the
# checkout is written. Both halves carry a guard that fails if the fixture cannot discriminate.
expect "--write keeps attested bytes on churn, replaces them on a geometry change" ok \
  "${PY}" -I "${ROOT}/scripts/pub_test.py" "${ROOT}" "${G}" "${T}/restamped.gds" "${T}"

# keep-out: the only intrusions are the VCTRL pin-access stack (3 shapes, Metal3/4/5), recorded in layout/README.md
"${PY}" "${ROOT}/layout/gen_top.py" --out "${T}/b.gds" --forbidden-json "${T}/f.json" >/dev/null 2>&1
klt keepout-check "${G}" --forbidden "${T}/f.json" --margin 20 --cells vco --format json >"${T}/ko.json" 2>/dev/null
n="$(jq '[.. | objects | select(has("kind"))] | length' "${T}/ko.json" 2>/dev/null)"
[ -n "${n}" ] && [ "${n}" = 3 ] && { echo "PASS keep-out: 3 recorded VCTRL intrusions"; pass=$((pass+1)); } \
  || { echo "FAIL keep-out intrusions = '${n}', expected the 3 recorded VCTRL ones"; bad=$((bad+1)); }

# Top metal vs the VCO's inductor exclusion markers (#361). keepout-check is blind to top metal by
# design: gen_top.py's FORBIDDEN_LAYERS stops at Metal5 because the tank routes VOP/VON are
# TopMetal1 and the VDDV strap is TopMetal2, so widening it would turn every tank route into a
# violation. The clearance of the top cell's OWN 126/0 and 134/0 shapes to the markers the VCO
# itself draws (27/0 IND, 148/0 NoRCX) is therefore asserted directly by scripts/indclear.py, which
# prints its result on one line; the PASS line quotes it, so the measured minimum distance is
# recorded -- the same reason the keep-out count above is hand-rolled rather than an expect() "ok".
# The success line is the baseline the out-of-tree control below compares against (#373). It is
# initialised here so that control is still scored when this check fails: under set -u an unassigned
# BASE_CLEAR aborted the script there and dropped every later case and the tally (#378). Empty
# means "not measured", never "matches anything".
BASE_CLEAR=""
if d="$("${PY}" -I "${ROOT}/scripts/indclear.py" "${G}" 2>&1)"; then
  echo "PASS ${d}"; pass=$((pass+1)); BASE_CLEAR="${d}"
else
  echo "FAIL ${d}"; bad=$((bad+1))
fi

# negative controls. The heredoc is guarded: a fixture that did not build is a harness failure,
# not a passing negative control (the script has no set -e; #282).
"${PY}" -I - "${G}" "${T}" <<'PYEOF' || { echo "FAIL fixture generation: negative-control streams did not build (see above)"; bad=$((bad+1)); }
import sys, klayout.db as db
g, t = sys.argv[1], sys.argv[2]
ly = db.Layout(); ly.read(g)
ly.cell("vco").shapes(ly.layer(8, 0)).insert(db.Box(0, 0, 1000, 1000)); ly.write(t + "/edited.gds")
ly = db.Layout(); ly.read(g)
ly.cell("lc_pll_top").shapes(ly.layer(8, 0)).insert(db.Box(-320000, 100000, -315000, 105000)); ly.write(t + "/intr.gds")
# #361: a 5 um TopMetal2 box on a 27/0 marker's own bbox centre, drawn on the top cell the way a
# rerouted VDDV strap would be. The markers are two octagons with a channel between them (their
# joint bbox centre falls inside that channel), so the centre of ONE marker is used, and the guard
# must prove the box landed on marker material -- otherwise the refusal below proves nothing.
ly = db.Layout(); ly.read(g)
mark = next(db.Region(ly.cell("vco").begin_shapes_rec(ly.layer(27, 0))).merged().each())
c = mark.bbox().center()
indbox = db.Box(c.x - 2500, c.y - 2500, c.x + 2500, c.y + 2500)
if (db.Region(indbox) & db.Region(mark)).is_empty():
    sys.exit("ind-intruder: a box at the 27/0 bbox centre (%d, %d) misses the marker; fixture cannot discriminate" % (c.x, c.y))
ly.cell("lc_pll_top").shapes(ly.layer(134, 0)).insert(indbox); ly.write(t + "/ind_intr.gds")
# ... and the zero-clearance edge case: the same box butted exactly against a marker's bottom
# edge -- touching without overlapping. Guarded both ways: it must not overlap (that case is the
# fixture above) and it must touch (a box that stops short would never exercise distance 0).
ly = db.Layout(); ly.read(g)
mark = next(db.Region(ly.cell("vco").begin_shapes_rec(ly.layer(27, 0))).merged().each())
bot = min((e for e in mark.each_edge() if e.p1.y == e.p2.y), key=lambda e: e.p1.y)
mid = (bot.p1.x + bot.p2.x) // 2
tbox = db.Box(mid - 2500, bot.p1.y - 5000, mid + 2500, bot.p1.y)
if not (db.Region(tbox) & db.Region(mark)).is_empty():
    sys.exit("ind-touch: the butted box overlaps the marker; wanted touch-only")
if (db.Region(tbox) & db.Region(mark).sized(1)).is_empty():
    sys.exit("ind-touch: the butted box does not reach the marker; fixture cannot discriminate")
ly.cell("lc_pll_top").shapes(ly.layer(134, 0)).insert(tbox); ly.write(t + "/ind_touch.gds")
# #369: placement fixtures. indclear.py reads the markers in the vco cell's own frame, so any
# placement other than one direct, single-element, identity-transform instance must be refused
# instead of silently mis-measured. ind_shift is the issue's measured false pass: the shifted
# markers overlap the top cell's own metal (292 um^2 on the committed stream) while the
# pre-guard checker still reports 23.00 um. The array uses a POSITIVE Y pitch -- KLayout
# normalizes a negative-pitch array to a displaced origin on readback (verified in #369), which
# would test the transform leg, not the multiplicity leg this fixture exists for.
def replace_vco(path, build, expect):
    """Rewrite the stream with the top cell's direct vco placements replaced, then re-read and
    require the recorded placement state -- (element count, cplx trans) per direct record -- so
    a KLayout normalization on write cannot quietly substitute a different fixture."""
    ly = db.Layout(); ly.read(g)
    top, vco = ly.cell("lc_pll_top"), ly.cell("vco")
    for i in [i for i in top.each_inst() if i.cell.cell_index() == vco.cell_index()]:
        top.erase(i)
    for a in build(vco.cell_index()):
        top.insert(a)
    ly.write(path)
    ly = db.Layout(); ly.read(path)
    vi = ly.cell("vco").cell_index()
    got = [(i.cell_inst.size(), str(i.cplx_trans)) for i in ly.cell("lc_pll_top").each_inst()
           if i.cell.cell_index() == vi]
    if got != expect:
        sys.exit("ind-placement: %s read back as %s, wanted %s; fixture cannot discriminate"
                 % (path, got, expect))


replace_vco(t + "/ind_shift.gds",
            lambda ci: [db.CellInstArray(ci, db.Trans(db.Trans.R0, 0, -50000))],
            [(1, "r0 *1 0,-50000")])
replace_vco(t + "/ind_missing.gds", lambda ci: [], [])
replace_vco(t + "/ind_dup.gds",
            lambda ci: [db.CellInstArray(ci, db.Trans()),
                        db.CellInstArray(ci, db.Trans(db.Trans.R0, 281000, -185000))],
            [(1, "r0 *1 0,0"), (1, "r0 *1 281000,-185000")])
replace_vco(t + "/ind_array.gds",
            lambda ci: [db.CellInstArray(ci, db.Trans(), db.Vector(0, 50000), db.Vector(0, 0), 2, 1)],
            [(2, "r0 *1 0,0")])
replace_vco(t + "/ind_rot.gds",
            lambda ci: [db.CellInstArray(ci, db.Trans(db.Trans.R90, 0, 0))],
            [(1, "r90 *1 0,0")])
replace_vco(t + "/ind_mirror.gds",
            lambda ci: [db.CellInstArray(ci, db.Trans(db.Trans.M0, 0, 0))],
            [(1, "m0 *1 0,0")])
# #373: nested-placement fixture. The direct vco is left untouched (one identity instance, so
# every direct leg above still passes) while a holder cell placed at the origin carries a second
# vco at (0, -50 um) through one intermediate cell -- the issue's measured false pass: the
# translated IND marker overlaps the top cell's own top metal by 292.22 um^2 while the pre-#373
# checker still reported 23.00 um. The intermediate cell puts vco TWO levels below the holder,
# so the readback guard's called_cells() test holds only while called_cells() stays transitive
# -- the property the hierarchy guard relies on for "at any depth".
ly = db.Layout(); ly.read(g)
top, vco = ly.cell("lc_pll_top"), ly.cell("vco")
holder, mid = ly.create_cell("nest_holder"), ly.create_cell("nest_mid")
mid.insert(db.CellInstArray(vco.cell_index(), db.Trans(db.Trans.R0, 0, -50000)))
holder.insert(db.CellInstArray(mid.cell_index(), db.Trans()))
top.insert(db.CellInstArray(holder.cell_index(), db.Trans()))
ly.write(t + "/ind_nested.gds")
ly = db.Layout(); ly.read(t + "/ind_nested.gds")
vi, hi = ly.cell("vco").cell_index(), ly.cell("nest_holder").cell_index()
direct = [(i.cell_inst.size(), str(i.cplx_trans)) for i in ly.cell("lc_pll_top").each_inst()
          if i.cell.cell_index() == vi]
if direct != [(1, "r0 *1 0,0")]:
    sys.exit("ind-nested: the direct placement read back as " + str(direct)
             + ", wanted [(1, 'r0 *1 0,0')]; a direct leg would fire instead of the nested one")
hpl = [(i.cell_inst.size(), str(i.cplx_trans)) for i in ly.cell("lc_pll_top").each_inst()
       if i.cell.cell_index() == hi]
if hpl != [(1, "r0 *1 0,0")] or vi not in ly.cell("nest_holder").called_cells():
    sys.exit("ind-nested: the holder-to-vco path read back as " + str(hpl)
             + "; fixture cannot discriminate")
# ... and the scoping control for the same guard: a cell that calls vco but is placed NOWHERE
# under lc_pll_top must not affect the result -- only the hierarchy rooted at the top cell is
# the checker's business. away_holder becomes a second top-level cell of its own.
ly = db.Layout(); ly.read(g)
away = ly.create_cell("away_holder")
away.insert(db.CellInstArray(ly.cell("vco").cell_index(), db.Trans(db.Trans.R0, 0, -50000)))
ly.write(t + "/ind_away.gds")
ly = db.Layout(); ly.read(t + "/ind_away.gds")
ai, vi = ly.cell("away_holder").cell_index(), ly.cell("vco").cell_index()
if vi not in ly.cell("away_holder").called_cells() or ai in ly.cell("lc_pll_top").called_cells():
    sys.exit("ind-away: the out-of-tree holder is in-tree or holds no vco; fixture cannot discriminate")
PYEOF
klt clip "${T}/edited.gds" --cell vco -o "${T}/edited_clip.gds" >/dev/null 2>&1
# Must carry klt's own violation status line (rc=3 detection), not merely exit non-zero: a missing
# input exits rc=1 with `file not found` and no status line, which bare `refuse` scored as a pass
# (#282). The status strings are klt's, not this repo's — re-measure if the klt pin moves.
expect "NEG edited VCO cell detected" "refuse:^status: different" klt diff "${T}/edited_clip.gds" "${T}/pinned.gds"
klt keepout-check "${T}/intr.gds" --forbidden "${T}/f.json" --margin 20 --cells vco --format json >"${T}/ko2.json" 2>/dev/null
n2="$(jq '[.. | objects | select(has("kind"))] | length' "${T}/ko2.json" 2>/dev/null)"
[ "${n2}" = 4 ] && { echo "PASS NEG extra keep-out intruder detected (4)"; pass=$((pass+1)); } || { echo "FAIL NEG intruder count '${n2}'"; bad=$((bad+1)); }
# #361: the clearance check must refuse both the intruding and the merely-touching TopMetal2
# fixtures with its own refusal text, not just a non-zero exit (the refuse:<ERE> rule, #234/#282).
expect "NEG TopMetal2 intruder into the IND markers refused" \
  "refuse:ind-clearance: top-cell top metal overlaps the IND markers \(27/0\) in [0-9]+ place\(s\); refusing" \
  "${PY}" -I "${ROOT}/scripts/indclear.py" "${T}/ind_intr.gds"
expect "NEG TopMetal2 touching a marker edge refused (zero clearance)" \
  "refuse:ind-clearance: minimum distance 0\.000 um to the IND markers \(27/0\) is under the [0-9.]+ um margin; refusing" \
  "${PY}" -I "${ROOT}/scripts/indclear.py" "${T}/ind_touch.gds"
# #369: each placement fixture must be refused with the checker's own placement diagnostic --
# the frame assumption the clearance comparison silently rests on, turned into a refusal before
# any distance is measured or reported.
expect "NEG translated VCO placement refused (markers would sit in the wrong frame)" \
  "refuse:ind-clearance: the 'vco' placement is r0 \*1 0,-50000, not the identity; the markers would be measured in the wrong frame; refusing" \
  "${PY}" -I "${ROOT}/scripts/indclear.py" "${T}/ind_shift.gds"
expect "NEG missing VCO placement refused" \
  "refuse:ind-clearance: the top cell does not directly instantiate 'vco'; the markers cannot be located; refusing" \
  "${PY}" -I "${ROOT}/scripts/indclear.py" "${T}/ind_missing.gds"
expect "NEG duplicate VCO placements refused" \
  "refuse:ind-clearance: the top cell directly places 'vco' 2 times \(r0 \*1 0,0; r0 \*1 281000,-185000\); exactly one placement is supported; refusing" \
  "${PY}" -I "${ROOT}/scripts/indclear.py" "${T}/ind_dup.gds"
expect "NEG two-element VCO array at an identity origin refused" \
  "refuse:ind-clearance: the 'vco' placement is a 2-element array \(r0 \*1 0,0\); a single-copy placement is supported; refusing" \
  "${PY}" -I "${ROOT}/scripts/indclear.py" "${T}/ind_array.gds"
expect "NEG rotated VCO placement refused (r90 at the origin)" \
  "refuse:ind-clearance: the 'vco' placement is r90 \*1 0,0, not the identity; the markers would be measured in the wrong frame; refusing" \
  "${PY}" -I "${ROOT}/scripts/indclear.py" "${T}/ind_rot.gds"
expect "NEG mirrored VCO placement refused (m0 at the origin)" \
  "refuse:ind-clearance: the 'vco' placement is m0 \*1 0,0, not the identity; the markers would be measured in the wrong frame; refusing" \
  "${PY}" -I "${ROOT}/scripts/indclear.py" "${T}/ind_mirror.gds"
# #373: the nested copy must be refused with the checker's own hierarchy diagnostic, naming the
# holder it is reached through, before any clearance is measured or reported.
expect "NEG nested VCO copy under a holder cell refused" \
  "refuse:ind-clearance: the top cell reaches 'vco' through 'nest_holder' \(placed r0 \*1 0,0\); a nested copy's markers are not measured; refusing" \
  "${PY}" -I "${ROOT}/scripts/indclear.py" "${T}/ind_nested.gds"
# ... and the scoping half of #373: a vco holder outside the lc_pll_top hierarchy leaves the
# measured result bit-for-bit unchanged.
d="$("${PY}" -I "${ROOT}/scripts/indclear.py" "${T}/ind_away.gds" 2>&1)"; rc=$?
if [ -z "${BASE_CLEAR}" ]; then
  echo "FAIL out-of-tree vco holder control: committed-stream ind-clearance baseline unavailable (not measured above)," \
    "so the result cannot be compared (rc=${rc}): ${d}"; bad=$((bad+1))
elif [ "${rc}" = 0 ] && [ "${d}" = "${BASE_CLEAR}" ]; then
  echo "PASS ${d} -- an out-of-tree vco holder leaves the result unchanged"; pass=$((pass+1))
else
  echo "FAIL an out-of-tree vco holder changed the result (rc=${rc}): ${d}"; bad=$((bad+1))
fi
mkdir -p "${T}/s/.fetched/sg13g2-vco/layout"; cp "${VCO}" "${T}/s/.fetched/sg13g2-vco/layout/vco.gds"
printf 'X' | dd of="${T}/s/.fetched/sg13g2-vco/layout/vco.gds" bs=1 seek=100 conv=notrunc 2>/dev/null
# Must carry gen_top.py's own sha256 refusal (reached through gen_integrated's build_base
# subprocess), not merely exit non-zero: see the expect() note above.
expect "NEG tampered stream: generator refuses" "refuse:${REFUSAL}" \
  "${PY}" "${ROOT}/layout/gen_integrated.py" --vco "${T}/s/.fetched/sg13g2-vco/layout/vco.gds" --check
# The ordering fix's own negative control: run the round-trip case against the pre-#263
# enumeration-order digest and it must refuse, with its own refusal text. Without this, removing
# the sort in layout/gen_integrated.py's digest() would be caught only by the positive case above,
# which a re-recorded provenance value would quietly re-satisfy.
expect "NEG enumeration-order digest fails the round trip" \
  "refuse:round-trip: the round-tripped stream digests to [0-9a-f]{64}, not the committed stream's [0-9a-f]{64}; refusing" \
  "${PY}" "${ROOT}/scripts/rt_test.py" "${ROOT}" "${G}" "${T}" --enumeration-order
# Metal1 pad-trim guard (#245). Drives gen_integrated.trim_pad over synthetic Metal1 so the guard
# is exercised in BOTH directions: it must stay quiet on a pad whose via survives the trim, and must
# report a pad cut back past its own Via1. A check that cannot fail is not a check (same reasoning as
# the refuse:<ERE> note above). Foreign Metal1 is placed NOT touching the pad, because metal that
# touches it is the pad's own landing polygon and trim_pad excludes it by construction.
expect "pad-trim guard discriminates" ok "${PY}" -I "${ROOT}/scripts/trimguard.py" "${ROOT}"

# The committed layout must carry the trim record and have no pad cut below its via (#245).
expect "committed layout records the pad trim" ok jq -e \
  '.metal1_pad_trim | .pads_total >= 1 and .pads_trimmed_below_via == 0
   and (.below_via | length) == 0 and .via_cover_margin_um > 0' \
  "${ROOT}/layout/provenance.json"

# The churned stream keeps the geometry digest (so --check still passes) but breaks the attestation
# pin, which is the whole trap in #257: the pin check must refuse it, with its own refusal text.
expect "NEG timestamp-churned stream fails the attestation pin" \
  "refuse:pin-check: .* sha256 [0-9a-f]{64} != attested [0-9a-f]{64}; refusing" \
  pin_check "${T}/restamped.gds"

# #413's own negative controls, on copies under ${T} (tracked evidence untouched): the stale-hash
# fixture is the issue as found -- one nested report pinning the previous stream's digest while
# the rest are fresh; the missing-hash fixture is an envelope with the field absent. Each must be
# refused with the checker's own text, naming the offending file. The string-form control beside
# them covers the other recorded shape of the layout input: after the 2026-11 refresh every
# committed report records {"scope":"repo","path":...}, so the report-relative-string branch is
# exercised by rewriting the top report's input to the equivalent "../top.gds" on a copy -- the
# exact-match on the success line asserts the rewritten report was still counted: the expected
# count is the unmodified tree's own count, taken from the same function, so a branch that silently
# skipped the rewritten report reports one fewer, and a newly committed envelope never breaks the
# control by changing the inventory size.
mkdir -p "${T}/lvstale/layout" "${T}/lvsmiss/layout" "${T}/lvsstr/layout"
cp -r "${ROOT}/layout/lvs" "${T}/lvstale/layout/"
cp -r "${ROOT}/layout/lvs" "${T}/lvsmiss/layout/"
cp -r "${ROOT}/layout/lvs" "${T}/lvsstr/layout/"
jq '.environment.layout_sha256 = "90fecb47625c46ee680def5c9dd0b8afabb5e15310468f464d1d32fb779c91db"' \
  "${ROOT}/layout/lvs/cells/lcpll_cp/lcpll_cp.lvs.json" > "${T}/lvstale/layout/lvs/cells/lcpll_cp/lcpll_cp.lvs.json"
jq 'del(.environment.layout_sha256)' \
  "${ROOT}/layout/lvs/cells/lcpll_loopfilter/lcpll_loopfilter.lvs.json" \
  > "${T}/lvsmiss/layout/lvs/cells/lcpll_loopfilter/lcpll_loopfilter.lvs.json"
jq '.layout = "../top.gds"' "${ROOT}/layout/lvs/top.lvs.json" > "${T}/lvsstr/layout/lvs/top.lvs.json"
expect "NEG stale LVS layout hash refused, report named" \
  "refuse:lvs-fresh: .*lcpll_cp\.lvs\.json pins layout sha256 90fecb47[0-9a-f]{56} != stream ${LVS_STREAM_SHA}; refusing" \
  lvs_fresh_check "${T}/lvstale" "${LVS_STREAM_SHA}"
expect "NEG missing LVS layout hash refused, report named" \
  "refuse:lvs-fresh: .*lcpll_loopfilter\.lvs\.json records no environment\.layout_sha256; refusing" \
  lvs_fresh_check "${T}/lvsmiss" "${LVS_STREAM_SHA}"
base="$(lvs_fresh_check "${ROOT}" "${LVS_STREAM_SHA}" 2>&1)"
d="$(lvs_fresh_check "${T}/lvsstr" "${LVS_STREAM_SHA}" 2>&1)"; rc=$?
if [ "${rc}" = 0 ] && [ "${d}" = "${base}" ] && [[ "${base}" =~ ^lvs-fresh:\ [1-9][0-9]*\ committed ]]; then
  echo "PASS LVS input recorded as a report-relative string still resolves and counts"; pass=$((pass+1))
else
  echo "FAIL report-relative string form (rc=${rc}): ${d}"; bad=$((bad+1))
fi
# #419's controls, same copy-tree shape: an unparseable envelope and a 0-byte one must each be
# refused with the checker's own text naming the file -- before the jq-empty gate both were
# silently skipped, so the freshness gate covered fewer files than layout/lvs/ held -- while a
# parsed document that is not a report (an extra {}) must stay skipped, not refused, and leave
# the success line (and its count) bit-for-bit the unmodified tree's own (base above).
mkdir -p "${T}/lvsbad/layout" "${T}/lvsempty/layout" "${T}/lvsnonrep/layout"
cp -r "${ROOT}/layout/lvs" "${T}/lvsbad/layout/"
cp -r "${ROOT}/layout/lvs" "${T}/lvsempty/layout/"
cp -r "${ROOT}/layout/lvs" "${T}/lvsnonrep/layout/"
printf '{ this is not json' > "${T}/lvsbad/layout/lvs/cells/lcpll_cp/lcpll_cp.lvs.json"
: > "${T}/lvsempty/layout/lvs/top.lvs.json"
printf '{}' > "${T}/lvsnonrep/layout/lvs/not-a-report.lvs.json"
expect "NEG malformed LVS envelope refused as not valid JSON, report named" \
  "refuse:lvs-fresh: .*lcpll_cp\.lvs\.json is not valid JSON; refusing" \
  lvs_fresh_check "${T}/lvsbad" "${LVS_STREAM_SHA}"
expect "NEG empty LVS envelope refused, report named" \
  "refuse:lvs-fresh: .*top\.lvs\.json is empty; refusing" \
  lvs_fresh_check "${T}/lvsempty" "${LVS_STREAM_SHA}"
d="$(lvs_fresh_check "${T}/lvsnonrep" "${LVS_STREAM_SHA}" 2>&1)"; rc=$?
if [ "${rc}" = 0 ] && [ "${d}" = "${base}" ]; then
  echo "PASS a valid non-report *.lvs.json is skipped without changing the count"; pass=$((pass+1))
else
  echo "FAIL non-report envelope changed the result (rc=${rc}): ${d}"; bad=$((bad+1))
fi
expect_summary || exit 1
