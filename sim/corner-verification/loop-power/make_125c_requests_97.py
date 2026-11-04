#!/usr/bin/env python3
"""Issue #97: diagnosis requests for the four 125 C stage-2 corners still not
dividing after the cml2cmos self-bias (single corner each, batch fleet).

Per corner: 300 ns transient (ramped start-up body unchanged); FB and divider
TC (mcounter terminal count) rising-edge times from td = 40 ns, clock (ck, ckl)
10-edge time and min/max over 200-300 ns, FB/TC min/max over 200-300 ns, and
counter state bits (q0..q3, b1..b3, tc, s0, s1, mc) sampled every 1.6 ns over
24 clocks from 200 ns.
"""
import json, copy
CORNERS = [("SLOW", 2.97), ("SLOW", 3.63), ("TYP", 2.97), ("FAST", 2.97)]
NODES = {"q0": "xdiv.xm.q0", "q1": "xdiv.xm.q1", "q2": "xdiv.xm.q2", "q3": "xdiv.xm.q3",
         "b1": "xdiv.xm.b1", "b2": "xdiv.xm.b2", "b3": "xdiv.xm.b3",
         "tc": "xdiv.tc", "s0": "xdiv.xa.s0", "s1": "xdiv.xa.s1", "mc": "mc"}
TSTOP, T0, NCLK = 300, 200.0, 24
def meas(name, unit, spice):
    return {"name": name, "unit": unit, "on_unreached": "null", "spice": spice}
for proc, vdd in CORNERS:
    r = json.load(open(f"request-stage2-97-s-{proc}-125-{vdd}.json"))
    r["_comment"] = r["_comment"][:4] + [
        f"Issue #97 diagnosis shard: {proc} 125 C {vdd} V, ramped start-up, {TSTOP} ns, FB/TC edge times, clock levels, counter state every 1.6 ns from {T0:.0f} ns; timeout_s 1800."]
    r["analysis"]["args"] = f"4p {TSTOP}n 0 4p"
    ms = [m for m in r["measurements"] if m["name"] in ("ipavg", "idavg")]
    for m in ms:
        m["spice"] = m["spice"].replace("120n", f"{TSTOP}n")
    for k in range(1, 9):
        ms.append(meas(f"fbr{k}", "s", f".meas tran fbr{k} when v(fb)=1.65 td=40n rise={k}"))
        ms.append(meas(f"tcr{k}", "s", f".meas tran tcr{k} when v(xdiv.tc)=1.65 td=40n rise={k}"))
    for n, node in (("fb", "fb"), ("tc", "xdiv.tc"), ("ck", "xdiv.ck"), ("ckl", "xdiv.ckl")):
        ms.append(meas(f"{n}max", "V", f".meas tran {n}max max v({node}) from=200n to={TSTOP}n"))
        ms.append(meas(f"{n}min", "V", f".meas tran {n}min min v({node}) from=200n to={TSTOP}n"))
    ms.append(meas("tck10", "s", ".meas tran tck10 trig v(xdiv.ck) val=1.65 td=200n rise=1 targ v(xdiv.ck) val=1.65 td=200n rise=11"))
    for k in range(NCLK):
        t = T0 + 1.6 * k
        for n, node in NODES.items():
            ms.append(meas(f"{n}_{k:02d}", "V", f".meas tran {n}_{k:02d} find v({node}) at={t:.1f}n"))
    r["measurements"] = ms
    json.dump(r, open(f"request-diag125-97-{proc}-{vdd}.json", "w"), indent=1)
