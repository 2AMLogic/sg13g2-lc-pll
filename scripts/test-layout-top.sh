#!/usr/bin/env bash
# Integrated layout check (#35): committed layout/top.gds reproduces, still matches the stream hash
# manifests/layout.attest.json pins (#257), holds the pinned VCO unmodified, keep-out intrusions are
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

# layout/gen_integrated.py's digest() is billed as writer-independent, so a KLayout read->write->read
# of the committed stream -- a clip, a merge, a DRC-prep step, an exported sub-cell -- must digest to
# the recorded value. It did not before #263: digest() hashed per-layer records in ly.layer_indexes()
# order, which a re-save permutes, so comparing layout/top.gds against any re-saved copy reported a
# geometry mismatch that was not one. Three guards keep the case from passing vacuously: the round
# trip must actually permute the enumeration order, the committed stream must itself digest to the
# recorded value, and an inserted shape must still move the digest.
cat >"${T}/rt_test.py" <<'RTEOF'
"""digest() must survive a KLayout re-save of the committed stream (#263).

  python rt_test.py <root> <committed.gds> <tmpdir> [--enumeration-order]

--enumeration-order re-runs the assertion against digest() as it was before #263 (per-layer
records hashed in ly.layer_indexes() order). It must then refuse: that is the negative control
for the ordering fix itself, so a future change that reinstates enumeration order is caught.
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(sys.argv[1], "layout"))
import klayout.db as db
import gen_integrated as gi
import cells.common as cc

root, committed, t = sys.argv[1], sys.argv[2], sys.argv[3]
enum_order = "--enumeration-order" in sys.argv[4:]


def fail(msg):
    sys.exit("round-trip: " + msg + "; refusing")


def enum_digest(ly, cell):
    """digest() before #263: identical records, hashed in layer_indexes() enumeration order."""
    h = hashlib.sha256()
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        r = db.Region(cell.begin_shapes_rec(li))
        r.merge()
        polys = sorted(str(p) for p in r.each())
        txt = sorted(f"{s.text_string}@{(it.trans() * s.text_trans.disp).x},{(it.trans() * s.text_trans.disp).y}"
                     for it in cell.begin_shapes_rec(li) for s in [it.shape()] if s.is_text())
        if polys or txt:
            h.update(f"{info.layer}/{info.datatype}|{';'.join(polys)}|{';'.join(txt)}\n".encode())
    return h.hexdigest()


fn = enum_digest if enum_order else cc.digest


def read(path):
    ly = db.Layout()
    ly.read(path)
    return ly


def dig(path):
    ly = read(path)
    return fn(ly, ly.cell(gi.TOP))


def order(path):
    ly = read(path)
    return [(ly.get_info(i).layer, ly.get_info(i).datatype) for i in ly.layer_indexes()]


# A plain KLayout save of the committed stream: same geometry, a different writer.
rt = os.path.join(t, "rt.gds")
read(committed).write(rt)

if order(rt) == order(committed):
    fail("the round trip did not permute the layer-index order, so this case cannot discriminate")
# Writer-independence first, stated without reference to the record: the stream and its re-save
# must digest alike. This is the leg --enumeration-order is pointed at, so it is checked before
# the one that reads layout/provenance.json.
if dig(rt) != dig(committed):
    fail("the round-tripped stream digests to " + dig(rt) + ", not the committed stream's " + dig(committed))
# ... and the value both sides agree on is the one layout/provenance.json records.
want = json.load(open(os.path.join(root, "layout/provenance.json")))["output"]["geometry_sha256"]
if dig(committed) != want:
    fail("the committed stream digests to " + dig(committed) + ", not the recorded " + want)

# Negative control in the same run: a real geometry change must still move the digest, or the
# assertions above would hold for a digest() that hashes nothing.
edited = os.path.join(t, "rt_edited.gds")
ly = read(committed)
ly.cell(gi.TOP).shapes(ly.layer(8, 0)).insert(db.Box(-320000, 100000, -315000, 105000))
ly.write(edited)
if dig(edited) == want:
    fail("an inserted shape did not move the digest, so it is not hashing the geometry")

print("round-trip: digest " + want + " survives a KLayout re-save; an inserted shape moves it")
RTEOF
expect "geometry digest survives a KLayout round trip" ok \
  "${PY}" "${T}/rt_test.py" "${ROOT}" "${G}" "${T}"

# The churn this guards against is the GDS timestamp fields and nothing else, so the fixture for it
# is a byte-level edit of the seconds in every BGNLIB/BGNSTR record -- same size, same geometry,
# different sha256. Re-saving the stream through KLayout is still NOT an equivalent fixture: it
# rewrites the whole stream (record layout, cell order, layer-index order), so it isolates nothing.
# What it no longer does is move the geometry digest -- since #263 digest() hashes layers in sorted
# (layer, datatype) order, and the round-trip case above is what holds that property.
cat >"${T}/gds_restamp.py" <<'STAMPEOF'
"""Shift the seconds field of every GDS BGNLIB/BGNSTR timestamp: a byte churn with no geometry."""
import sys

src, dst = sys.argv[1], sys.argv[2]
data = bytearray(open(src, "rb").read())
i, n, hits = 0, len(data), 0
while i + 4 <= n:
    rlen = int.from_bytes(data[i:i + 2], "big")
    if rlen < 4:
        break
    # record type 0x01 = BGNLIB, 0x05 = BGNSTR; data type 0x02 = INT2; 12 int2 = mod/access y m d h m s
    if data[i + 3] == 0x02 and data[i + 2] in (0x01, 0x05) and rlen >= 28:
        for off in (i + 14, i + 26):            # the two seconds fields
            data[off:off + 2] = ((int.from_bytes(data[off:off + 2], "big") + 7) % 60).to_bytes(2, "big")
        hits += 1
    i += rlen
if hits == 0:
    sys.exit("gds-restamp: no BGNLIB/BGNSTR record found in " + src + "; refusing")
open(dst, "wb").write(bytes(data))
print("gds-restamp: re-stamped " + str(hits) + " records")
STAMPEOF
expect "timestamp-churn fixture builds" ok "${PY}" -I "${T}/gds_restamp.py" "${G}" "${T}/restamped.gds"

# --write must keep the attested bytes when the geometry is unchanged and replace them when it is
# not. Exercises layout/gen_integrated.py's publish_stream() on copies under ${T}; nothing in the
# checkout is written. Both halves carry a guard that fails if the fixture cannot discriminate.
cat >"${T}/pub_test.py" <<'PUBEOF'
import hashlib
import os
import shutil
import sys

sys.path.insert(0, os.path.join(sys.argv[1], "layout"))
import klayout.db as db
import gen_integrated as gi
import cells.common as cc

committed, restamped, t = sys.argv[2], sys.argv[3], sys.argv[4]


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def dig(path):
    ly = db.Layout()
    ly.read(path)
    return cc.digest(ly, ly.cell(gi.TOP))


def fail(msg):
    sys.exit("publish-stream: " + msg + "; refusing")


# 1. timestamp churn only: the destination must keep its committed bytes
dest = os.path.join(t, "pub_dest.gds")
shutil.copyfile(committed, dest)
if sha(restamped) == sha(committed):
    fail("the re-stamped fixture is byte-identical, so this control cannot discriminate")
if dig(restamped) != dig(committed):
    fail("the re-stamped fixture moved the geometry digest, so it is not a timestamp-only churn")
if gi.publish_stream(restamped, dest, dig(restamped)) is not False:
    fail("replaced a stream whose geometry is unchanged")
if sha(dest) != sha(committed):
    fail("churned the bytes of a stream whose geometry is unchanged")

# 2. a real geometry change must be published. Both fixtures are KLayout saves, so they differ by
#    the inserted box alone; since #263 a save does not move the digest either way.
plain = os.path.join(t, "pub_plain.gds")
ly = db.Layout()
ly.read(committed)
ly.write(plain)
edited = os.path.join(t, "pub_edited.gds")
ly = db.Layout()
ly.read(committed)
ly.cell(gi.TOP).shapes(ly.layer(8, 0)).insert(db.Box(-320000, 100000, -315000, 105000))
ly.write(edited)
if dig(edited) == dig(plain):
    fail("the inserted shape did not move the geometry digest, so this control cannot discriminate")
shutil.copyfile(plain, dest)
if gi.publish_stream(edited, dest, dig(edited)) is not True:
    fail("kept a stale stream after the geometry changed")
if dig(dest) != dig(edited):
    fail("the published stream does not carry the new geometry")

# 3. an absent destination is created
missing = os.path.join(t, "pub_missing.gds")
if gi.publish_stream(restamped, missing, dig(restamped)) is not True or not os.path.exists(missing):
    fail("did not create an absent destination")

print("publish-stream: timestamp churn kept the attested bytes, geometry change replaced them")
PUBEOF
expect "--write keeps attested bytes on churn, replaces them on a geometry change" ok \
  "${PY}" -I "${T}/pub_test.py" "${ROOT}" "${G}" "${T}/restamped.gds" "${T}"

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
# itself draws (27/0 IND, 148/0 NoRCX) is therefore asserted directly. The checker prints its
# result on one line and the PASS line quotes it, so the measured minimum distance is recorded --
# the same reason the keep-out count above is hand-rolled rather than an expect() "ok".
cat >"${T}/indclear.py" <<'INDEOF'
"""Top-cell top metal must keep clear of the VCO inductor exclusion markers (#361).

  python indclear.py <stream.gds>

keepout-check cannot make this assertion: its forbidden set deliberately stops at Metal5 (the
tank routes VOP/VON are TopMetal1, the VDDV strap TopMetal2, so adding top metal to the set
would flag every tank route). This checks the top cell's OWN TopMetal1 (126/0) and TopMetal2
(134/0) shapes against the vco cell's 27/0 (IND) and 148/0 (NoRCX) markers instead. Overlap,
touching (zero clearance) and anything closer than MIN_CLEARANCE_UM refuse; the success line
reports the measured minimum distance so the caller can quote it.

The markers are read in the vco cell's OWN frame (begin_shapes_rec applies no instance
transform), so the comparison is valid only while lc_pll_top places vco as exactly one
single-element identity-transform instance -- the placement layout/gen_top.py pins. Any other
placement is refused up front (#369): measuring it would report clearance against markers that
are not where the top cell's coordinates say they are.
"""
import sys

import klayout.db as db

TOP_CELL, VCO_CELL = "lc_pll_top", "vco"
TOP_METAL = ((126, 0, "TopMetal1"), (134, 0, "TopMetal2"))
MARKERS = ((27, 0, "IND"), (148, 0, "NoRCX"))
MIN_CLEARANCE_UM = 5.0


def fail(msg):
    sys.exit("ind-clearance: " + msg + "; refusing")


def pt_seg(px, py, ax, ay, bx, by):
    """Distance from point to segment; unit is the layout's database unit."""
    dx, dy = bx - ax, by - ay
    sq = dx * dx + dy * dy
    if sq == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = ((px - ax) * dx + (py - ay) * dy) / sq
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5


def seg_seg(e1, e2):
    """Segment-segment distance: the minimum of each endpoint against the other segment. Exact
    for segments that do not cross; crossing edges imply overlapping polygons, and overlap is
    refused before any distance is computed."""
    a1, b1, a2, b2 = e1.p1, e1.p2, e2.p1, e2.p2
    return min(pt_seg(a1.x, a1.y, a2.x, a2.y, b2.x, b2.y),
               pt_seg(b1.x, b1.y, a2.x, a2.y, b2.x, b2.y),
               pt_seg(a2.x, a2.y, a1.x, a1.y, b1.x, b1.y),
               pt_seg(b2.x, b2.y, a1.x, a1.y, b1.x, b1.y))


if len(sys.argv) != 2:
    fail("usage: indclear.py <stream.gds>")
ly = db.Layout()
ly.read(sys.argv[1])
top = ly.cell(TOP_CELL) or fail("no cell '" + TOP_CELL + "' in the stream")
vco = ly.cell(VCO_CELL) or fail("no cell '" + VCO_CELL + "' in the stream")
dbu = ly.dbu
# Frame guard (#369): the marker regions below are built with begin_shapes_rec on the vco cell,
# which yields vco-LOCAL coordinates -- the transform of the vco instance inside lc_pll_top is
# NOT applied. The comparison therefore holds only while that placement is exactly one copy at
# the identity, and a placement that is anything else must refuse here, before any distance is
# measured: under it the checker would compare top-cell metal against markers that are not
# where it thinks they are and could report a comfortable clearance that is false.
places = [i for i in top.each_inst() if i.cell.cell_index() == vco.cell_index()]
if not places:
    fail("the top cell does not directly instantiate '" + VCO_CELL + "'; the markers cannot be located")
if len(places) > 1:
    fail("the top cell directly places '" + VCO_CELL + "' " + str(len(places)) + " times ("
         + "; ".join(str(i.cplx_trans) for i in places) + "); exactly one placement is supported")
place = places[0]
if place.cell_inst.size() != 1:
    fail("the '" + VCO_CELL + "' placement is a " + str(place.cell_inst.size()) + "-element array ("
         + str(place.cplx_trans) + "); a single-copy placement is supported")
if place.cplx_trans != db.CplxTrans():
    fail("the '" + VCO_CELL + "' placement is " + str(place.cplx_trans)
         + ", not the identity; the markers would be measured in the wrong frame")
metal = db.Region()
for layer, dtype, name in TOP_METAL:
    li = ly.find_layer(layer, dtype)
    if li is not None:
        metal += db.Region(top.shapes(li))
metal = metal.merged()
if metal.is_empty():
    fail("the top cell draws no " + "/".join(n for _, _, n in TOP_METAL) + "; nothing to assert")
worst = None
for layer, dtype, name in MARKERS:
    li = ly.find_layer(layer, dtype)
    if li is None:
        fail("no %d/%d (%s) layer in the stream" % (layer, dtype, name))
    marks = db.Region(vco.begin_shapes_rec(li)).merged()
    if marks.is_empty():
        fail("the vco cell draws no %d/%d (%s); the markers are pinned VCO content" % (layer, dtype, name))
    overlap = metal & marks
    if not overlap.is_empty():
        fail("top-cell top metal overlaps the %s markers (%d/%d) in %d place(s)"
             % (name, layer, dtype, overlap.count()))
    dist = min(seg_seg(e1, e2) * dbu
               for p1 in metal.each() for p2 in marks.each()
               for e1 in p1.each_edge() for e2 in p2.each_edge())
    if dist < MIN_CLEARANCE_UM:
        fail("minimum distance %.3f um to the %s markers (%d/%d) is under the %.1f um margin"
             % (dist, name, layer, dtype, MIN_CLEARANCE_UM))
    worst = dist if worst is None else min(worst, dist)
print("ind-clearance: top-cell %s keeps %.2f um from the VCO %s markers (>= %.1f um required)"
      % ("/".join(n for _, _, n in TOP_METAL), worst,
         "+".join(n for _, _, n in MARKERS), MIN_CLEARANCE_UM))
INDEOF
if d="$("${PY}" -I "${T}/indclear.py" "${G}" 2>&1)"; then
  echo "PASS ${d}"; pass=$((pass+1))
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
  "${PY}" -I "${T}/indclear.py" "${T}/ind_intr.gds"
expect "NEG TopMetal2 touching a marker edge refused (zero clearance)" \
  "refuse:ind-clearance: minimum distance 0\.000 um to the IND markers \(27/0\) is under the [0-9.]+ um margin; refusing" \
  "${PY}" -I "${T}/indclear.py" "${T}/ind_touch.gds"
# #369: each placement fixture must be refused with the checker's own placement diagnostic --
# the frame assumption the clearance comparison silently rests on, turned into a refusal before
# any distance is measured or reported.
expect "NEG translated VCO placement refused (markers would sit in the wrong frame)" \
  "refuse:ind-clearance: the 'vco' placement is r0 \*1 0,-50000, not the identity; the markers would be measured in the wrong frame; refusing" \
  "${PY}" -I "${T}/indclear.py" "${T}/ind_shift.gds"
expect "NEG missing VCO placement refused" \
  "refuse:ind-clearance: the top cell does not directly instantiate 'vco'; the markers cannot be located; refusing" \
  "${PY}" -I "${T}/indclear.py" "${T}/ind_missing.gds"
expect "NEG duplicate VCO placements refused" \
  "refuse:ind-clearance: the top cell directly places 'vco' 2 times \(r0 \*1 0,0; r0 \*1 281000,-185000\); exactly one placement is supported; refusing" \
  "${PY}" -I "${T}/indclear.py" "${T}/ind_dup.gds"
expect "NEG two-element VCO array at an identity origin refused" \
  "refuse:ind-clearance: the 'vco' placement is a 2-element array \(r0 \*1 0,0\); a single-copy placement is supported; refusing" \
  "${PY}" -I "${T}/indclear.py" "${T}/ind_array.gds"
expect "NEG rotated VCO placement refused (r90 at the origin)" \
  "refuse:ind-clearance: the 'vco' placement is r90 \*1 0,0, not the identity; the markers would be measured in the wrong frame; refusing" \
  "${PY}" -I "${T}/indclear.py" "${T}/ind_rot.gds"
expect "NEG mirrored VCO placement refused (m0 at the origin)" \
  "refuse:ind-clearance: the 'vco' placement is m0 \*1 0,0, not the identity; the markers would be measured in the wrong frame; refusing" \
  "${PY}" -I "${T}/indclear.py" "${T}/ind_mirror.gds"
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
  "${PY}" "${T}/rt_test.py" "${ROOT}" "${G}" "${T}" --enumeration-order
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

# The churned stream keeps the geometry digest (so --check still passes) but breaks the attestation
# pin, which is the whole trap in #257: the pin check must refuse it, with its own refusal text.
expect "NEG timestamp-churned stream fails the attestation pin" \
  "refuse:pin-check: .* sha256 [0-9a-f]{64} != attested [0-9a-f]{64}; refusing" \
  pin_check "${T}/restamped.gds"
expect_summary || exit 1
