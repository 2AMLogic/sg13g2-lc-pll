#!/usr/bin/env python3
"""Render the dated sim/cp-mc record (markdown, stdout) from the klt sim reports and klt yield JSON (stdlib only)."""
import argparse, json, re, collections, os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
import ngpin  # noqa: E402  (the simulator pin check, computed once in sim/ngpin.py)

ap = argparse.ArgumentParser()
for a in ("nominal", "negative", "yield_target", "yield_fallback"):
    ap.add_argument(a)
for a in ("id", "commit", "pdk_tag", "host", "klt"):
    ap.add_argument("--" + a.replace("_", "-"), required=True)
for a in ("n", "n_control", "seed"):
    ap.add_argument("--" + a.replace("_", "-"), required=True, type=int)
a = ap.parse_args()
nom = json.load(open(a.nominal)); neg = json.load(open(a.negative))
yt = {m["name"]: m for m in json.load(open(a.yield_target))["measurements"]}
yf = {m["name"]: m for m in json.load(open(a.yield_fallback))["measurements"]}
env = nom["environment"]; rem = env.get("remote") or {}; remn = {}

def ci(m, k="empirical"):
    y = m["yield"][k]; c = y["confidence_interval"]
    return "%.4f [%.4f, %.4f]" % (y["estimate"], c["low"], c["high"])

# per originating corner: sample count, max value, and count over the target limit
LIM = {"mm": 2.0, "vr": 0.52}
percorner = collections.defaultdict(lambda: collections.defaultdict(list))
for c in nom["corners"]:
    cid = re.sub(r"/mc\d+$", "", c["corner_id"])
    for m in c["measurements"]:
        if m["name"][:2] in LIM and m.get("value") is not None:
            percorner[m["name"]][cid].append(m["value"])
names = sorted(yt, key=lambda s: (s[:2] != "mm", s))
print("# cp-mc run %s\n" % a.id)
bad = [n for n in names if yt[n]["status"] != "pass"]
print("**Result (simulated, not measured; Monte Carlo of per-instance device mismatch only).** Pooled over the %d-corner grid at %d samples per corner, `klt yield` status against the row-7 / row-9 **target** limits is `%s`; per-measurement numbers are in the tables. **Spec row 7 is NOT closed:** V_hi,req is unresolved (gate G4), so the upper compliance edge is not pinned; the V_out points below are probes, not the requirement. **Spec row 9 is NOT closed:** only the CP-mismatch to reference-ripple contribution is covered here, not the locked-loop spur (method T).\n"
      % (len(percorner[names[0]]), a.n, "fail" if bad else "pass"))
print("- **Method**: `klt sim` Monte Carlo (`vary: mismatch`, seed %d, n = %d per corner, %d corners), `ngspice` `op` steps on ONE instance of `cp` (design/netlist/cp.spice, drift-checked against design/cp.sch), per sample UP-on/DN-off then DN-on/UP-off at each V_out, so I_up and I_dn share one mismatch draw. mismatch %% = |I_up - I_dn| / 200 uA x 100 (static DC; no switching, charge sharing or pulse-width effect). Ripple vr = 2 |I_up - I_dn| (t_rst/T_ref = 0.1, a stated DR-001 allowance, not derived) |Z_filter(50 MHz)| (83.10 ohm from sim/loop-model/loop-filter.json, unloaded R3-C3 pole included): first-harmonic ripple from the mismatch only. Spur in dBc is not computed here." % (a.seed, a.n, len(percorner[names[0]])))
print("- **Estimator**: `klt yield` (%s), Clopper-Pearson empirical yield, 95 %% confidence; limits `sim/cp-mc/limits-target.json` (row 7: 2 %%; row 9: 0.52 mV peak) and `limits-fallback.json` (6 %%; -40 dBc = 1.644 mV). `target_yield` 0.9973 (3 sigma) is **this campaign's choice; the ratified spec states no yield target.**" % a.klt)
print("- **Pooling caveat**: the estimate pools all %d corners with equal weight, a worst-case envelope and not one distribution (klt yield warns of this); the per-corner table gives the worst single corner." % len(percorner[names[0]]))
print("- **Corners**: MOS {tt,ss,ff,sf,fs} x T {-40,27,125} C at 3.300 V (15) + {SLOW=ss, TYP=tt, FAST=ff} x {2.970, 3.630} V x T (18) = 33; every point uses the `mos_*_mismatch` section of cornerMOShv.lib. The CP has no MIM or HBT, so those stage-1 axes do not apply. Stage 3 (405-point cross) not run.")
print("- **Negative control**: same grid and seed, n = %d per corner, up-leg mirror+cascode widened 3.8u->4.6u (about +20 %% I_up; the skew of scripts/test-cp-dc-negative.sh); `klt yield-samples` derives the control from the two unedited reports." % a.n_control)
print("- **Backend**: batch fleet. sharded into batch jobs of at most 696 units (job ids in the `klt sim` stderr files beside this record; the fleet launched them over several `--resume` passes because of capacity limits); engine %s on `%s`, %s (`scripts/lib-pdk.sh` applies the same check to the local binary). A 2-sample batch probe reproduced the local values bit for bit." % (ngpin.engine(env.get("engine_version")), env.get("engine_host"), ngpin.verdict(env.get("engine_version"))))
print("- **PDK**: IHP-Open-PDK %s, libraries staged to the worker (`options.stage_model_inputs`); psp103.osdi from the pinned PDK. Note sim/pins.json hashes cornerMOShv.lib but not its `sg13g2_moshv_*mismatch.lib` includes; the staged-input sha256s are in the nominal report's `environment.staged_model_inputs`." % a.pdk_tag)
print("- **Commit**: `%s` (the tree was uncommitted when this ran: the bench files were new); **Host**: %s; run id %s\n" % (a.commit, a.host, a.id))
print("## Pooled yield, target limits (row 7: mismatch <= 2 %; row 9 contribution: ripple <= 0.52 mV)\n")
print("| measurement | n | mean | sigma | max | yield (empirical, 95 % CI) | yield, fallback limit | sample size | negative control |")
print("|---|---|---|---|---|---|---|---|---|")
for n in names:
    m = yt[n]; d = m["distribution"]; nc = m.get("negative_control") or {}
    print("| %s (%s) | %d | %.4g | %.3g | %.4g | %s | %s | %s | %s |" % (n, m.get("unit", ""), m["n"], d["mean"], d["stddev"], d["max"], ci(m), ci(yf[n]), m["sample_size"]["verdict"], nc.get("verdict")))
print("\n## Worst single corner (per originating corner, %d samples each)\n" % a.n)
print("| measurement | limit | worst corner by max | max there | corners with any sample over limit | worst failure count |")
print("|---|---|---|---|---|---|")
for n in names:
    lim = LIM[n[:2]]; pc = percorner[n]
    wc = max(pc, key=lambda c: max(pc[c]))
    over = {c: sum(v > lim for v in vs) for c, vs in pc.items()}
    anyover = [c for c, k in over.items() if k]
    print("| %s | %g | %s | %.4g | %d of %d | %d of %d |" % (n, lim, wc, max(pc[wc]), len(anyover), len(pc), max(over.values()), a.n))
print("\n## Warnings from klt yield (target limits)\n")
for w in json.load(open(a.yield_target)).get("warnings", []):
    if "declares no spec limits" not in w:
        print("- " + w)
print("\nFiles beside this record: the two requests, `-yield-target.json`, `-yield-fallback.json`, `-yield-target.txt`, and the `klt sim` stderr of each job.")
