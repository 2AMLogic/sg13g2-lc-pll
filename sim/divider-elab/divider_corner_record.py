#!/usr/bin/env python3
"""Grade a `klt sim` report of divider_corner_{speed,count}.request.json and write the record.

Per run: windows are the intervals between consecutive rising FB edges (>= 3 edges needed); clocks are rising CK edges in a
window, MC-high clocks are those where MC was high 0.3 ns before the edge (state from the MC rise/fall crossings);
N = 8 x clocks + MC-high (prescaler P = 8/9). The run passes if every full window gives the expected N = 8 M + A
(M, A decoded from the tie voltages in the run's params). A run that did not converge, whose crossing lists were truncated,
or that has fewer than 3 FB edges is never a pass: verdict FAIL if any converged run gives a wrong N, else INCOMPLETE
if any is not graded, else PASS.

    divider_corner_record.py --report R.json [--report R2.json ...] --out-dir DIR --id ID --commit SHA
"""
import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEAD = 0.3e-9


def _code(p):
    bit = lambda k, n: sum((1 << i) for i in range(n) if float(p[f"{k}{i}v"]) > 1.65)
    return bit("m", 4), bit("a", 3)


def _meas(c, name):
    for m in c["measurements"]:
        if m["name"] == name:
            return m.get("crossings") or {}
    return {}


def mc_high_at(rise, fall, t):
    ev = sorted([(x, 1) for x in rise] + [(x, 0) for x in fall])
    state = 1 if (ev and ev[0][1] == 0) else 0   # first event a fall: MC started high
    for x, s in ev:
        if x > t:
            break
        state = s
    return state


def grade_run(c):
    p = c.get("params") or {}
    m, a = _code(p)
    want = 8 * m + a
    row = {"corner": f"{c['process']}/{c['temperature_c']}C", "fin_mhz": float(p["fin"]) / 1e6, "m": m, "a": a, "want": want,
           "fb_edges": None, "ck": None, "mc_hi": None, "n": None, "status": "not-graded", "why": ""}
    cr = {k: _meas(c, k) for k in ("ck_rise", "fb_rise", "mc_rise", "mc_fall")}
    if c["status"] not in ("pass", "fail") or any(not v for v in cr.values()):
        row["why"] = "did not converge" if c["status"] not in ("pass", "fail") else "no crossing data"
        return row
    if any(v.get("truncated") for v in cr.values()):
        row["why"] = "crossing list truncated"
        return row
    fb, ck = cr["fb_rise"]["times"], cr["ck_rise"]["times"]
    row["fb_edges"] = len(fb)
    if len(fb) < 3:
        row["why"] = "no toggle (fewer than 3 FB edges)"
        return row
    ns = []
    for x, y in zip(fb, fb[1:]):
        e = [t for t in ck if x <= t < y]
        hi = sum(1 for t in e if mc_high_at(cr["mc_rise"]["times"], cr["mc_fall"]["times"], t - LEAD))
        ns.append((8 * len(e) + hi, len(e), hi))
    row["ck"], row["mc_hi"] = ns[-1][1], ns[-1][2]
    row["n"] = ns[-1][0] if len({n for n, _, _ in ns}) == 1 else None
    row["status"] = "pass" if row["n"] == want else "FAIL"
    row["why"] = "" if row["n"] is not None else "window N inconsistent: " + ",".join(str(n) for n, _, _ in ns)
    return row


def grade(report):
    rows = [grade_run(c) for c in report["corners"]]
    bad = sum(1 for r in rows if r["status"] == "FAIL")
    ng = sum(1 for r in rows if r["status"] == "not-graded")
    return {"rows": rows, "verdict": "FAIL" if bad else ("INCOMPLETE" if ng else "PASS"), "n_fail": bad, "n_not_graded": ng}


def render(parts, rec_id, commit):
    out = [f"# divider corner check {rec_id}", ""]
    allrows = [r for _, g, _, _ in parts for r in g["rows"]]
    verdict = "FAIL" if any(g["verdict"] == "FAIL" for _, g, _, _ in parts) else ("INCOMPLETE" if any(g["verdict"] == "INCOMPLETE" for _, g, _, _ in parts) else "PASS")
    out += [f"**Result (simulated, not measured): **{verdict}**: {sum(r['status']=='pass' for r in allrows)} of {len(allrows)} runs divide to the expected N; "
            f"{sum(r['status']=='FAIL' for r in allrows)} wrong, {sum(r['status']=='not-graded' for r in allrows)} not graded.**", ""]
    out += ["- **Scope**: the real divider chain (`cml2cmos` + counters, 3-bit `acounter`, `design/netlist/divider.spice`) at SLOW (hbt_wcs, mos_ss, cap_wcs), TYP (hbt_typ, mos_tt, cap_typ) and FAST (hbt_bcs, mos_ff, cap_bcs) x -40 / 27 / 125 C, 3.3 V. TYP/27C is the nominal point. Not covered: supply other than 3.3 V, the real prescaler driving the converter (ideal 0.4 Vpp sine at 3.18 V common mode instead), layout, noise, Monte Carlo, N codes other than those listed.",
            "- **Method**: `klt sim` corner requests (`gen_corner_requests.py`), batch fleet; tran with crossing measurements of `xd.ck`, `fb` and `mc` at 1.65 V; N = 8 x clocks + MC-high clocks per FB window (MC sampled 0.3 ns before each CK edge), required equal to 8 M + A on every full window, >= 3 FB edges. Speed requests: 150 ns, fin 625 / 687.5 MHz (= 5.0 / 5.5 GHz / 8). Count request: 640 ns at 100 MHz.",
            f"- **Commit**: `{commit}` of this repository", ""]
    for name, g, rep, req in parts:
        env, rem = rep["environment"], rep["environment"].get("remote", {})
        out += [f"## {name}", "", f"Request `{req.name}` sha256 `{hashlib.sha256(req.read_bytes()).hexdigest()}`; `ngspice-{env.get('engine_version')}`, job `{rem.get('job_id')}`, {rem.get('instance_type')}, {rem.get('lifecycle')}; verdict **{g['verdict']}**.", "",
                "| corner | fin (MHz) | M | A | FB edges | CK/window | MC-high | N | expected N | result |", "|---|---|---|---|---|---|---|---|---|---|"]
        for r in g["rows"]:
            out.append("| %s | %g | %d | %d | %s | %s | %s | %s | %d | %s%s |" % (r["corner"], r["fin_mhz"], r["m"], r["a"], r["fb_edges"], r["ck"], r["mc_hi"],
                       r["n"], r["want"], r["status"], (": " + r["why"]) if r["why"] else ""))
        out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--part", action="append", nargs=3, metavar=("NAME", "REPORT", "REQUEST"), required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--id", required=True)
    ap.add_argument("--commit", default="unknown")
    a = ap.parse_args(argv)
    rec = Path(a.out_dir) / f"{a.id}-corners.md"
    if rec.exists():
        sys.exit(f"records are append-only: {rec} exists")
    Path(a.out_dir).mkdir(parents=True, exist_ok=True)
    parts = []
    for name, rep, req in a.part:
        raw = Path(rep).read_bytes()
        gz = Path(a.out_dir) / f"{a.id}-{name}-klt-report.json.gz"
        if gz.exists():
            sys.exit(f"records are append-only: {gz} exists")
        gz.write_bytes(gzip.compress(raw, 9, mtime=0))
        r = json.loads(raw)
        parts.append((name, grade(r), r, Path(req)))
    rec.write_text(render(parts, a.id, a.commit))
    print(rec, [g["verdict"] for _, g, _, _ in parts])
    return 0


if __name__ == "__main__":
    sys.exit(main())
