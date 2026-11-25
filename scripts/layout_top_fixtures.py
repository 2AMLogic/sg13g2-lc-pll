#!/usr/bin/env python3
"""Build the negative-control GDS streams scripts/test-layout-top.sh feeds its checkers.

usage: layout_top_fixtures.py <top.gds> <out_dir>

Writes edited, intr, ind_intr, ind_touch, ind_shift, ind_missing, ind_dup, ind_array, ind_rot,
ind_mirror, ind_nested and ind_away (.gds) into <out_dir>. Every fixture is read back and the
property it exists to exercise is asserted; a fixture that cannot discriminate exits non-zero
with a message, which the caller scores as a harness failure rather than a passing control.
Run as `python -I` with a python that can import klayout.
"""
import sys
import klayout.db as db


def load_layout(path):
    ly = db.Layout()
    ly.read(path)
    return ly


def direct_placements(ly, cell_index):
    """(element count, cplx trans) of each direct placement of cell_index under lc_pll_top."""
    return [(i.cell_inst.size(), str(i.cplx_trans)) for i in ly.cell("lc_pll_top").each_inst()
            if i.cell.cell_index() == cell_index]


def first_ind_marker(ly):
    """First merged 27/0 marker polygon of the vco cell, in the vco cell's own frame."""
    return next(db.Region(ly.cell("vco").begin_shapes_rec(ly.layer(27, 0))).merged().each())


def main(g, t):
    ly = load_layout(g)
    ly.cell("vco").shapes(ly.layer(8, 0)).insert(db.Box(0, 0, 1000, 1000)); ly.write(t + "/edited.gds")
    ly = load_layout(g)
    ly.cell("lc_pll_top").shapes(ly.layer(8, 0)).insert(db.Box(-320000, 100000, -315000, 105000)); ly.write(t + "/intr.gds")
    # #361: a 5 um TopMetal2 box on a 27/0 marker's own bbox centre, drawn on the top cell the way a
    # rerouted VDDV strap would be. The markers are two octagons with a channel between them (their
    # joint bbox centre falls inside that channel), so the centre of ONE marker is used, and the guard
    # must prove the box landed on marker material -- otherwise the refusal below proves nothing.
    ly = load_layout(g)
    mark = first_ind_marker(ly)
    c = mark.bbox().center()
    indbox = db.Box(c.x - 2500, c.y - 2500, c.x + 2500, c.y + 2500)
    if (db.Region(indbox) & db.Region(mark)).is_empty():
        sys.exit("ind-intruder: a box at the 27/0 bbox centre (%d, %d) misses the marker; fixture cannot discriminate" % (c.x, c.y))
    ly.cell("lc_pll_top").shapes(ly.layer(134, 0)).insert(indbox); ly.write(t + "/ind_intr.gds")
    # ... and the zero-clearance edge case: the same box butted exactly against a marker's bottom
    # edge -- touching without overlapping. Guarded both ways: it must not overlap (that case is the
    # fixture above) and it must touch (a box that stops short would never exercise distance 0).
    ly = load_layout(g)
    mark = first_ind_marker(ly)
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
        ly = load_layout(g)
        top, vco = ly.cell("lc_pll_top"), ly.cell("vco")
        for i in [i for i in top.each_inst() if i.cell.cell_index() == vco.cell_index()]:
            top.erase(i)
        for a in build(vco.cell_index()):
            top.insert(a)
        ly.write(path)
        ly = load_layout(path)
        got = direct_placements(ly, ly.cell("vco").cell_index())
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
    ly = load_layout(g)
    top, vco = ly.cell("lc_pll_top"), ly.cell("vco")
    holder, mid = ly.create_cell("nest_holder"), ly.create_cell("nest_mid")
    mid.insert(db.CellInstArray(vco.cell_index(), db.Trans(db.Trans.R0, 0, -50000)))
    holder.insert(db.CellInstArray(mid.cell_index(), db.Trans()))
    top.insert(db.CellInstArray(holder.cell_index(), db.Trans()))
    ly.write(t + "/ind_nested.gds")
    ly = load_layout(t + "/ind_nested.gds")
    vi, hi = ly.cell("vco").cell_index(), ly.cell("nest_holder").cell_index()
    direct = direct_placements(ly, vi)
    if direct != [(1, "r0 *1 0,0")]:
        sys.exit("ind-nested: the direct placement read back as " + str(direct)
                 + ", wanted [(1, 'r0 *1 0,0')]; a direct leg would fire instead of the nested one")
    hpl = direct_placements(ly, hi)
    if hpl != [(1, "r0 *1 0,0")] or vi not in ly.cell("nest_holder").called_cells():
        sys.exit("ind-nested: the holder-to-vco path read back as " + str(hpl)
                 + "; fixture cannot discriminate")
    # ... and the scoping control for the same guard: a cell that calls vco but is placed NOWHERE
    # under lc_pll_top must not affect the result -- only the hierarchy rooted at the top cell is
    # the checker's business. away_holder becomes a second top-level cell of its own.
    ly = load_layout(g)
    away = ly.create_cell("away_holder")
    away.insert(db.CellInstArray(ly.cell("vco").cell_index(), db.Trans(db.Trans.R0, 0, -50000)))
    ly.write(t + "/ind_away.gds")
    ly = load_layout(t + "/ind_away.gds")
    ai, vi = ly.cell("away_holder").cell_index(), ly.cell("vco").cell_index()
    if vi not in ly.cell("away_holder").called_cells() or ai in ly.cell("lc_pll_top").called_cells():
        sys.exit("ind-away: the out-of-tree holder is in-tree or holds no vco; fixture cannot discriminate")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: layout_top_fixtures.py <top.gds> <out_dir>")
    main(sys.argv[1], sys.argv[2])
