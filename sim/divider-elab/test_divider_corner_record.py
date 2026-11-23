"""Negative controls for the divider corner grader: a wrong N fails, an unconverged / truncated / non-toggling run is never a pass."""
import gzip
import json
import re
from pathlib import Path

import divider_corner_record as dr


def _run(fb, ck, mc_rise, mc_fall, status="pass", truncated=False, a=4):
    P = {"fin": 625e6, "m0v": 0, "m1v": 0, "m2v": 3.3, "m3v": 3.3, "a0v": 0, "a1v": 0, "a2v": 3.3 if a == 4 else 0}
    cr = lambda t: {"crossings": {"times": t, "edges": [], "truncated": truncated}}
    return {"process": "TYP", "temperature_c": 27, "params": P, "status": status,
            "measurements": [dict(name="ck_rise", **cr(ck)), dict(name="fb_rise", **cr(fb)), dict(name="mc_rise", **cr(mc_rise)), dict(name="mc_fall", **cr(mc_fall))]}


def test_expected_n_passes():
    ck = [i + 0.5 for i in range(60)]
    fb = [0.0, 12.0, 24.0, 36.0]
    fall = [12.0, 24.0, 36.0]
    r = dr.grade_run(_run(fb, ck, [x + 0.01 for x in (8.0, 20.0, 32.0)], fall))
    assert r["status"] == "pass" and r["n"] == 100


def test_wrong_n_fails():
    ck = [i + 0.5 for i in range(60)]
    r = dr.grade_run(_run([0.0, 11.0, 22.0, 33.0], ck, [], []))
    assert r["status"] == "FAIL"


def test_unconverged_truncated_and_no_toggle_are_not_passes():
    ck = [i + 0.5 for i in range(60)]
    # The unconverged and truncated runs carry a crossing set that grades "pass" on its own
    # (the control below), so each assertion can only hold via the guard it names. With fewer
    # than 4 FB edges instead, dropping either guard would just fall through to the no-toggle
    # guard, which returns "not-graded" too -- so both assertions would still pass.
    fb, mc_rise, mc_fall = [0.0, 12.0, 24.0, 36.0], [8.01, 20.01, 32.01], [12.0, 24.0, 36.0]
    assert dr.grade_run(_run(fb, ck, mc_rise, mc_fall))["status"] == "pass"
    assert dr.grade_run(_run(fb, ck, mc_rise, mc_fall, status="error"))["status"] == "not-graded"
    assert dr.grade_run(_run(fb, ck, mc_rise, mc_fall, truncated=True))["status"] == "not-graded"
    assert dr.grade_run(_run([0.0, 12.0, 24.0], ck, [1.0], [2.0]))["status"] == "not-graded"
    assert dr.grade({"corners": [_run([0.0, 12.0], ck, [1.0], [2.0])]})["verdict"] == "INCOMPLETE"


def test_bad_startup_window_is_ignored_but_bad_later_window_fails():
    ck = [i + 0.5 for i in range(80)]
    ok = dr.grade_run(_run([0.0, 7.0, 19.0, 31.0, 43.0], ck, [], [], a=0))   # window 1 is 7 clocks, later ones 12
    assert ok["first_n"] != 100 and ok["status"] == "pass"
    bad = dr.grade_run(_run([0.0, 12.0, 24.0, 35.0, 47.0], ck, [], [], a=0))
    assert bad["status"] == "FAIL"


def _parts_verdict(tmp_path, *grades):
    req = tmp_path / "divider_corner_speed.request.json"
    req.write_bytes(b"{}")
    parts = [(f"part{i}", g, {"environment": {}}, req) for i, g in enumerate(grades)]
    headline = dr.render(parts, "t", "deadbeef").splitlines()[2]
    return headline.split("**")[2]


def test_empty_report_grades_incomplete(tmp_path):
    empty = dr.grade({"corners": []})
    assert empty["verdict"] == "INCOMPLETE"
    assert _parts_verdict(tmp_path, empty) == "INCOMPLETE"


def test_passing_part_beside_empty_part_is_incomplete(tmp_path):
    ck = [i + 0.5 for i in range(60)]
    fb, mc_rise, mc_fall = [0.0, 12.0, 24.0, 36.0], [8.01, 20.01, 32.01], [12.0, 24.0, 36.0]
    passing = dr.grade({"corners": [_run(fb, ck, mc_rise, mc_fall)]})
    assert passing["verdict"] == "PASS"
    assert _parts_verdict(tmp_path, passing, dr.grade({"corners": []})) == "INCOMPLETE"


def test_failing_part_beside_empty_part_fails(tmp_path):
    ck = [i + 0.5 for i in range(60)]
    failing = dr.grade({"corners": [_run([0.0, 11.0, 22.0, 33.0], ck, [], [])]})
    assert failing["verdict"] == "FAIL"
    assert _parts_verdict(tmp_path, failing, dr.grade({"corners": []})) == "FAIL"


def _write_report(tmp_path, corners, name):
    rep = tmp_path / name
    rep.write_text(json.dumps({"environment": {"engine_version": "46", "remote": {"job_id": "j", "instance_type": "it", "lifecycle": "spot"}}, "corners": corners}))
    return rep


def _section(text, name):
    _, sep, sec = text.partition(f"## {name}\n")
    assert sep, f"no {name} section"
    return sec.split("\n## ")[0]


def _tables(text, name):
    return [l for l in _section(text, name).splitlines() if l.startswith("|")]


def _verdicts(text, name):
    return [l.split("verdict **")[1].split("**")[0] for l in _section(text, name).splitlines() if "verdict **" in l]


def test_speed_only_replay_claims_only_what_it_ran(tmp_path):
    ck = [i + 0.5 for i in range(60)]
    fb, mc_rise, mc_fall = [0.0, 12.0, 24.0, 36.0], [8.01, 20.01, 32.01], [12.0, 24.0, 36.0]
    rep = _write_report(tmp_path, [_run(fb, ck, mc_rise, mc_fall)], "speed-report.json")
    req = tmp_path / "divider_corner_speed.request.json"
    req.write_bytes(b"{}")
    assert dr.main(["--part", "speed", str(rep), str(req), "--out-dir", str(tmp_path), "--id", "t", "--commit", "deadbeef"]) == 0
    text = (tmp_path / "t-corners.md").read_text()
    speed = _section(text, "speed")
    # the table identifies the one row that ran: TYP/27C, 625 MHz, N = 100, pass
    assert len([l for l in speed.splitlines() if l.startswith("|")]) == 3   # header, separator, exactly one data row
    assert "| TYP/27C | 625 | 12 | 4 | 4 | 100 | 12 | 4 | 100 | 100 | pass |" in speed
    assert "verdict **PASS**" in speed
    # the global prose claims neither the count bench nor corners that were not run
    prose = text.split("\n## speed\n")[0]
    assert "1 of 1 runs" in prose
    assert not re.search(r"\bcount\b", prose, re.IGNORECASE)
    for claim in ("SLOW", "FAST", "hbt_", "-40", "125", "687.5"):
        assert claim not in prose


def test_archived_speed_and_count_replay_preserves_tables_and_verdicts(tmp_path):
    recs = Path(__file__).parent / "records"
    args = ["--out-dir", str(tmp_path), "--id", "t", "--commit", "deadbeef"]
    for part in ("speed", "count"):
        rep = tmp_path / f"{part}-report.json"
        rep.write_bytes(gzip.decompress((recs / f"20261110-pdk-resistors-2022314-{part}-klt-report.json.gz").read_bytes()))
        args += ["--part", part, str(rep), str(recs.parent / f"divider_corner_{part}.request.json")]
    assert dr.main(args) == 0
    new = (tmp_path / "t-corners.md").read_text()
    arch = (recs / "20261110-pdk-resistors-2022314-corners.md").read_text()
    for part in ("speed", "count"):
        assert _tables(new, part) == _tables(arch, part)
        assert _verdicts(new, part) == _verdicts(arch, part)
    assert new.splitlines()[2] == arch.splitlines()[2]   # headline: 43 of 54 runs, INCOMPLETE
