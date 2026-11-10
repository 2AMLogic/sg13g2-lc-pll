#!/usr/bin/env python3
"""Generate the klt sim requests of the divider corner check (divider_corner_*.request.json).

  gen_corner_requests.py            write the request files
  gen_corner_requests.py --check    exit 1 if the committed files differ

Process SLOW / TYP / FAST = (hbt_wcs, mos_ss, cap_wcs) / (hbt_typ, mos_tt, cap_typ) / (hbt_bcs, mos_ff, cap_bcs),
-40 / 27 / 125 C, 3.3 V. corners.params arrays are zipped by index, one entry per case.
 Bench start (issue #166): VDD, IREF and the input common mode ramp from 0 over tr = 3 ns (divider_corner.cir); the stop times carry 10 ns more.
 speed: 160 ns at the prescaler output rates, N = 100 at 625 and 687.5 MHz, A = 0 (N = 96) and A = 7 (N = 103) at 687.5 MHz.
 count: 650 ns at 100 MHz, N = 100 (A = 4) and N = 90 (M = 11, A = 2).
timeout_s: the default 120 s per-corner timeout killed the first batch run (a 150 ns real-chain run takes minutes). Not sharded:
units run in parallel on one fleet host; klt only warns that the serial bound exceeds the ceiling.
Measurements are crossing times of ck, fb and mc at 1.65 V; divider_corner_record.py turns them into N.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
L = "libs.tech/ngspice/models/"
PROC = [("SLOW", "hbt_wcs", "mos_ss", "cap_wcs"), ("TYP", "hbt_typ", "mos_tt", "cap_typ"), ("FAST", "hbt_bcs", "mos_ff", "cap_bcs")]
# PDK resistor loading (issue #164): cornerRES.lib section per process name, r3_cmc OSDI, ngbehavior=hsa as sim/prescaler-div89.
RES = {"SLOW": "res_wcs", "TYP": "res_typ", "FAST": "res_bcs"}
OSDI = "$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/osdi/"
V = 3.3
# case: (fin, M, A, expected N)
SPEED = [("N100-625", 625e6, 12, 4), ("N100-687.5", 687.5e6, 12, 4), ("A0-687.5", 687.5e6, 12, 0), ("A7-687.5", 687.5e6, 12, 7)]
COUNT = [("N100-100M", 100e6, 12, 4), ("N90-100M", 100e6, 11, 2)]


def params(cases):
    bit = lambda x, i: V if (x >> i) & 1 else 0
    return {
        "fin": [c[1] for c in cases],
        **{f"m{i}v": [bit(c[2], i) for c in cases] for i in range(4)},
        **{f"a{i}v": [bit(c[3], i) for c in cases] for i in range(3)},
    }


def request(stop, cases, timeout_s):
    xs = [("ck_rise", "v(xd.ck)", "rise"), ("fb_rise", "v(fb)", "rise"), ("mc_rise", "v(mc)", "rise"), ("mc_fall", "v(mc)", "fall")]
    return {
        "netlist": "divider_corner.cir",
        "engine": "ngspice",
        "models": {"pdk": "sg13g2"},
        "analysis": {"kind": "tran", "args": f"20p {stop} 0 20p"},
        "corners": {
            "process": [{"name": n, "sections": [{"lib": L + "cornerHBT.lib", "section": h}, {"lib": L + "cornerMOShv.lib", "section": m},
                                                  {"lib": L + "cornerCAP.lib", "section": c},
                                                  {"lib": L + "cornerRES.lib", "section": RES[n]}]} for n, h, m, c in PROC],
            "temperature_c": [-40, 27, 125],
            "params": params(cases),
        },
        "options": {"osdi_preload": [OSDI + "psp103.osdi", OSDI + "r3_cmc.osdi"], "stage_model_inputs": True, "timeout_s": timeout_s,
                    "ngspice_init": ["set ngbehavior=hsa"]},
        "measurements": [{"name": n, "unit": "s", "crossings": {"signal": s, "level": 1.65, "edge": e, "from": "0", "max": 200}} for n, s, e in xs],
    }


def build():
    return {"divider_corner_speed.request.json": request("160n", SPEED, 600), "divider_corner_count.request.json": request("650n", COUNT, 900)}


if __name__ == "__main__":
    out = {k: json.dumps(v, indent=2) + "\n" for k, v in build().items()}
    if "--check" in sys.argv:
        bad = [k for k, v in out.items() if not (HERE / k).exists() or (HERE / k).read_text() != v]
        for k in bad:
            print("stale:", k, file=sys.stderr)
        sys.exit(1 if bad else 0)
    for k, v in out.items():
        (HERE / k).write_text(v)
        print("wrote", k)
