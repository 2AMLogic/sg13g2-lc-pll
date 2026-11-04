#!/usr/bin/env python3
"""Issue #97 step 1c: counter-state sampling requests (single corner each, fleet).

Samples mcounter q0..q3, b1..b3, TC, TCN and acounter s0, s1, MC at 1.6 ns
steps (625 MHz clock) from t0 over N clocks, via `.meas find v(node) at=t`.
Variants: a = TYP 27 C 3.63 V ramped; b = TYP 125 C 2.97 V ramped;
c = TYP 125 C 2.97 V nominal start-up (DC supplies, nodeset).
"""
import json, sys, copy
base = json.load(open("request-modulus-97-a2.json"))
NODES = {"q0": "xdiv.xm.q0", "q1": "xdiv.xm.q1", "q2": "xdiv.xm.q2", "q3": "xdiv.xm.q3",
         "b1": "xdiv.xm.b1", "b2": "xdiv.xm.b2", "b3": "xdiv.xm.b3",
         "tc": "xdiv.tc", "tcn": "xdiv.tcn", "s0": "xdiv.xa.s0", "s1": "xdiv.xa.s1",
         "mc": "xdiv.xa.mc"}
def build(tag, temp, vdd, t0, nclk, tstop, netlist, comment):
    r = copy.deepcopy(base)
    r["_comment"] = [comment]
    r["netlist"] = netlist
    r["analysis"]["args"] = f"4p {tstop}n 0 4p"
    keep = [m for m in r["measurements"] if m["name"] in ("ipavg", "idavg", "fbmax", "fbmin", "tcr1", "tcf1", "tcr2", "tcf2")]
    for m in keep:
        m["spice"] = m["spice"].replace("200n", f"{tstop}n")
    ms = keep
    for k in range(nclk):
        t = t0 + 1.6 * k
        for n, node in NODES.items():
            ms.append({"name": f"{n}_{k:02d}", "unit": "V", "on_unreached": "null",
                       "spice": f".meas tran {n}_{k:02d} find v({node}) at={t:.1f}n"})
    r["measurements"] = ms
    r["corners"]["temperature_c"] = [temp]
    r["corners"]["params"]["vddv"] = [vdd]
    json.dump(r, open(f"request-state-97-{tag}.json", "w"), indent=1)
a = (27, 3.63, 120.0, 30, 160, "loop_power_body.spice",
     "Issue #97 step 1c: TYP 27 C 3.63 V, counter state bits every 1.6 ns over 30 clocks from 120 ns (two thirds of one 44 ns FB period expected), ramped start-up, timeout_s 1800.")
b = (125, 2.97, 120.0, 30, 160, "loop_power_body.spice",
     "Issue #97 step 1c: TYP 125 C 2.97 V, counter state bits every 1.6 ns over 30 clocks from 120 ns, ramped start-up.")
c = (125, 2.97, 120.0, 30, 160, "loop_power_body_nominal_startup.spice",
     "Issue #97 step 1c: TYP 125 C 2.97 V, same sampling, nominal (DC supply, nodeset) start-up, to test the start-up lock-up hypothesis.")
for tag, args in (("a", a), ("b", b), ("c", c)):
    build(tag, *args)
