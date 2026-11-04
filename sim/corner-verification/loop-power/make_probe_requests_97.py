#!/usr/bin/env python3
"""Issue #97 step 1d: flop-level probe at the stuck corner TYP 125 C 2.97 V (ramped).
Samples mcounter D0..D3, DT, DTN, the clock the flops see (ckl) and q0's
internal clkb / ckbb / m / s every 0.4 ns over 8 ns from 140 ns."""
import json, copy
r = copy.deepcopy(json.load(open("request-state-97-b.json")))
r["_comment"] = ["Issue #97 step 1d: TYP 125 C 2.97 V ramped start-up. mcounter D inputs, the flop clock phases and the q0 flop internals every 0.4 ns over 8 ns from 140 ns, to see whether the stuck 1111 state is a missing clock at the flop or a wrong D."]
NODES = {"ckl": "xdiv.ckl", "d0": "xdiv.xm.d0", "d1": "xdiv.xm.d1", "d2": "xdiv.xm.d2", "d3": "xdiv.xm.d3",
         "dt": "xdiv.xm.dt", "dtn": "xdiv.xm.dtn", "q0": "xdiv.xm.q0", "q0n": "xdiv.xm.q0n",
         "clkb": "xdiv.xm.xq0.clkb", "ckbb": "xdiv.xm.xq0.ckbb", "m": "xdiv.xm.xq0.m", "s": "xdiv.xm.xq0.s",
         "mc": "mc"}
ms = [m for m in r["measurements"] if m["name"] in ("ipavg", "idavg")]
for k in range(21):
    t = 140.0 + 0.4 * k
    for n, node in NODES.items():
        ms.append({"name": f"{n}_{k:02d}", "unit": "V", "on_unreached": "null",
                   "spice": f".meas tran {n}_{k:02d} find v({node}) at={t:.1f}n"})
r["measurements"] = ms
r["analysis"]["args"] = "4p 160n 0 4p"
json.dump(r, open("request-probe-97-b.json", "w"), indent=1)
