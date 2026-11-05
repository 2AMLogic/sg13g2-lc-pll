#!/usr/bin/env python3
"""Issue #97: 1.485 V crossing times of ckl, TC, TC2, q0..q3, q2n, D0..D3 of the M counter on the
in-tree netlist (q2 Q-bar tap + second TC flop) at the two stage-2 corners that still do not divide:
TYP 125 C 2.97 V and SLOW 125 C 2.97 V. Window start TD per corner, rise/fall 1..K of each node."""
import json
CASES = {("TYP", 125, 2.97): 40, ("SLOW", 125, 2.97): 262}
K, SPAN = 16, 40
NODES = {"ckl": "xdiv.ckl", "tc": "xdiv.tc", "tc2": "xdiv.xm.tc2", "q2n": "xdiv.xm.q2n"}
for i in range(4):
    NODES[f"q{i}"] = f"xdiv.xm.q{i}"
    NODES[f"d{i}"] = f"xdiv.xm.d{i}"
for (PROC, T, VDD), TD in CASES.items():
    r = json.load(open(f"request-stage2-97-s-{PROC}-{T}-{VDD}.json"))
    r["_comment"] = r["_comment"][:4] + [f"Issue #97 M-counter bit trace on the in-tree netlist: {PROC} {T} C {VDD} V, rise/fall 1..{K} from {TD} ns; timeout_s 1800."]
    r["analysis"]["args"] = f"4p {TD+SPAN}n 0 4p"
    r["measurements"] = [
        {"name": f"{n}_{e[0]}{k}", "unit": "s", "on_unreached": "null",
         "spice": f".meas tran {n}_{e[0]}{k} when v({node})=1.485 {e}={k} td={TD}n"}
        for n, node in NODES.items() for k in range(1, K + 1) for e in ("rise", "fall")]
    json.dump(r, open(f"request-bittrace2-97-{PROC}-{T}-{VDD}.json", "w"), indent=1)
