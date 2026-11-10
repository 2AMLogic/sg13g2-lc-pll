#!/usr/bin/env python3
"""Add the PDK resistor loading (issue #164) to the divider corner requests: cornerRES.lib section per process name
(SLOW=res_wcs, TYP=res_typ, FAST=res_bcs), the r3_cmc OSDI, and ngbehavior=hsa as sim/prescaler-div89.

  python3 gen_res_requests.py          rewrite divider_corner_{speed,count}.request.json in place (idempotent)
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = {"SLOW": "res_wcs", "TYP": "res_typ", "FAST": "res_bcs"}
OSDI = "$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/osdi/"
for f in ("divider_corner_speed", "divider_corner_count"):
    p = HERE / (f + ".request.json")
    r = json.loads(p.read_text())
    for proc in r["corners"]["process"]:
        proc["sections"] = [s for s in proc["sections"] if not s["lib"].endswith("cornerRES.lib")]
        proc["sections"].append({"lib": "libs.tech/ngspice/models/cornerRES.lib", "section": RES[proc["name"]]})
    o = r["options"]
    o["osdi_preload"] = [OSDI + "psp103.osdi", OSDI + "r3_cmc.osdi"]
    o["ngspice_init"] = ["set ngbehavior=hsa"]
    p.write_text(json.dumps(r, indent=2) + "\n")
