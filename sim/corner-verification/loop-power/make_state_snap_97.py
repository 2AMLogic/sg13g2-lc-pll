#!/usr/bin/env python3
"""Issue #97: counter state snapshot (q0..q3, b1..b3, tc, tcn) at 50 ns of FAST 125 C 2.97 V (divides on the in-tree
netlist), to supply a known-valid state for the forced-state trial on SLOW 125 C 2.97 V (make_forced_state_97.py)."""
import json
PROC, T, VDD, AT = "FAST", 125, 2.97, 50
NODES = {"tc": "xdiv.tc", "tcn": "xdiv.tcn"}
for i in range(4): NODES[f"q{i}"] = f"xdiv.xm.q{i}"
for i in (1, 2, 3): NODES[f"b{i}"] = f"xdiv.xm.b{i}"
r = json.load(open(f"request-stage2-97-s-{PROC}-{T}-{VDD}.json"))
r["_comment"] = r["_comment"][:4] + [f"Issue #97 counter state snapshot at {AT} ns, {PROC} {T} C {VDD} V."]
r["analysis"]["args"] = f"4p {AT + 12}n 0 4p"
r["measurements"] = [{"name": f"{n}_at", "unit": "V", "on_unreached": "null",
    "spice": f".meas tran {n}_at find v({node}) at={AT}n"} for n, node in NODES.items()]
r["measurements"].append({"name": "tfb", "unit": "s", "on_unreached": "null",
    "spice": ".meas tran tfb trig v(fb) val=1.65 td=20n rise=1 targ v(fb) val=1.65 td=20n rise=4"})
json.dump(r, open(f"request-statesnap-97-{PROC}-{T}-{VDD}.json", "w"), indent=1)
