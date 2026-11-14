"""The pin check must be computed, and must never call an unchecked run a match."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ngpin  # noqa: E402


def _pins(tmp_path, version):
    p = tmp_path / "pins.json"
    p.write_text(json.dumps({"ngspice": {"version": version}}))
    return str(p)


def test_pinned_reads_the_repo_pin():
    pin = ngpin.pinned()
    assert pin is not None and ngpin.vnum(pin) == pin


def test_match(tmp_path):
    v = ngpin.verdict("47", path=_pins(tmp_path, "47"))
    assert "**match**" in v and "pin is 47" in v


def test_mismatch_is_not_a_match(tmp_path):
    v = ngpin.verdict("46", path=_pins(tmp_path, "47"))
    assert "**mismatch**" in v and "**match**" not in v


def test_point_release_matches_its_pin(tmp_path):
    # the prefix rule of scripts/lib-ngpin.sh: 47.1 matches a pin of 47, 46 does not
    assert ngpin.matches("47.1", "47") and not ngpin.matches("46", "47")
    assert ngpin.matches("ngspice-47.1.2", "47") and not ngpin.matches("470", "47")
    assert "**match**" in ngpin.verdict("ngspice-47.1", path=_pins(tmp_path, "47"))


def test_missing_version_is_unchecked_never_match(tmp_path):
    for bad in (None, "", "unknown", []):
        v = ngpin.verdict(bad, source="the reports", path=_pins(tmp_path, "47"))
        assert "**unchecked**" in v and "**match**" not in v and "**mismatch**" not in v
        assert "the reports" in v


def test_unreadable_pin_is_not_a_match(tmp_path):
    v = ngpin.verdict("47", path=str(tmp_path / "absent.json"))
    assert "the pin was not read" in v and "**match**" not in v


def test_pin_without_a_version_key_is_not_a_match(tmp_path):
    p = tmp_path / "pins.json"
    p.write_text(json.dumps({"ngspice": {}}))
    assert "the pin was not read" in ngpin.verdict("47", path=str(p))


def test_several_reports_mismatch_if_any_differs(tmp_path):
    v = ngpin.verdict(["47", "46"], path=_pins(tmp_path, "47"))
    assert "**mismatch**" in v and "more than one version is reported here (47, 46)" in v


def test_several_agreeing_reports_state_the_single_verdict(tmp_path):
    v = ngpin.verdict(["46", "46"], path=_pins(tmp_path, "47"))
    assert "**mismatch**" in v and "more than one version" not in v


def test_several_matching_reports_say_so(tmp_path):
    v = ngpin.verdict(["47", "47.1"], path=_pins(tmp_path, "47"))
    assert "**match**" in v and "more than one version is reported here (47, 47.1)" in v


def test_engine_renders_what_ran():
    assert ngpin.engine("46") == "`ngspice-46`"
    assert ngpin.engine(["46", "46"]) == "`ngspice-46`"
    assert ngpin.engine(["46", "47"]) == "`ngspice-46` and `ngspice-47`"
    assert ngpin.engine(None) == "an ngspice version the run did not report"
    assert ngpin.engine([], unknown="not recorded") == "not recorded"


def test_reported_renders_what_ran():
    assert ngpin.reported("ngspice-46") == "46"
    assert ngpin.reported(["46", "46"]) == "46"
    assert ngpin.reported(["46", "47"]) == "46 and 47"
    assert ngpin.reported(None) == "not reported"
    assert ngpin.reported([], unknown="not recorded in the artifacts") == "not recorded in the artifacts"


def test_a_report_without_a_version_cannot_be_called_a_match(tmp_path):
    # the hole this module exists to close: one report on the pin, one that never said what it
    # ran on. The sentence speaks for the whole record, so it must not answer **match**.
    v = ngpin.verdict(["47", None], source="the reports", path=_pins(tmp_path, "47"))
    assert "**match**" not in v
    assert "**unchecked**" in v
    assert "no `engine_version` in 1 of the 2 runs here" in v
    assert "47" in v  # the version that *was* reported is still stated


def test_a_known_mismatch_is_not_softened_by_a_missing_peer(tmp_path):
    # the other direction of the same rule: a version on file that misses the pin stays a
    # **mismatch**; an unreported peer must not downgrade it to **unchecked**.
    v = ngpin.verdict(["46", None], source="the reports", path=_pins(tmp_path, "47"))
    assert "**mismatch**" in v and "**unchecked**" not in v
    assert "no `engine_version` in 1 of the 2 runs here" in v


def test_every_report_missing_a_version_is_still_plain_unchecked(tmp_path):
    for bad in ([None], [None, None], ["", "unknown"]):
        v = ngpin.verdict(bad, source="the reports", path=_pins(tmp_path, "47"))
        assert "**unchecked**" in v and "**match**" not in v and "**mismatch**" not in v
        assert "the reports" in v


def test_a_non_string_version_is_compared_not_raised(tmp_path):
    # a report whose engine_version is a JSON number must not abort the generator; matches()
    # already stringifies, so these helpers do too.
    assert "**match**" in ngpin.verdict(47, path=_pins(tmp_path, "47"))
    assert "**mismatch**" in ngpin.verdict(46, path=_pins(tmp_path, "47"))
    assert ngpin.engine(46) == "`ngspice-46`"
    assert ngpin.reported(46) == "46"
    assert ngpin.engine([46, 47]) == "`ngspice-46` and `ngspice-47`"
    assert "**match**" in ngpin.verdict([47, "47.1"], path=_pins(tmp_path, "47"))
