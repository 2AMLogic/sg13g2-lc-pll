#!/usr/bin/env python3
"""Speed check of the divider at the prescaler output rates, from the divider_speed wrdata file.
usage: divider_speed_counts.py REAL CTRL   (default: real-625 / real-687.5 from the divider_speed wrdata file REAL, ideal-clk-625 / ideal-clk-687.5
       from the divider_speedC wrdata file CTRL; each file is (t, v) pairs for ck mc fb x 2 cases and has its own adaptive time axis)
       divider_speed_counts.py DATA A      (A-code deck divider_speedA: ck mc fb x 4 cases in one file)
Per case prints: CASE FB_RISES CK_PER_WINDOW MC_HIGH N WANT   (N = 8*clocks + mc_high (P = 8/9) over the last full FB window),
or "no-toggle" when FB has fewer than 3 rising edges (fewer than 2 full windows). Exit 0 only if all four cases
divide to their expected N (100 at A = 4, 96 at A = 0, 103 at A = 7) on every full window; exit 1 otherwise (output is still printed, for the record)."""
import sys
# each group is (data file, ((case name, expected N = 8*M + A), ...)); cases are numbered within their own file
if len(sys.argv) == 3 and sys.argv[2] == "A":   # divider_speedA deck: M = 12, A = 0 and A = 7, real chain
    GROUPS = ((sys.argv[1], (("real-A0-625", 96), ("real-A0-687.5", 96), ("real-A7-625", 103), ("real-A7-687.5", 103))),)
elif len(sys.argv) == 3:
    GROUPS = ((sys.argv[1], (("real-625", 100), ("real-687.5", 100))), (sys.argv[2], (("ideal-clk-625", 100), ("ideal-clk-687.5", 100))))
else:
    sys.exit(__doc__)
def load(path):
    rows = [list(map(float, l.split())) for l in open(path) if l.strip()]
    if not rows:
        sys.exit(f"divider_speed_counts: empty data {path}")
    return rows
def col(rows, k, j):                # wrdata layout: (t, v) pair per signal
    return [r[2 * (3 * k + j) + 1] for r in rows]
def rises(t, v, th=1.65):
    return [t[i-1] + (th - v[i-1]) / (v[i] - v[i-1]) * (t[i] - t[i-1]) for i in range(1, len(v)) if v[i-1] < th <= v[i]]
def before(t, v, tt):
    for i in range(len(t)):
        if t[i] >= tt:
            return v[max(i - 1, 0)]
    return v[-1]
ok = True
for path, cases in GROUPS:
    rows = load(path)
    t = [r[0] for r in rows]
    for k, (name, want) in enumerate(cases):
        ck, mc, fb = col(rows, k, 0), col(rows, k, 1), col(rows, k, 2)
        f = rises(t, fb)
        if len(f) < 3:
            print(f"{name} {len(f)} no-toggle - - - {want}"); ok = False; continue
        c = rises(t, ck); ns = set(); last = None
        for a, b in zip(f, f[1:]):
            e = [x for x in c if a <= x < b]
            hi = sum(1 for x in e if before(t, mc, x - 0.3e-9) > 1.65)
            ns.add(8 * len(e) + hi); last = (len(e), hi)
        n = ns.pop() if len(ns) == 1 else -1
        ok &= (n == want)
        print(f"{name} {len(f)} {last[0]} {last[1]} {n if n >= 0 else 'inconsistent'} {want}")
sys.exit(0 if ok else 1)
