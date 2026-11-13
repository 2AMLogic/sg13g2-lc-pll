#!/usr/bin/env python3
"""Count N per FB window for the local divider decks and grade it against the expected N.

usage: divider_speed_counts.py REAL CTRL     (speed decks: real-625 / real-687.5 from the divider_speed wrdata file REAL,
       ideal-clk-625 / ideal-clk-687.5 from the divider_speedC wrdata file CTRL; each file is (t, v) pairs for ck mc fb x 2
       cases and has its own adaptive time axis)
       divider_speed_counts.py DATA A        (A-code deck divider_speedA: ck mc fb x 4 cases in one file)
       divider_speed_counts.py DATA COUNT    (relaxed-clock count deck divider_tran, issue #236: one SHARED ck column, then
       mc fb for N = 100 and N = 90, so the column map is per case and not 3 x case)

N = 8 x clocks + mc_high (prescaler P = 8/9, issue #158) over an FB window, where a window is the interval between
consecutive rising FB edges, clocks are the rising CK edges in it, and mc_high counts those clocks where MC was high
0.3 ns before the edge.

Window rule, the same for every deck here: every full window is graded, and at least 3 rising FB edges (2 full windows)
are required. `sim/divider-elab/divider_corner_record.py` grades the `klt sim` corner runs of the same circuit under a
DIFFERENT rule -- first full window reported but not graded, >= 4 FB edges -- and the reason is in the decks, not in the
rule: `sim/divider-elab/divider_corner.cir` ramps VDD, IREF and the input common mode from 0 V over 3 ns, so FB crosses
the 1.65 V threshold once on the way up and that spurious edge opens a start-up window. The local decks hold all three
at their final values from t = 0 and solve a DC operating point, so FB sits at a settled logic level and the first
rising FB edge is a real counter reload. Keep the two rules in step if either deck family's start-up changes.

Speed modes print one line per case, over the LAST full window:
  CASE FB_RISES CK_PER_WINDOW MC_HIGH N WANT      (N is "inconsistent" when the full windows disagree)
COUNT mode prints one line per full window, so the record keeps its per-window table:
  CASE FBWINDOW_NS CK_PER_WINDOW MC_HIGH N WANT
A case with fewer than 3 FB rises prints "CASE FB_RISES no-toggle - - WANT" in place of the per-window numbers, and fails.

Exit 0 only if every case divides to its expected N on every full window; exit 1 otherwise (the output is still
printed, for the record). Expected N: at M = 12, 100 at A = 4, 96 at A = 0, 103 at A = 7; 90 at M = 11, A = 2.
"""
import sys

TH = 1.65        # CMOS logic threshold at VDD = 3.3 V, the same threshold the corner crossings use
LEAD = 0.3e-9    # MC is sampled this far before each CK edge
MIN_FB = 3       # at least 2 full windows

# a case is (name, expected N = 8 M + A, (ck, mc, fb) signal indices within its own data file)
SPEED = (("real-625", 100), ("real-687.5", 100))
CTRL = (("ideal-clk-625", 100), ("ideal-clk-687.5", 100))
ACODE = (("real-A0-625", 96), ("real-A0-687.5", 96), ("real-A7-625", 103), ("real-A7-687.5", 103))
# divider_tran writes v(xd100.ck) v(mc100) v(fb100) v(mc90) v(fb90): one clock, shared by both codes
COUNT = (("N100", 100, (0, 1, 2)), ("N90", 90, (0, 3, 4)))


def lanes(cases):   # the speed decks: ck mc fb per case, cases numbered within their own file
    return tuple((name, want, (3 * k, 3 * k + 1, 3 * k + 2)) for k, (name, want) in enumerate(cases))


if len(sys.argv) == 3 and sys.argv[2] == "A":
    GROUPS, PER_WINDOW = ((sys.argv[1], lanes(ACODE)),), False
elif len(sys.argv) == 3 and sys.argv[2] == "COUNT":
    GROUPS, PER_WINDOW = ((sys.argv[1], COUNT),), True
elif len(sys.argv) == 3:
    GROUPS, PER_WINDOW = ((sys.argv[1], lanes(SPEED)), (sys.argv[2], lanes(CTRL))), False
else:
    sys.exit(__doc__)


def load(path):
    rows = [list(map(float, l.split())) for l in open(path) if l.strip()]
    if not rows:
        sys.exit(f"divider_speed_counts: empty data {path}")
    return rows


def col(rows, s):                   # wrdata layout: a (t, v) pair per signal, all on one time axis per file
    return [r[2 * s + 1] for r in rows]


def rises(t, v, th=TH):
    return [t[i-1] + (th - v[i-1]) / (v[i] - v[i-1]) * (t[i] - t[i-1]) for i in range(1, len(v)) if v[i-1] < th <= v[i]]


def before(t, v, tt):
    for i in range(len(t)):
        if t[i] >= tt:
            return v[max(i - 1, 0)]
    return v[-1]


def windows(t, ck, mc, fb):         # (a, b, clocks, mc_high, N) per full FB window
    c = rises(t, ck)
    out = []
    for a, b in zip(fb, fb[1:]):
        e = [x for x in c if a <= x < b]
        hi = sum(1 for x in e if before(t, mc, x - LEAD) > TH)
        out.append((a, b, len(e), hi, 8 * len(e) + hi))
    return out


ok = True
for path, cases in GROUPS:
    rows = load(path)
    t = [r[0] for r in rows]
    for name, want, (ick, imc, ifb) in cases:
        f = rises(t, col(rows, ifb))
        if len(f) < MIN_FB:
            print(f"{name} {len(f)} no-toggle - - {want}")
            ok = False
            continue
        w = windows(t, col(rows, ick), col(rows, imc), f)
        ok &= all(n == want for *_, n in w)
        if PER_WINDOW:
            for a, b, clocks, hi, n in w:
                print(f"{name} {a*1e9:.0f}-{b*1e9:.0f} {clocks} {hi} {n} {want}")
        else:
            n = w[-1][4] if len({x[4] for x in w}) == 1 else None
            print(f"{name} {len(f)} {w[-1][2]} {w[-1][3]} {n if n is not None else 'inconsistent'} {want}")
sys.exit(0 if ok else 1)
