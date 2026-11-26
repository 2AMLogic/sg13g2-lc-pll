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
are not where the top cell's coordinates say they are. A vco nested under another cell is
refused for the same reason (#373): begin_shapes_rec yields one copy of the markers per cell,
so a nested copy's keep-out would simply never be compared against the top cell's metal.
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
# Hierarchy guard (#373): each_inst above reads only lc_pll_top's OWN instance records, so a
# second vco reached through another cell passes every direct leg while its markers are never
# compared against the top cell's metal at all -- on the committed stream a nested copy's
# translated IND marker overlaps top metal by 292.22 um^2 while the pre-#373 checker still
# reported 23.00 um. Any other direct child that reaches vco at any depth (called_cells() is
# transitive) must refuse here like the direct legs do: before any distance is measured.
vi = vco.cell_index()
for i in top.each_inst():
    child = i.cell
    if child.cell_index() != vi and vi in child.called_cells():
        fail("the top cell reaches '" + VCO_CELL + "' through '" + child.name + "' (placed "
             + str(i.cplx_trans) + "); a nested copy's markers are not measured")
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
