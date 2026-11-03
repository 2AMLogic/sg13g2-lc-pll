#!/usr/bin/env python3
"""Top-cell generator for the LC PLL: places the pinned sg13g2-vco stream
UNMODIFIED, then draws the inductor keep-out, an outer substrate guard ring and
metal fill around it.

    layout/gen_top.py [--vco .fetched/sg13g2-vco/layout/vco.gds] [--out layout/build/lc_pll_top.gds]

Needs the `klayout` Python module (see layout/README.md). Run scripts/fetch-vco.sh first.

Scope: nothing in the `vco` cell subtree is edited -- the whole input stream is read
verbatim and the top cell only *instantiates* `vco` at the origin with no transform.
The generator refuses an input stream whose sha256 differs from reuse.lock.json.
Loop blocks (PFD, charge pump, filter, divider, prescaler) are separate work.

Geometry (micrometres, VCO placed at the origin)
  keep-out   KEEPOUT_UM around the VCO bbox: nothing from FORBIDDEN_LAYERS may be drawn
             by this top cell inside it; a NoMetFiller marker covers it so a chip-level
             fill tool leaves it alone. The inductor's own exclusion markers (27/0 IND,
             x/23, 148/0 NoRCX) ship inside the VCO cell and are untouched.
  guard ring one closed annulus, RING_GAP_UM outside the VCO bbox (so outside the
             keep-out): Activ + pSD + Cont + Metal1, RING_W_UM wide (a p+ substrate tap).
  fill       square Metal1..Metal5 filler shapes (datatype 22) in a band outside the ring.
             A placeholder scheme: density sign-off is a chip-assembly / DRC step (#36).

Layer numbers come from the pinned PDK's KLayout layer properties,
$PDK_ROOT/ihp-sg13g2/libs.tech/klayout/tech/sg13g2.lyp (and sg13g2.map for the
x/22 FILL purposes); the table below is a copy of those rows, not a guess.
"""
import argparse
import hashlib
import json
import os
import sys

import klayout.db as db

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# name -> (layer, datatype), from sg13g2.lyp / sg13g2.map of the pinned IHP-Open-PDK.
LAYERS = {
    "Activ": (1, 0), "GatPoly": (5, 0), "Cont": (6, 0), "pSD": (14, 0),
    "Metal1": (8, 0), "Metal2": (10, 0), "Metal3": (30, 0), "Metal4": (50, 0), "Metal5": (67, 0),
    "Metal1.filler": (8, 22), "Metal2.filler": (10, 22), "Metal3.filler": (30, 22),
    "Metal4.filler": (50, 22), "Metal5.filler": (67, 22),
    "NoMetFiller": (160, 0),
}
# Shapes this top cell must not put near the inductor/VCO (devices, taps, lower metal, fill).
FORBIDDEN_LAYERS = ["Activ", "GatPoly", "Cont", "pSD", "Metal1", "Metal2", "Metal3", "Metal4",
                    "Metal5", "Metal1.filler", "Metal2.filler", "Metal3.filler",
                    "Metal4.filler", "Metal5.filler"]

KEEPOUT_UM = 20.0   # design choice: exceeds the VCO's own 16 um inductor-to-core gap
RING_GAP_UM = 5.0   # ring inner edge sits this far outside the keep-out
RING_W_UM = 1.0
CONT_UM, CONT_PITCH_UM = 0.16, 0.34
PSD_ENC_UM = 0.3
FILL_GAP_UM, FILL_BAND_UM = 5.0, 40.0
FILL_SIZE_UM, FILL_PITCH_UM = 4.0, 8.0
TOP_NAME, VCO_NAME = "lc_pll_top", "vco"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pinned_sha(lock_path, local_rel):
    with open(lock_path) as f:
        lock = json.load(f)
    for imp in lock["imports"]:
        for fe in imp["files"]:
            if fe["local"] == local_rel:
                return fe["sha256"]
    raise SystemExit(f"gen_top: {local_rel} not in {lock_path}")


def grow(box, d):
    return db.DBox(box.left - d, box.bottom - d, box.right + d, box.top + d)


def ring_region(ly, inner, w):
    """Closed annulus: box `inner` (DBox) grown by w, minus `inner`."""
    outer = db.Region(grow(inner, w).to_itype(ly.dbu))
    return outer - db.Region(inner.to_itype(ly.dbu))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--vco", default=os.path.join(ROOT, ".fetched/sg13g2-vco/layout/vco.gds"))
    ap.add_argument("--out", default=os.path.join(ROOT, "layout/build/lc_pll_top.gds"))
    ap.add_argument("--lock", default=os.path.join(ROOT, "reuse.lock.json"))
    ap.add_argument("--forbidden-json", default=None,
                    help="also write the --forbidden layer list for klt keepout-check here")
    a = ap.parse_args()

    want = pinned_sha(a.lock, ".fetched/sg13g2-vco/layout/vco.gds")
    got = sha256(a.vco)
    if got != want:
        sys.exit(f"gen_top: {a.vco} sha256 {got} != pinned {want}; refusing (run scripts/fetch-vco.sh)")

    ly = db.Layout()
    ly.read(a.vco)  # whole stream verbatim: the vco subtree is never touched
    vco = ly.cell(VCO_NAME)
    if vco is None or ly.top_cells() != [vco]:
        sys.exit("gen_top: expected exactly one top cell named 'vco' in the VCO stream")
    box = vco.dbbox()  # bbox of the placement (identity transform)

    top = ly.create_cell(TOP_NAME)
    top.insert(db.CellInstArray(vco.cell_index(), db.Trans()))
    li = {n: ly.layer(*ln) for n, ln in LAYERS.items()}
    dbu = ly.dbu

    # Keep-out marker: a chip-level fill tool must leave the VCO + margin alone.
    top.shapes(li["NoMetFiller"]).insert(db.Box(grow(box, KEEPOUT_UM).to_itype(dbu)))

    # Guard ring: Activ/pSD/Metal1 annuli + a Cont row along the centre line.
    r_in = grow(box, KEEPOUT_UM + RING_GAP_UM)
    ring = ring_region(ly, r_in, RING_W_UM)
    top.shapes(li["Activ"]).insert(ring)
    top.shapes(li["Metal1"]).insert(ring)
    top.shapes(li["pSD"]).insert(ring.sized(round(PSD_ENC_UM / dbu)))
    c = grow(r_in, RING_W_UM / 2)  # centre line of the ring
    half, step, n = round(CONT_UM / dbu) // 2, round(CONT_PITCH_UM / dbu), 0
    xs0, xs1 = round(c.left / dbu), round(c.right / dbu)
    ys0, ys1 = round(c.bottom / dbu), round(c.top / dbu)
    pts = set()
    for x in range(xs0, xs1 + 1, step):
        pts.update([(x, ys0), (x, ys1)])
    for y in range(ys0, ys1 + 1, step):
        pts.update([(xs0, y), (xs1, y)])
    for x, y in sorted(pts):
        top.shapes(li["Cont"]).insert(db.Box(x - half, y - half, x + half, y + half))
        n += 1

    # Fill band outside the ring: filler datatype only, never touching the ring.
    f_in = grow(r_in, RING_W_UM + FILL_GAP_UM)
    f_out = grow(f_in, FILL_BAND_UM)
    nfill = 0
    x = f_out.left
    while x + FILL_SIZE_UM <= f_out.right:
        y = f_out.bottom
        while y + FILL_SIZE_UM <= f_out.top:
            sq = db.DBox(x, y, x + FILL_SIZE_UM, y + FILL_SIZE_UM)
            if not sq.overlaps(f_in) and not f_in.contains(sq.p1) and not f_in.contains(sq.p2):
                for m in range(1, 6):
                    top.shapes(li[f"Metal{m}.filler"]).insert(db.Box(sq.to_itype(dbu)))
                nfill += 1
            y += FILL_PITCH_UM
        x += FILL_PITCH_UM

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    ly.write(a.out)
    if a.forbidden_json:
        with open(a.forbidden_json, "w") as f:
            json.dump([list(LAYERS[n]) for n in FORBIDDEN_LAYERS], f)
    print(f"gen_top: wrote {a.out} (top {TOP_NAME}; {VCO_NAME} at origin, vco bbox {box}; "
          f"{n} ring contacts, {nfill} fill sites x5 metals)")


if __name__ == "__main__":
    main()
