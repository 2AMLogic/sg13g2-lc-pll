#!/usr/bin/env python3
"""Issue #97: SLOW 125 C 2.97 V with the counter state (q0..q3, b1..b3, tc, tcn) held for T0..T1 ns at the state
FAST 125 C 2.97 V is in at 50 ns (q=1011, b=000, tc=0, tcn=1; request-statesnap-97-*), then released. Bench-only
forcing (B current sources through R); no design file is touched. Separates an unreachable terminal-count cycle
from a corner-specific timing failure. Body variant: loop_power_body_forced97.spice."""
import json
PROC, T, VDD, T0, T1, R, END = "SLOW", 125, 2.97, 8, 20, 200, 120
VAL = {"q0": 1, "q1": 1, "q2": 0, "q3": 1, "b1": 0, "b2": 0, "b3": 0, "tc": 0, "tcn": 1}
NODE = {k: (f"xdiv.xm.{k}" if k[0] in "qb" else f"xdiv.{k}") for k in VAL}
body = open("loop_power_body.spice").read().rstrip("\n") + "\n"
body += (f"* Issue #97 bench-only forcing {T0}-{T1} ns toward the FAST 125 C state at 50 ns (see make_forced_state_97.py).\n"
         f".param vforce={{vddv}}\n")
for k, v in VAL.items():
    tgt = "vforce" if v else "0"
    body += f"BF{k} {NODE[k]} 0 I=(time>{T0}n && time<{T1}n ? (v({NODE[k]})-{tgt})/{R} : 0)\n"
open("loop_power_body_forced97.spice", "w").write(body)
r = json.load(open(f"request-stage2-97-s-{PROC}-{T}-{VDD}.json"))
r["netlist"] = "loop_power_body_forced97.spice"
r["_comment"] = r["_comment"][:4] + [f"Issue #97 forced-state trial, {PROC} {T} C {VDD} V, counter held {T0}-{T1} ns then released."]
r["analysis"]["args"] = f"4p {END}n 0 4p"
r["measurements"] = [m for m in r["measurements"] if m["name"] == "tfb"] + [
    {"name": "tfb_late", "unit": "s", "on_unreached": "null",
     "spice": ".meas tran tfb_late trig v(fb) val=1.65 td=60n rise=1 targ v(fb) val=1.65 td=60n rise=3"},
    {"name": "fbmax", "unit": "V", "on_unreached": "null", "spice": ".meas tran fbmax max v(fb) from=30n to=120n"},
    {"name": "q3_edges", "unit": "s", "on_unreached": "null", "spice": ".meas tran q3r1 when v(xdiv.xm.q3)=1.485 rise=1 td=25n"},
    {"name": "tc_rise", "unit": "s", "on_unreached": "null", "spice": ".meas tran tcr1 when v(xdiv.tc)=1.485 rise=1 td=25n"}]
json.dump(r, open(f"request-forced-97-{PROC}-{T}-{VDD}.json", "w"), indent=1)
