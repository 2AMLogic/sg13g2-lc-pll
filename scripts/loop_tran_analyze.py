#!/usr/bin/env python3
"""Analyse a sim/loop-tran transient: lock time (spec row 10) and reference spur (row 9).

Usage: loop_tran_analyze.py DATA N F0 VC0 KV_SIGNED F_REF_HZ
DATA columns (ngspice wrdata, wr_singlescale): time v(ref) v(fb) v(vctrl) v(vcp) i(VDD).
Prints one JSON object. Standard library only (no numpy: the worker has none).

Estimators (each is written into the record next to the number):
  edges      rising crossings of 1.65 V, linear interpolation between samples.
  phase err  per REF rising edge, t_FB - t_REF to the nearest FB rising edge, wrapped to +-T_ref/2.
  freq err   per reference period, f_out = F0 + KV*(mean Vctrl over that period - VC0) (the stand-in line)
             minus 5.0 GHz; no edge counting, so no timing noise in it.
  lock time  the first REF edge after the last period in which the violation holds. Two readings of spec
             row 10 are reported: OR (|f err| > 1 MHz or |phase err| > 5 % T_ref: strict) and AND (both:
             the row's literal wording).
  spur       Vctrl over the LAST 40 reference periods (20 ps uniform resample), linear trend removed,
             coherent Fourier component at f_ref (peak V_r); dBc = 20 log10(KV V_r / (2 f_ref))
             (small-index FM, spec row 9).
"""
import bisect
import cmath
import json
import math
import sys

data_path = sys.argv[1]
n_div, f0, vc0, kv, f_ref = int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
t_ref = 1.0 / f_ref
t, vref, vfb, vct, idd = [], [], [], [], []
with open(data_path) as fh:
    for line in fh:
        p = line.split()
        if len(p) < 6:
            continue
        x = [float(s) for s in p[:6]]
        if not all(math.isfinite(v) for v in x):
            print(json.dumps({"error": "non-finite samples"}))
            sys.exit(2)
        t.append(x[0]); vref.append(x[1]); vfb.append(x[2]); vct.append(x[3]); idd.append(x[5])
if len(t) < 1000:
    print(json.dumps({"error": "short or malformed data", "samples": len(t)}))
    sys.exit(2)


def rising(v, level=1.65):
    out = []
    for i in range(len(v) - 1):
        if v[i] < level <= v[i + 1]:
            out.append(t[i] + (level - v[i]) / (v[i + 1] - v[i]) * (t[i + 1] - t[i]))
    return out


def interp(x, xs, ys):
    j = min(max(bisect.bisect_right(xs, x) - 1, 0), len(xs) - 2)
    return ys[j] + (ys[j + 1] - ys[j]) * (x - xs[j]) / (xs[j + 1] - xs[j])


er, ef = rising(vref), rising(vfb)
if len(er) < 100 or len(ef) < 100:
    print(json.dumps({"error": "too few edges", "ref_edges": len(er), "fb_edges": len(ef)}))
    sys.exit(2)
k = len(er) - 1
pe = []
for i in range(k):
    j = bisect.bisect_left(ef, er[i])
    c = [ef[m] - er[i] for m in (j - 1, j) if 0 <= m < len(ef)]
    pe.append(min(c, key=abs))
cum = [0.0]
for i in range(len(t) - 1):
    cum.append(cum[-1] + 0.5 * (vct[i] + vct[i + 1]) * (t[i + 1] - t[i]))
ci = [interp(e, t, cum) for e in er]
vmean = [(ci[i + 1] - ci[i]) / (er[i + 1] - er[i]) for i in range(k)]
ferr = [kv * (v - vc0) for v in vmean]  # Hz vs 5.0 GHz
viol_or = [abs(ferr[i]) > 1e6 or abs(pe[i]) > 0.05 * t_ref for i in range(k)]
viol_and = [abs(ferr[i]) > 1e6 and abs(pe[i]) > 0.05 * t_ref for i in range(k)]


def lock_time(viol):
    bad = [i for i, b in enumerate(viol) if b]
    if not bad:
        return er[0]
    j = bad[-1] + 1
    return er[j] if j < k else None


tl_or, tl_and = lock_time(viol_or), lock_time(viol_and)
tstop = t[-1]
res = {"n_div": n_div, "tstop_s": tstop, "samples": len(t), "ref_edges": len(er), "fb_edges": len(ef),
       "lock_time_or_s": tl_or, "lock_time_and_s": tl_and, "vctrl_start_v": vct[0], "vctrl_end_v": vct[-1]}
pa = None if tl_or is None else int((tstop - tl_or) // t_ref)
res["periods_after_lock_or"] = pa
res["locked"] = bool(pa is not None and pa >= 41)
tr = []
tt = 0.0
while tt < tstop:
    j = min(bisect.bisect_left(er, tt), k - 1)
    tr.append({"t_us": round(tt * 1e6, 1), "vctrl_v": round(interp(tt, t, vct), 4),
               "phase_err_ps": round(pe[j] * 1e12, 1), "f_err_mhz": round(ferr[j] / 1e6, 3)})
    tt += 2e-6
res["trace"] = tr
if res["locked"]:
    t0, t1 = er[-41], er[-1]
    n = int((t1 - t0) / 20e-12)
    tg = [t0 + i * 20e-12 for i in range(n)]
    v = [interp(x, t, vct) for x in tg]
    tw = [x - t0 for x in tg]
    mt, mv = sum(tw) / n, sum(v) / n
    slope = sum((a - mt) * (b - mv) for a, b in zip(tw, v)) / sum((a - mt) ** 2 for a in tw)
    vd = [b - mv - slope * (a - mt) for a, b in zip(tw, v)]
    w = 2 * math.pi * 40 / (n * 20e-12)
    vr = 2.0 / n * abs(sum(x * cmath.exp(-1j * w * a) for x, a in zip(vd, tw)))
    res["spur"] = {"window_s": [t0, t1], "periods": 40, "vr_peak_v": vr, "delta_f_peak_hz": abs(kv) * vr,
                   "spur_dbc": 20 * math.log10(max(abs(kv) * vr, 1e-30) / (2 * f_ref)),
                   "vctrl_mean_v": mv, "vctrl_pp_v": max(vd) - min(vd)}
    # supply current over the same window (trapezoid)
    i0, i1 = bisect.bisect_left(t, t0), bisect.bisect_right(t, t1)
    q = sum(0.5 * (idd[i] + idd[i + 1]) * (t[i + 1] - t[i]) for i in range(i0, i1 - 1))
    iavg = q / (t[i1 - 1] - t[i0])
    res["supply"] = {"i_vdd_mean_a": iavg, "p_w": abs(iavg) * 3.3}
    res["phase_err_final_ps"] = sum(pe[-40:]) / 40 * 1e12
json.dump(res, sys.stdout, indent=1)
print()
