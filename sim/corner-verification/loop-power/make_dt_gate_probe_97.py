#!/usr/bin/env python3
"""Issue #97: gate-by-gate crossings of the DT decode (q0..q3 -> f32, g10 -> dtn -> dt) at SLOW 125 C 2.97 V.
Same forced-state bench, corner and window as request-forcedprobe-97-SLOW-125-2.97.json; only the probed nodes differ
(1.485 V crossings, first NCROSS rises/falls after 14 ns). Bench only."""
import json
NCROSS = int(__import__("sys").argv[1]) if len(__import__("sys").argv) > 1 else 14
base = json.load(open("request-forcedprobe-97-SLOW-125-2.97.json"))
nodes = {"ckl": "xdiv.ckl", "q0": "xdiv.xm.q0", "q1": "xdiv.xm.q1", "q2": "xdiv.xm.q2", "q3": "xdiv.xm.q3",
         "q1n": "xdiv.xm.q1n", "f32": "xdiv.xm.f32", "g10": "xdiv.xm.g10", "dtn": "xdiv.xm.dtn", "dt": "xdiv.xm.dt",
         "tc": "xdiv.tc"}
ms = []
for n, node in nodes.items():
    for i in range(1, NCROSS + 1):
        for e in ("rise", "fall"):
            nm = f"{n}_{e[0]}{i}"
            ms.append({"name": nm, "unit": "s", "on_unreached": "null",
                       "spice": f".meas tran {nm} when v({node})=1.485 {e}={i} td=14n"})
r = dict(base)
r["measurements"] = ms
r["_comment"] = base["_comment"][:4] + ["Issue #97 DT decode gate probe (q0..q3, f32, g10, dtn, dt, tc), SLOW 125 C 2.97 V, forced state released at 20 ns."]
json.dump(r, open(("request-dtgate-97-SLOW-125-2.97.json" if NCROSS == 14 else f"request-dtgate-97-SLOW-125-2.97-n{NCROSS}.json"), "w"), indent=1)
print(len(ms), "measurements")
