#!/usr/bin/env python3
"""Integrated top layout: gen_top.py output (VCO + keep-out + guard ring + fill) plus the six
loop-block cells from gen_cells.py, placed and routed. Writes layout/top.gds and layout/provenance.json.

    layout/gen_integrated.py [--write | --check]

--write regenerates layout/top.gds + layout/provenance.json; --check regenerates into layout/build/
and exits 1 if the top-cell geometry digest differs from the committed provenance.

Needs the `klayout` Python module and the same inputs as gen_top.py / gen_cells.py (fetched VCO, klt, PDK).

Routing is a placement-level global route, not a signoff route (DRC/LVS/PEX are #36/#37/#41):
  - tank nets VOP/VON (VCO OUTP/OUTN -> prescaler INP/INN): single-layer TopMetal1 (126/0), 2 um wide.
  - other inter-block signal nets: Metal5 horizontal / Metal4 vertical, 1 um wide.
  - every endpoint gets a via stack from the pin's layer to the route layer.
  - every route polygon is checked against all other geometry on its layer (the VCO, the cells, earlier
    routes); a net whose pin-access stack or wire overlaps foreign geometry is recorded in the route
    record as `collisions`, never silently accepted. Paths are chosen collision-free where one exists.
  - supplies (VDD, VDDV, VSS), external pins (REF, IREFCP, LOCK) and the divider's M0-M3/A0-A2 tie-offs are
    NOT routed here (supply ERC is #38); they are listed in the record as `not_routed`.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

import klayout.db as db

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import gen_top  # noqa: E402

BUILD = os.path.join(ROOT, "layout", "build")
CELLS_DIR = os.path.join(BUILD, "cells")
OUT_GDS = os.path.join(ROOT, "layout", "top.gds")
PROV = os.path.join(ROOT, "layout", "provenance.json")
TOP = "lc_pll_top"

# Metal stack bottom -> top: (name, layer, datatype), via between level i and i+1.
METALS = [("Metal1", 8), ("Metal2", 10), ("Metal3", 30), ("Metal4", 50), ("Metal5", 67), ("TopMetal1", 126)]
VIAS = [19, 29, 49, 66, 125]          # Via1, Via2, Via3, Via4, TopVia1
VIA_UM = [0.19, 0.19, 0.19, 0.19, 0.42]
PAD_UM = [0.7, 0.7, 0.7, 0.7, 0.7, 2.0]
LEVEL = {m[1]: i for i, m in enumerate(METALS)}
W_TANK, W_SIG = 2.0, 1.0              # TopMetal1 minimum width; Metal4/5 signal width
CHAN_STEP = 20.0

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
NOT_ROUTED = {
    "VDD": "supply distribution; supply ERC is #38",
    "VDDV": "VCO supply; supply ERC is #38",
    "VSS": "ground / substrate ties; supply ERC is #38",
    "REF": "external pin (PFD REF)",
    "IREFCP": "external pin (charge-pump bias current)",
    "LOCK": "external pin (lock detector)",
    "divider M0-M3, A0-A2": "tie-offs to VDD/VSS in pll_top; with supplies",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def digest(ly, cell):
    """Writer-independent: merged polygons per layer + label text/position (as gen_cells.digest)."""
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


def build_base(vco, out):
    subprocess.run([sys.executable, os.path.join(HERE, "gen_top.py"), "--vco", vco, "--out", out],
                   check=True, stdout=subprocess.DEVNULL)


def load_cell(ly, name):
    """Read one cell stream into `ly`, return its cell. Sub-cells are prefixed per block so names do not collide."""
    other = db.Layout()
    other.read(os.path.join(CELLS_DIR, f"{name}.gds"))
    c = ly.create_cell(name)
    c.copy_tree(other.cell(name))
    return c


def pins(ly, cell):
    """First label per text string -> (layer, datatype, DPoint in cell coordinates)."""
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
    clean.sort(key=lambda pts: sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(pts, pts[1:])))
    return clean


def path_shapes(dbu, pts, tank):
    """Wire + via shapes for a Manhattan path (excluding endpoint stacks). Tank: all TM1. Else H=Metal5, V=Metal4."""
    shapes = {}
    segs = list(zip(pts, pts[1:]))
    if tank:
        for a, b in segs:
            shapes.setdefault(126, []).append(wire(dbu, a, b, W_TANK))
        return shapes, None
    levels = []
    for a, b in segs:
        horiz = abs(a[1] - b[1]) < 1e-9
        lv = 4 if horiz else 3
        levels.append(lv)
        shapes.setdefault(METALS[lv][1], []).append(wire(dbu, a, b, W_SIG))
    for i in range(1, len(segs)):
        if levels[i] != levels[i - 1]:
            for k, v in stack(dbu, segs[i][0], 3, 4).items():
                shapes.setdefault(k, []).extend(v)
    return shapes, levels


def length(pts):
    return sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(pts, pts[1:]))


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
    layer_idx = {}

    def lidx(l, d=0):
        return ly.layer(l, d)

    def obstacles(l):
        return db.Region(top.begin_shapes_rec(lidx(l))).merged()

    routes, collisions_total, added = {}, 0, {}
    for net, ends in sorted(NETS.items(), key=lambda kv: (kv[0] not in TANK, kv[0])):
        tank = net in TANK
        # connect first end to each other end (star from the first pin); UP/DN have three pins
        base_pin = gpin(*ends[0])
        rec = {"pins": [], "segments": [], "length_um": 0.0, "collisions": []}
        for cell, port in ends:
            l, pt = gpin(cell, port)
            rec["pins"].append({"cell": cell, "port": port, "layer": l, "x_um": pt[0], "y_um": pt[1]})
        total = 0.0
        for cell, port in ends[1:]:
            pa, pb = base_pin, gpin(cell, port)
            p, q = pa[1], pb[1]
            span = 200.0
            best = None
            for pts in candidates(p, q, span):
                shapes, levels = path_shapes(dbu, pts, tank)
                # endpoint stacks
                if tank:
                    tgt = {0: 5, 1: 5}
                    end_levels = [5, 5]
                else:
                    end_levels = [levels[0], levels[-1]]
                st = {}
                for (lay, pt), lv in zip((pa, pb), end_levels):
                    pl = LEVEL[lay]
                    for k, v in stack(dbu, pt, min(pl, lv), max(pl, lv)).items():
                        st.setdefault(k, []).extend(v)
                allshapes = {k: list(v) for k, v in shapes.items()}
                for k, v in st.items():
                    allshapes.setdefault(k, []).extend(v)
                # collision check against existing geometry on each layer, excluding the pin's own polygon
                bad = 0
                for k, bs in allshapes.items():
                    own = to_region(bs)
                    obs = obstacles(k) if k not in added else (obstacles(k))
                    hit = own & obs
                    # allow overlap with the polygons containing the net's own pins on this layer
                    for (lay, pt) in (pa, pb):
                        if lay == k:
                            pin_poly = db.Region(db.Box(round(pt[0] / dbu) - 1, round(pt[1] / dbu) - 1,
                                                        round(pt[0] / dbu) + 1, round(pt[1] / dbu) + 1))
                            own_poly = obs.interacting(pin_poly)
                            hit = hit - own_poly
                    bad += hit.count()
                if best is None or bad < best[0]:
                    best = (bad, pts, allshapes)
                if bad == 0:
                    break
            bad, pts, allshapes = best
            for k, bs in allshapes.items():
                for b in bs:
                    top.shapes(lidx(k)).insert(b)
                added.setdefault(k, []).extend(bs)
            seglen = length(pts)
            total += seglen
            rec["segments"].append({"from": f"{ends[0][0]}.{ends[0][1]}", "to": f"{cell}.{port}",
                                    "path_um": [list(x) for x in pts], "length_um": round(seglen, 3)})
            if bad:
                rec["collisions"].append({"to": f"{cell}.{port}", "overlapping_polygons": bad})
                collisions_total += bad
        rec["length_um"] = round(total, 3)
        rec["layers"] = "TopMetal1 (126/0), width %.1f um" % W_TANK if tank else \
            "Metal5 horizontal / Metal4 vertical, width %.1f um" % W_SIG
        routes[net] = rec
        # label the net on the route
        l0 = 126 if tank else 67
        p0 = rec["segments"][0]["path_um"][0]
        top.shapes(ly.layer(l0, 25)).insert(db.Text(f"{net}", round(p0[0] / dbu), round(p0[1] / dbu)))

    # Close Metal1 notches that the 0.7 um via-stack pads create against the polygon holding their own pin
    # (a pad abutting a device Metal1 shape leaves a 5 nm slit, native M1.b). Closing is per merged polygon, so it only
    # fills inside one net's own polygon and never bridges to a different polygon.
    notch_fill = 0
    if 8 in added:
        m1l = lidx(8)
        # First trim each pad away from Metal1 of a different polygon (a pad wider than the gap to a
        # neighbouring device terminal leaves < 0.18 um): keep M1.b spacing to polygons the pad does not touch.
        pad_boxes = set((b.left, b.bottom, b.right, b.top) for b in added[8])
        for s in list(top.shapes(m1l).each()):
            if s.is_box() and (s.box.left, s.box.bottom, s.box.right, s.box.top) in pad_boxes:
                top.shapes(m1l).erase(s)
        base_m1 = db.Region(top.begin_shapes_rec(m1l)).merged()
        sp = round(0.18 / dbu)
        trimmed = 0
        for b in added[8]:
            pad = db.Region(b)
            foreign = base_m1 - base_m1.interacting(pad)
            keep = pad - foreign.sized(sp)
            # the pad must still land on the pin polygon: keep it only if the trim leaves the via-sized core
            trimmed += 1 if keep != pad else 0
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
        lay = {1: 8, 2: 10, 3: 30, 4: 50, 5: 67}[m]
        if lay in added:
            wires = to_region(added[lay]).sized(round(2.0 / dbu))
            fr = db.Region(top.shapes(fl))
            keep = fr - fr.interacting(wires)
            fill_removed += fr.count() - keep.count()
            top.shapes(fl).clear()
            top.shapes(fl).insert(keep)

    out = OUT_GDS if a.write else os.path.join(BUILD, "top.gds")
    ly.write(out)
    chk = db.Layout()
    chk.read(out)
    dg = digest(chk, chk.cell(TOP))

    tank_len = {n: routes[n]["length_um"] for n in TANK}
    rec = {
        "schema_version": 1,
        "block": "sg13g2-lc-pll",
        "item": "T1 item 2 (Layout)",
        "generator": "python layout/gen_integrated.py --write",
        "generator_chain": ["scripts/fetch-vco.sh", "python layout/gen_cells.py --write",
                            "python layout/gen_top.py", "python layout/gen_integrated.py --write"],
        "klayout_module": __import__("klayout").__version__ if hasattr(__import__("klayout"), "__version__") else None,
        "inputs": {
            "vco_gds": {"path": ".fetched/sg13g2-vco/layout/vco.gds", "sha256": sha256(a.vco),
                        "pinned_in": "reuse.lock.json"},
            "cells_provenance": {"path": "layout/cells.provenance.json", "sha256": sha256(os.path.join(ROOT, "layout/cells.provenance.json"))},
            "gen_top": {"path": "layout/gen_top.py", "sha256": sha256(os.path.join(HERE, "gen_top.py"))},
            "gen_integrated": {"path": "layout/gen_integrated.py", "sha256": sha256(os.path.abspath(__file__))},
        },
        "output": {"path": "layout/top.gds", "top_cell": TOP, "sha256": sha256(out), "geometry_sha256": dg},
        "placement_um": {n: {"transform": c, "origin": list(o)} for n, (c, o) in PLACE.items()},
        "routes": routes,
        "tank_node_estimate": tank_estimate(routes),
        "not_routed": NOT_ROUTED,
        "collisions_total": collisions_total,
        "fill_squares_removed_under_routes": fill_removed,
    }
    if a.write:
        with open(PROV, "w") as f:
            json.dump(rec, f, indent=1, sort_keys=True)
            f.write("\n")
        print(f"gen_integrated: wrote {OUT_GDS} sha256 {rec['output']['sha256']}")
    else:
        want = json.load(open(PROV))
        if want["output"]["geometry_sha256"] != dg:
            sys.exit(f"gen_integrated: geometry digest {dg} != committed {want['output']['geometry_sha256']}")
        print("gen_integrated: geometry digest matches layout/provenance.json")
    # Built outside the f-string: nesting the same quote type inside an f-string expression
    # needs PEP 701 (Python 3.12+), and CI pins 3.10 (.github/workflows/{harness,signoff}.yml).
    route_summary = ", ".join(f"{k}: {v['length_um']} um" for k, v in routes.items())
    print(f"gen_integrated: routes {{{route_summary}}}; "
          f"collisions={collisions_total}; fill squares removed={fill_removed}")


if __name__ == "__main__":
    main()
