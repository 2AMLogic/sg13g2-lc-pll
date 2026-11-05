#!/usr/bin/env python3
"""Issue #97: place the D-input transitions of the SLOW 125 C 2.97 V probed forced-state run (probe 1, 14 ns+) against
the clock edge that launched them. Reads only the already-recorded crossings in
records/20261105-issue97-slow-125c-forced-state-probed-measurements.json (no new simulation). Prints, per D node, the
phase (ns) of each transition after the last ckl rise, for transitions after release (>= 20.5 ns) and within the
recorded ckl window. A phase close to the clock period means the node settles at the next capture edge."""
import bisect, json, re
d = json.load(open("records/20261105-issue97-slow-125c-forced-state-probed-measurements.json"))["probe1_td_14ns"]
ev = {}
for k, v in d.items():
    m = re.match(r"(\w+?)_([rf])(\d+)$", k)
    if m and v is not None:
        ev.setdefault((m[1], m[2]), []).append(v * 1e9)
ck = sorted(ev[("ckl", "r")])
tmax = ck[-1]
res = {}
for n in ("d0", "d1", "d2", "d3", "db1", "db2", "db3", "dt", "dtn"):
    ph = []
    for e in "rf":
        for t in ev.get((n, e), []):
            if 20.5 <= t <= tmax:
                ph.append(round(t - ck[bisect.bisect_right(ck, t) - 1], 2))
    res[n] = sorted(ph)
    print(n, res[n])
print("ckl rises", len(ck), "last", round(tmax, 2), "period", round((ck[-1] - ck[0]) / (len(ck) - 1), 3))
json.dump({"phase_after_launch_ns": res, "period_ns": round((ck[-1] - ck[0]) / (len(ck) - 1), 3)},
          open("records/20261105-issue97-slow-125c-setup-phase-analysis.json", "w"), indent=1)
