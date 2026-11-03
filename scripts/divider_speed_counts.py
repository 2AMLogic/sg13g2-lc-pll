#!/usr/bin/env python3
"""Speed check of the divider at the prescaler output rates, from the divider_speed wrdata file.
usage: divider_speed_counts.py DATA   (wrdata pairs t,v for: ck mc fb x 4 cases; see divider_speed.spice.tmpl)
Per case prints: CASE FB_RISES CK_PER_WINDOW MC_HIGH N   (N = 8*clocks + 2*mc_high over the last full FB window),
or "no-toggle" when FB has fewer than 3 rising edges (fewer than 2 full windows). Exit 0 only if all four cases
divide N = 100 on every full window; exit 1 otherwise (output is still printed, for the record)."""
import sys
CASES = ("real-625", "real-687.5", "ideal-clk-625", "ideal-clk-687.5")
rows = [list(map(float, l.split())) for l in open(sys.argv[1]) if l.strip()]
if not rows:
    sys.exit("divider_speed_counts: empty data")
t = [r[0] for r in rows]
def col(k, j):                      # wrdata layout: (t, v) pair per signal
    return [r[2 * (3 * k + j) + 1] for r in rows]
def rises(v, th=1.65):
    return [t[i-1] + (th - v[i-1]) / (v[i] - v[i-1]) * (t[i] - t[i-1]) for i in range(1, len(v)) if v[i-1] < th <= v[i]]
def before(v, tt):
    for i in range(len(t)):
        if t[i] >= tt:
            return v[max(i - 1, 0)]
    return v[-1]
ok = True
for k, name in enumerate(CASES):
    ck, mc, fb = col(k, 0), col(k, 1), col(k, 2)
    f = rises(fb)
    if len(f) < 3:
        print(f"{name} {len(f)} no-toggle - - -"); ok = False; continue
    c = rises(ck); ns = set(); last = None
    for a, b in zip(f, f[1:]):
        e = [x for x in c if a <= x < b]
        hi = sum(1 for x in e if before(mc, x - 0.3e-9) > 1.65)
        ns.add(8 * len(e) + 2 * hi); last = (len(e), hi)
    n = ns.pop() if len(ns) == 1 else -1
    ok &= (n == 100)
    print(f"{name} {len(f)} {last[0]} {last[1]} {n if n >= 0 else 'inconsistent'}")
sys.exit(0 if ok else 1)
