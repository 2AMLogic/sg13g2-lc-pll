#!/usr/bin/env python3
"""Write the record for a `klt sim` run of sim/cp-dc/cp_icp_corners.request.json (I_cp over the 18 supply sub-corners).

    icp_record.py --report REPORT.json --out-dir sim/cp-dc/records --id YYYYMMDD-HHMMSS-sha [--commit SHA]

Copies the klt report next to the record (gzip, zeroed header) so sim/loop-model/envelope.py can read it.
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

ICP_NOM_UA = 200.0


def currents(report):
    """[(corner_id, i_up_uA, i_dn_uA)]; refuses a report with an unconverged corner or a missing value."""
    out = []
    for c in report["corners"]:
        m = {x["name"]: x.get("value") for x in c["measurements"]}
        if c["status"] not in ("pass", "fail") or m.get("i_up_ua") is None or m.get("i_dn_ua") is None:
            raise SystemExit("corner %s did not produce I_up/I_dn (status %s)" % (c["corner_id"], c["status"]))
        out.append((c["corner_id"], abs(m["i_up_ua"]), abs(m["i_dn_ua"])))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", required=True)
    ap.add_argument("--request", default=str(HERE / "cp_icp_corners.request.json"))
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--id", required=True)
    ap.add_argument("--commit", default="unknown")
    a = ap.parse_args(argv)
    raw = Path(a.report).read_bytes()
    rep = json.loads(raw)
    rows = currents(rep)
    out = Path(a.out_dir)
    gz, md = out / ("%s-icp-corners-klt-report.json.gz" % a.id), out / ("%s-icp-corners.md" % a.id)
    if gz.exists() or md.exists():
        sys.exit("records are append-only: %s exists" % md)
    out.mkdir(parents=True, exist_ok=True)
    gz.write_bytes(gzip.compress(raw, 9, mtime=0))
    allv = [v for _, u, d in rows for v in (u, d)]
    lo, hi = min(allv), max(allv)
    env, rem = rep["environment"], rep["environment"].get("remote", {})
    L = ["# cp-dc I_cp over the supply sub-corners %s" % a.id, "",
         "**Result (simulated, not measured): the charge-pump output current at V_out = 1.65 V, IREF = 20 uA per copy, spans %.1f to %.1f uA over the 18 supply sub-corners (%.1f %% to +%.1f %% of the 200 uA nominal), I_up and I_dn taken separately. 18 of 18 corners converged.**" % (lo, hi, (lo / ICP_NOM_UA - 1) * 100, (hi / ICP_NOM_UA - 1) * 100), "",
         "- **Scope**: the supply sub-corners of the spec 'Corner set' stage 2, {2.970, 3.630} V x {SLOW, TYP, FAST} x {-40, 27, 125} C. The cp has HV MOS only, so SLOW/TYP/FAST select `mos_ss`/`mos_tt`/`mos_ff` of `cornerMOShv.lib` (the HBT and MIM members of the DR-004 bundles do not enter). One operating point per corner (V_out = 1.65 V, the mid-compliance point of `20261023-171440-2d82c85.md`); the compliance window and mismatch sweep are not repeated per corner. IREF is an ideal 20 uA source in every corner, so this measures the mirror and supply effect on I_cp, not a reference-current spread.",
         "- **Method**: `klt sim` corner request `cp_icp_corners.request.json`, `analysis.kind` op, `expr` measurements `-i(VA)` (I_up, copy A with UP on) and `i(VMB)` (I_dn, copy B with DN on); `corners.supply_v` moves VDD and the UP/DN logic-high rail together. Netlist body `cp_icp.cir` includes `design/netlist/cp.spice`.",
         "- **Simulator**: %s on the Spot batch fleet (`engine_host` %s), %s. Job `%s`, %s." % (
             ngpin.engine(env.get("engine_version")), env.get("engine_host"), ngpin.verdict(env.get("engine_version")), rem.get("job_id"), rem.get("instance_type")),
         "- **Request** sha256 `%s`; report [`%s`](%s) sha256 (uncompressed JSON) `%s`" % (hashlib.sha256(Path(a.request).read_bytes()).hexdigest(), gz.name, gz.name, hashlib.sha256(raw).hexdigest()),
         "- **PDK**: `models.pdk` sg13g2 on the fleet image; `cornerMOShv.lib` and `psp103.osdi` staged from this host's IHP-Open-PDK v0.3.0 install",
         "- **Commit**: `%s` of this repository" % a.commit,
         "- **Jitter-like numbers**: none.", "",
         "| corner | I_up (uA) | I_dn (uA) | I_up - nominal (%) | I_dn - nominal (%) |", "|---|---|---|---|---|"]
    for cid, u, d in rows:
        L.append("| %s | %.2f | %.2f | %+.2f | %+.2f |" % (cid, u, d, (u / ICP_NOM_UA - 1) * 100, (d / ICP_NOM_UA - 1) * 100))
    md.write_text("\n".join(L) + "\n")
    print("%s: I_cp %.2f..%.2f uA" % (md, lo, hi))
    return 0


if __name__ == "__main__":
    sys.exit(main())
