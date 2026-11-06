#!/usr/bin/env python3
"""Issue #97: SLOW 125 C 2.97 V from the first clock: 1.485 V crossings 1..K of ckl, q0..q3, b1..b3, TC, TCN,
over 0..END ns on the in-tree netlist (ramped start-up), to see how q3/q2 get stuck."""
import json
PROC, T, VDD, END, K = "SLOW", 125, 2.97, 90, 12
NODES = {"ckl": "xdiv.ckl", "tc": "xdiv.tc", "tcn": "xdiv.tcn"}
for i in range(4): NODES[f"q{i}"] = f"xdiv.xm.q{i}"
for i in (1, 2, 3): NODES[f"b{i}"] = f"xdiv.xm.b{i}"
r = json.load(open(f"request-stage2-97-s-{PROC}-{T}-{VDD}.json"))
r["_comment"] = r["_comment"][:4] + [f"Issue #97 first-clock bit trace, {PROC} {T} C {VDD} V, rise/fall 1..{K} from 0 to {END} ns."]
r["analysis"]["args"] = f"4p {END}n 0 4p"
r["measurements"] = [{"name": f"{n}_{e[0]}{k}", "unit": "s", "on_unreached": "null",
    "spice": f".meas tran {n}_{e[0]}{k} when v({node})=1.485 {e}={k}"}
    for n, node in NODES.items() for k in range(1, K + 1) for e in ("rise", "fall")]
json.dump(r, open(f"request-bittrace3-97-{PROC}-{T}-{VDD}.json", "w"), indent=1)
