#!/usr/bin/env python3
"""Estimators for the G2 bench (stdlib only; run as `python3 -I analyze.py <outdir>`).

Reads wrdata files written by ngspice (tran_<tag>_<vctrl>, ac_<tag>; an optional ".data" suffix is accepted,
ngspice-46 writes none) and prints one JSON object.

Transient estimators (v = v(OUTP) - v(OUTN), window 10-20 ns, after startup):
  f_ghz      rising crossings of the window mean, (N-1) / span between first and last crossing
  vpp        peak-to-peak over the window
  t90_ns     first time a half-cycle peak-to-peak envelope reaches 90 % of vpp (startup time from the deck's
             10 mV .ic kick)
AC estimator (differential current probe, 1 A): f_res = frequency of max |Z|, z_peak_ohm = that |Z|. Only the pull
of the load on this resonance is used; no loss or gain is read from it.
"""
import json
import math
import os
import sys

WIN0, WIN1 = 10e-9, 20e-9


def read_cols(path):
    for p in (path, path + ".data"):
        if os.path.isfile(p) and os.path.getsize(p) > 0:
            with open(p) as fh:
                return [[float(x) for x in ln.split()] for ln in fh if ln.strip()]
    return None


def tran_metrics(rows):
    if not rows:
        return None
    t = [r[0] for r in rows]
    v = [r[1] for r in rows]
    if any(math.isnan(x) for x in v):
        return None
    w = [(a, b) for a, b in zip(t, v) if WIN0 <= a <= WIN1]
    if len(w) < 10:
        return None
    mean = sum(b for _, b in w) / len(w)
    vpp = max(b for _, b in w) - min(b for _, b in w)
    xs = []
    for (t0, v0), (t1, v1) in zip(w, w[1:]):
        if v0 < mean <= v1 and v1 != v0:
            xs.append(t0 + (mean - v0) * (t1 - t0) / (v1 - v0))
    f = (len(xs) - 1) / (xs[-1] - xs[0]) / 1e9 if len(xs) >= 2 else None
    # half-cycle extrema of the whole run (local maxima/minima of the sampled wave, alternating)
    ext = []
    for i in range(1, len(v) - 1):
        if (v[i] > v[i - 1] and v[i] >= v[i + 1]) or (v[i] < v[i - 1] and v[i] <= v[i + 1]):
            ext.append((t[i], v[i]))
    half = [(ext[i + 1][0], abs(ext[i + 1][1] - ext[i][1])) for i in range(len(ext) - 1)]
    t90 = next((a * 1e9 for a, h in half if vpp > 0 and h >= 0.9 * vpp), None)
    return {"f_ghz": f, "vpp": vpp, "t90_ns": t90, "cycles": len(xs) - 1 if xs else 0}


def ac_metrics(rows):
    if not rows:
        return None
    best = None
    for r in rows:
        f, re, im = r[0], r[1], r[2]
        mag = math.hypot(re, im)
        if best is None or mag > best[0]:
            best = (mag, f, re, im)
    mag, f, re, im = best
    return {"f_res_ghz": f / 1e9, "z_peak_ohm": mag}


def main(outdir):
    res = {}
    for tag in ("unloaded", "loaded"):
        res[tag] = {"ac": ac_metrics(read_cols(os.path.join(outdir, "ac_" + tag)))}
        for vc in ("0", "1.65", "3.3"):
            res[tag]["tran_" + vc] = tran_metrics(read_cols(os.path.join(outdir, "tran_%s_%s" % (tag, vc))))
    json.dump(res, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main(sys.argv[1])
