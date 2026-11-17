#!/usr/bin/env python3
"""Generate the two klt sim requests for the CP static C-grid envelope (spec rows 6, 7).

Run from anywhere: python3 -I sim/corner-verification/cp-dc/make_requests.py
Writes request-stage1.json and request-stage2.json next to this file.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
import corner_set  # noqa: E402  (the spec C-grid, defined once in sim/corner_set.py)


def req(stage):
    comment = [
        "Item 5 corner envelope, CP static bench (spec rows 6 and 7), stage %d of the spec C-grid." % stage,
        "The netlist is the CP alone: it holds only HV MOS (sg13_hv_nmos/pmos, PSP103), so the HBT and MIM axes of the 135-point grid do not touch it.",
        "Stage 1 = MOS {tt,ss,ff,sf,fs} x T {-40,27,125} at 3.300 V: 15 distinct points for this netlist (the other 120 of the 135 repeat them).",
        "Stage 2 = SLOW/TYP/FAST (mos_ss/mos_tt/mos_ff for this netlist) x T {-40,27,125} x supply {2.970,3.630} V = 18 sub-corners.",
        "Row 7 upper edge (V_hi,req) is NOT graded: gate G4. vtop_est is reported only and assumes mismatch rises monotonically from 1.65 V.",
    ]
    d = {
        "_comment": comment,
        "netlist": "../../cp-dc/cp_icp.cir",
        "netlist_source": "schematic",
        "engine": "ngspice",
        "backend": "batch",
        "models": {"pdk": "ihp-sg13g2", "lib": corner_set.lib_path("mos")},
        "analysis": {"kind": "dc", "args": "VA 1.65 3.3 0.05"},
        "measurements": [
            {"name": "iup_165", "unit": "A", "spec_row": "6", "expr": "i(va)[0]", "limits": {"min": 100e-6, "max": 400e-6}},
            {"name": "idn_165", "unit": "A", "spec_row": "6", "expr": "i(vmb)[0]", "limits": {"min": 100e-6, "max": 400e-6}},
            {"name": "mm_165", "unit": "%", "expr": "abs(i(va)[0]-i(vmb)[0])/200u*100", "limits": {"max": 2.0}},
            {"name": "n_ok", "unit": "points", "expr": "mean((abs(i(va)-i(vmb))/200u*100) le 2.0)*length(i(va))"},
            {"name": "vtop_est", "unit": "V", "expr": "1.65+0.05*(n_ok-1)"},
        ],
        "options": {
            "timeout_s": 120,
            "keep_artifacts": True,
            "osdi_preload": ["$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/osdi/psp103.osdi"],
        },
    }
    # MOS-only: the stage-1 MIM and HBT axes do not touch this netlist, and the
    # stage-2 bundles reduce to their MOS corner.
    if stage == 1:
        d["corners"] = {
            "process": [corner_set.section("mos", m) for m in corner_set.MOS],
            "temperature_c": list(corner_set.TEMPS),
        }
    else:
        d["corners"] = {
            "process": [corner_set.section("mos", m) for m in corner_set.bundle_corners("mos")],
            "temperature_c": list(corner_set.TEMPS),
            "supply_v": {"VDD": list(corner_set.V_STAGE2), "VHI": list(corner_set.V_STAGE2)},
        }
        comment.append("supply_v arrays sweep together by index, so VDD and VHI move as one rail.")
    return d


for s in (1, 2):
    with open(os.path.join(HERE, "request-stage%d.json" % s), "w") as f:
        json.dump(req(s), f, indent=1)
        f.write("\n")
