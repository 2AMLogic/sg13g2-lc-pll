#!/usr/bin/env python3
"""Issue #97: the probe-1 request of make_forced_probe_97.py (same forcing, same nodes, same window) at FAST and TYP
125 C 2.97 V, so the D-settle phase of analyze_setup_phase_97.py can be compared with SLOW 125 C 2.97 V. Bench only."""
import json
base = json.load(open("request-forcedprobe-97-SLOW-125-2.97.json"))
for proc in ("FAST", "TYP"):
    s = json.load(open(f"request-stage2-97-s-{proc}-125-2.97.json"))
    r = dict(base)
    r["corners"] = s["corners"]
    r["_comment"] = base["_comment"][:4] + [f"Issue #97 probed forced-state trial, {proc} 125 C 2.97 V, same forcing and probes as the SLOW run."]
    json.dump(r, open(f"request-forcedprobe-97-{proc}-125-2.97.json", "w"), indent=1)
