#!/usr/bin/env python3
"""Issue #97: phase of each DT-decode node transition after the launching ckl rise (SLOW 125 C 2.97 V, forced state
released at 20 ns). Reads the saved report.json crossings only; writes records/20261106-issue97-dt-gate-probe-*.json."""
import bisect, json, re, sys
rep = json.load(open(sys.argv[1]))
def find(o):
    if isinstance(o, dict):
        if isinstance(o.get("measurements"), list): return o["measurements"]
        for v in o.values():
            x = find(v)
            if x is not None: return x
    if isinstance(o, list):
        for v in o:
            x = find(v)
            if x is not None: return x
raw = {m["name"]: m["worst_case"]["value"] for m in find(rep) if m.get("worst_case") and m["worst_case"].get("value") is not None}
ev = {}
for k, v in raw.items():
    n, e, i = re.match(r"(\w+?)_([rf])(\d+)$", k).groups()
    ev.setdefault((n, e), []).append(v * 1e9)
ck = sorted(ev[("ckl", "r")]); tmax = ck[-1]
out = {"period_ns": round((ck[-1] - ck[0]) / (len(ck) - 1), 3), "n_ckl_rises": len(ck), "phase_after_launch_ns": {}}
for n in ("q0", "q1", "q1n", "q2", "q3", "f32", "g10", "dtn", "dt", "tc"):
    out["phase_after_launch_ns"][n] = sorted((round(t - ck[bisect.bisect_right(ck, t) - 1], 2), e, round(t, 2))
                                            for e in "rf" for t in ev.get((n, e), []) if 20.5 <= t <= tmax)
    print(n, out["phase_after_launch_ns"][n])
print(out["period_ns"], out["n_ckl_rises"])
json.dump({"raw_crossings_s": raw, "analysis": out}, open(sys.argv[2], "w"), indent=1)
