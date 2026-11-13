#!/usr/bin/env python3
"""The loop-power record generator's simulator-version source.

The version the record states must come from a klt report the caller names with `--report`
and from nothing else. Two routes were tried and removed (PR #265 review): the ngspice
start-up banner in a corner's `ngspice.log`, which `ngspice -b -o FILE` writes to stdout
rather than into FILE and which no capture on file carries, and the first JSON found beside
the corner directories, which in a `--art DIR/<job>` tree can be another job's report. These
tests are the regression guards for both.
"""
import gzip
import importlib.util
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_module():
    spec = importlib.util.spec_from_file_location("lp_make_record", os.path.join(HERE, "make_record.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mr = _load_module()
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
import ngpin  # noqa: E402


def _report(path, version, job_id=None, compress=False):
    env = {"engine_version": version}
    if job_id is not None:
        env["remote"] = {"job_id": job_id}
    raw = json.dumps({"environment": env}).encode()
    path.write_bytes(gzip.compress(raw) if compress else raw)
    return str(path)


def test_no_report_is_unchecked_never_match():
    """The whole point of the change: with nothing named, the record does not claim a match."""
    engines = mr.report_engines([])
    assert engines == []
    v = ngpin.verdict(engines, source="the reports given with `--report`")
    assert "unchecked" in v
    assert "**match**" not in v


def test_named_report_supplies_the_version(tmp_path):
    p = _report(tmp_path / "r.json", 46)
    assert mr.report_engines([p]) == [46]
    assert "**mismatch**" in ngpin.verdict(mr.report_engines([p]))


def test_gzipped_report_is_read(tmp_path):
    """Records keep their reports gzipped, so regenerating from one on file has to work."""
    p = _report(tmp_path / "r.json.gz", 47, compress=True)
    assert mr.report_engines([p]) == [47]


def test_report_from_another_job_is_refused(tmp_path):
    """The defect the parent-directory glob could cause: a foreign job's version labelling these corners."""
    p = _report(tmp_path / "other.json", 47, job_id="klt-sim-notmine")
    with pytest.raises(SystemExit) as e:
        mr.report_engines([p], ["klt-sim-aaaa", "klt-sim-bbbb"])
    assert "not among --jobs" in str(e.value)


def test_report_of_a_graded_job_is_used(tmp_path):
    p = _report(tmp_path / "mine.json", 46, job_id="klt-sim-aaaa")
    assert mr.report_engines([p], ["klt-sim-aaaa", "klt-sim-bbbb"]) == [46]


def test_report_without_a_job_id_is_used(tmp_path):
    """A report that records no remote job (a local run) is still the caller's explicit choice."""
    p = _report(tmp_path / "local.json", 46)
    assert mr.report_engines([p], ["klt-sim-aaaa"]) == [46]


def test_disagreeing_reports_are_a_mismatch(tmp_path):
    a = _report(tmp_path / "a.json", 46, job_id="klt-sim-aaaa")
    b = _report(tmp_path / "b.json", 47, job_id="klt-sim-bbbb")
    engines = mr.report_engines([a, b], ["klt-sim-aaaa", "klt-sim-bbbb"])
    v = ngpin.verdict(engines)
    assert "**mismatch**" in v
    assert "more than one version is reported here (46, 47)" in v


def test_no_version_in_the_report_is_unchecked(tmp_path):
    p = str(tmp_path / "empty.json")
    open(p, "w").write(json.dumps({"environment": {}}))
    assert "unchecked" in ngpin.verdict(mr.report_engines([p]))


def test_the_banner_route_is_gone():
    """`ngspice -b -o FILE` puts the banner on stdout, not in FILE; no capture on file has one."""
    assert not hasattr(mr, "engine_version")
    src = open(os.path.join(HERE, "make_record.py")).read()
    assert "re.search(r\"^\\*{2,}" not in src
