#!/usr/bin/env python3
"""Issue #97: 1.485 V crossing times of ckl, q0..q3 and D0..D3 of the M counter around the
terminal-count reload at FAST 125 C 2.97 V (fails). Tells which bits miss their capture, not only q2.
Window from td = 262 ns, rise/fall 1..8 of each node."""
import json
PROC, T, VDD = "FAST", 125, 2.97
NODES = {"ckl": "xdiv.ckl", "tc": "xdiv.tc"}
for i in range(4):
    NODES[f"q{i}"] = f"xdiv.xm.q{i}"
    NODES[f"d{i}"] = f"xdiv.xm.d{i}"
TD, K = 262, 8
r = json.load(open(f"request-stage2-97-s-{PROC}-{T}-{VDD}.json"))
r["_comment"] = r["_comment"][:4] + [f"Issue #97 M-counter bit trace: {PROC} {T} C {VDD} V, rise/fall 1..{K} from {TD} ns; timeout_s 1800."]
r["analysis"]["args"] = f"4p {TD+12}n 0 4p"
r["measurements"] = [
    {"name": f"{n}_{e[0]}{k}", "unit": "s", "on_unreached": "null",
     "spice": f".meas tran {n}_{e[0]}{k} when v({node})=1.485 {e}={k} td={TD}n"}
    for n, node in NODES.items() for k in range(1, K + 1) for e in ("rise", "fall")]
json.dump(r, open(f"request-bittrace-97-{PROC}-{T}-{VDD}.json", "w"), indent=1)
