#!/usr/bin/env python3
"""Grade the row 11 loop-power C-grid artifacts and write the dated append-only record.

    python3 -I make_record.py --stage 1 --art DIR [--art DIR ...] [--report R.json ...] \
        --jobs ID[,ID...] --out-dir records [--commit SHA]

DIR holds one sub-directory per corner (corner.json, ngspice.log), as downloaded by `klt sim --attach <shard job>`
into -o DIR/<job>. The values are read from the .meas lines of each corner's ngspice.log.
A corner counts as "divides" only if tfb (three FB periods, rise 1 to rise 4 after 40 ns) is 58.5-61.5 ns, i.e. FB = 50 MHz.
Not-dividing corners keep their currents, labelled not-a-row-11-number, and are left out of the min/typ/max.
PFD + CP + bias is NOT simulated here: a single nominal-corner constant from the newest sim/loop-tran record is added
and labelled as such.
The simulator pin verdict is computed by sim/ngpin.py from `environment.engine_version` of the klt reports named
with `--report`. Nothing is inferred from the downloaded corner artifacts: they carry no version this repo can
show (see report_engines). With no `--report` the record states the check as "unchecked", never as a match.
"""
import argparse
import datetime
import glob
import gzip
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
import ngpin  # noqa: E402  (the simulator pin check, computed once in sim/ngpin.py)

VDD_TXT = 3.3
PFD_CP_BIAS_MW = 1.71  # sim/loop-power/records/20261103-065025-67d1431-dirty.md, nominal corner only
BUDGET_MW = 20.0
TFB_LO, TFB_HI = 58.5e-9, 61.5e-9


def read_report(path):
    """A klt report JSON, plain or gzipped (`.json.gz`, as the records keep them)."""
    with open(path, "rb") as f:
        raw = f.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw)


def report_engines(paths, jobs=()):
    """The ngspice version each `--report` records, from `environment.engine_version`.

    The version is read only from a report the caller names: nothing is inferred from the
    artifact tree. The corner artifacts `klt sim --attach` downloads are not a source here --
    they carry no version this repo can show. `ngspice -b -o FILE` writes the start-up banner
    to stdout, not into FILE, and all 32 ngspice captures on file are `-o`-shaped and carry no
    `ngspice-<n>` line; a corner's `ngspice.log` is therefore not known to hold one. With no
    `--report` the list is empty and the record reads "unchecked" -- never "match".

    A report whose `environment.remote.job_id` names a job this record is not grading is
    refused rather than used: it would label these corners with a version they did not run on.
    """
    out = []
    for p in paths:
        env = read_report(p).get("environment") or {}
        jid = (env.get("remote") or {}).get("job_id")
        if jobs and jid and jid not in jobs:
            sys.exit("--report %s is job %s, which is not among --jobs (%s): it does not "
                     "describe these corners" % (p, jid, ", ".join(jobs)))
        out.append(env.get("engine_version"))
    return out


def meas(log, name):
    m = re.search(r"^%s\s+=\s+(\S+)" % name, log, re.M)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def load(dirs):
    rows = {}
    for root in dirs:
        for cj in glob.glob(os.path.join(root, "*", "corner.json")):
            cid = json.load(open(cj))["corner_id"]
            cdir = os.path.dirname(cj)
            log = open(os.path.join(cdir, "ngspice.log"), errors="replace").read()
            m = re.search(r"vddv=([0-9.]+)", cid)
            ip, idd = meas(log, "ipavg"), meas(log, "idavg")
            rows[cid] = {
                "id": cid, "proc": cid.split("/novdd/")[0], "t": int(re.search(r"/(-?\d+)C/", cid).group(1)),
                "vdd": float(m.group(1)), "ip": None if ip is None else -ip, "id_": None if idd is None else -idd,
                "tfb": meas(log, "tfb"), "pspp": meas(log, "pspp"),
                "converged": ip is not None and idd is not None,
                "diag": [l for l in log.splitlines() if "timestep too small" in l or "aborted" in l][:1],
            }
    return sorted(rows.values(), key=lambda r: (r["proc"], r["t"], r["vdd"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, required=True)
    ap.add_argument("--art", action="append", required=True)
    ap.add_argument("--report", action="append", default=[],
                    help="klt report JSON for a shard job (repeatable). The simulator pin verdict is "
                         "computed from environment.engine_version of these reports; with none given the "
                         "record states the check as unchecked.")
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--commit", default="unknown")
    ap.add_argument("--expected", type=int, required=True)
    a = ap.parse_args()
    dirs = []
    for d in a.art:
        dirs += [x for x in glob.glob(os.path.join(d, "klt-sim-*")) if os.path.isdir(x)] or [d]
    rows = load(dirs)
    engines = report_engines(a.report, [j for j in a.jobs.split(",") if j])
    for r in rows:
        r["divides"] = r["converged"] and r["tfb"] is not None and TFB_LO <= r["tfb"] <= TFB_HI
        r["pp"] = None if not r["divides"] else r["ip"] * r["vdd"] * 1e3
        r["pd"] = None if not r["divides"] else r["id_"] * r["vdd"] * 1e3
        r["sum"] = None if not r["divides"] else r["pp"] + r["pd"] + PFD_CP_BIAS_MW
    ok = [r for r in rows if r["divides"]]
    nconv = sum(r["converged"] for r in rows)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = os.path.join(a.out_dir, "%s-%s-stage%d.md" % (stamp, a.commit, a.stage))
    assert not os.path.exists(path), "records are append-only"
    out = []
    w = out.append
    w("# loop-power C-grid envelope, stage %d (%s)\n" % (a.stage, stamp))
    if ok:
        mx = max(ok, key=lambda r: r["sum"])
        mn = min(ok, key=lambda r: r["sum"])
        nbad = len(rows) - len(ok)
        if mx["sum"] > BUDGET_MW or nbad or len(rows) < a.expected:
            verdict = "fail"
        else:
            verdict = "within the 20 mW target before the owed blocks"
        w("**Result (simulated, not measured): **%s**. %d of %d expected corners returned, %d converged, only %d divide to 50 MHz; "
          "the other %d are not-a-row-11-number (row 11 is graded locked at 5.0 GHz, so a corner that does not divide fails the row's condition). "
          "Over the %d dividing corners the sum (prescaler + M/A divider + PFD/CP/bias nominal constant) is %.2f to %.2f mW against the %.0f mW target "
          "(binding: %s %d C %.2f V); this excludes the lock detector, reference and clock buffering, which are owed (up to 8 mW allocated), so it is not a pass. "
          "The target is not relaxed; #84 owns the budget.**\n"
          % (verdict, len(rows), a.expected, nconv, len(ok), nbad, len(ok), mn["sum"], mx["sum"], BUDGET_MW, mx["proc"], mx["t"], mx["vdd"]))
    else:
        w("**Result (simulated, not measured): INCOMPLETE, no row 11 number. %d of %d expected corners returned (the rest were never run or never returned: shard jobs failed, "
          "were interrupted, or were still pending when the submitter hit its time limit), %d converged, %d divide to 50 MHz. This is not a pass and not an envelope; "
          "the missing corners are owed.**\n" % (len(rows), a.expected, nconv, len(ok)))
    w(("- **Method**: `klt sim` on the Spot batch fleet (`backend batch`), request `request-stage%d.json` generated by `make_requests.py`; "
      "transient `4p 120n`, supply current of each rail averaged over 40-120 ns (`.meas avg`), power = V_dd x |I|. Division check: `tfb` = three FB periods "
      "(rise 1 to rise 4 after 40 ns) must be 58.5-61.5 ns (FB = 50 MHz at N = 100). Fleet shard jobs: %s.") % (a.stage, "`" + a.jobs.replace(",", "`, `") + "`"))
    w("- **Simulator**: the fleet ran %s, %s. The earlier nominal record (`sim/loop-power/records/`) used a different start-up, see below; "
      "a divide failure here may be a start-up artifact of the ramp and is not proven to be a design failure."
      % (ngpin.engine(engines, unknown="an ngspice version no `--report` was given to state"),
         ngpin.verdict(engines, source="the reports given with `--report`")))
    w("- **Start-up (differs from `scripts/run-loop-power.sh`)**: the HBT prescaler DC operating point did not converge from the powered state at most corners "
      "(`timestep too small` on the reference HBT; a first pass of 18 stage-2 corners returned 4 converged). Supplies, IREF and the drive common mode ramp from 0 V over 3 ns "
      "(`loop_power_body.spice`); the window is 40-120 ns. No `.ic`/`.nodeset` seeding of the latches.")
    w("- **PFD + CP + bias**: %.2f mW, **one nominal-corner constant** from `sim/loop-power/records/20261103-065025-67d1431-dirty.md`; it is not simulated per corner here, "
      "so the per-corner sum carries nominal PFD/CP/bias, not a corner value." % PFD_CP_BIAS_MW)
    w("- **Owed, not zero**: lock detector, reference and clock buffering have no schematic and are not counted (row 11 allocates up to 4 mW for counters + lock detector and up to 4 mW for buffering).")
    w("- **Commit**: `%s`; netlists `design/netlist/{prescaler,divider}.spice` as of that commit.\n" % a.commit)
    w("| corner | T (C) | Vdd (V) | converged | divides | prescaler (mW) | M/A divider (mW) | sum with PFD/CP/bias (mW) | tfb (ns) |")
    w("|---|---|---|---|---|---|---|---|---|")
    f = lambda v, p=2: "-" if v is None else "%.*f" % (p, v)
    for r in rows:
        if r["divides"]:
            pp, pd, s = f(r["pp"]), f(r["pd"]), f(r["sum"])
        elif r["converged"]:
            pp, pd, s = ("not-a-row-11-number %s" % f(r["ip"] * r["vdd"] * 1e3), f(r["id_"] * r["vdd"] * 1e3), "-")
        else:
            pp, pd, s = "-", "-", "-"
        w("| %s | %d | %.2f | %s | %s | %s | %s | %s | %s |" % (r["proc"], r["t"], r["vdd"], "yes" if r["converged"] else "NO", "yes" if r["divides"] else "NO",
                                                              pp, pd, s, f(None if r["tfb"] is None else r["tfb"] * 1e9, 1)))
    w("\nCorners that did not converge or do not divide are findings, not passes, and are excluded from the envelope.")
    open(path, "w").write("\n".join(out) + "\n")
    print(path)


if __name__ == "__main__":
    main()
