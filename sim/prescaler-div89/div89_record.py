#!/usr/bin/env python3
"""Grade `klt sim` reports of sim/prescaler-div89 and write the dated record.

chain report (div89_chain.request.json): per corner, MC static. Pass iff the differential output has
  - at least MIN_EDGES rising zero crossings after T_FROM (the divider is running),
  - every period within TOL_TIN input periods of N x T_in (N = 8 for MC low, 9 for MC high), and
  - the +0.1 V rise and -0.1 V fall crossing counts within one of the zero-crossing count (swing >= 0.2 Vpp).
async reports (div89_async_*.request.json): MC is one 8 ns pulse at phase phi. Pass iff every period is 8 or 9
  input periods (within TOL_TIN), the 8/9 sequence changes at most twice (8..8 9..9 8..8, starting and ending
  on 8), the number of 9-periods is plausible for the 8 ns window, and the swing rule above holds.
A corner that errored, or gave no crossings, is never a pass: the verdict is FAIL if any corner fails, else
INCOMPLETE if any did not run, else PASS.

    div89_record.py --chain R.json --async R1.json R2.json --out-dir records --commit SHA
"""
import argparse
import gzip
import hashlib
import json
import math
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
T_FROM = 6e-9          # crossings before this are start-up and are ignored
MIN_EDGES = 8
TOL_TIN = 0.25         # a period is accepted within +-0.25 input periods of an integer multiple
MC_WINDOW_S = 8e-9     # width of the async MC pulse (div89_async.cir)


def _times(corner, name):
    for m in corner.get("measurements") or []:
        if m["name"] == name and m.get("crossings") is not None:
            return [t for t in m["crossings"]["times"] if t >= T_FROM]
    return None


def _swing_ok(z, hi, lo):
    return hi is not None and lo is not None and abs(len(hi) - len(z)) <= 1 and abs(len(lo) - len(z)) <= 1


def _periods(z):
    return [b - a for a, b in zip(z, z[1:])]


def grade_chain_corner(c):
    p = c["params"]
    n = 9 if p["mcv"] > 1.0 else 8
    tin = 1.0 / p["fin"]
    z, hi, lo = _times(c, "x_zero"), _times(c, "x_hi"), _times(c, "x_lo")
    row = {"corner_id": c["corner_id"], "process": c["process"], "temperature_c": c["temperature_c"],
           "vdd_v": p["vddv"], "fin_hz": p["fin"], "n_expected": n, "diagnostics": [d["message"][:120] for d in c.get("diagnostics", [])]}
    if z is None or c["status"] not in ("pass", "fail") or len(z) < MIN_EDGES:
        return dict(row, ran=False, ok=False, ratio=None, why="did not run" if z is None or c["status"] not in ("pass", "fail") else "too few edges (%d)" % len(z))
    per = _periods(z)
    ratios = [q / tin for q in per]
    ok_ratio = all(abs(r - n) <= TOL_TIN for r in ratios)
    ok_swing = _swing_ok(z, hi, lo)
    why = "" if ok_ratio and ok_swing else ("ratio %.2f..%.2f" % (min(ratios), max(ratios)) if not ok_ratio else "swing < 0.2 Vpp (crossings %d/%d/%d)" % (len(z), len(hi or []), len(lo or [])))
    return dict(row, ran=True, ok=ok_ratio and ok_swing, ratio=sum(ratios) / len(ratios), rmin=min(ratios), rmax=max(ratios), why=why)


def grade_async_corner(c):
    p = c["params"]
    tin = 1.0 / p["fin"]
    z, hi, lo = _times(c, "x_zero"), _times(c, "x_hi"), _times(c, "x_lo")
    row = {"corner_id": c["corner_id"], "process": c["process"], "temperature_c": c["temperature_c"],
           "vdd_v": p["vddv"], "phi_ps": p["phi"] * 1e12, "diagnostics": [d["message"][:120] for d in c.get("diagnostics", [])]}
    if z is None or c["status"] not in ("pass", "fail") or len(z) < MIN_EDGES:
        return dict(row, ran=False, ok=False, seq="", why="did not run")
    rs = [q / tin for q in _periods(z)]
    ns = [round(r) for r in rs]
    why = []
    if any(abs(r - n) > TOL_TIN or n not in (8, 9) for r, n in zip(rs, ns)):
        why.append("period of %s input periods" % ",".join("%.2f" % r for r, n in zip(rs, ns) if abs(r - n) > TOL_TIN or n not in (8, 9))[:60])
    changes = sum(1 for a, b in zip(ns, ns[1:]) if a != b)
    if changes > 2 or ns[0] != 8 or ns[-1] != 8:
        why.append("sequence not 8..9..8 (%d changes)" % changes)
    n9 = ns.count(9)
    lo9, hi9 = math.floor(MC_WINDOW_S / (9 * tin)) - 1, math.ceil(MC_WINDOW_S / (8 * tin)) + 1
    if not lo9 <= n9 <= hi9:
        why.append("%d nine-periods outside %d..%d" % (n9, lo9, hi9))
    if not _swing_ok(z, hi, lo):
        why.append("swing < 0.2 Vpp")
    return dict(row, ran=True, ok=not why, seq="".join(str(n - 8) if n in (8, 9) else "x" for n in ns), n9=n9, why="; ".join(why))


P_BUDGET_MW = 10.0     # spec row 11 allocation for the prescaler
P_BASELINE_MW = 6.41   # sim/loop-power/records/20261106-051958-0503364-dirty.md: prescaler + 50 uA reference, 1941.7 uA at 3.3 V


def power_rows(chain_report):
    """[(power_mw, corner_id, fin, mcv, vdd)] from the i_vdd_avg measurement (supply current, negative); none if absent."""
    out = []
    for c in chain_report["corners"]:
        m = next((x for x in c.get("measurements") or [] if x["name"] == "i_vdd_avg" and x.get("value") is not None), None)
        if m is not None:
            p = c["params"]
            out.append((-m["value"] * p["vddv"] * 1e3, c["corner_id"], p["fin"], p["mcv"], p["vddv"]))
    return sorted(out)


def verdict(rows):
    if any(r["ran"] and not r["ok"] for r in rows):
        return "FAIL"
    return "INCOMPLETE" if any(not r["ran"] for r in rows) else "PASS"


def grade(chain_report, async_reports):
    ch = [grade_chain_corner(c) for c in chain_report["corners"]]
    asy = [grade_async_corner(c) for r in async_reports for c in r["corners"]]
    return {"chain": ch, "async": asy, "chain_verdict": verdict(ch), "async_verdict": verdict(asy)}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def render(g, reports, rec_id, commit, files, netlist):
    ch, asy = g["chain"], g["async"]
    nfail = sum(1 for r in ch + asy if r["ran"] and not r["ok"])
    nrun = sum(1 for r in ch + asy if not r["ran"])
    overall = "FAIL" if "FAIL" in (g["chain_verdict"], g["async_verdict"]) else ("INCOMPLETE" if "INCOMPLETE" in (g["chain_verdict"], g["async_verdict"]) else "PASS")
    out = ["# prescaler-div89 run %s" % rec_id, ""]
    out += ["**Result (simulated, not measured): /8 and /9 at 5.0 and 5.5 GHz over %d chain corners (SLOW/TYP/FAST x -40/27/125 C x 2.970/3.300/3.630 V): %s (%d of %d pass); modulus toggled at 16 phases of the output period over %d async corners (5.5 GHz, 2.970 and 3.630 V): %s (%d of %d pass). %d unit(s) failed, %d did not run and are not counted as passes. Overall: %s.**" % (
        len(ch), g["chain_verdict"], sum(r["ok"] for r in ch), len(ch), len(asy), g["async_verdict"], sum(r["ok"] for r in asy), len(asy), nfail, nrun, overall), ""]
    rem = reports[0]["environment"].get("remote", {})
    out += [
        "- **Netlist**: `design/netlist/prescaler.spice` sha256 `%s` (checked against its schematic with `design/netlist.sh --check`)" % netlist,
        "- **Stimulus**: 0.4 Vpp differential sine (0.1 V per side, antiphase) on INP/INN at a common mode equal to the supply; supply, IREF (50 uA ideal) and MC ramp 0 -> final in 1 ns, the inputs follow v(vdd) (power-up start; see the comment in `div89_chain.cir`). Ideal resistors. No VCO, no routing parasitics.",
        "- **Pass rule (chain)**: transient 24 ns; rising zero crossings of v(OUTP)-v(OUTN) from 6 ns; at least %d; every period within +-%.2f input periods of N x T_in (N = 8 for MC low, 9 for MC high); crossing counts at +0.1 V (rise) and -0.1 V (fall) within one of the zero-crossing count, i.e. the output swings at least 0.2 Vpp at every cycle. Nominal-only numbers are never labelled corner-bounded here." % (MIN_EDGES, TOL_TIN),
        "- **Pass rule (async)**: transient 34 ns; MC is one 8 ns CMOS-level pulse rising at 8 ns + phi, phi = 0..1500 ps in 100 ps steps (the output period is 1.45-1.64 ns, so every phase of the S1/S2 swallow window is hit); every output period 8 or 9 input periods (+-%.2f), the 8/9 sequence 8..8 9..9 8..8 with at most two changes and starting and ending on 8, 9-periods count within 8 ns / (9 T_in) - 1 .. 8 ns / (8 T_in) + 1, and the swing rule above. This is the asynchronous-modulus retiming check: one swallowed input cycle per prescaler period, no /10 or /17 or /8-hiccup." % TOL_TIN,
        "- **Simulator**: `ngspice-%s` on the Spot batch fleet (`environment.engine_host` = %s, %s), against sim/pins.json pin 47: **mismatch (fleet ran %s)**. Jobs: %s." % (
            reports[0]["environment"].get("engine_version"), reports[0]["environment"].get("engine_host"), rem.get("instance_type"), reports[0]["environment"].get("engine_version"),
            ", ".join("`%s`" % r["environment"].get("remote", {}).get("job_id") for r in reports)),
        "- **Requests / reports**: " + "; ".join("`%s` sha256 `%s`, report [`%s`](%s) sha256 `%s`" % (f["request_name"], f["request_sha"], f["report_name"], f["report_name"], f["report_sha"]) for f in files),
        "- **PDK**: `models.pdk` sg13g2 on the fleet image; `cornerHBT.lib` staged from this host's IHP-Open-PDK v0.3.0 install (`environment.staged_model_inputs`). SLOW = hbt_wcs, TYP = hbt_typ, FAST = hbt_bcs.",
        "- **Commit**: `%s` of this repository" % commit,
        "- **Jitter / phase-noise numbers**: none (functional division only).",
        "",
        "## Chain: ratio per corner (cells: mean output period / T_in, verdict)",
        "",
        "| process | T (C) | vdd (V) | 5.0 GHz /8 | 5.0 GHz /9 | 5.5 GHz /8 | 5.5 GHz /9 |",
        "|---|---|---|---|---|---|---|",
    ]
    keys = sorted({(r["process"], r["temperature_c"], r["vdd_v"]) for r in ch})
    for k in keys:
        cells = []
        for fin in (5.0e9, 5.5e9):
            for n in (8, 9):
                rr = [r for r in ch if (r["process"], r["temperature_c"], r["vdd_v"]) == k and r["fin_hz"] == fin and r["n_expected"] == n]
                if not rr:
                    cells.append("-")
                elif not rr[0]["ran"]:
                    cells.append("NOT RUN (%s)" % rr[0]["why"])
                else:
                    cells.append("%.2f %s" % (rr[0]["ratio"], "pass" if rr[0]["ok"] else "FAIL: " + rr[0]["why"]))
        out.append("| %s | %d | %.3f | %s |" % (k[0], k[1], k[2], " | ".join(cells)))
    out += ["", "## Async modulus: per-period sequence (0 = /8 period, 1 = /9 period; each row the 16 phases phi = 0..1500 ps in order)", "",
            "| process | T (C) | vdd (V) | phases passing | worst phase | note |", "|---|---|---|---|---|---|"]
    for k in sorted({(r["process"], r["temperature_c"], r["vdd_v"]) for r in asy}):
        rr = [r for r in asy if (r["process"], r["temperature_c"], r["vdd_v"]) == k]
        bad = [r for r in rr if not r["ok"]]
        out.append("| %s | %d | %.3f | %d/%d | %s | %s |" % (k[0], k[1], k[2], sum(r["ok"] for r in rr), len(rr),
                   ("phi=%d ps" % bad[0]["phi_ps"]) if bad else "-", (bad[0]["why"] or "did not run") if bad else ""))
    pw = power_rows(reports[0])
    if pw:
        nom = [x for x in pw if "TYP/" in x[1] and "/27C/" in x[1] and abs(x[4] - 3.3) < 1e-9]
        out += ["", "## Supply power (prescaler + 50 uA reference)", "",
                "Mean supply current over 8-24 ns (`.meas AVG i(vdd)`), power = |I| x vddv. Baseline: the pre-change /8-/10 prescaler, %.2f mW at TYP / 27 C / 3.3 V (`sim/loop-power/records/20261106-051958-0503364-dirty.md`, window 40-120 ns, so the delta is indicative to a few hundredths of a mW). Spec row 11 allocation: <= %.0f mW." % (P_BASELINE_MW, P_BUDGET_MW), "",
                "| corner | fin (GHz) | ratio | power (mW) | delta vs baseline (mW) |", "|---|---|---|---|---|"]
        for x in nom:
            out.append("| TYP / 27 C / 3.300 V | %.1f | /%d | %.3f | %+.3f |" % (x[2] / 1e9, 9 if x[3] > 1 else 8, x[0], x[0] - P_BASELINE_MW))
        out.append("")
        out.append("Over all %d chain corners: minimum %.3f mW (`%s`), **maximum %.3f mW** (`%s`); %s the %.0f mW allocation at every corner." % (
            len(pw), pw[0][0], pw[0][1], pw[-1][0], pw[-1][1], "within" if pw[-1][0] <= P_BUDGET_MW else "**OVER**", P_BUDGET_MW))
    bad_rows = [r for r in ch + asy if not r["ok"]]
    if bad_rows:
        out += ["", "## Units not passing", "", "| unit | reason |", "|---|---|"] + ["| `%s` | %s |" % (r["corner_id"], r["why"] or "-") for r in bad_rows]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--chain", required=True)
    ap.add_argument("--async", dest="asyn", nargs="+", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--id", required=True)
    ap.add_argument("--commit", default="unknown")
    a = ap.parse_args()
    paths = [a.chain] + a.asyn
    reports = [json.load(open(p)) for p in paths]
    g = grade(reports[0], reports[1:])
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rec = out / ("%s.md" % a.id)
    if rec.exists():
        raise SystemExit("%s exists; records are append-only" % rec)
    files = []
    for p, r in zip(paths, reports):
        name = "%s-%s.json.gz" % (a.id, Path(p).stem.replace("report-", ""))
        with open(p, "rb") as f, gzip.open(out / name, "wb") as z:
            shutil.copyfileobj(f, z)
        req = HERE / (Path(p).stem.replace("report-", "") + ".request.json")
        files.append({"request_name": req.name, "request_sha": _sha(req), "report_name": name, "report_sha": _sha(out / name)})
    rec.write_text(render(g, reports, a.id, a.commit, files, _sha(HERE.parent.parent / "design/netlist/prescaler.spice")))
    print("record:", rec, g["chain_verdict"], g["async_verdict"])


if __name__ == "__main__":
    main()
