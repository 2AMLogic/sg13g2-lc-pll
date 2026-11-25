"""Negative controls for the /8-/9 grader: a wrong ratio, a collapsed swing, a glitchy modulus sequence, a unit that
did not run must each fail or be incomplete; only a clean series passes. CLI replays of the archived l7p8 reports:
an empty supplied report is INCOMPLETE (never PASS), a graded failure takes precedence over one."""
import gzip
import json
import shutil
import sys

import pytest
from pathlib import Path

import div89_record as d

TIN = 1 / 5.5e9
REC = Path(__file__).parent / "records"
L7P8 = "20261110-186-cml-dff-latch-l7p8"


def _x(times):
    return {"times": times, "edges": ["rise"] * len(times), "truncated": False}


def _series(periods_in_tin, t0=8e-9):
    t, out = t0, [t0]
    for n in periods_in_tin:
        t += n * TIN
        out.append(t)
    return out


def _corner(periods, hi_drop=0, status="pass", mcv=0.0, phi=None):
    z = _series(periods)
    params = {"vddv": 3.3, "fin": 5.5e9, "mcv": mcv}
    if phi is not None:
        params = {"vddv": 3.3, "fin": 5.5e9, "phi": phi}
    ms = [{"name": "x_zero", "crossings": _x(z)},
          {"name": "x_hi", "crossings": _x(z[hi_drop:])},
          {"name": "x_lo", "crossings": _x(z[hi_drop:])}]
    return {"corner_id": "TYP/27C", "process": "TYP", "temperature_c": 27, "params": params, "status": status,
            "diagnostics": [], "measurements": ms}


def test_clean_div8_and_div9_pass():
    assert d.grade_chain_corner(_corner([8] * 10))["ok"]
    assert d.grade_chain_corner(_corner([9] * 10, mcv=1.0))["ok"]


def test_wrong_ratio_fails():
    assert not d.grade_chain_corner(_corner([9] * 10, mcv=0.0))["ok"]          # /9 where /8 was asked
    assert not d.grade_chain_corner(_corner([8] * 9 + [10]))["ok"]             # one /10 hiccup


def test_collapsed_swing_fails():
    r = d.grade_chain_corner(_corner([8] * 10, hi_drop=5))
    assert not r["ok"] and "swing" in r["why"]


def test_too_few_edges_or_error_is_not_a_pass():
    assert not d.grade_chain_corner(_corner([8] * 3))["ok"]
    r = d.grade_chain_corner(_corner([8] * 10, status="error"))
    assert not r["ran"] and not r["ok"]
    assert d.verdict([r]) == "INCOMPLETE"
    assert d.verdict([r, dict(r, ran=True, ok=False)]) == "FAIL"


def test_async_clean_sequence_passes():
    assert d.grade_async_corner(_corner([8] * 3 + [9] * 5 + [8] * 4, phi=3e-10))["ok"]


def test_async_glitches_fail():
    for seq in ([8] * 3 + [10] + [9] * 4 + [8] * 3,          # /10 in the sequence
                [8] * 3 + [17] + [8] * 4,                     # two swallows in one period
                [8, 8, 9, 8, 9, 9, 9, 8, 8, 8, 8, 8],         # 8 9 8 9 hiccup: more than two changes
                [9] * 4 + [8] * 8,                            # starts on 9
                [8] * 12):                                    # MC pulse never swallowed
        assert not d.grade_async_corner(_corner(seq, phi=3e-10))["ok"], seq


def test_empty_collection_is_incomplete():
    assert d.verdict([]) == "INCOMPLETE"
    assert d._verdict([]) == "INCOMPLETE"
    assert d._verdict(["PASS", "INCOMPLETE"]) == "INCOMPLETE"
    assert d._verdict(["INCOMPLETE", "FAIL"]) == "FAIL"
    assert d._verdict(["PASS", "PASS"]) == "PASS"


def test_grade_grades_each_supplied_report_before_combining():
    g = d.grade({"corners": []}, [{"corners": []}, {"corners": []}])
    assert g["chain_verdict"] == "INCOMPLETE"
    assert g["async_report_counts"] == [0, 0]
    assert g["async_report_verdicts"] == ["INCOMPLETE", "INCOMPLETE"]
    assert g["async_verdict"] == "INCOMPLETE"


def _report(name):
    with gzip.open(REC / ("%s-%s.json.gz" % (L7P8, name))) as f:
        return json.load(f)


def _record(monkeypatch, tmp_path, reports):
    paths = []
    for stem, rep in reports:
        p = tmp_path / ("report-%s.json" % stem)
        p.write_text(json.dumps(rep))
        paths.append(str(p))
    out = tmp_path / "records"
    monkeypatch.setattr(sys, "argv", ["div89_record.py", "--chain", paths[0], "--async", *paths[1:],
                                      "--out-dir", str(out), "--id", "t", "--commit", "0000000"])
    d.main()
    return (out / "t.md").read_text()


def _force_ratio_fail(c):
    t, times = 8e-9, []
    for _ in range(11):
        times.append(t)
        t += 10 * (1.0 / c["params"]["fin"])
    for m in c["measurements"]:
        if m["name"] in ("x_zero", "x_hi", "x_lo"):
            m["crossings"] = {"times": list(times), "edges": ["rise"] * len(times), "truncated": False}
    c["status"] = "pass"


def test_cli_replayed_reports_pass(monkeypatch, tmp_path):
    md = _record(monkeypatch, tmp_path, [("div89_chain", _report("div89_chain")),
                                         ("div89_async_2p97", _report("div89_async_2p97")),
                                         ("div89_async_3p63", _report("div89_async_3p63"))])
    assert "Overall: PASS." in md
    assert "PASS (288 of 288 pass)" in md
    assert "288 async corner(s) observed across 2 supplied report(s) (144 + 144 by report)" in md


def test_cli_empty_async_report_is_incomplete_not_pass(monkeypatch, tmp_path):
    a3 = _report("div89_async_3p63")
    a3["corners"] = []
    md = _record(monkeypatch, tmp_path, [("div89_chain", _report("div89_chain")),
                                         ("div89_async_2p97", _report("div89_async_2p97")),
                                         ("div89_async_3p63", a3)])
    assert "Overall: INCOMPLETE." in md
    assert "INCOMPLETE (144 of 144 pass)" in md
    assert "144 async corner(s) observed across 2 supplied report(s) (144 + 0 by report)" in md


def test_cli_all_reports_empty_is_incomplete(monkeypatch, tmp_path):
    reports = []
    for stem in ("div89_chain", "div89_async_2p97", "div89_async_3p63"):
        rep = _report(stem)
        rep["corners"] = []
        reports.append((stem, rep))
    md = _record(monkeypatch, tmp_path, reports)
    assert "Overall: INCOMPLETE." in md
    assert "0 async corner(s) observed across 2 supplied report(s) (0 + 0 by report)" in md
    assert "INCOMPLETE (0 of 0 pass)" in md


def test_cli_graded_failure_takes_precedence_over_empty_report(monkeypatch, tmp_path):
    chain = _report("div89_chain")
    _force_ratio_fail(chain["corners"][0])
    a3 = _report("div89_async_3p63")
    a3["corners"] = []
    md = _record(monkeypatch, tmp_path, [("div89_chain", chain),
                                         ("div89_async_2p97", _report("div89_async_2p97")),
                                         ("div89_async_3p63", a3)])
    assert "Overall: FAIL." in md


# --- The headline's grid parenthesis and the PDK process-to-section mapping come from the
# --- chain request the CLI already resolves and hashes, never typed back in (#401). ---

def test_cli_derives_the_headline_grid_and_pdk_map_from_the_chain_request(monkeypatch, tmp_path):
    fake_here = tmp_path / "sim/prescaler-div89"
    fake_here.mkdir(parents=True)
    (tmp_path / "design/netlist").mkdir(parents=True)
    shutil.copyfile(d.HERE.parent.parent / "design/netlist/prescaler.spice",
                    tmp_path / "design/netlist/prescaler.spice")
    for stem in ("div89_async_2p97", "div89_async_3p63"):
        shutil.copyfile(d.HERE / ("%s.request.json" % stem), fake_here / ("%s.request.json" % stem))
    req = json.loads((d.HERE / "div89_chain.request.json").read_text())
    req["corners"]["process"] = [{"name": "NOM", "sections": [
        {"lib": "libs.tech/ngspice/models/cornerHBT.lib", "section": "hbt_nom_x"},
        {"lib": "libs.tech/ngspice/models/cornerRES.lib", "section": "res_nom_y"}]}]
    req["corners"]["temperature_c"] = [27]
    req["corners"]["params"]["vddv"] = [3.3, 3.3]
    (fake_here / "div89_chain.request.json").write_text(json.dumps(req))
    monkeypatch.setattr(d, "HERE", fake_here)
    md = _record(monkeypatch, tmp_path, [("div89_chain", _report("div89_chain")),
                                         ("div89_async_2p97", _report("div89_async_2p97")),
                                         ("div89_async_3p63", _report("div89_async_3p63"))])
    assert "over 108 chain corners (NOM x 27 C x 3.300 V):" in md
    assert "SLOW/TYP/FAST" not in md
    assert "NOM = hbt_nom_x + res_nom_y" in md
    assert "hbt_wcs" not in md and "res_wcs" not in md
    # The async stimulus description and the observed counts are untouched by the derivation.
    assert "16 phases of the output period (5.5 GHz, 2.970 and 3.630 V)" in md
    assert "288 async corner(s) observed across 2 supplied report(s)" in md


def test_cli_refuses_an_existing_json_gz_and_leaves_it_untouched(monkeypatch, tmp_path):
    out = tmp_path / "records"
    out.mkdir()
    stale = out / "r1-div89_chain.json.gz"
    stale.write_bytes(b"keep me")
    p = tmp_path / "report-div89_chain.json"
    p.write_text(json.dumps(_report("div89_chain")))
    q = tmp_path / "report-div89_async_2p97.json"
    q.write_text(json.dumps(_report("div89_async_2p97")))
    monkeypatch.setattr(sys, "argv", ["div89_record.py", "--chain", str(p), "--async", str(q),
                                      "--out-dir", str(out), "--id", "r1"])
    with pytest.raises(SystemExit) as e:
        d.main()
    assert "r1-div89_chain.json.gz" in str(e.value)
    assert stale.read_bytes() == b"keep me" and not (out / "r1.md").exists()


def test_cli_json_gz_archive_is_deterministic(monkeypatch, tmp_path):
    import time
    reps = [("div89_chain", _report("div89_chain")), ("div89_async_2p97", _report("div89_async_2p97"))]
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    _record(monkeypatch, tmp_path / "a", reps)
    time.sleep(1.1)
    _record(monkeypatch, tmp_path / "b", reps)
    for n in ("t-div89_chain.json.gz", "t-div89_async_2p97.json.gz"):
        assert (tmp_path / "a/records" / n).read_bytes() == (tmp_path / "b/records" / n).read_bytes()
    assert (tmp_path / "a/records/t.md").read_text() == (tmp_path / "b/records/t.md").read_text()
