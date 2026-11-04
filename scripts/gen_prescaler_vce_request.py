#!/usr/bin/env python3
"""Generate the `klt sim` stress measurements for every HBT Vce in design/netlist/prescaler.spice.

Flattens the generated prescaler netlist (no ngspice involved): every `X<name> c b e s npn13G2v ...`
card, at every instance depth, becomes one `expr` measurement vecmax(|v(C) - v(E)|) over the recorded
window (the skeleton's tran `tstart` hides the start-up transient), graded against BVCEO (limits.max).
(`stress` would say the same thing, but the batch runner image predates it: see the record.) Node names are the hierarchical names ngspice gives the
flattened nets (<instance path>.<local net>, lower case; a port is the net it is wired to).

    scripts/gen_prescaler_vce_request.py            # rewrite sim/prescaler-g1/prescaler_vce.request.json
    scripts/gen_prescaler_vce_request.py --check    # exit 1 if the committed request is stale

The request skeleton (corners, analysis, models) lives in sim/prescaler-g1/prescaler_vce.skeleton.json;
only measurements[] is generated here.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "layout" / "cells"))
import netlist  # noqa: E402  (klayout-free; layout/cells/common.py needs klayout)
NETLIST = ROOT / "design" / "netlist" / "prescaler.spice"
SKELETON = ROOT / "sim" / "prescaler-g1" / "prescaler_vce.skeleton.json"
REQUEST = ROOT / "sim" / "prescaler-g1" / "prescaler_vce.request.json"
HBT_MODEL = "npn13G2v"
TOP_INSTANCE = "x1"  # the prescaler instance in sim/prescaler-g1/prescaler_vce.cir


def hbts(subckts, top="prescaler"):
    """[(device path, collector net, emitter net)] for every HBT below `top`, lower case, with
    the top-level ground port wired to node 0 as in the .cir. Parsing and flattening are the
    shared layout/cells/netlist.py ones (continuations, port-count check); a leaf here is
    any card whose model is not itself a .subckt, and only the HBTs are kept."""
    leaves = {c["model"] for s in subckts.values() for c in s["cards"]} - set(subckts)
    top_map = {p: "0" if p.lower() == "vss" else p.lower() for p in subckts[top]["ports"]}
    devs = netlist.flatten(subckts, top, leaves, net_map=top_map, prefix=TOP_INSTANCE + ".")
    return [(d["path"].lower(), d["nets"][0].lower(), d["nets"][2].lower())
            for d in devs if d["model"].lower() == HBT_MODEL.lower()]


def build_request():
    sk = json.loads(SKELETON.read_text())
    limit = sk["_bveceo_min_v"]
    meas = []
    for dev, c, e in hbts(netlist.read_subckts(NETLIST)):
        meas.append({
            "name": "vce_" + dev.replace(".", "_"),
            "expr": "vecmax(abs(v(%s)-v(%s)))" % (c, e),
            "unit": "V",
            "limits": {"max": limit},
        })
    req = {k: v for k, v in sk.items() if not k.startswith("_")}
    req["measurements"] = meas
    return json.dumps(req, indent=2) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if the committed request differs")
    args = ap.parse_args(argv)
    new = build_request()
    if args.check:
        if not REQUEST.exists() or REQUEST.read_text() != new:
            print("stale: %s (run scripts/gen_prescaler_vce_request.py)" % REQUEST, file=sys.stderr)
            return 1
        return 0
    REQUEST.write_text(new)
    print("wrote %s (%d HBT stress measurements)" % (REQUEST.relative_to(ROOT), new.count("expr")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
