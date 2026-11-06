#!/usr/bin/env python3
"""Issue #97: probed repeat of the SLOW 125 C 2.97 V forced-state trial (make_forced_state_97.py). Same bench-only
forcing 8-20 ns (q=1011, b=000, tc=0, tcn=1 through 200 ohm); adds 1.485 V crossings 1..K of ckl, the forced nodes
and the next-state nodes D0..D3, DT, DTN, DB1..DB3 from t=0, so that (a) the forcing is shown to have reached the target
levels and (b) the first node that departs from the FAST-corner sequence after release is read. Bench only."""
import json
PROC, T, VDD, K, END = "SLOW", 125, 2.97, 14, 60
NODES = {"ckl": "xdiv.ckl", "tc": "xdiv.tc", "tcn": "xdiv.tcn"}
for i in range(4): NODES[f"q{i}"] = f"xdiv.xm.q{i}"
for i in (1, 2, 3): NODES[f"b{i}"] = f"xdiv.xm.b{i}"
for n in ("d0", "d1", "d2", "d3", "dt", "dtn", "db1", "db2", "db3"): NODES[n] = f"xdiv.xm.{n}"
r = json.load(open("request-forced-97-SLOW-125-2.97.json"))
r["_comment"] = r["_comment"][:4] + [f"Issue #97 probed forced-state trial, {PROC} {T} C {VDD} V, crossings 1..{K} of counter nodes after release at 20 ns."]
r["analysis"]["args"] = f"4p {END}n 0 4p"
ms = [{"name": f"{n}_{e[0]}{k}", "unit": "s", "on_unreached": "null",
       "spice": f".meas tran {n}_{e[0]}{k} when v({node})=1.485 {e}={k} td=14n"}
      for n, node in NODES.items() for k in range(1, K + 1) for e in ("rise", "fall")]
# level reached by the forcing, sampled at 19 ns
ms += [{"name": f"lvl_{n}", "unit": "V", "on_unreached": "null",
        "spice": f".meas tran lvl_{n} find v({NODES[n]}) at=19n"} for n in ("q0", "q1", "q2", "q3", "b1", "b2", "b3", "tc", "tcn")]
r["measurements"] = ms
json.dump(r, open(f"request-forcedprobe-97-{PROC}-{T}-{VDD}.json", "w"), indent=1)
