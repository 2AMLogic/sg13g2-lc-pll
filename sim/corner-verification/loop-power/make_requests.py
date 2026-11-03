#!/usr/bin/env python3
"""Generate the two klt sim requests for the row 11 loop-power C-grid envelope.

Run from anywhere: python3 -I sim/corner-verification/loop-power/make_requests.py
Writes request-stage1.json and request-stage2.json next to this file.
`--missing RECORD...` instead writes request-stage1-missing<i>.json for the stage-1 units absent from the given records.
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


def returned(record):
    """(process, T) units that appear in a stage-1 record table (a row = a corner that came back)."""
    done = set()
    for line in open(record):
        c = [x.strip() for x in line.split("|")]
        if len(c) > 4 and c[1].startswith("mos_"):
            done.add((c[1], int(c[2])))
    return done


def missing_requests(records):
    """Stage-1 requests for the units absent from RECORDS. The grid is a product, so units are grouped by the
    set of missing temperatures: one request per distinct set (processes sharing it)."""
    done = set()
    for r in records:
        done |= returned(r)
    full = req(1)
    by_t = {}
    for p in full["corners"]["process"]:
        miss = tuple(t for t in full["corners"]["temperature_c"] if (p["name"], t) not in done)
        if miss:
            by_t.setdefault(miss, []).append(p)
    out = []
    for i, (miss, procs) in enumerate(sorted(by_t.items())):
        d = json.loads(json.dumps(full))
        d["corners"]["process"], d["corners"]["temperature_c"] = procs, list(miss)
        d["_comment"].append("MISSING-UNIT resubmission %d: %d processes x T=%s (units absent from %s)." % (
            i, len(procs), list(miss), ", ".join(os.path.basename(r) for r in records)))
        out.append((i, d, len(procs) * len(miss)))
    return out


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--missing":
        reqs = missing_requests(sys.argv[2:])
        for i, d, n in reqs:
            with open(os.path.join(HERE, "request-stage1-missing%d.json" % i), "w") as f:
                json.dump(d, f, indent=1)
                f.write("\n")
        print("missing units: %d of 135 (%d returned) in %d requests" % (sum(n for _, _, n in reqs), 135 - sum(n for _, _, n in reqs), len(reqs)))
    else:
        for s in (1, 2):
            with open(os.path.join(HERE, "request-stage%d.json" % s), "w") as f:
                json.dump(req(s), f, indent=1)
                f.write("\n")
