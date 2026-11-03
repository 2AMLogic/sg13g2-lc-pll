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
NETLIST = ROOT / "design" / "netlist" / "prescaler.spice"
SKELETON = ROOT / "sim" / "prescaler-g1" / "prescaler_vce.skeleton.json"
REQUEST = ROOT / "sim" / "prescaler-g1" / "prescaler_vce.request.json"
HBT_MODEL = "npn13G2v"
TOP_INSTANCE = "x1"  # the prescaler instance in sim/prescaler-g1/prescaler_vce.cir
GLOBAL_GROUND = {"vss", "0"}


def parse_subckts(text):
    """{name: {"ports": [...], "cards": [(inst, nodes, model)]}} for every .subckt in the file."""
    subckts, cur = {}, None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("*"):
            continue
        tok = line.split()
        head = tok[0].lower()
        if head == ".subckt":
            cur = {"ports": [t.lower() for t in tok[2:]], "cards": []}
            subckts[tok[1].lower()] = cur
        elif head == ".ends":
            cur = None
        elif cur is not None and head.startswith("x"):
            toks = [t for t in tok[1:] if "=" not in t]  # drop name=value parameters
            cur["cards"].append((tok[0].lower(), [t.lower() for t in toks[:-1]], toks[-1].lower()))
    return subckts


def flatten(subckts, top="prescaler"):
    """[(device path, collector net, emitter net)] for every HBT below `top`."""
    out = []

    def walk(name, path, netmap):
        for inst, nodes, model in subckts[name]["cards"]:
            def net(n):
                if n in netmap:
                    return netmap[n]
                return "0" if n in GLOBAL_GROUND else path + "." + n
            outer = [net(n) for n in nodes]
            if model == HBT_MODEL.lower():
                out.append((path + "." + inst, outer[0], outer[2]))
            elif model in subckts:
                walk(model, path + "." + inst, dict(zip(subckts[model]["ports"], outer)))
            else:
                raise SystemExit("unknown subcircuit or model %r in %s" % (model, name))

    ports = subckts[top]["ports"]
    top_map = {p: ("0" if p == "vss" else p) for p in ports}  # top-level nets as wired in the .cir
    top_map.update({"inp": "inp", "inn": "inn", "mc": "mc", "iref": "iref", "outp": "outp", "outn": "outn", "vdd": "vdd"})
    walk(top, TOP_INSTANCE, top_map)
    return out


def build_request():
    sk = json.loads(SKELETON.read_text())
    limit = sk["_bveceo_min_v"]
    meas = []
    for dev, c, e in flatten(parse_subckts(NETLIST.read_text())):
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
