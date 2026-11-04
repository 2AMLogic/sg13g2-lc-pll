#!/usr/bin/env python3
"""Generate the loop-block cells (layout/cells/*.py); write or check layout/cells.provenance.json.

    layout/gen_cells.py [--out layout/build/cells] [--blocks a,b] [--write | --check]

Needs the `klayout` Python module, `klt`, and an IHP-SG13G2 PDK that klt can resolve
(~/share/pdk/ihp-sg13g2). --write rewrites the provenance file; --check regenerates and exits 1
if any cell's geometry digest, area, unit count or netlist hash differs from the committed file.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import klayout.db as db  # noqa: E402
from cells import charge_pump, common, divider, loop_filter, lock_detector, pfd, prescaler  # noqa: E402

BLOCKS = {m.CELL: m for m in (prescaler, divider, charge_pump, loop_filter, pfd, lock_detector)}
PROV = os.path.join(common.ROOT, "layout", "cells.provenance.json")


def digest(gds, cell):
    """Writer-independent digest: merged polygons per layer plus label text/position."""
    ly = db.Layout()
    ly.read(gds)
    c = ly.cell(cell)
    h = hashlib.sha256()
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        r = db.Region(c.begin_shapes_rec(li))
        r.merge()
        polys = sorted(str(p) for p in r.each())
        txt = sorted(f"{s.text_string}@{s.text_trans.disp.x},{s.text_trans.disp.y}"
                     for s in (it.shape() for it in c.begin_shapes_rec(li)) if s.is_text())
        if polys or txt:
            h.update(f"{info.layer}/{info.datatype}|{';'.join(polys)}|{';'.join(txt)}\n".encode())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(common.ROOT, "layout/build/cells"))
    ap.add_argument("--blocks", default=",".join(BLOCKS))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    recs = []
    for name in a.blocks.split(","):
        r = BLOCKS[name].generate(out)
        if r["status"] != "undrawn":
            r["geometry_sha256"] = digest(os.path.join(out, name + ".gds"), name)
            r["gds"] = f"layout/build/cells/{name}.gds"
        else:
            r["geometry_sha256"] = None
        r["generator"] = f"python layout/gen_cells.py --blocks {name}"
        recs.append(r)
        print(f"gen_cells: {name}: {r['status']}: {r['device_units']} units drawn, {len(r['undrawn_devices'])} undrawn, {r['area_um2']} um2, "
              f"{len(r['port_labels'])}/{len(r['ports'])} ports labelled"
              + (f" (UNLABELLED: {r['ports_unlabelled']})" if r["ports_unlabelled"] else ""))
    klt_v = subprocess.run(common.klt_cmd() + ["--version"], capture_output=True, text=True).stdout.strip()
    doc = {"schema": 1, "klt": klt_v, "pdk": common.PDK,
           "command": ".venv/bin/python layout/gen_cells.py --write", "cells": recs}
    if a.write:
        with open(PROV, "w") as f:
            json.dump(doc, f, indent=1, sort_keys=True)
            f.write("\n")
        print(f"gen_cells: wrote {PROV}")
    elif a.check:
        old = json.load(open(PROV))
        bad = 0
        for r in recs:
            o = next((c for c in old["cells"] if c["cell"] == r["cell"]), None)
            for k in ("geometry_sha256", "area_um2", "netlist_sha256", "device_units"):
                if o is None or o[k] != r[k]:
                    print(f"gen_cells: MISMATCH {r['cell']}.{k}: {o and o[k]} != {r[k]}")
                    bad += 1
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
