"""The shared I_cp report reader (icp_report.py) and the charge-pump record CLI (#368).

The archive `records/20261103-030519-221e27b-icp-corners-klt-report.json.gz` is the full
18-corner grid; the altered inputs vary only its corners array, on copies in tmp_path.
An incomplete or duplicated grid must fail the reader and `icp_record.py` with a nonzero
exit before any output file is written. The row-5 consumer (`sim/loop-model/envelope.py`)
is exercised on the same cases in `sim/loop-model/test_envelope.py`.
"""
import gzip
import json
import subprocess
import sys
from pathlib import Path

import pytest

import icp_record
import icp_report

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "records" / "20261103-030519-221e27b-icp-corners-klt-report.json.gz"


def _report():
    return json.loads(gzip.decompress(ARCHIVE.read_bytes()))


def _single_row(d):
    d["corners"] = d["corners"][:1]


def _duplicate_last(d):
    d["corners"][-1] = d["corners"][0]


ALTERATIONS = {"incomplete": _single_row, "duplicate": _duplicate_last}


def _altered_report(path, how):
    d = _report()
    how(d)
    path.write_text(json.dumps(d))
    return path


def _cli(*args):
    return subprocess.run([sys.executable, str(HERE / "icp_record.py"), *args],
                          capture_output=True, text=True)


def test_reader_accepts_the_archive_and_keeps_the_recorded_range():
    rows = icp_report.currents(_report(), icp_report.load_request())
    assert len(rows) == 18
    vals = [v for _, u, d in rows for v in (u, d)]
    assert min(vals) == pytest.approx(189.40, abs=0.005)
    assert max(vals) == pytest.approx(203.87, abs=0.005)


def test_reader_refuses_the_incomplete_grid():
    d = _report()
    _single_row(d)
    with pytest.raises(SystemExit, match="covers 1 of the 18"):
        icp_report.currents(d, icp_report.load_request())


def test_reader_refuses_a_duplicated_grid_point():
    d = _report()
    _duplicate_last(d)
    with pytest.raises(SystemExit, match="duplicates the grid point"):
        icp_report.currents(d, icp_report.load_request())


def test_reader_refuses_a_corner_off_the_request_grid():
    d = _report()
    d["corners"][-1] = dict(d["corners"][-1], temperature_c=85)
    with pytest.raises(SystemExit, match="is not on the cp_icp_corners request grid"):
        icp_report.currents(d, icp_report.load_request())


def test_cli_accepts_the_original_archive(tmp_path):
    report = tmp_path / "report.json"
    report.write_bytes(gzip.decompress(ARCHIVE.read_bytes()))
    out = tmp_path / "out"
    r = _cli("--report", str(report), "--out-dir", str(out), "--id", "t")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "I_cp 189.40..203.87 uA" in r.stdout
    md = (out / "t-icp-corners.md").read_text()
    assert "18 of 18 corners converged" in md
    assert (out / "t-icp-corners-klt-report.json.gz").exists()


@pytest.mark.parametrize("case", sorted(ALTERATIONS))
def test_cli_refuses_an_altered_grid_before_writing(tmp_path, case):
    report = _altered_report(tmp_path / "altered.json", ALTERATIONS[case])
    out = tmp_path / "out"
    r = _cli("--report", str(report), "--out-dir", str(out), "--id", "t")
    assert r.returncode != 0, r.stdout + r.stderr
    assert "corner" in (r.stderr + r.stdout)
    assert not out.exists() or not any(out.iterdir())


def test_cli_has_no_request_override_so_a_partial_report_cannot_pass(tmp_path):
    d = _report()
    _single_row(d)
    report = tmp_path / "one-corner.json"
    report.write_text(json.dumps(d))
    req = icp_report.load_request()
    first = d["corners"][0]
    req["corners"]["process"] = [p for p in req["corners"]["process"] if p["name"] == first["process"]]
    req["corners"]["supply_v"] = {r: [v for v in vs if v == first["supply_v"][r]]
                                  for r, vs in req["corners"]["supply_v"].items()}
    req["corners"]["temperature_c"] = [t for t in req["corners"]["temperature_c"]
                                       if t == first["temperature_c"]]
    narrowed = tmp_path / "narrowed.request.json"
    narrowed.write_text(json.dumps(req))
    out = tmp_path / "out"
    r = _cli("--report", str(report), "--request", str(narrowed),
             "--out-dir", str(out), "--id", "t")
    assert r.returncode != 0, r.stdout + r.stderr
    assert "unrecognized arguments" in r.stderr
    assert not out.exists() or not any(out.iterdir())


def _narrowed_request(d, tmp_path):
    """A request copy cut down to the single grid point of the report's first corner."""
    req = icp_report.load_request()
    first = d["corners"][0]
    req["corners"]["process"] = [p for p in req["corners"]["process"] if p["name"] == first["process"]]
    req["corners"]["supply_v"] = {r: [v for v in vs if v == first["supply_v"][r]]
                                  for r, vs in req["corners"]["supply_v"].items()}
    req["corners"]["temperature_c"] = [t for t in req["corners"]["temperature_c"]
                                       if t == first["temperature_c"]]
    narrowed = tmp_path / "narrowed.request.json"
    narrowed.write_text(json.dumps(req))
    return narrowed


def test_writer_derives_the_count_and_grid_from_a_narrowed_request(tmp_path, monkeypatch):
    d = _report()
    d["corners"] = d["corners"][:1]
    report = tmp_path / "one-corner.json"
    report.write_text(json.dumps(d))
    monkeypatch.setattr(icp_report, "REQUEST_PATH", _narrowed_request(d, tmp_path))
    out = tmp_path / "out"
    assert icp_record.main(["--report", str(report), "--out-dir", str(out), "--id", "t"]) == 0
    md = (out / "t-icp-corners.md").read_text()
    assert "1 of 1 corners converged" in md
    assert "over the 1 supply sub-corners" in md
    assert "{2.970} V x {SLOW} x {-40} C" in md
    assert "18 of 18" not in md
    assert "the 18 supply sub-corners" not in md


def test_writer_derives_the_count_from_a_wider_request_grid(tmp_path, monkeypatch):
    d = _report()
    req = icp_report.load_request()
    req["corners"]["temperature_c"] = req["corners"]["temperature_c"] + [85]
    widened = tmp_path / "widened.request.json"
    widened.write_text(json.dumps(req))
    d["corners"] = d["corners"] + [dict(c, temperature_c=85) for c in d["corners"]
                                   if c["temperature_c"] == -40]
    report = tmp_path / "24-corner.json"
    report.write_text(json.dumps(d))
    monkeypatch.setattr(icp_report, "REQUEST_PATH", widened)
    out = tmp_path / "out"
    assert icp_record.main(["--report", str(report), "--out-dir", str(out), "--id", "t"]) == 0
    md = (out / "t-icp-corners.md").read_text()
    assert "24 of 24 corners converged" in md
    assert "over the 24 supply sub-corners" in md
    assert "{-40, 27, 125, 85} C" in md
    assert "18 of 18" not in md
