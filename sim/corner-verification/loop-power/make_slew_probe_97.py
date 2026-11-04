#!/usr/bin/env python3
"""Issue #97: clock-edge probe. Hypothesis under test: the local CLKB/CKBB
inverter pair inside dff_tg_hv overlaps (race-through) when the divider clock
CKL edge is slow against one inverter delay, worst at hot/low-VDD/SLOW.
Measures, over 200-300 ns, 20-80 % rise/fall times of CKL and of the first
mcounter flop's local CLKB / CKBB, and the CLKB-vs-CKBB crossing skew."""
import json
CORNERS = [("SLOW", 125, 2.97), ("TYP", 125, 2.97), ("TYP", 27, 2.97)]
NODES = {"ckl": "xdiv.ckl", "clkb": "xdiv.xm.xq0.clkb", "ckbb": "xdiv.xm.xq0.ckbb"}
def meas(name, unit, spice):
    return {"name": name, "unit": unit, "on_unreached": "null", "spice": spice}
for proc, temp, vdd in CORNERS:
    r = json.load(open(f"request-stage2-97-s-{proc}-125-{vdd}.json"))
    r["_comment"] = r["_comment"][:4] + [f"Issue #97 clock-edge probe: {proc} {temp} C {vdd} V, ramped start-up, 300 ns; timeout_s 1800."]
    r["analysis"]["args"] = "4p 300n 0 4p"
    r["corners"]["temperature_c"] = [temp]
    ms = []
    for n, node in NODES.items():
        for e, (a, b) in (("r", ("0.2", "0.8")), ("f", ("0.8", "0.2"))):
            ms.append(meas(f"{n}_t{e}", "s", f".meas tran {n}_t{e} trig v({node}) val='{a}*vddv' td=250n {'rise' if e=='r' else 'fall'}=1 targ v({node}) val='{b}*vddv' td=250n {'rise' if e=='r' else 'fall'}=1"))
        ms.append(meas(f"{n}_max", "V", f".meas tran {n}_max max v({node}) from=200n to=300n"))
        ms.append(meas(f"{n}_min", "V", f".meas tran {n}_min min v({node}) from=200n to=300n"))
    # skew: time CKL crosses mid on a rising edge, then CLKB falls mid / CKBB rises mid
    ms.append(meas("d_ckl_clkbf", "s", ".meas tran d_ckl_clkbf trig v(xdiv.ckl) val='0.5*vddv' td=250n rise=1 targ v(xdiv.xm.xq0.clkb) val='0.5*vddv' td=250n fall=1"))
    ms.append(meas("d_ckl_ckbbr", "s", ".meas tran d_ckl_ckbbr trig v(xdiv.ckl) val='0.5*vddv' td=250n rise=1 targ v(xdiv.xm.xq0.ckbb) val='0.5*vddv' td=250n rise=1"))
    ms.append(meas("fbr1", "s", ".meas tran fbr1 when v(fb)=1.65 td=40n rise=1"))
    r["measurements"] = ms
    json.dump(r, open(f"request-slew-97-{proc}-{temp}-{vdd}.json", "w"), indent=1)
