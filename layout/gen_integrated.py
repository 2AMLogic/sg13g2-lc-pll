#!/usr/bin/env python3
"""Integrated top layout: gen_top.py output (VCO + keep-out + guard ring + fill) plus the six
loop-block cells from gen_cells.py, placed and routed. Writes layout/top.gds and layout/provenance.json.

    layout/gen_integrated.py [--write | --check]

--write regenerates layout/provenance.json and refreshes layout/top.gds only when the geometry
actually changed (GDS records carry wall-clock timestamps, so an unchanged design still produces a
different byte stream, and those bytes are what manifests/layout.attest.json pins -- #257);
--check regenerates into layout/build/ and exits 1 if the top-cell geometry digest differs from the
committed provenance.

Needs the `klayout` Python module and the same inputs as gen_top.py / gen_cells.py (fetched VCO, klt, PDK).

Routing is a placement-level global route, not a signoff route (DRC/LVS/PEX are #36/#37/#41):
  - tank nets VOP/VON (VCO OUTP/OUTN -> prescaler INP/INN): single-layer TopMetal1 (126/0), 2 um wide.
  - other inter-block signal nets: Metal5 horizontal / Metal4 vertical, 1 um wide.
  - supplies (#344): VDD and VSS are stars from a labelled top-level landing pad on the south edge
    (Metal5 horizontal / Metal4 vertical, 1 um wide) reaching every block cell's supply port and the
    divider's M0-M3/A0-A2 rail tie-offs (XDIV in design/netlist/pll_top.spice: M0 M1 M2 M3 = VSS VSS
    VDD VDD, A0 A1 A2 = VSS VSS VDD), and -- VSS only -- the top-level p+ guard ring (the substrate
    tap this top draws; cell-internal bulk ties are #343's boundary). VDDV is its own branch (#344,
    spec section 5): a 4 um TopMetal2 strap from a labelled landing straight to the VCO's TopMetal2
    VDD bar, never joined on-chip to VDD. TopMetal2 and TopVia1/2 are outside the keep-out's
    forbidden set, so the strap crosses it legally.
  - external pins REF, IREFCP, LOCK are stubs from a labelled top-level landing to their block pin.
  - every endpoint gets a via stack from the pin's layer to the route layer. A landing's via tower
    is drawn once; a signal star's base-pin stack is still drawn per leg, and a leg's collision
    check excludes only shapes this generator drew for the same net (never cell internals).
  - every route polygon is checked against all other geometry on its layer (the VCO, the cells, earlier
    routes); a net whose pin-access stack or wire overlaps foreign geometry is recorded in the route
    record as `collisions`, never silently accepted. Paths are chosen collision-free where one exists.
  - not routed (recorded in `not_routed`): the VCO's ground pin `0` -- Metal1 ~21 um inside the
    keep-out with no top-metal conductor above it, unreachable without forbidden metal (upstream
    pin-access issue on 2AMLogic/sg13g2-vco).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

import klayout.db as db

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import gen_top  # noqa: E402
from cells import common  # noqa: E402

BUILD = os.path.join(ROOT, "layout", "build")
CELLS_DIR = os.path.join(BUILD, "cells")
OUT_GDS = os.path.join(ROOT, "layout", "top.gds")
PROV = os.path.join(ROOT, "layout", "provenance.json")
TOP = "lc_pll_top"

# Metal stack bottom -> top: (name, layer, datatype), via between level i and i+1.
METALS = [("Metal1", 8), ("Metal2", 10), ("Metal3", 30), ("Metal4", 50), ("Metal5", 67), ("TopMetal1", 126),
          ("TopMetal2", 134)]
VIAS = [19, 29, 49, 66, 125, 133]       # Via1, Via2, Via3, Via4, TopVia1, TopVia2
VIA_UM = [0.19, 0.19, 0.19, 0.19, 0.42, 0.9]
PAD_UM = [0.7, 0.7, 0.7, 0.7, 0.7, 2.0, 4.0]
LEVEL = {m[1]: i for i, m in enumerate(METALS)}
W_TANK, W_SIG = 2.0, 1.0              # TopMetal1 minimum width; Metal4/5 signal width
W_SUP, W_TM2 = 1.0, 4.0               # Metal4/5 supply width (divider M/A pin pitch 1.74 um); TopMetal2 VDDV strap
CHAN_STEP = 20.0
SPAN_UM = 200.0                       # channel search reaches this far outside an endpoint pair's bbox
M1B_SP_UM = 0.18                      # native M1.b Metal1 spacing; the pad trim keeps this to foreign Metal1

# Cell placements: name -> (transform, origin_um). Prescaler is mirrored about the x axis so its
# INP/INN (y = 1.8 um in the cell) face the VCO above it, INP left of INN as OUTP is left of OUTN.
PRESC_TOP_Y = -185.0
PLACE = {
    "lcpll_prescaler": ("M0", (281.0, PRESC_TOP_Y)),
    "lcpll_divider": ("R0", (445.0, -310.0)),
    "lcpll_loopfilter": ("R0", (-440.0, -430.0)),
    "lcpll_pfd": ("R0", (-440.0, -230.0)),
    "lcpll_cp": ("R0", (-380.0, -230.0)),
    "lcpll_lockdet": ("R0", (-250.0, -280.0)),
}
# net -> list of (cell, port).
NETS = {
    "VOP": [("vco", "OUTP"), ("lcpll_prescaler", "INP")],
    "VON": [("vco", "OUTN"), ("lcpll_prescaler", "INN")],
    "VCTRL": [("lcpll_loopfilter", "VCTRL"), ("vco", "VCTRL")],
    "VCP": [("lcpll_cp", "VOUT"), ("lcpll_loopfilter", "VIN")],
    "UP": [("lcpll_pfd", "UP"), ("lcpll_cp", "UP"), ("lcpll_lockdet", "UP")],
    "DN": [("lcpll_pfd", "DN"), ("lcpll_cp", "DN"), ("lcpll_lockdet", "DN")],
    "FB": [("lcpll_divider", "FB"), ("lcpll_pfd", "FB")],
    "MC": [("lcpll_divider", "MC"), ("lcpll_prescaler", "MC")],
    "PSP": [("lcpll_prescaler", "OUTP"), ("lcpll_divider", "INP")],
    "PSN": [("lcpll_prescaler", "OUTN"), ("lcpll_divider", "INN")],
    "IREFPS": [("lcpll_prescaler", "IREF"), ("lcpll_divider", "IREF")],
}
TANK = ("VOP", "VON")

# ---- Supplies and external pins (#344) -------------------------------------------------------------
# Top-level landings: labelled pads on the south edge, 20 um below the loop-filter bottom edge
# (the lowest placed geometry). One landing per pll_top external supply/signal port; each is the
# star base of its net, so no two endpoints of a net share conductor except at the landing itself.
LAND_Y = -450.0
LANDING_X = {"REF": -420.0, "IREFCP": -320.0, "VSS": -220.0, "VDD": -120.0, "VDDV": 0.0, "LOCK": 120.0}
# XDIV tie-offs in design/netlist/pll_top.spice: M0 M1 M2 M3 = VSS VSS VDD VDD, A0 A1 A2 = VSS VSS VDD.
DIV_TIES = {"M0": "VSS", "M1": "VSS", "M2": "VDD", "M3": "VDD", "A0": "VSS", "A1": "VSS", "A2": "VDD"}
_tie_ends = {net: [("lcpll_divider", p) for p, t in sorted(DIV_TIES.items()) if t == net]
             for net in ("VDD", "VSS")}
# Guard-ring tie: on the ring's south arm centre line (the ring is drawn by gen_top.py at VCO
# bbox + KEEPOUT_UM + RING_GAP_UM, 1 um wide) -- west of centre, clear of the keep-out (bbox + 20).
RING_TIE_X = -160.0

# net -> {"mode", "ends"}: ends[0] is the landing anchor; the rest are star endpoints.
SUPPLY_NETS = {
    "VDD": {"mode": "supply", "ends": _tie_ends["VDD"] + [
        ("lcpll_divider", "VDD"), ("lcpll_prescaler", "VDD"), ("lcpll_pfd", "VDD"),
        ("lcpll_cp", "VDD"), ("lcpll_lockdet", "VDD"),
    ]},
    "VSS": {"mode": "supply", "ends": _tie_ends["VSS"] + [
        ("lcpll_divider", "VSS"), ("lcpll_prescaler", "VSS"), ("lcpll_pfd", "VSS"),
        ("lcpll_cp", "VSS"), ("lcpll_lockdet", "VSS"), ("lcpll_loopfilter", "VSS"),
    ]},
    "VDDV": {"mode": "tm2", "ends": [("vco", "VDD")]},
}
EXT_NETS = {
    "REF": {"mode": "ext", "ends": [("lcpll_pfd", "REF")]},
    "IREFCP": {"mode": "ext", "ends": [("lcpll_cp", "IREF")]},
    "LOCK": {"mode": "ext", "ends": [("lcpll_lockdet", "LOCK")]},
}

# (net, cell, port) whose final approach segment must be HORIZONTAL (#344): the pfd's west-edge
# pins share the x column -439.33 (VSS -229, REF -227.29, FB -223.97 are 1.7-3.3 um apart), so a
# vertical Metal4 approach to one pin runs through its neighbours' pin stacks and shorts them
# (found as a real erc.multiply_driven_net REF x VSS, not just a counted overlap). FB is one of
# the pre-existing collision nets the issue asks to reroute; REF lands on the same edge.
FINAL_HORIZONTAL = {
    ("FB", "lcpll_pfd", "FB"),
    ("REF", "lcpll_pfd", "REF"),
}

# (net, cell, port) whose final approach must be VERTICAL (#344): the pfd/cp south pins sit in a
# 5 um band (y = -229 .. -223.97) -- VSS into lcpll_pfd.VSS and lcpll_cp.VSS on Metal5 at y = -229
# leaves no room for VDD's westward run (0.0 um edge gap to a y = -230 Metal5, metal5.space.1),
# so both VSS legs drop to their pins on Metal4 and draw no Metal5 in that row at all.
FINAL_VERTICAL = {
    ("VDD", "lcpll_pfd", "VDD"),
    ("VSS", "lcpll_pfd", "VSS"),
    ("VSS", "lcpll_cp", "VSS"),
}

NOT_ROUTED = {
    "VCO ground (`0`)": ("pin-access: the VCO ground pin is Metal1 ~21 um inside the 20 um keep-out with no "
                         "TopMetal1/2 conductor above it, so a top-level tie needs forbidden metal; "
                         "upstream pin-access request 2AMLogic/sg13g2-vco#427 (VCTRL is #314)"),
}


def publish_stream(fresh, dest, fresh_digest):
    """Install `fresh` at `dest` only when the geometry actually differs (#257).

    GDS records carry wall-clock time (BGNLIB/BGNSTR), so re-running the generator on an
    unchanged design produces a different byte stream with identical geometry. `dest` is the
    stream whose sha256 manifests/layout.attest.json pins, so replacing it unconditionally
    silently invalidates the T1 item 2 attestation while --check -- a geometry digest -- keeps
    passing. Compare the digest of the stream already on disk, not a recorded field: the file is
    what the attestation pins.

    Returns True when `dest` was replaced, False when the committed bytes were kept.
    """
    if os.path.exists(dest):
        try:
            cur = db.Layout()
            cur.read(dest)
            cell = cur.cell(TOP)
        except Exception:               # unreadable/corrupt stream on disk: replace it
            cell = None
        if cell is not None and common.digest(cur, cell) == fresh_digest:
            return False
    shutil.copyfile(fresh, dest)
    return True


def build_base(vco, out):
    subprocess.run([sys.executable, os.path.join(HERE, "gen_top.py"), "--vco", vco, "--out", out],
                   check=True, stdout=subprocess.DEVNULL)


def load_cell(ly, name):
    """Read one cell stream into `ly`, return its cell.

    Sub-cell names are not rewritten here: gen_cells.py already prefixes each block's device cells
    (`lcpll_cp_nfet_w2_l0p5__core`), and copy_tree leaves the rest to KLayout's `$N` uniquifier, so a
    name two blocks share (`via_stack`, `npn13G2V`) lands as `via_stack$1` rather than merging.
    """
    other = db.Layout()
    other.read(os.path.join(CELLS_DIR, f"{name}.gds"))
    c = ly.create_cell(name)
    c.copy_tree(other.cell(name))
    return c


def pins(ly, cell):
    """First label per text string -> (layer, DPoint in cell coordinates). Datatype is not kept: a pin
    is matched by layer number alone (LEVEL), and every pin label here sits on datatype 0."""
    out = {}
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        for it in cell.begin_shapes_rec(li):
            s = it.shape()
            if s.is_text():
                p = it.trans() * s.text_trans.disp
                out.setdefault(s.text_string, (info.layer, db.DPoint(p.x * ly.dbu, p.y * ly.dbu)))
    return out


def trans_of(code, org):
    t = {"R0": db.DTrans.R0, "M0": db.DTrans.M0}[code]
    return db.DTrans(t, db.DVector(*org))


def box(dbu, cx, cy, w, h):
    return db.Box(round((cx - w / 2) / dbu), round((cy - h / 2) / dbu), round((cx + w / 2) / dbu), round((cy + h / 2) / dbu))


def wire(dbu, a, b, w):
    """Rectangle for a Manhattan segment a->b of width w, ends extended by w/2."""
    x0, x1 = sorted((a[0], b[0]))
    y0, y1 = sorted((a[1], b[1]))
    return db.Box(round((x0 - w / 2) / dbu), round((y0 - w / 2) / dbu), round((x1 + w / 2) / dbu), round((y1 + w / 2) / dbu))


def stack(dbu, pt, lo, hi):
    """Shapes {layer: [Box]} for a via stack at pt from metal level lo to hi (indices into METALS)."""
    shapes = {}
    for lv in range(lo, hi + 1):
        shapes.setdefault(METALS[lv][1], []).append(box(dbu, pt[0], pt[1], PAD_UM[lv], PAD_UM[lv]))
        if lv < hi:
            shapes.setdefault(VIAS[lv], []).append(box(dbu, pt[0], pt[1], VIA_UM[lv], VIA_UM[lv]))
    return shapes


def length(pts):
    return sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(pts, pts[1:]))


def candidates(p, q, span):
    """Manhattan paths p->q as lists of points, H-first or V-first, with an intermediate channel."""
    paths = [[p, (q[0], p[1]), q], [p, (p[0], q[1]), q]]
    lo_x, hi_x = min(p[0], q[0]) - span, max(p[0], q[0]) + span
    lo_y, hi_y = min(p[1], q[1]) - span, max(p[1], q[1]) + span
    x = lo_x
    while x <= hi_x:
        paths.append([p, (x, p[1]), (x, q[1]), q])
        x += CHAN_STEP
    y = lo_y
    while y <= hi_y:
        paths.append([p, (p[0], y), (q[0], y), q])
        y += CHAN_STEP
    # dedupe zero-length legs
    clean = []
    for path in paths:
        pts = [path[0]]
        for pt in path[1:]:
            if abs(pt[0] - pts[-1][0]) > 1e-9 or abs(pt[1] - pts[-1][1]) > 1e-9:
                pts.append(pt)
        if len(pts) >= 2:
            clean.append(pts)
    clean.sort(key=length)
    return clean


def path_shapes(dbu, pts, tank, width=None, tm2=False):
    """Wire + via shapes for a Manhattan path (excluding endpoint stacks). Tank: all TM1.
    tm2 (#344): all TopMetal2 at the strap width. Else H=Metal5, V=Metal4 at `width`."""
    shapes = {}
    segs = list(zip(pts, pts[1:]))
    if tank:
        for a, b in segs:
            shapes.setdefault(126, []).append(wire(dbu, a, b, W_TANK))
        return shapes, None
    if tm2:
        for a, b in segs:
            shapes.setdefault(134, []).append(wire(dbu, a, b, W_TM2))
        return shapes, None
    levels = []
    for a, b in segs:
        horiz = abs(a[1] - b[1]) < 1e-9
        lv = 4 if horiz else 3
        levels.append(lv)
        shapes.setdefault(METALS[lv][1], []).append(wire(dbu, a, b, width if width is not None else W_SIG))
    for i in range(1, len(segs)):
        if levels[i] != levels[i - 1]:
            for k, v in stack(dbu, segs[i][0], 3, 4).items():
                shapes.setdefault(k, []).extend(v)
    return shapes, levels


def trim_pad(dbu, b, base_m1, sp):
    """Trim one Metal1 via-stack pad box `b` back from Metal1 polygons it does not touch.

    `base_m1` is the merged Metal1 of the top cell, `sp` the M1.b spacing in dbu. Returns
    (keep, trimmed, uncovered): the region to insert in place of the pad, whether the trim removed
    anything, and the part of the pad's own concentric Via1 the trim left uncovered -- empty when
    the pad still encloses its via, non-empty when the pad was cut back past it (an open, or at
    best a via-enclosure violation). Callers record `uncovered` rather than dropping the pad:
    changing geometry here would hide a defect DRC (#36) and LVS (#37) must still see.
    """
    pad = db.Region(b)
    foreign = base_m1 - base_m1.interacting(pad)
    keep = pad - foreign.sized(sp)
    cx, cy = (b.left + b.right) / 2 * dbu, (b.bottom + b.top) / 2 * dbu
    uncovered = db.Region(box(dbu, cx, cy, VIA_UM[0], VIA_UM[0])) - keep
    # `keep != pad` would NOT answer this: db.Region's __eq__ reports two regions holding identical
    # geometry as unequal, so comparing them directly scores every pad as trimmed. keep is a subset
    # of pad by construction, so the set difference is the real test.
    return keep, not (pad - keep).is_empty(), uncovered


def to_region(boxes):
    r = db.Region()
    for b in boxes:
        r.insert(b)
    return r.merged()


# TopMetal1 over substrate, IHP-Open-PDK libs.tech/magic/ihp-sg13g2-extract.tech (metal6 = TopMetal1):
# defaultareacap 5.649 aF/um^2, defaultperimeter 37.383 aF/um.
TM1_AREA_AF_UM2, TM1_PERIM_AF_UM = 5.649, 37.383
TANK_BUDGET_FF = 2.1


def tank_estimate(routes):
    """Geometric estimate of the tank-to-prescaler-input route capacitance. NOT extracted (PEX is #41)."""
    per_um_ff = (W_TANK * TM1_AREA_AF_UM2 + 2 * TM1_PERIM_AF_UM) / 1000.0
    nets = {n: {"length_um": routes[n]["length_um"], "c_route_ff": round(routes[n]["length_um"] * per_um_ff, 2)}
            for n in TANK}
    return {
        "method": ("route length x (width x area_cap + 2 x perimeter_cap) of an isolated TopMetal1 wire over "
                   "substrate, from IHP-Open-PDK magic extract.tech; excludes sidewall coupling to neighbours, "
                   "the via-stack pads, the underlying devices and the prescaler's own input capacitance"),
        "per_um_ff": round(per_um_ff, 4),
        "width_um": W_TANK,
        "budget_ff": TANK_BUDGET_FF,
        "nets": nets,
        "within_budget": all(v["c_route_ff"] <= TANK_BUDGET_FF for v in nets.values()),
        "status": "estimate, not extracted; klt pex delta is #41",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--vco", default=os.path.join(ROOT, ".fetched/sg13g2-vco/layout/vco.gds"))
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    a = ap.parse_args()

    os.makedirs(BUILD, exist_ok=True)
    base = os.path.join(BUILD, "lc_pll_base.gds")
    build_base(a.vco, base)
    # cell streams (gen_cells output); regenerate if missing
    need = [n for n in PLACE if not os.path.exists(os.path.join(CELLS_DIR, f"{n}.gds"))]
    if need:
        subprocess.run([sys.executable, os.path.join(HERE, "gen_cells.py")], check=True, stdout=subprocess.DEVNULL)

    ly = db.Layout()
    ly.read(base)
    dbu = ly.dbu
    top = ly.cell(TOP)
    vco = ly.cell("vco")
    pin_tab = {"vco": pins(ly, vco)}
    for name, (code, org) in PLACE.items():
        c = load_cell(ly, name)
        pin_tab[name] = pins(ly, c)
        top.insert(db.DCellInstArray(c.cell_index(), trans_of(code, org)))

    def gpin(cell, port):
        layer, p = pin_tab[cell][port]
        if cell == "vco":
            t = db.DTrans()
        else:
            code, org = PLACE[cell]
            t = trans_of(code, org)
        q = t * p
        return layer, (round(q.x, 3), round(q.y, 3))

    # obstacle geometry per layer: everything placed so far (VCO, cells, ring, fill)
    def lidx(l):
        return ly.layer(l, 0)

    routes, collisions_total, added = {}, 0, {}
    # Shapes this run drew per net (#344): a supply star's shared trunk, its landing tower and the
    # endpoint stacks its legs redraw at the anchor are all one electrical node, so a later leg's
    # overlap with them is not a foreign collision. Only top-level shapes this generator itself drew
    # for the same net are excluded -- never geometry inside the placed cells (the generator is not
    # net-aware there; #37 decides those overlaps).
    added_net = {}
    net_label_cache = {}

    def foreign(k, net):
        obs = db.Region(top.begin_shapes_rec(lidx(k))).merged()
        if net is not None:
            own_net = to_region(added_net.get(net, {}).get(k, []))
            if not own_net.is_empty():
                obs = obs - own_net
            # A polygon carrying this net's own label is that net's conductor: overlapping it is a
            # labelled same-net tie, not a foreign collision (e.g. the lock detector's VSS pin is a
            # 46 um Metal5 slab its westward VSS run must cross). The label is evidence, not an
            # assertion -- unlabelled cell internals stay counted, for #37 to resolve.
            if (k, net) not in net_label_cache:
                marks = db.Region()
                for li in ly.layer_indexes():
                    if ly.get_info(li).layer != k:
                        continue
                    for it in top.begin_shapes_rec(li):
                        s = it.shape()
                        if s.is_text() and s.text_string == net:
                            # compose the transforms, then take the displacement: multiplying
                            # the instance trans by the raw disp leaves instance texts at cell
                            # coordinates, where they mark nothing (or the wrong thing).
                            p = (it.trans() * s.text_trans).disp
                            marks.insert(db.Box(p.x - 500, p.y - 500, p.x + 500, p.y + 500))
                net_label_cache[(k, net)] = marks
            marks = net_label_cache[(k, net)]
            if not marks.is_empty():
                obs = obs - obs.interacting(marks)
        return obs

    def commit(net, allshapes):
        for k, bs in allshapes.items():
            for b in bs:
                top.shapes(lidx(k)).insert(b)
            added.setdefault(k, []).extend(bs)
            if net is not None:
                added_net.setdefault(net, {}).setdefault(k, []).extend(bs)

    def star(net, base_pin, ends, width, tank=False, tm2=False, span=SPAN_UM, stack_at_base=True):
        """Route one net as a star from `base_pin` (a (layer, (x, y)) pin tuple) to each entry of
        `ends` ((cell, port, layer, (x, y))), choosing the least-colliding Manhattan path per leg.
        `stack_at_base=False` (#344 landings): the anchor's via tower is drawn once by the caller,
        so legs only stack at their far endpoint."""
        nonlocal collisions_total
        rec = {"pins": [], "segments": [], "length_um": 0.0, "collisions": []}
        total = 0.0
        for cell, port, l, pt in ends:
            rec["pins"].append({"cell": cell, "port": port, "layer": l, "x_um": pt[0], "y_um": pt[1]})
        for cell, port, l, pt in ends[1:]:
            pa, pb = base_pin, (l, pt)
            p, q = pa[1], pb[1]
            best = None
            obs_cache = {}
            for pts in candidates(p, q, span):
                if (net, cell, port) in FINAL_HORIZONTAL and abs(pts[-1][0] - pts[-2][0]) < 1e-9:
                    continue  # forced horizontal approach: skip vertical-final candidates
                if (net, cell, port) in FINAL_VERTICAL and abs(pts[-1][1] - pts[-2][1]) < 1e-9:
                    continue  # forced vertical approach: skip horizontal-final candidates
                shapes, levels = path_shapes(dbu, pts, tank, width, tm2)
                # endpoint stacks
                if tank:
                    end_levels = [5, 5]
                elif tm2:
                    end_levels = [6, 6]
                else:
                    end_levels = [levels[0], levels[-1]]
                st = {}
                pin_lvls = [(pa, end_levels[0]), (pb, end_levels[1])] if stack_at_base \
                    else [(pb, end_levels[1])]
                for (lay, ptx), lv in pin_lvls:
                    pl = LEVEL[lay]
                    for k, v in stack(dbu, ptx, min(pl, lv), max(pl, lv)).items():
                        st.setdefault(k, []).extend(v)
                allshapes = {k: list(v) for k, v in shapes.items()}
                for k, v in st.items():
                    allshapes.setdefault(k, []).extend(v)
                # collision check against existing geometry on each layer, excluding the pin's own polygon
                bad = 0
                for k, bs in allshapes.items():
                    if k not in obs_cache:
                        obs_cache[k] = foreign(k, net)
                    own = to_region(bs)
                    hit = own & obs_cache[k]
                    # allow overlap with the polygons containing the net's own pins on this layer
                    for (lay, pt2) in (pa, pb):
                        if lay == k:
                            pin_poly = db.Region(db.Box(round(pt2[0] / dbu) - 1, round(pt2[1] / dbu) - 1,
                                                        round(pt2[0] / dbu) + 1, round(pt2[1] / dbu) + 1))
                            own_poly = obs_cache[k].interacting(pin_poly)
                            hit = hit - own_poly
                    bad += hit.count()
                if best is None or bad < best[0]:
                    best = (bad, pts, allshapes)
                if bad == 0:
                    break
            bad, pts, allshapes = best
            if os.environ.get("LAYOUT_DEBUG_COLLISIONS"):
                for k, bs in allshapes.items():
                    obs = foreign(k, net)
                    hit = to_region(bs) & obs
                    for (lay, pt2) in (pa, pb):
                        if lay == k:
                            pin_poly = db.Region(db.Box(round(pt2[0] / dbu) - 1, round(pt2[1] / dbu) - 1,
                                                        round(pt2[0] / dbu) + 1, round(pt2[1] / dbu) + 1))
                            hit = hit - obs.interacting(pin_poly)
                    if not hit.is_empty():
                        for poly in hit.each():
                            b = poly.bbox()
                            print(f"DBG {net}->{cell}.{port} layer {k}/{0}: hits foreign polygon "
                                  f"[{b.left*dbu:.2f},{b.bottom*dbu:.2f},{b.right*dbu:.2f},{b.top*dbu:.2f}]")
            commit(net, allshapes)
            seglen = length(pts)
            total += seglen
            rec["segments"].append({"from": f"{ends[0][0]}.{ends[0][1]}", "to": f"{cell}.{port}",
                                    "path_um": [list(x) for x in pts], "length_um": round(seglen, 3)})
            if bad:
                rec["collisions"].append({"to": f"{cell}.{port}", "overlapping_polygons": bad})
                collisions_total += bad
        rec["length_um"] = round(total, 3)
        if tank:
            rec["layers"] = "TopMetal1 (126/0), width %.1f um" % W_TANK
        elif tm2:
            rec["layers"] = "TopMetal2 (134/0), width %.1f um" % W_TM2
        else:
            rec["layers"] = "Metal5 horizontal / Metal4 vertical, width %.1f um" % width
        routes[net] = rec
        # label the net on the route
        l0 = 126 if tank else 67
        p0 = rec["segments"][0]["path_um"][0]
        top.shapes(ly.layer(l0, 25)).insert(db.Text(f"{net}", round(p0[0] / dbu), round(p0[1] / dbu)))
        return rec

    for net, ends in sorted(NETS.items(), key=lambda kv: (kv[0] not in TANK, kv[0])):
        tank = net in TANK
        # connect first end to each other end (star from the first pin); UP/DN have three pins
        base_pin = gpin(*ends[0])
        resolved = [(c, p, *gpin(c, p)) for c, p in ends]
        star(net, base_pin, resolved, W_SIG, tank=tank)

    # ---- supplies and external pins (#344) ----------------------------------------------
    # One labelled landing tower per pll_top external port on the south edge, 20 um below the
    # loop filter (the lowest placed geometry): a full Metal1..Metal5 via tower (VDDV: ..TopMetal2)
    # with the net's text on 67/25, drawn once, then a star from it.
    vco_bb = vco.bbox()
    ring_south_y = round(((vco_bb.bottom * dbu) - gen_top.KEEPOUT_UM - gen_top.RING_GAP_UM
                          - gen_top.RING_W_UM / 2), 3)
    for net in list(EXT_NETS) + list(SUPPLY_NETS):
        x = LANDING_X[net]
        commit(net, stack(dbu, (x, LAND_Y), 0, 6 if SUPPLY_NETS.get(net, {}).get("mode") == "tm2" else 4))
    # VSS also ties the top-level p+ guard ring (the substrate tap this top draws): a stack on the
    # ring's south-arm Metal1, outside the keep-out (bbox + KEEPOUT_UM + RING_GAP_UM).
    ring_pin = (8, (RING_TIE_X, ring_south_y))
    for net, spec in {**EXT_NETS, **SUPPLY_NETS}.items():
        if spec["mode"] == "tm2":
            # VDDV: its own branch (spec section 5) -- one TopMetal2 strap from the labelled
            # landing straight to the VCO's TopMetal2 VDD bar, never joined on-chip to VDD.
            # TopMetal2/TopVia1/2 are outside the keep-out's forbidden set, so it crosses legally.
            ends = [("(landing)", net, 67, (LANDING_X[net], LAND_Y)), ("vco", "VDD", *gpin("vco", "VDD"))]
            star(net, (67, (LANDING_X[net], LAND_Y)), ends, W_TM2, tm2=True, stack_at_base=False)
        else:
            ends = [("(landing)", net, 67, (LANDING_X[net], LAND_Y))]
            ends += [(c, p, *gpin(c, p)) for c, p in spec["ends"]]
            if net == "VSS":
                ends.append(("(guard_ring)", "VSS", *ring_pin))
            star(net, (67, (LANDING_X[net], LAND_Y)), ends, W_SUP, stack_at_base=False)

    # Close Metal1 notches that the 0.7 um via-stack pads create against the polygon holding their own pin
    # (a pad abutting a device Metal1 shape leaves a 5 nm slit, native M1.b). Closing is per merged polygon, so it only
    # fills inside one net's own polygon and never bridges to a different polygon.
    notch_fill = 0
    pads_trimmed = 0
    pads_below_via = []
    if 8 in added:
        m1l = lidx(8)
        # First trim each pad away from Metal1 of a different polygon (a pad wider than the gap to a
        # neighbouring device terminal leaves < 0.18 um): keep M1.b spacing to polygons the pad does not touch.
        pad_boxes = set((b.left, b.bottom, b.right, b.top) for b in added[8])
        for s in list(top.shapes(m1l).each()):
            if s.is_box() and (s.box.left, s.box.bottom, s.box.right, s.box.top) in pad_boxes:
                top.shapes(m1l).erase(s)
        base_m1 = db.Region(top.begin_shapes_rec(m1l)).merged()
        sp = round(M1B_SP_UM / dbu)
        # Every Metal1 pad in added[8] is the bottom of an endpoint via stack: a route end level is
        # never below Metal4 (path_shapes picks level 3/4, the tank 5), so stack() spans level 0..>=3
        # and drops a Via1 of VIA_UM[0] concentrically inside each pad. trim_pad tests that the trim
        # leaves that core covered -- the check the comment here used to state but never ran -- and
        # the result is recorded in provenance.json rather than silently accepted, as the module
        # docstring requires of every geometry edit in this file.
        for b in added[8]:
            keep, trimmed, uncovered = trim_pad(dbu, b, base_m1, sp)
            if trimmed:
                pads_trimmed += 1
            if not uncovered.is_empty():
                cx, cy = (b.left + b.right) / 2 * dbu, (b.bottom + b.top) / 2 * dbu
                pads_below_via.append({"x_um": round(cx, 3), "y_um": round(cy, 3),
                                       "via1_um": VIA_UM[0],
                                       "uncovered_um2": round(uncovered.area() * dbu * dbu, 6)})
            top.shapes(m1l).insert(keep)
        m1 = db.Region(top.begin_shapes_rec(m1l)).merged()
        g = round(0.091 / dbu)  # 2*g > 0.18 um (M1.b)
        for poly in m1.interacting(to_region(added[8])).each():
            pr = db.Region(poly)
            fill = pr.sized(g).sized(-g) - pr
            notch_fill += fill.count()
            top.shapes(m1l).insert(fill)

    # remove filler under the new wires (a chip-level fill tool does this; the placeholder fill here must not short them)
    fill_removed = 0
    for m in range(1, 6):
        fl = ly.layer(*gen_top.LAYERS[f"Metal{m}.filler"])
        lay = METALS[m - 1][1]
        if lay in added:
            wires = to_region(added[lay]).sized(round(2.0 / dbu))
            fr = db.Region(top.shapes(fl))
            keep = fr - fr.interacting(wires)
            fill_removed += fr.count() - keep.count()
            top.shapes(fl).clear()
            top.shapes(fl).insert(keep)

    # Always produce the fresh stream under layout/build/; --write then publishes it to
    # layout/top.gds only if the geometry moved (#257).
    build_gds = os.path.join(BUILD, "top.gds")
    ly.write(build_gds)
    chk = db.Layout()
    chk.read(build_gds)
    dg = common.digest(chk, chk.cell(TOP))
    replaced = publish_stream(build_gds, OUT_GDS, dg) if a.write else None
    # output.sha256 is the hash of the stream as it sits on disk at output.path.
    out = OUT_GDS if a.write else build_gds

    # klayout_module describes the writer of `output`. When the committed stream is kept, the
    # module running now did not produce it, so carry the recorded value forward rather than
    # re-attributing attested bytes to whichever klayout happens to be installed here (#257).
    klayout_module = getattr(__import__("klayout"), "__version__", None)
    if replaced is False and os.path.exists(PROV):
        try:
            klayout_module = json.load(open(PROV)).get("klayout_module", klayout_module)
        except (OSError, ValueError):
            pass

    rec = {
        "schema_version": 1,
        "block": "sg13g2-lc-pll",
        "item": "T1 item 2 (Layout)",
        "generator": "python layout/gen_integrated.py --write",
        "generator_chain": ["scripts/fetch-vco.sh", "python layout/gen_cells.py --write",
                            "python layout/gen_top.py", "python layout/gen_integrated.py --write"],
        "klayout_module": klayout_module,
        "inputs": {
            "vco_gds": {"path": ".fetched/sg13g2-vco/layout/vco.gds", "sha256": common.sha256(a.vco),
                        "pinned_in": "reuse.lock.json"},
            "cells_provenance": {"path": "layout/cells.provenance.json", "sha256": common.sha256(os.path.join(ROOT, "layout/cells.provenance.json"))},
            "gen_top": {"path": "layout/gen_top.py", "sha256": common.sha256(os.path.join(HERE, "gen_top.py"))},
            "gen_integrated": {"path": "layout/gen_integrated.py", "sha256": common.sha256(os.path.abspath(__file__))},
        },
        "output": {"path": "layout/top.gds", "top_cell": TOP, "sha256": common.sha256(out), "geometry_sha256": dg},
        "placement_um": {n: {"transform": c, "origin": list(o)} for n, (c, o) in PLACE.items()},
        "routes": routes,
        "landings_um": {n: {"x": LANDING_X[n], "y": LAND_Y,
                            "tower": "Metal1..TopMetal2" if SUPPLY_NETS.get(n, {}).get("mode") == "tm2"
                            else "Metal1..Metal5",
                            "label_layer": "67/25"}
                        for n in list(EXT_NETS) + list(SUPPLY_NETS)},
        "supply_route_method": {
            "same_net_exclusion": ("a supply/external leg's collision check excludes only the shapes "
                                   "this generator drew for the same net (shared star trunk, landing "
                                   "tower, anchor stacks) -- top-level shapes, never geometry inside "
                                   "the placed cells, which stay counted for #37"),
            "guard_ring_tie": {"net": "VSS", "x_um": RING_TIE_X, "y_um": ring_south_y,
                               "layer": "Metal1 (8/0)"},
            "vco_keepout_margin_um": gen_top.KEEPOUT_UM,
        },
        "tank_node_estimate": tank_estimate(routes),
        "not_routed": NOT_ROUTED,
        "collisions_total": collisions_total,
        "fill_squares_removed_under_routes": fill_removed,
        "metal1_pad_trim": {
            "method": ("each endpoint via-stack Metal1 pad (%.2f um) is trimmed back by the M1.b spacing "
                       "%.2f um from Metal1 polygons it does not touch, then tested for full coverage of "
                       "its own concentric Via1 (%.2f um). Foreign Metal1 that touches the pad is the "
                       "pad's own landing polygon, so it never trims; a non-touching polygon trims from "
                       "at best the pad edge, reaching %.3f um from the pad centre against the via's "
                       "%.4f um half-width -- so at these three constants the trim cannot reach the via, "
                       "with via_cover_margin_um to spare. The guard is the regression gate on that "
                       "margin: it arms if the pad shrinks, the via grows, or M1.b widens."
                       % (PAD_UM[0], M1B_SP_UM, VIA_UM[0], PAD_UM[0] / 2 - M1B_SP_UM, VIA_UM[0] / 2)),
            "via_cover_margin_um": round(PAD_UM[0] / 2 - M1B_SP_UM - VIA_UM[0] / 2, 4),
            "pads_total": len(added.get(8, [])),
            "pads_trimmed": pads_trimmed,
            "pads_trimmed_below_via": len(pads_below_via),
            "below_via": pads_below_via,
            "notch_fill_polygons": notch_fill,
        },
    }
    if a.write:
        with open(PROV, "w") as f:
            json.dump(rec, f, indent=1, sort_keys=True)
            f.write("\n")
        print(f"gen_integrated: wrote {PROV}")
        if replaced:
            print(f"gen_integrated: geometry changed -- replaced {OUT_GDS} "
                  f"sha256 {rec['output']['sha256']}")
            print("gen_integrated: manifests/layout.attest.json now pins a STALE stream hash; "
                  "re-stamp item 2 with: klt signoff --attest 2 --input layout/top.gds "
                  "(and refresh the manifests that cite it)")
        else:
            print(f"gen_integrated: geometry unchanged -- kept {OUT_GDS} "
                  f"sha256 {rec['output']['sha256']} (attested bytes preserved)")
    else:
        want = json.load(open(PROV))
        if want["output"]["geometry_sha256"] != dg:
            print(f"gen_integrated: geometry digest {dg} != committed {want['output']['geometry_sha256']}")
            mismatch = True
        else:
            print("gen_integrated: geometry digest matches layout/provenance.json")
            mismatch = False
    # Built outside the f-string: nesting the same quote type inside an f-string expression
    # needs PEP 701 (Python 3.12+), and CI pins 3.10 (.github/workflows/{harness,signoff}.yml).
    route_summary = ", ".join(f"{k}: {v['length_um']} um" for k, v in routes.items())
    print(f"gen_integrated: routes {{{route_summary}}}; "
          f"collisions={collisions_total}; fill squares removed={fill_removed}")
    print(f"gen_integrated: Metal1 pads {len(added.get(8, []))}, trimmed={pads_trimmed}, "
          f"trimmed below Via1={len(pads_below_via)}; notch-fill polygons={notch_fill}")
    for net in list(EXT_NETS) + list(SUPPLY_NETS):
        c = routes[net]["collisions"]
        if c:
            print(f"gen_integrated: {net} collisions: {c}")
    if not a.write and mismatch:
        sys.exit(1)


if __name__ == "__main__":
    main()
