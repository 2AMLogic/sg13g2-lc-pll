#!/usr/bin/env python3
"""Generate the loop-block cells (layout/cells/*.py); write or check layout/cells.provenance.json.

    layout/gen_cells.py [--out layout/build/cells] [--blocks a,b] [--write | --check]

Needs the `klayout` Python module, `klt`, and an IHP-SG13G2 PDK that klt can resolve
(~/share/pdk/ihp-sg13g2). --write rewrites the provenance file; --check regenerates and exits 1
if any cell's geometry digest, area, unit count or netlist hash differs from the committed file.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import klayout.db as db  # noqa: E402
from cells import common, prescaler  # noqa: E402

# Blocks that differ only in cell name, .subckt and netlist file: (CELL, SUBCKT, NETLIST, ROUTE).
# pfd and lock_detector are the sg13g2-pll subckts as carried in design/netlist/pll_top.spice
# (adopted at the netlist level, pinned sg13g2-pll@e71ff61, see reuse.lock.json and layout/README.md).
# ROUTE (#343): the loop filter is wired intra-cell through klt gen-compose
# routing (its guard rings and nets tied). Every other cell was trialled routed in #346 and stays
# placement-only: the router leaves 11 of 18 nets unrouted on the charge pump, 33 of 37 on the pfd,
# 18 of 23 on the lock detector, 252 of 288 on the divider and 135 of 138 on the prescaler
# ("crosses already-routed net" etc., klayout-tools#6961; trials and reports in layout/routing/cells/).
TABLE = (
    ("lcpll_divider", "divider", "design/netlist/divider.spice", False),
    ("lcpll_cp", "cp", "design/netlist/cp.spice", False),
    ("lcpll_loopfilter", "loopfilter", "design/netlist/loopfilter.spice", True),
    ("lcpll_pfd", "pfd", "design/netlist/pll_top.spice", False),
    ("lcpll_lockdet", "lock_detector", "design/netlist/pll_top.spice", False),
)


def _table_block(cell, subckt, netlist, route):
    return lambda out_dir: common.build_block(cell, subckt, os.path.join(common.ROOT, netlist),
                                              out_dir, route=route)


# Order matters: it fixes the order of cells in layout/cells.provenance.json.
# prescaler keeps its own module (input_first placement of the tank-loading INP/INN group).
BLOCKS = {prescaler.CELL: prescaler.generate}
BLOCKS.update({c: _table_block(c, s, n, r) for c, s, n, r in TABLE})
PROV = os.path.join(common.ROOT, "layout", "cells.provenance.json")


def klt_version():
    """`klt --version` of the klt this run drives ($KLT_CMD or `klt`); a failed probe is reported, not hidden."""
    try:
        p = subprocess.run(common.klt_cmd() + ["--version"], capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError) as e:
        return f"unknown (version probe failed: {e})"
    v = p.stdout.strip()
    if p.returncode != 0 or not v:
        return f"unknown (version probe exit {p.returncode}: {(p.stderr.strip() or 'no output')[:120]})"
    return v


def pdk_identity():
    """The PDK klt resolves, as far as this script can see: $PDK_ROOT or ~/share/pdk, plus a git rev when it is a checkout."""
    root = os.environ.get("PDK_ROOT") or os.path.expanduser("~/share/pdk")
    path = os.path.join(root, common.PDK)
    if not os.path.isdir(path):
        return f"{common.PDK}: not found under {root} (klt may resolve it elsewhere)"
    try:
        p = subprocess.run(
            ["git", "-C", path, "rev-parse", "--show-toplevel", "--short", "HEAD"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return f"{path} (git probe failed: {e})"
    lines = p.stdout.strip().splitlines()
    if p.returncode == 0 and len(lines) == 2 and os.path.realpath(lines[0]) == os.path.realpath(path):
        rev = lines[1]
    else:
        rev = "no revision marker (not a git checkout)"
    return f"{path} ({rev})"


def _klt_known(version):
    return isinstance(version, str) and bool(version.strip()) and not version.strip().startswith("unknown")


def toolchain_note(recorded, running):
    """Clause appended to a mismatch line: names a klt difference, or says the klt build is the same."""
    if not (_klt_known(recorded) and _klt_known(running)):
        return f"klt versions not comparable (recorded: {recorded or 'unknown'}; running: {running})"
    if recorded != running:
        return f"klt differs: recorded {recorded}, running {running} -- the generator build may explain this"
    return f"same klt build ({running}): not a toolchain difference"


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
        r = BLOCKS[name](out)
        if r["status"] != "undrawn":
            ly = db.Layout()
            ly.read(os.path.join(out, name + ".gds"))
            r["geometry_sha256"] = common.digest(ly, ly.cell(name))
            r["gds"] = f"layout/build/cells/{name}.gds"
        else:
            r["geometry_sha256"] = None
        r["generator"] = f"python layout/gen_cells.py --blocks {name}"
        recs.append(r)
        route_s = f", routing {r['routing']['status']}" if r.get("routing") else ""
        print(f"gen_cells: {name}: {r['status']}: {r['device_units']} units drawn, {len(r['undrawn_devices'])} undrawn, {r['area_um2']} um2, "
              f"{len(r['port_labels'])}/{len(r['ports'])} ports labelled{route_s}"
              + (f" (UNLABELLED: {r['ports_unlabelled']})" if r["ports_unlabelled"] else ""))
    klt_v = klt_version()
    doc = {"schema": 1, "klt": klt_v, "pdk": common.PDK,
           "command": ".venv/bin/python layout/gen_cells.py --write", "cells": recs}
    if a.write:
        with open(PROV, "w") as f:
            json.dump(doc, f, indent=1, sort_keys=True)
            f.write("\n")
        print(f"gen_cells: wrote {PROV}")
    elif a.check:
        with open(PROV) as f:
            old = json.load(f)
        bad = 0
        raw_rec = old.get("klt")
        rec_klt = raw_rec.strip() if isinstance(raw_rec, str) and raw_rec.strip() else "unknown"
        print(f"gen_cells: recorded klt: {rec_klt}; running klt: {klt_v}; PDK: {pdk_identity()}")
        note = toolchain_note(rec_klt, klt_v)
        for r in recs:
            o = next((c for c in old["cells"] if c["cell"] == r["cell"]), None)
            for k in ("geometry_sha256", "area_um2", "netlist_sha256", "device_units"):
                if o is None or o[k] != r[k]:
                    print(f"gen_cells: MISMATCH {r['cell']}.{k}: {o and o[k]} != {r[k]} ({note})")
                    bad += 1
        if bad and _klt_known(rec_klt) and _klt_known(klt_v) and rec_klt != klt_v:
            print("gen_cells: FAIL: geometry does not reproduce under a different klt than recorded; "
                  "compare with the recorded build via KLT_CMD (see layout/README.md)")
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
