#!/usr/bin/env python3
"""Generate the two klt sim requests for the row 11 loop-power C-grid envelope.

Run from anywhere: python3 -I sim/corner-verification/loop-power/make_requests.py
Writes request-stage1.json and request-stage2.json next to this file.
Stage 1 = 5 MOS x 3 MIM x 3 HBT x 3 T = 135 points at 3.300 V.
Stage 2 = SLOW/TYP/FAST x 3 T x {2.970, 3.630} V = 18 sub-corners (DR-004 bundles).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = "libs.tech/ngspice/models/"
MOS = ["tt", "ss", "ff", "sf", "fs"]
MIM = ["typ", "bcs", "wcs"]
HBT = ["typ", "bcs", "wcs"]
W0, TSTOP = "40n", "120n"


def sections(mos, mim, hbt):
    return [
        {"lib": LIB + "cornerMOShv.lib", "section": "mos_" + mos},
        {"lib": LIB + "cornerCAP.lib", "section": "cap_" + mim},
        {"lib": LIB + "cornerHBT.lib", "section": "hbt_" + hbt},
    ]


def req(stage):
    comment = [
        "Item 5 corner envelope, spec row 11 (loop power excluding the VCO core), stage %d of the spec C-grid." % stage,
        "Circuit: CML prescaler + M/A divider at N = 100 driven at 5.0 GHz (design/netlist/{prescaler,divider}.spice). PFD + CP + bias, lock detector, reference and clock buffering are NOT in this circuit.",
        "Per corner: ipavg / idavg = mean supply current of each rail over %s-%s; tfb = 3 FB periods (rise 1 to rise 4 after %s); 3 x 19.5-20.5 ns means the divider divides to 50 MHz." % (W0, TSTOP, W0),
        "Power limits are NOT set on the requests: the 20 mW budget needs PFD+CP+bias added and the owed blocks; the record grades it.",
    ]
    d = {"_comment": comment, "netlist": "loop_power_body.spice", "netlist_source": "schematic",
         "engine": "ngspice", "backend": "batch",
         "models": {"pdk": "ihp-sg13g2"},
         "analysis": {"kind": "tran", "args": "4p %s 0 4p" % TSTOP}}
    d["measurements"] = [
        {"name": "ipavg", "unit": "A", "spec_row": "11",
         "spice": ".meas tran ipavg avg i(vddp) from=%s to=%s" % (W0, TSTOP)},
        {"name": "idavg", "unit": "A", "spec_row": "11",
         "spice": ".meas tran idavg avg i(vddd) from=%s to=%s" % (W0, TSTOP)},
        {"name": "tfb", "unit": "s", "spec_row": "11", "on_unreached": "null",
         "spice": ".meas tran tfb trig v(fb) val=1.65 td=%s rise=1 targ v(fb) val=1.65 td=%s rise=4" % (W0, W0)},
        {"name": "fbmax", "unit": "V", "spice": ".meas tran fbmax max v(fb) from=%s to=%s" % (W0, TSTOP)},
        {"name": "fbmin", "unit": "V", "spice": ".meas tran fbmin min v(fb) from=%s to=%s" % (W0, TSTOP)},
        {"name": "pspp", "unit": "V", "spice": ".meas tran pspp pp v(psp) from=%s to=%s" % (W0, TSTOP)},
    ]
    if stage == 1:
        d["corners"] = {
            "process": [{"name": "mos_%s/cap_%s/hbt_%s" % (m, c, h), "sections": sections(m, c, h)}
                        for m in MOS for c in MIM for h in HBT],
            "temperature_c": [-40, 27, 125],
            "params": {"vddv": [3.3]},
        }
    else:
        d["corners"] = {
            "process": [
                {"name": "SLOW", "sections": sections("ss", "wcs", "wcs")},
                {"name": "TYP", "sections": sections("tt", "typ", "typ")},
                {"name": "FAST", "sections": sections("ff", "bcs", "bcs")},
            ],
            "temperature_c": [-40, 27, 125],
            "params": {"vddv": [2.97, 3.63]},
        }
    d["options"] = {"timeout_s": 600, "keep_artifacts": True,
                    "osdi_preload": ["$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/osdi/psp103.osdi"]}
    return d


for s in (1, 2):
    with open(os.path.join(HERE, "request-stage%d.json" % s), "w") as f:
        json.dump(req(s), f, indent=1)
        f.write("\n")
