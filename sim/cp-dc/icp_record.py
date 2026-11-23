#!/usr/bin/env python3
"""Write the record for a `klt sim` run of sim/cp-dc/cp_icp_corners.request.json (I_cp over the supply sub-corners).

    icp_record.py --report REPORT.json --out-dir sim/cp-dc/records --id YYYYMMDD-HHMMSS-sha [--commit SHA]

Copies the klt report next to the record (gzip, zeroed header) so sim/loop-model/envelope.py can read it.
The corner currents themselves come from the shared reader (icp_report.py), which checks the
report covers the request grid exactly once before anything is written.
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

from icp_report import REQUEST_PATH, currents, grid, load_request  # noqa: E402  (the shared reader, same directory)

ICP_NOM_UA = 200.0


def _grid_text(request):
    """The '{2.970, 3.630} V x {SLOW, TYP, FAST} x {-40, 27, 125} C' Scope fragment, read off the request grid."""
    points = grid(request)
    procs = list(dict.fromkeys(p for p, _, _ in points))
    supplies = list(dict.fromkeys(s for _, s, _ in points))
    temps = list(dict.fromkeys(t for _, _, t in points))

    def sup(s):
        vals = {v for _, v in s}
        return "%.3f" % vals.pop() if len(vals) == 1 else " ".join("%s=%.3f" % kv for kv in s)

    return "{%s} V x {%s} x {%s} C" % (", ".join(sup(s) for s in supplies), ", ".join(procs),
                                       ", ".join("%g" % t for t in temps))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--id", required=True)
    ap.add_argument("--commit", default="unknown")
    a = ap.parse_args(argv)
    raw = Path(a.report).read_bytes()
    rep = json.loads(raw)
    req = load_request()
    rows = currents(rep, req)
    n = len(rows)
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
         "**Result (simulated, not measured): the charge-pump output current at V_out = 1.65 V, IREF = 20 uA per copy, spans %.1f to %.1f uA over the %d supply sub-corners (%.1f %% to +%.1f %% of the 200 uA nominal), I_up and I_dn taken separately. %d of %d corners converged.**" % (lo, hi, n, (lo / ICP_NOM_UA - 1) * 100, (hi / ICP_NOM_UA - 1) * 100, n, n), "",
         "- **Scope**: the supply sub-corners of the spec 'Corner set' stage 2, %s. The cp has HV MOS only, so SLOW/TYP/FAST select `mos_ss`/`mos_tt`/`mos_ff` of `cornerMOShv.lib` (the HBT and MIM members of the DR-004 bundles do not enter). One operating point per corner (V_out = 1.65 V, the mid-compliance point of `20261023-171440-2d82c85.md`); the compliance window and mismatch sweep are not repeated per corner. IREF is an ideal 20 uA source in every corner, so this measures the mirror and supply effect on I_cp, not a reference-current spread." % _grid_text(req),
         "- **Method**: `klt sim` corner request `cp_icp_corners.request.json`, `analysis.kind` op, `expr` measurements `-i(VA)` (I_up, copy A with UP on) and `i(VMB)` (I_dn, copy B with DN on); `corners.supply_v` moves VDD and the UP/DN logic-high rail together. Netlist body `cp_icp.cir` includes `design/netlist/cp.spice`.",
         "- **Simulator**: %s on the Spot batch fleet (`engine_host` %s), %s. Job `%s`, %s." % (
             ngpin.engine(env.get("engine_version")), env.get("engine_host"), ngpin.verdict(env.get("engine_version")), rem.get("job_id"), rem.get("instance_type")),
         "- **Request** sha256 `%s`; report [`%s`](%s) sha256 (uncompressed JSON) `%s`" % (hashlib.sha256(REQUEST_PATH.read_bytes()).hexdigest(), gz.name, gz.name, hashlib.sha256(raw).hexdigest()),
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
