#!/usr/bin/env python3
"""Issue #97: terminal-count chain levels (DT, DTN, TC, TCN, TC2) on the in-tree netlist at the two
stage-2 corners that still do not divide. The bit trace (make_bit_trace_97b.py) saw no 1.485 V crossing
on TC/TC2 at either corner; this records max/min and 0.5 V / 2.5 V crossings of each node over the same window."""
import json
CASES = {("TYP", 125, 2.97): 40, ("SLOW", 125, 2.97): 262}
SPAN = 40
NODES = {"dt": "xdiv.xm.dt", "dtn": "xdiv.xm.dtn", "tc": "xdiv.tc", "tcn": "xdiv.tcn", "tc2": "xdiv.xm.tc2"}
for (PROC, T, VDD), TD in CASES.items():
    r = json.load(open(f"request-stage2-97-s-{PROC}-{T}-{VDD}.json"))
    r["_comment"] = r["_comment"][:4] + [f"Issue #97 terminal-count chain levels on the in-tree netlist: {PROC} {T} C {VDD} V, window {TD}-{TD+SPAN} ns; timeout_s 1800."]
    r["analysis"]["args"] = f"4p {TD+SPAN}n 0 4p"
    ms = []
    for n, node in NODES.items():
        ms.append((f"{n}_max", f".meas tran {n}_max max v({node}) from={TD}n to={TD+SPAN}n"))
        ms.append((f"{n}_min", f".meas tran {n}_min min v({node}) from={TD}n to={TD+SPAN}n"))
        for lvl, tag in ((0.5, "lo"), (2.5, "hi")):
            for e in ("rise", "fall"):
                for k in (1, 2, 3):
                    ms.append((f"{n}_{tag}_{e[0]}{k}", f".meas tran {n}_{tag}_{e[0]}{k} when v({node})={lvl} {e}={k} td={TD}n"))
    r["measurements"] = [{"name": nm, "unit": "V" if nm.endswith(("max", "min")) else "s", "on_unreached": "null", "spice": sp} for nm, sp in ms]
    json.dump(r, open(f"request-tclevels-97-{PROC}-{T}-{VDD}.json", "w"), indent=1)
