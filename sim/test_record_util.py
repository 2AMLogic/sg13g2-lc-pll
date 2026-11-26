"""sim/record_util.py: the verdict rule, request-grid reader and append-only deterministic archive."""
import gzip
import time

import pytest

import record_util as ru


def test_verdict_precedence_and_empty():
    assert ru.verdict(["PASS", "FAIL", "INCOMPLETE"]) == "FAIL"
    assert ru.verdict(["PASS", "INCOMPLETE"]) == "INCOMPLETE"
    assert ru.verdict([]) == "INCOMPLETE"
    assert ru.verdict(["PASS", "PASS"]) == "PASS"
    assert ru.verdict(iter(["PASS"])) == "PASS"


def test_verdict_ungraded_states_are_configurable():
    assert ru.verdict(["PASS", "not-graded"], ungraded=("INCOMPLETE", "not-graded")) == "INCOMPLETE"


def test_section_of_picks_lib_by_basename_prefix():
    b = {"name": "SLOW", "sections": [{"lib": "/p/cornerRES.lib", "section": "res_wcs"},
                                      {"lib": "/p/cornerHBT.lib", "section": "hbt_wcs"}, "junk", {"lib": "x"}]}
    assert ru.section_of(b, "cornerHBT") == "hbt_wcs"
    assert ru.section_of(b, "cornerRES") == "res_wcs"
    assert ru.section_of(b, "cornerMOS") is None
    assert ru.section_of({"name": "T"}, "cornerHBT") is None


def test_request_corners_normalises_missing_axes():
    req = {"corners": {"process": [{"name": "A"}, "bad", {"nope": 1}], "temperature_c": [-40, 27],
                       "params": {"vddv": [3.63, 2.97, 3.63]}}}
    blocks, temps, vddv, supplies = ru.request_corners(req)
    assert [b["name"] for b in blocks] == ["A"] and temps == [-40, 27]
    assert vddv == [3.63, 2.97, 3.63] and supplies == [2.97, 3.63]
    assert ru.request_corners({}) == ([], [], [], [])
    assert ru.request_corners(None) == ([], [], [], [])


def test_ensure_new_names_the_colliding_path_and_writes_nothing(tmp_path):
    a, b = tmp_path / "a.md", tmp_path / "b.json.gz"
    b.write_bytes(b"x")
    with pytest.raises(SystemExit) as e:
        ru.ensure_new(a, b)
    assert str(b) in str(e.value) and "append-only" in str(e.value)
    assert not a.exists()
    ru.ensure_new(a, tmp_path / "c")  # nothing exists: no error


def test_write_report_gz_is_deterministic_across_timestamps(tmp_path):
    raw = b'{"corners": []}' * 50
    ru.write_report_gz(tmp_path / "1.gz", raw)
    time.sleep(1.1)
    ru.write_report_gz(tmp_path / "2.gz", raw)
    assert (tmp_path / "1.gz").read_bytes() == (tmp_path / "2.gz").read_bytes()
    assert gzip.decompress((tmp_path / "1.gz").read_bytes()) == raw
    assert ru.sha256_bytes(raw) == ru.sha256_bytes(gzip.decompress((tmp_path / "2.gz").read_bytes()))
