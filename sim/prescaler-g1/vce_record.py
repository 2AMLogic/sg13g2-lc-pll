#!/usr/bin/env python3
"""Grade a `klt sim` report of sim/prescaler-g1/prescaler_vce.request.json and write the record.

Every measurement is vecmax(|Vce|) of one HBT over the recorded window (10-20 ns). The verdict is
against BVCEO(min) (the request's limits.max): FAIL if any converged corner exceeds it, INCOMPLETE
if none does but a corner did not converge or the report has no corners, PASS only if the report
has corners and every one converged with none exceeding.
A corner that errored is never counted as a pass.

    vce_record.py --report REPORT.json --out-dir sim/prescaler-g1/records [--commit SHA]
"""
import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import ngpin  # noqa: E402  (the simulator pin check, computed once in sim/ngpin.py)

BVCEO_MIN_V = 2.2
SUPPLY_LO, SUPPLY_HI = 2.97, 3.63


def _vdd(corner):
    return float((corner.get("params") or {}).get("vddv", float("nan")))


def _mc(corner):
    """MC level as a fraction of the supply (0 = /8, 1 = /9); None if the report has no mcv axis."""
    v = (corner.get("params") or {}).get("mcv")
    return None if v is None else float(v)


def grade(report, bveceo=BVCEO_MIN_V):
    """{rows, verdict, ...}: one row per corner with its worst device; verdict per the module doc."""
    rows = []
    for c in report["corners"]:
        vals = [(m["value"], m["name"]) for m in c["measurements"] if m.get("value") is not None]
        converged = c["status"] in ("pass", "fail") and len(vals) == len(c["measurements"]) and bool(vals)
        worst = max(vals) if vals else (None, None)
        rows.append({
            "corner_id": c["corner_id"], "process": c["process"], "temperature_c": c["temperature_c"],
            "vdd_v": _vdd(c), "mc": _mc(c), "converged": converged, "worst_vce_v": worst[0],
            "worst_device": worst[1].removeprefix("vce_") if worst[1] else None,
            "margin_v": None if worst[0] is None else bveceo - worst[0],
            "exceeds": worst[0] is not None and worst[0] > bveceo,
            "n_exceeding": sum(1 for v, _ in vals if v > bveceo),
            "diagnostics": [d["message"][:140] for d in c.get("diagnostics", [])],
        })
    n_err = sum(1 for r in rows if not r["converged"])
    n_exc = sum(1 for r in rows if r["exceeds"])
    verdict = "FAIL" if n_exc else ("INCOMPLETE" if n_err or not rows else "PASS")
    return {"rows": rows, "verdict": verdict, "n_corners": len(rows), "n_exceeding": n_exc, "n_not_converged": n_err,
            "bveceo_v": bveceo}


def _mc_label(mc):
    return "n/a" if mc is None else ("low (/8)" if mc == 0 else "high (/9)")


def _fmt(v):
    return "n/a" if v is None else "%.3f" % v


def _has_rail(supplies, rail):
    return any(abs(s - rail) < 1e-6 for s in supplies)


def _legend_entry(block):
    """'NAME = hbt_x' from the block's cornerHBT section; NAME alone when it has none."""
    for s in block.get("sections") or []:
        if isinstance(s, dict) and s.get("section") and Path(str(s.get("lib", ""))).name.startswith("cornerHBT"):
            return "%s = %s" % (block["name"], s["section"])
    return block["name"]


def render(g, report, rec_id, commit, report_name, request_path):
    env, rem = report["environment"], report["environment"].get("remote", {})
    rows = g["rows"]
    lo = [r for r in rows if r["converged"] and abs(r["vdd_v"] - SUPPLY_LO) < 1e-6]
    hi = [r for r in rows if r["converged"] and abs(r["vdd_v"] - SUPPLY_HI) < 1e-6]
    wlo = max(lo, key=lambda r: r["worst_vce_v"], default=None)
    whi = max(hi, key=lambda r: r["worst_vce_v"], default=None)
    req_bytes = Path(request_path).read_bytes()
    req = json.loads(req_bytes)
    grid = req.get("corners") or {}
    blocks = [b for b in grid.get("process") or [] if isinstance(b, dict) and "name" in b]
    procs = [b["name"] for b in blocks]
    legend = ", ".join(_legend_entry(b) for b in blocks)
    temps = list(grid.get("temperature_c") or [])
    params = grid.get("params") or {}
    vddv = list(params.get("vddv") or [])
    supplies = sorted(set(vddv))
    mcv = params.get("mcv")
    mc_levels = None if mcv is None else sorted(set(mcv))
    n_corners = len(procs) * len(temps) * len(supplies)
    n_req_runs = len(procs) * len(temps) * len(vddv)
    mc_axis = ("MC low/high" if mc_levels == [0, 1]
               else (None if not mc_levels else "%d MC levels" % len(mc_levels)))
    runs_req = ("%d sub-corners x %s" % (n_corners, mc_axis)) if mc_axis else "%d sub-corners" % n_corners
    grid_text = "{%s} V x {%s} x {%s} C" % (
        ", ".join("%.3f" % s for s in supplies), ", ".join(procs), ", ".join("%g" % t for t in temps))
    n_req_dev = len(req.get("measurements") or [])
    out = ["# prescaler-vce run %s" % rec_id, ""]
    head = ("**Result (simulated, not measured): worst HBT |Vce| against BVCEO(min) %.1f V: **%s**. " % (g["bveceo_v"], g["verdict"]))
    if rows:
        head += "At the minimum supply %.3f V the worst converged corner is %s V (%s, %s)" % (
            SUPPLY_LO, _fmt(wlo and wlo["worst_vce_v"]), (wlo and wlo["corner_id"]) or "n/a", (wlo and wlo["worst_device"]) or "n/a")
        if _has_rail(supplies, SUPPLY_HI):
            head += "; at %.3f V it is %s V (%s, %s)" % (
                SUPPLY_HI, _fmt(whi and whi["worst_vce_v"]), (whi and whi["corner_id"]) or "n/a", (whi and whi["worst_device"]) or "n/a")
        head += ". "
        head += "%d of %d observed runs (%d requested: %s) exceed the rating; %d did not converge and are not graded.**" % (
            g["n_exceeding"], g["n_corners"], n_req_runs, runs_req, g["n_not_converged"])
    else:
        head += ("No corner was observed: the report covers 0 of %d requested runs (%s) and no "
                 "measurement, so no run is graded.**" % (n_req_runs, runs_req))
    out += [head, ""]
    scope_grid = ", ".join(p for p in (grid_text, legend) if p)
    scope_rail = (" The %.3f V half is beyond the issue's %.3f V ask: Vce stress rises with the supply, "
                  "so it is the corner a rating check has to include." % (SUPPLY_HI, SUPPLY_LO)
                  if _has_rail(supplies, SUPPLY_HI) else "")
    out += [
        "- **Scope**: the %d supply sub-corners of spec section 'Corner set' stage 2: %s (the prescaler has HBTs and PDK rppd resistors only; the cornerRES section res_wcs/res_typ/res_bcs is paired with each HBT corner, so the MOS and MIM members of the bundles do not enter).%s Not covered: the 135-point 3.3 V grid, Monte Carlo, routing parasitics, the VCO driving the input (gate G2), self-heating beyond the model's." % (n_corners, scope_grid, scope_rail),
        "- **Method**: `klt sim` corner request `%s` (generated by `scripts/gen_prescaler_vce_request.py` from `design/netlist/prescaler.spice`, one measurement per HBT, %d devices requested per run). Transient `1p 24n 10n 2p`: supply, IREF and MC ramp up over 1 ns, data are recorded from 10 ns (the dividers have settled), 70 input cycles; each measurement is `vecmax(abs(v(collector)-v(emitter)))` over 10-24 ns, so a transient peak counts, not just the DC level. Stimulus as `div89_chain.cir`: 0.4 Vpp differential 5.0 GHz at a common mode equal to the supply, IREF = 50 uA (ideal source), PDK rppd resistors, **MC = 0 (/8) and MC = 1 at the supply level (/9) both run** at every one of the %d supply sub-corners (%d runs requested, %d observed)." % (Path(request_path).name, n_req_dev, n_corners, n_req_runs, g["n_corners"]),
        "- **Limit**: BVCEO %.1f V min (2.5 V typ), the figure from the #44 EE key review, applied to the instantaneous |Vce| of every HBT. BVCEO is an open-base rating; with the base driven the device tolerates more, so a transient excursion over it is a flag for the designer, not a proven breakdown. The record reports it as the issue asks: against 2.2 V." % g["bveceo_v"],
        "- **Simulator**: %s on the Spot batch fleet (`environment.engine_host` = %s), %s. Job `%s`, %s, %s." % (
            ngpin.engine(env.get("engine_version")), env.get("engine_host"), ngpin.verdict(env.get("engine_version")),
            rem.get("job_id"), rem.get("instance_type"), rem.get("lifecycle")),
        "- **Request**: `%s` sha256 `%s`; report [`%s`](%s) (klt report, gzip) sha256 `%s`" % (Path(request_path).name, hashlib.sha256(req_bytes).hexdigest(), report_name, report_name, report.get("_report_sha256", "see file")),
        "- **PDK**: `models.pdk` sg13g2 on the fleet image (`/opt/pdk`); model library `cornerHBT.lib` staged from this host's IHP-Open-PDK v0.3.0 install (`environment.staged_model_inputs`)",
        "- **Commit**: `%s` of this repository" % commit,
        "- **Jitter-like numbers**: none (voltage stress only).",
        "",
        "| corner | vdd (V) | MC | worst device | worst Vce (V) | margin to %.1f V (V) | devices over | note |" % g["bveceo_v"],
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        note = "NOT CONVERGED, not graded" if not r["converged"] else ("EXCEEDS" if r["exceeds"] else "ok")
        if r["diagnostics"] and r["converged"]:
            note += "; " + r["diagnostics"][0]
        out.append("| %s/%dC | %.2f | %s | %s | %s | %s | %d | %s |" % (r["process"], r["temperature_c"], r["vdd_v"], _mc_label(r["mc"]), r["worst_device"] or "-",
                   _fmt(r["worst_vce_v"]), _fmt(r["margin_v"]), r["n_exceeding"], note))
    bad = [r for r in rows if not r["converged"]]
    if bad:
        out += ["", "Non-converged corners (ngspice: %s): %s." % (bad[0]["diagnostics"][0] if bad[0]["diagnostics"] else "no diagnostic",
                ", ".join("%s/%dC/%.2f V/MC %s" % (r["process"], r["temperature_c"], r["vdd_v"], _mc_label(r["mc"])) for r in bad))]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", required=True)
    ap.add_argument("--request", default=str(HERE / "prescaler_vce.request.json"))
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--commit", default="unknown")
    ap.add_argument("--id", required=True, help="record id, e.g. 20261103-020900-abc1234")
    args = ap.parse_args(argv)
    raw = Path(args.report).read_bytes()
    report = json.loads(raw)
    gz = Path(args.out_dir) / ("%s-klt-report.json.gz" % args.id)
    rec = Path(args.out_dir) / ("%s-vce.md" % args.id)
    if gz.exists() or rec.exists():
        sys.exit("records are append-only: %s exists" % rec)
    gz.parent.mkdir(parents=True, exist_ok=True)
    gz.write_bytes(gzip.compress(raw, 9, mtime=0))
    report["_report_sha256"] = hashlib.sha256(raw).hexdigest()
    g = grade(report)
    rec.write_text(render(g, report, args.id, args.commit, gz.name, args.request))
    print("%s: %s (%d exceed, %d not converged of %d)" % (rec, g["verdict"], g["n_exceeding"], g["n_not_converged"], g["n_corners"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
