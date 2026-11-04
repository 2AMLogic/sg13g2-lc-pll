#!/usr/bin/env python3
"""Issue #97: edge-aligned counter trace. For each of NEDGE rising edges of the
divider clock xdiv.ckl (from td=250 ns) record, at the crossing itself, the
counter state bits and the flop D inputs. Pre-edge value = what the master holds.
Two single-corner requests: FAST 125 C 2.97 V (fails) and TYP 27 C 2.97 V (divides, reference)."""
import json
CASES = [("FAST", 125, 2.97), ("TYP", 27, 2.97)]
NODES = {"q0": "xdiv.xm.q0", "q1": "xdiv.xm.q1", "q2": "xdiv.xm.q2", "q3": "xdiv.xm.q3",
         "b1": "xdiv.xm.b1", "b2": "xdiv.xm.b2", "b3": "xdiv.xm.b3",
         "tc": "xdiv.tc", "tcn": "xdiv.tcn",
         "d0": "xdiv.xm.d0", "d1": "xdiv.xm.d1", "d2": "xdiv.xm.d2", "d3": "xdiv.xm.d3",
         "dt": "xdiv.xm.dt", "db1": "xdiv.xm.db1", "db2": "xdiv.xm.db2", "db3": "xdiv.xm.db3"}
NEDGE, TD = 30, 250
def meas(n, spice): return {"name": n, "unit": "V", "on_unreached": "null", "spice": spice}
for proc, T, vdd in CASES:
    r = json.load(open(f"request-stage2-97-s-{proc}-{T}-{vdd}.json"))
    r["_comment"] = r["_comment"][:4] + [f"Issue #97 edge-aligned counter trace: {proc} {T} C {vdd} V, 30 ckl rising edges from {TD} ns, state and D inputs at each crossing; timeout_s 1800."]
    r["analysis"]["args"] = f"4p {TD+60}n 0 4p"
    ms = []
    for k in range(1, NEDGE + 1):
        for n, node in NODES.items():
            ms.append(meas(f"{n}_{k:02d}", f".meas tran {n}_{k:02d} find v({node}) when v(xdiv.ckl)=1.65 rise={k} td={TD}n"))
    r["measurements"] = ms
    json.dump(r, open(f"request-edge-97-{proc}-{T}-{vdd}.json", "w"), indent=1)
