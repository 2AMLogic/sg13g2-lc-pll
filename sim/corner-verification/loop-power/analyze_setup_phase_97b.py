#!/usr/bin/env python3
"""Issue #97: D-input phase after the launching clock rise for FAST and TYP 125 C 2.97 V (the corners compared with
SLOW by analyze_setup_phase_97.py). Reads records/20261105-issue97-fast-typ-125c-setup-phase-measurements.json only."""
import bisect, json, re
src = json.load(open("records/20261105-issue97-fast-typ-125c-setup-phase-measurements.json"))
res = {}
for p, o in src.items():
    ev = {}
    for k, v in o["probe1_td_14ns"].items():
        m = re.match(r"(\w+?)_([rf])(\d+)$", k)
        if m and v is not None:
            ev.setdefault((m[1], m[2]), []).append(v * 1e9)
    ck = sorted(ev[("ckl", "r")]); tmax = ck[-1]
    rr = {n: sorted(round(t - ck[bisect.bisect_right(ck, t) - 1], 2) for e in "rf"
                    for t in ev.get((n, e), []) if 20.5 <= t <= tmax)
          for n in ("d0", "d1", "d2", "d3", "db1", "db2", "db3", "dt", "dtn")}
    res[p] = {"phase_after_launch_ns": rr, "period_ns": round((ck[-1] - ck[0]) / (len(ck) - 1), 3)}
    print(p, res[p])
json.dump(res, open("records/20261105-issue97-fast-typ-125c-setup-phase-analysis.json", "w"), indent=1)
