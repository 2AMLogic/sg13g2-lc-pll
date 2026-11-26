#!/usr/bin/env python3
"""Write the two single-unit trace requests of the hot-corner stall (issue #197) next to this script.

  gen_hot_trace_requests.py [PDK_ROOT]

The two 30 ns requests use the ramped-start divider_corner.cir from #198 with M=12, A=4.
They cover SLOW/125C at 625 MHz and TYP/125C at 687.5 MHz and retain the ASCII waveform.raw.
Pass the local PDK root to generate the OSDI paths. For example, from this directory run

  klt sim hot_trace_slow125.request.json --backend local -o OUT --pdk-root PDK_ROOT
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_corner_requests as g

root = sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / "share/pdk")
for name, proc, case in (("slow125", "SLOW", 0), ("typ125", "TYP", 1)):
    r = g.build()["divider_corner_speed.request.json"]
    r["corners"]["process"] = [p for p in r["corners"]["process"] if p["name"] == proc]
    r["corners"]["temperature_c"] = [125]
    r["corners"]["params"] = {k: v[case:case + 1] for k, v in r["corners"]["params"].items()}
    r["analysis"]["args"] = "20p 30n 0 20p"
    r["options"].update(keep_artifacts=True, waveforms=True, timeout_s=300)
    r["options"]["osdi_preload"] = [p.replace("$PDK_ROOT", root) for p in r["options"]["osdi_preload"]]
    out = Path(__file__).resolve().parent / f"hot_trace_{name}.request.json"
    out.write_text(json.dumps(r, indent=2) + "\n")
    print("wrote", out.name)
