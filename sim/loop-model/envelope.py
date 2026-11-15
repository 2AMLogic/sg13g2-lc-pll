#!/usr/bin/env python3
"""Spec row 5 envelope: f_c and PM over the measured I_cp spread and the Kvco range (method L).

I_cp comes from the `klt sim` run of sim/cp-dc (the 18 supply sub-corners, I_up and I_dn taken as
separate I_cp values), Kvco from loop_model.KVCO_GRID (381-606 MHz/V, spec section 3), the loop
filter is the committed nominal one. Pure-Python model run (no ngspice): row 5 is a method-L row.

    envelope.py --icp-report sim/cp-dc/records/<id>-icp-corners-klt-report.json.gz \\
                --out-dir sim/loop-model/records --id YYYYMMDD-HHMMSS-sha [--commit SHA]

Exit 1 if any point violates row 5 (f_c outside [0.5, 2.0] MHz or PM < 45 deg). The filter is NOT
varied with the corner here (R1, C1, C2, R3, C3 nominal): the record says so. The JSON record is the
`klt signoff` `model-run` envelope (schema_version 1) around the original verdict/points/binding/
loop_filter content.
"""
import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

import loop_model as lm


def load_icp_points(report):
    """[(corner_id, which, I_cp amps)] from a klt report of cp_icp_corners.request.json."""
    pts = []
    for c in report["corners"]:
        m = {x["name"]: x.get("value") for x in c["measurements"]}
        if c["status"] not in ("pass", "fail") or m.get("i_up_ua") is None or m.get("i_dn_ua") is None:
            raise ValueError("corner %s has no I_up/I_dn" % c["corner_id"])
        pts.append((c["corner_id"], "I_up", abs(m["i_up_ua"]) * 1e-6))
        pts.append((c["corner_id"], "I_dn", abs(m["i_dn_ua"]) * 1e-6))
    return pts


def envelope(flt, icp_points, kvco_grid=None):
    """Every (I_cp point, Kvco) with f_c, PM and its violated row-5 bounds."""
    rows = []
    for cid, which, icp in icp_points:
        for kvco in (kvco_grid or lm.KVCO_GRID):
            f_c = lm.unity_gain_hz(flt, icp, kvco)
            pm = lm.phase_margin_deg(f_c, flt)
            rows.append({"corner_id": cid, "icp_source": which, "icp_a": icp, "kvco_hz_per_v": kvco,
                         "f_c_hz": f_c, "pm_deg": pm, "violations": lm.check_point(f_c, pm)})
    return rows


def binding(rows):
    """The row that binds each row-5 bound: lowest/highest f_c, lowest PM."""
    return {"f_c_min": min(rows, key=lambda r: r["f_c_hz"]), "f_c_max": max(rows, key=lambda r: r["f_c_hz"]),
            "pm_min": min(rows, key=lambda r: r["pm_deg"])}


MODEL_RUN_SCHEMA_VERSION = 1


def _fc_worst_case(b):
    """The binding f_c point closest to a row-5 limit, with its margin, both in MHz."""
    lo, hi = lm.FC_BAND_HZ
    m_lo = b["f_c_min"]["f_c_hz"] - lo
    m_hi = hi - b["f_c_max"]["f_c_hz"]
    r, m = (b["f_c_min"], m_lo) if m_lo <= m_hi else (b["f_c_max"], m_hi)
    return {"corner_id": r["corner_id"], "value": r["f_c_hz"] / 1e6, "margin": m / 1e6}


def model_run_doc(verdict, flt, b, rows, icp_name, icp_sha256, icp_path):
    """The `klt signoff` `model-run` envelope around the row-5 rollup (schema_version 1).

    Carries the grader's required keys (schema_version, kind, status, method, measurements) and
    the optional corners/provenance, alongside the existing verdict/points/binding/loop_filter
    content. `status` is the grader's lowercase token, deliberately not the record's own uppercase
    `verdict`; every `corners` entry carries its own `status` because the grader re-grades the
    list point by point. Only `min`/`max` are recognised limit keys.
    """
    fc_ok = all(lm.FC_BAND_HZ[0] <= r["f_c_hz"] <= lm.FC_BAND_HZ[1] for r in rows)
    pm_ok = all(r["pm_deg"] >= lm.PM_MIN_DEG for r in rows)
    method = ("Method L: the linear phase-domain loop model of spec section 4 "
              "(sim/loop-model/loop_model.py: L(s) = I_cp Kvco Z(s) / (N s), type-II third order; "
              "f_c by bisection on |L| = 1, PM from the factor phases; N = %d, f_ref = %g MHz). "
              "Inputs: I_cp = the currents of klt report %s (sha256 %s); Kvco = KVCO_GRID %s MHz/V "
              "(spec section 3 range %g-%g); loop filter = committed loop-filter.json held nominal "
              "in every corner (R1, C1, C2, R3, C3 not varied with corner)."
              % (lm.N_DIV, lm.F_REF_HZ / 1e6, icp_name, icp_sha256,
                 "/".join("%g" % (k / 1e6) for k in lm.KVCO_GRID),
                 lm.KVCO_RANGE_HZ_PER_V[0] / 1e6, lm.KVCO_RANGE_HZ_PER_V[1] / 1e6))
    return {
        "schema_version": MODEL_RUN_SCHEMA_VERSION,
        "kind": "model-run",
        "status": "pass" if verdict == "PASS" else "fail",
        "method": method,
        "measurements": [
            {"name": "f_c_mhz", "unit": "MHz",
             "limits": {"min": lm.FC_BAND_HZ[0] / 1e6, "max": lm.FC_BAND_HZ[1] / 1e6},
             "status": "pass" if fc_ok else "fail", "worst_case": _fc_worst_case(b)},
            {"name": "pm_deg", "unit": "deg", "limits": {"min": lm.PM_MIN_DEG},
             "status": "pass" if pm_ok else "fail",
             "worst_case": {"corner_id": b["pm_min"]["corner_id"], "value": b["pm_min"]["pm_deg"],
                            "margin": b["pm_min"]["pm_deg"] - lm.PM_MIN_DEG}},
        ],
        "corners": [dict(r, status="pass" if not r["violations"] else "fail") for r in rows],
        "provenance": {"input": {"path": icp_path, "sha256": icp_sha256}},
        "verdict": verdict,
        "loop_filter": flt,
        "binding": b,
        "points": rows,
    }


def _flt():
    d = json.loads(lm.FILTER_JSON.read_text())
    return {k: d[k] for k in ("r1_ohm", "c1_f", "c2_f", "r3_ohm", "c3_f")}


def _row(label, r):
    return "| %s | %s %s | %.0f | %.3f | %.2f | %.2f |" % (label, r["corner_id"], r["icp_source"], r["kvco_hz_per_v"] / 1e6,
                                                            r["icp_a"] * 1e6, r["f_c_hz"] / 1e6, r["pm_deg"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--icp-report", required=True, help="klt report (.json or .json.gz) of cp_icp_corners.request.json")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--id", required=True)
    ap.add_argument("--commit", default="unknown")
    a = ap.parse_args(argv)
    p = Path(a.icp_report)
    raw = p.read_bytes()
    jraw = gzip.decompress(raw) if p.suffix == ".gz" else raw
    pts = load_icp_points(json.loads(jraw))
    flt = _flt()
    rows = envelope(flt, pts)
    b = binding(rows)
    bad = [r for r in rows if r["violations"]]
    verdict = "PASS" if not bad else "FAIL"
    out = Path(a.out_dir)
    md, js = out / ("%s-row5-envelope.md" % a.id), out / ("%s-row5-envelope.json" % a.id)
    if md.exists() or js.exists():
        sys.exit("records are append-only: %s exists" % md)
    out.mkdir(parents=True, exist_ok=True)
    repo = Path(__file__).resolve().parents[2]
    try:
        icp_path = p.resolve().relative_to(repo).as_posix()
    except ValueError:
        icp_path = p.resolve().as_posix()
    doc = model_run_doc(verdict, flt, b, rows, p.name, hashlib.sha256(raw).hexdigest(), icp_path)
    js.write_text(json.dumps(doc, indent=1) + "\n")
    icps = [x[2] * 1e6 for x in pts]
    L = ["# row 5 envelope %s" % a.id, "",
         "**Result (simulated, method L, not measured): spec row 5 %s over %d points (%d I_cp values x %d Kvco). f_c %.3f to %.3f MHz against [0.5, 2.0]; PM minimum %.2f deg against >= 45.**" % (
             verdict, len(rows), len(pts), len(lm.KVCO_GRID), b["f_c_min"]["f_c_hz"] / 1e6, b["f_c_max"]["f_c_hz"] / 1e6, b["pm_min"]["pm_deg"]), "",
         "- **Method**: L, the linear phase-domain model of spec section 4 (`sim/loop-model/loop_model.py`: `L(s) = I_cp Kvco Z(s) / (N s)`, type-II third order; f_c by bisection on |L| = 1, PM from the factor phases). No jitter, spur or noise number is produced here, so there are no section 4 estimator fields to state. N = %d, f_ref = 50 MHz." % lm.N_DIV,
         "- **Inputs**: I_cp = the %d currents (I_up and I_dn at each of the 18 supply sub-corners, %.2f to %.2f uA) of `%s` (sha256 of the file `%s`); Kvco = KVCO_GRID %s MHz/V (spec section 3 range 381-606). Loop filter = committed `loop-filter.json`: R1 %.1f ohm, C1 %.2f pF, C2 %.2f pF, R3 %.1f ohm, C3 %.2f pF, **held nominal in every corner**." % (
             len(pts), min(icps), max(icps), p.name, hashlib.sha256(raw).hexdigest(), [int(k / 1e6) for k in lm.KVCO_GRID],
             flt["r1_ohm"], flt["c1_f"] * 1e12, flt["c2_f"] * 1e12, flt["r3_ohm"], flt["c3_f"] * 1e12),
         "- **Not covered**: filter R/C spread across the corner grid (poly R1/R3 and MIM C1/C2/C3 are not varied here), the 135-point 3.300 V model grid, the local Kvco from the VCO's graded f(Vctrl) (G4: the Kvco axis is the section 3 range, not graded VCO data), the I_cp range 100-400 uA of row 6 (the committed `results/loop-model.json` flags those points and does not gate them), and everything the loop model does not model (sampling, CP nonlinearity, supply and substrate coupling). The full corner-by-corner row 5 grade over the VCO's graded corners is #70.",
         "- **Commit**: `%s` of this repository" % a.commit,
         "- **Envelope**: emitted in the `klt signoff` `model-run` shape (`schema_version` %d: `kind`, `status` `%s`, `method`, `measurements` with the row-5 `limits`, per-point `corners`) alongside the original `verdict`/`points`/`binding`/`loop_filter` keys. The pinned `klt` 0.8.0 does not grade the `model-run` kind yet; citing this record as item-5 evidence follows the pin bump (#304)." % (doc["schema_version"], doc["status"]),
         "- **Points**: [`%s`](%s) (every (I_cp, Kvco) point)" % (js.name, js.name), "",
         "| bound | binding point | Kvco (MHz/V) | I_cp (uA) | f_c (MHz) | PM (deg) |", "|---|---|---|---|---|---|",
         _row("f_c minimum", b["f_c_min"]), _row("f_c maximum", b["f_c_max"]), _row("PM minimum", b["pm_min"])]
    if bad:
        L += ["", "Violations (%d points): first %s" % (len(bad), "; ".join("%s %s Kvco %.0f: %s" % (r["corner_id"], r["icp_source"], r["kvco_hz_per_v"] / 1e6, ", ".join(r["violations"])) for r in bad[:5]))]
    md.write_text("\n".join(L) + "\n")
    print("%s: %s (f_c %.3f..%.3f MHz, PM min %.2f deg)" % (md, verdict, b["f_c_min"]["f_c_hz"] / 1e6, b["f_c_max"]["f_c_hz"] / 1e6, b["pm_min"]["pm_deg"]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
