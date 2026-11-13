#!/usr/bin/env python3
"""Estimator for the method T cost bench (sim/jitter, gate G6): TIE of the divided-down FB clock.

Usage: jitter_t_analyze.py DATA T_REF_S SETTLE_S WINDOW_S [WINDOW_S ...]
DATA columns (ngspice wrdata, wr_singlescale): time v(fb). Prints one JSON object. Standard library only.

Estimator (each is written into the record next to the numbers):
  edges      rising crossings of 1.65 V of v(fb), linear interpolation between samples.
  TIE        per window of length W (non-overlapping, starting at SETTLE_S): edge times t_k against the edge
             index k, least-squares line removed (static phase offset and mean period absorbed), residual in s.
  sigma_W    rms of that residual in one window. Over K = floor((t_end - SETTLE_S)/W) windows report the mean of
             sigma_W, the standard deviation across windows, and the relative standard error of the mean
             (std/mean/sqrt(K)): the Welch-style variance of spec section 4, per W. K < 2 gives no variance.
Not a phase-noise or jitter RESULT: the noise level is a placeholder, see the record.
"""
import json
import math
import sys

path, t_ref, settle = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
windows = [float(w) for w in sys.argv[4:]]
t, v = [], []
with open(path) as fh:
    for line in fh:
        p = line.split()
        if len(p) < 2:
            continue
        a, b = float(p[0]), float(p[1])
        if not (math.isfinite(a) and math.isfinite(b)):
            print(json.dumps({"error": "non-finite samples"})); sys.exit(2)
        t.append(a); v.append(b)
if len(t) < 100:
    print(json.dumps({"error": "short or malformed data", "samples": len(t)})); sys.exit(2)
edges = [t[i] + (1.65 - v[i]) / (v[i + 1] - v[i]) * (t[i + 1] - t[i]) for i in range(len(t) - 1) if v[i] < 1.65 <= v[i + 1]]
out = {"samples": len(t), "t_end_s": t[-1], "fb_edges": len(edges), "windows": []}
for w in windows:
    n_win = int((t[-1] - settle) // w)
    sig = []
    for k in range(n_win):
        a, b = settle + k * w, settle + (k + 1) * w
        e = [x for x in edges if a <= x < b]
        if len(e) < 10:
            continue
        idx = list(range(len(e)))
        mi, me = sum(idx) / len(e), sum(e) / len(e)
        sxx = sum((i - mi) ** 2 for i in idx)
        slope = sum((i - mi) * (x - me) for i, x in zip(idx, e)) / sxx
        res = [x - (me + slope * (i - mi)) for i, x in zip(idx, e)]
        sig.append(math.sqrt(sum(r * r for r in res) / (len(res) - 2)))
    row = {"window_s": w, "windows_available": n_win, "windows_used": len(sig)}
    if sig:
        m = sum(sig) / len(sig)
        row["sigma_mean_s"] = m
        if len(sig) >= 2:
            sd = math.sqrt(sum((x - m) ** 2 for x in sig) / (len(sig) - 1))
            row["sigma_std_s"] = sd
            row["rel_std_err"] = sd / m / math.sqrt(len(sig))
    out["windows"].append(row)
print(json.dumps(out))
