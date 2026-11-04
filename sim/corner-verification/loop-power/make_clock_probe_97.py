#!/usr/bin/env python3
"""Issue #97 step 1e: clock-chain waveform at 0.1 ns over two clock periods.
Nodes: cml2cmos cmo (CML-side output), cmob, ck, ckb, ckl, and the flop-q0 clkb / ckbb.
a = TYP 27 C 3.63 V, b = TYP 125 C 2.97 V, ramped start-up, from 140 ns."""
import json, copy
src = {"a": "request-state-97-a.json", "b": "request-state-97-b.json"}
NODES = {"cmo": "xdiv.xcv.cmo", "cmob": "xdiv.xcv.cmob", "ck": "xdiv.ck", "ckb": "xdiv.ckb", "ckl": "xdiv.ckl",
         "clkb": "xdiv.xm.xq0.clkb", "ckbb": "xdiv.xm.xq0.ckbb"}
for tag, f in src.items():
    r = copy.deepcopy(json.load(open(f)))
    r["_comment"] = [f"Issue #97 step 1e ({tag}): clock chain cmo/cmob/ck/ckb/ckl and flop-q0 clkb/ckbb every 0.1 ns over 3.2 ns from 140 ns, ramped start-up."]
    ms = [m for m in r["measurements"] if m["name"] in ("ipavg", "idavg")]
    for k in range(33):
        t = 140.0 + 0.1 * k
        for n, node in NODES.items():
            ms.append({"name": f"{n}_{k:02d}", "unit": "V", "on_unreached": "null",
                       "spice": f".meas tran {n}_{k:02d} find v({node}) at={t:.1f}n"})
    r["measurements"] = ms
    r["analysis"]["args"] = "4p 144n 0 4p"
    json.dump(r, open(f"request-clock-97-{tag}.json", "w"), indent=1)
