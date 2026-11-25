#!/usr/bin/env python3
"""PDK-free, fleet-free unit tests for the vco-prescaler-load C-grid record writer.

Synthetic klt report dicts only. Every write is redirected into tmp_path by pointing the module's
HERE at a scratch tree, so nothing under the real records/ directory is touched (append-only).
"""
import importlib.util
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "make_record.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("vpl_make_record", SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mr = _load_module()


def test_import_leaves_sys_path_and_output_untouched(capsys):
    before = list(sys.path)
    _load_module()
    assert sys.path == before
    out = capsys.readouterr()
    assert out.out == "" and out.err == ""


# ---- parse_args ----

def test_dsubw_is_an_exact_flag():
    dsubw, _, _, _, pos = mr.parse_args(["--dsubw", "id", "loaded=r.json"])
    assert dsubw is True and pos == ["id", "loaded=r.json"]
    dsubw, _, _, _, pos = mr.parse_args(["--dsub", "id"])
    assert dsubw is False
    assert pos == ["--dsub", "id"]  # not an abbreviation: left as a positional


def test_value_flags_take_next_argument_verbatim():
    _, controls, requests, note, pos = mr.parse_args(
        ["--control", "-c.csv", "--request", "-x=-r.json", "--note", "-n.md", "id", "loaded=r.json"])
    assert controls == ["-c.csv"]
    assert requests == ["-x=-r.json"]
    assert note == "-n.md"
    assert pos == ["id", "loaded=r.json"]


def test_last_note_wins_and_repeats_accumulate():
    _, controls, requests, note, _ = mr.parse_args(
        ["--note", "a.md", "--control", "c1", "--note", "b.md", "--control", "c2", "id"])
    assert note == "b.md"
    assert controls == ["c1", "c2"]
    assert requests == []


def test_no_note_is_none():
    assert mr.parse_args(["id"])[3] is None


# ---- requested_by_label ----

def _request(path, vddv, vctrl, temps=(27, 125), procs=("TYP", "SLOW")):
    path.write_text(json.dumps({"corners": {
        "temperature_c": list(temps), "process": [{"name": p} for p in procs],
        "params": {"vddv": vddv, "vctrl": vctrl}}}))
    return str(path)


def test_requested_by_label_rejects_other_labels(tmp_path):
    r = _request(tmp_path / "r.json", [3.3], [0.9])
    with pytest.raises(SystemExit):
        mr.requested_by_label(["both=" + r])
    with pytest.raises(SystemExit):
        mr.requested_by_label(["Loaded=" + r])


def test_requested_by_label_unions_and_keeps_empty_declared_grid(tmp_path):
    a = _request(tmp_path / "a.json", [3.3], [0.9], procs=("TYP",))
    b = _request(tmp_path / "b.json", [3.0], [1.1], procs=("TYP",))
    no125 = _request(tmp_path / "c.json", [3.3], [0.9], temps=(27,))
    got = mr.requested_by_label(["loaded=" + a, "loaded=" + b, "unloaded=" + no125])
    assert got["loaded"] == {("TYP", 3.3, 0.9), ("TYP", 3.0, 1.1)}
    assert "unloaded" in got and got["unloaded"] == set()  # declared, but asks for no 125 C unit
    assert "other" not in got


# ---- classify_units ----

def _u(status="pass", f=5.0, vpp=0.5, tst=100.0):
    return {"status": status, "f_ghz": f, "vpp": vpp, "tst_ps": tst}


def test_classify_units_partitions():
    good = _u()
    errored = _u(status="error", f=None, vpp=None, tst=None)
    no_osc = _u(f=None, vpp=None, tst=None)  # passed but never oscillated
    out_band = _u(f=6.0)
    low = _u(vpp=0.30)
    unreached = _u(tst=None)
    c = mr.classify_units([good, errored, no_osc, out_band, low, unreached])
    assert c["ok"] == [good, out_band, low, unreached]
    assert c["bad"] == [errored, no_osc]
    assert c["inband"] == [good, low, unreached]
    assert c["low"] == [low]
    assert c["unreached"] == [unreached]


def test_classify_units_empty():
    assert mr.classify_units([]) == {"ok": [], "bad": [], "inband": [], "low": [], "unreached": []}


# ---- main(): atomicity and write redirection ----

def _report(path, case_corners):
    corners = []
    for cid, proc, t, vdd, vctrl, status in case_corners:
        corners.append({
            "corner_id": cid, "process": proc, "temperature_c": t,
            "params": {"vddv": vdd, "vctrl": vctrl}, "status": status,
            "measurements": [{"name": "fosc_t40", "value": 6e-9}, {"name": "vpp", "value": 0.5},
                             {"name": "tst", "value": 1e-10}] if status == "pass" else [],
            "diagnostics": [] if status == "pass" else [{"severity": "error", "code": "abort"}]})
    path.write_text(json.dumps({"corners": corners,
                                "environment": {"engine_version": "46", "remote": {"job_id": "job-1"}}}))
    return str(path)


@pytest.fixture
def scratch(tmp_path, monkeypatch):
    """A scratch tree shaped like sim/corner-verification/vco-prescaler-load, with HERE pointed at it."""
    here = tmp_path / "sim" / "corner-verification" / "vco-prescaler-load"
    (here / "records").mkdir(parents=True)
    monkeypatch.setattr(mr, "HERE", str(here))
    rep = _report(tmp_path / "report.json", [("TYP/27C/a", "TYP", 27, 3.3, 0.9, "pass"),
                                              ("TYP/27C/b", "TYP", 27, 3.3, 1.1, "error")])
    return here, tmp_path, rep


def _snapshot(d):
    return {n: (d / n).read_bytes() for n in sorted(os.listdir(d))}


def test_main_writes_pair_only_into_scratch_records(scratch, capsys):
    here, tmp_path, rep = scratch
    spice = tmp_path / "design" / "netlist"
    spice.mkdir(parents=True)
    (spice / "prescaler.spice").write_text("* stub\n")
    real_records = os.path.join(HERE, "records")
    before = sorted(os.listdir(real_records))
    mr.main(["rid1", "loaded=" + rep])
    assert sorted(os.listdir(here / "records")) == ["rid1-corners.csv", "rid1.md"]
    assert sorted(os.listdir(real_records)) == before
    text = (here / "records" / "rid1.md").read_text()
    assert text.startswith("# vco-prescaler-load C-grid rid1")
    assert "1 errored" in text
    assert capsys.readouterr().out.strip() == text.strip()


def test_main_render_failure_leaves_existing_record_byte_identical(scratch):
    here, _, rep = scratch  # no design/netlist/prescaler.spice in the scratch tree: render raises
    md, csv_ = here / "records" / "rid1.md", here / "records" / "rid1-corners.csv"
    md.write_bytes(b"old markdown\n")
    csv_.write_bytes(b"old,csv\n")
    before = _snapshot(here / "records")
    with pytest.raises(FileNotFoundError):
        mr.main(["rid1", "loaded=" + rep])
    assert _snapshot(here / "records") == before


def test_main_render_failure_creates_no_new_record(scratch):
    here, _, rep = scratch
    with pytest.raises(FileNotFoundError):
        mr.main(["rid2", "loaded=" + rep])
    assert os.listdir(here / "records") == []
