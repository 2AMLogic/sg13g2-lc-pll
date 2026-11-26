"""The cp-mc record writer takes the worst-corner limit of each measurement from the maximum recorded for that
measurement in the target yield report, the limit `klt yield` graded the samples against (#492). Two mismatch
measurements with different limits and the same samples get their own displayed limit and failure count, and a
sample equal to the limit is not over it. Synthetic one-corner reports only: no PDK, no fleet."""
import json
import subprocess
import sys
from pathlib import Path

SUMMARIZE = Path(__file__).resolve().parent / "summarize.py"
CORNER = "mos_tt_mismatch/3.300V/27C"
SAMPLES = [2.0, 2.5, 3.0]  # 2.0 sits on the 2 % limit and 3.0 on the 3 % one: neither is over it
TARGET = {"mm_v165_pct": 2.0, "mm_v200_pct": 3.0}
FALLBACK = {"mm_v165_pct": 6.0, "mm_v200_pct": 9.0}


def _yield(names, maxima):
    """A `klt yield` report of SAMPLES, each measurement graded against its own recorded maximum."""
    ms = []
    for n in names:
        over = sum(v > maxima[n] for v in SAMPLES)
        ms.append({"name": n, "unit": "%", "n": len(SAMPLES), "status": "fail" if over else "pass",
                   "limits": {"max": maxima[n], "target_yield": 0.9973},
                   "distribution": {"mean": sum(SAMPLES) / len(SAMPLES), "stddev": 0.1, "max": max(SAMPLES)},
                   "yield": {"empirical": {"estimate": 1 - over / len(SAMPLES),
                                           "confidence_interval": {"low": 0.0, "high": 1.0}}},
                   "sample_size": {"verdict": "sufficient"}, "negative_control": {"verdict": "detected"}})
    return {"measurements": ms, "warnings": []}


def _record(tmp_path, target=TARGET, fallback=FALLBACK):
    names = list(target)
    raw = [{"name": "up_v165.cur", "value": 1e-4}, {"name": "dn_v165.cur", "value": 1.01e-4}]
    nom = {"corners": [{"corner_id": "%s/mc%d" % (CORNER, i),
                        "measurements": raw + [{"name": n, "value": v} for n in names]} for i, v in enumerate(SAMPLES)],
           "environment": {"engine_version": "46", "engine_host": "worker"}}
    paths = {k: tmp_path / (k + ".json") for k in ("nom", "neg", "yt", "yf")}
    for k, obj in (("nom", nom), ("neg", {"corners": []}), ("yt", _yield(names, target)), ("yf", _yield(names, fallback))):
        paths[k].write_text(json.dumps(obj))
    return subprocess.run(
        [sys.executable, str(SUMMARIZE), str(paths["nom"]), str(paths["neg"]), str(paths["yt"]), str(paths["yf"]),
         "--id", "t", "--commit", "deadbeef", "--pdk-tag", "v0.0.0", "--host", "h", "--klt", "klt 0",
         "--n", str(len(SAMPLES)), "--n-control", "1", "--seed", "1"],
        capture_output=True, text=True, check=True).stdout


def _line(md, start):
    return next(l for l in md.splitlines() if l.startswith(start))


def test_worst_corner_rows_take_each_limit_from_the_target_report(tmp_path):
    md = _record(tmp_path)
    assert _line(md, "| mm_v165_pct |") == "| mm_v165_pct | 2 | %s | 3 | 1 of 1 | 2 of 3 |" % CORNER
    assert _line(md, "| mm_v200_pct |") == "| mm_v200_pct | 3 | %s | 3 | 0 of 1 | 0 of 3 |" % CORNER
    assert "up_v165.cur" not in md  # in the nominal report, but not graded, so not in the target report


def test_limit_text_is_read_from_the_reports_not_typed(tmp_path):
    md = _record(tmp_path)
    est = _line(md, "- **Estimator**")
    assert ("limits `sim/cp-mc/limits-target.json` (maximum recorded per measurement: 2 %, 3 %) and "
            "`limits-fallback.json` (6 %, 9 %)") in est
    assert _line(md, "## Pooled yield") == (
        "## Pooled yield, target limits (spec rows 7 and 9; per-measurement maximum as recorded in the target "
        "yield report)")
    for typed in ("mismatch <= 2 %", "0.52 mV", "1.644"):
        assert typed not in md
