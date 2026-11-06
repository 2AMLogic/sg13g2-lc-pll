#!/usr/bin/env python3
"""Issue #97: second probe of the SLOW 125 C 2.97 V forced-state trial. Same forcing and window as
make_forced_probe_97.py; crossings 1..K from td=36 ns of ckl, q0..q3, dt, dtn, tc, tcn so the DT pulse at 44-45 ns
can be placed against the actual clock edges (the first probe only recorded ckl to 35.7 ns). Bench only."""
import json
PROC, T, VDD, K, END, TD = "SLOW", 125, 2.97, 16, 62, 36
NODES = {"ckl": "xdiv.ckl", "tc": "xdiv.tc", "tcn": "xdiv.tcn", "dt": "xdiv.xm.dt", "dtn": "xdiv.xm.dtn"}
for i in range(4): NODES[f"q{i}"] = f"xdiv.xm.q{i}"
r = json.load(open("request-forced-97-SLOW-125-2.97.json"))
r["_comment"] = r["_comment"][:4] + [f"Issue #97 probed forced-state trial 2, {PROC} {T} C {VDD} V, crossings 1..{K} from {TD} ns."]
r["analysis"]["args"] = f"4p {END}n 0 4p"
r["measurements"] = [{"name": f"{n}_{e[0]}{k}", "unit": "s", "on_unreached": "null",
    "spice": f".meas tran {n}_{e[0]}{k} when v({node})=1.485 {e}={k} td={TD}n"}
    for n, node in NODES.items() for k in range(1, K + 1) for e in ("rise", "fall")]
json.dump(r, open(f"request-forcedprobe2-97-{PROC}-{T}-{VDD}.json", "w"), indent=1)
