#!/usr/bin/env python3
"""Issue #97: absolute crossing times (s) of the flop-internal clocks, D2, the q2 master/slave
and its logic cone around edges 9-12 at FAST 125 C 2.97 V (fails) and TYP 27 C 2.97 V (divides).
Tests the setup/hold reading of the q2 miscapture. td = 262 ns (edge ~10 is near 264 ns)."""
import json
CASES = [("FAST", 125, 2.97), ("TYP", 27, 2.97)]
NODES = {"ckl": "xdiv.ckl", "clkb": "xdiv.xm.xq2.clkb", "ckbb": "xdiv.xm.xq2.ckbb",
         "d2": "xdiv.xm.d2", "m2": "xdiv.xm.xq2.m", "s2": "xdiv.xm.xq2.s", "q2": "xdiv.xm.q2",
         "l2b": "xdiv.xm.l2b", "c2": "xdiv.xm.c2", "tc": "xdiv.tc"}
TD, K = 262, 8
def meas(n, spice): return {"name": n, "unit": "s", "on_unreached": "null", "spice": spice}
for proc, T, vdd in CASES:
    r = json.load(open(f"request-stage2-97-s-{proc}-{T}-{vdd}.json"))
    r["_comment"] = r["_comment"][:4] + [f"Issue #97 q2 settle/hold crossing times: {proc} {T} C {vdd} V, rise/fall 1..{K} of each node from {TD} ns; timeout_s 1800."]
    r["analysis"]["args"] = f"4p {TD+12}n 0 4p"
    ms = []
    for n, node in NODES.items():
        for k in range(1, K + 1):
            for e in ("rise", "fall"):
                ms.append(meas(f"{n}_{e[0]}{k}", f".meas tran {n}_{e[0]}{k} when v({node})=1.485 {e}={k} td={TD}n"))
    r["measurements"] = ms
    json.dump(r, open(f"request-d2settle-97-{proc}-{T}-{vdd}.json", "w"), indent=1)
