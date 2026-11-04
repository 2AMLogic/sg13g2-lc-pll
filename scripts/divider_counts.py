#!/usr/bin/env python3
"""Count clocks per FB period and clocks with MC high from the divider_tran wrdata file.
usage: divider_counts.py DATA   (columns: t ck, t mc100, t fb100, t mc90, t fb90)
Prints one line per FB window: CODE FBWINDOW_NS CK_CYCLES MC_HIGH N (N = 8*cycles + 2*mc_high)."""
import sys
rows = [list(map(float, l.split())) for l in open(sys.argv[1]) if l.strip()]
t = [r[0] for r in rows]
def rises(i, th=1.65):
    out = []
    for k in range(1, len(rows)):
        if rows[k-1][i] < th <= rows[k][i]:
            out.append(t[k-1] + (th - rows[k-1][i]) / (rows[k][i] - rows[k-1][i]) * (t[k] - t[k-1]))
    return out
def before(i, tt):
    for k in range(len(t)):
        if t[k] >= tt:
            return rows[max(k-1, 0)][i]
    return rows[-1][i]
ck = rises(1)
if len(ck) < 10:
    sys.exit("divider_counts: clock never toggled")
for name, mc, fb in (("N100", 3, 5), ("N90", 7, 9)):
    f = rises(fb)
    for a, b in zip(f, f[1:]):
        e = [x for x in ck if a <= x < b]
        hi = sum(1 for x in e if before(mc, x - 0.3e-9) > 1.65)
        print(f"{name} {a*1e9:.0f}-{b*1e9:.0f} {len(e)} {hi} {8*len(e)+2*hi}")
