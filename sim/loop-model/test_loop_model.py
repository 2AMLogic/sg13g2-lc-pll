"""Tests for the method-L loop model, incl. the C2 = C1 negative control."""
import json

import pytest

import loop_model as lm


def _load():
    d = json.loads(lm.FILTER_JSON.read_text())
    return {k: d[k] for k in ("r1_ohm", "c1_f", "c2_f", "r3_ohm", "c3_f")}


def test_design_point_f_c_and_pm():
    flt = _load()
    f_c = lm.unity_gain_hz(flt, lm.ICP_DESIGN_A, lm.KVCO_DESIGN_HZ_PER_V)
    assert abs(f_c - 1e6) / 1e6 < 0.01
    assert lm.phase_margin_deg(f_c, flt) >= lm.PM_MIN_DEG


def test_committed_filter_matches_sizing():
    derived, flt = lm.size_filter(), _load()
    for k, v in derived.items():
        assert abs(flt[k] - v) / v < 1e-9


def test_r1_matches_hand_check_order():
    # Hand value I_cp*R1 = 1.31 V gives 6.5 kohm; the exact-|L| solve stays within 15 %.
    assert abs(_load()["r1_ohm"] - 6.54e3) / 6.54e3 < 0.15


def test_negative_control_c2_equals_c1_fails_pm():
    flt = _load()
    flt["c2_f"] = flt["c1_f"]
    f_c = lm.unity_gain_hz(flt, lm.ICP_DESIGN_A, lm.KVCO_DESIGN_HZ_PER_V)
    pm = lm.phase_margin_deg(f_c, flt)
    assert pm < lm.PM_MIN_DEG
    assert any("PM" in v for v in lm.check_point(f_c, pm))


def test_cli_passes_and_writes_json(tmp_path):
    out = tmp_path / "r.json"
    assert lm.main(["--out", str(out)]) == 0
    res = json.loads(out.read_text())
    assert res["gate_pass"] and "method" in res
    for p in res["points"]:
        assert {"f_c_hz", "pm_deg", "jitter_rms_s"} <= p.keys()
        assert "not measured" in p["jitter_label"] and "method L" in p["jitter_label"]


def test_cli_exits_nonzero_on_perturbed_r1(tmp_path):
    flt = _load()
    flt["r1_ohm"] *= 3  # f_c ~ 3 MHz at the design point
    f = tmp_path / "f.json"
    f.write_text(json.dumps(flt))
    assert lm.main(["--filter", str(f)]) == 1


def test_corners_flagged_not_gated(tmp_path):
    out = tmp_path / "r.json"
    assert lm.main(["--out", str(out)]) == 0
    res = json.loads(out.read_text())
    assert res["flagged_outside_spec_not_gated"]
    assert all(p["icp_a"] != lm.ICP_DESIGN_A for p in res["flagged_outside_spec_not_gated"])


# --- in-band noise inputs (#247): three terms are inputs, never zero placeholders ---

FLAT = [[1e3, -143.0]]  # a one-point table is a flat floor


def _inputs(path, terms, source="test fixture, not a measurement"):
    path.write_text(json.dumps({t: {"ssb_dbc_per_hz": FLAT, "source": source} for t in terms}))
    return str(path)


def test_no_inputs_reports_three_terms_missing_not_zero(tmp_path):
    out = tmp_path / "r.json"
    assert lm.main(["--out", str(out)]) == 0
    res = json.loads(out.read_text())
    assert res["method"]["missing_terms"] == list(lm.NOISE_INPUT_TERMS)
    assert "placeholders_zero" not in res["method"]["inputs"]
    for p in res["points"]:
        by = p["sigma_phi_sq_rad2_by_term"]
        assert p["missing_terms"] == list(lm.NOISE_INPUT_TERMS)
        for t in lm.NOISE_INPUT_TERMS:
            assert by[t] is None  # JSON null, never 0.0
        assert "partial" in p["jitter_label"]
        assert all(t in p["jitter_label"] for t in lm.NOISE_INPUT_TERMS)


def test_design_point_unchanged_without_inputs():
    """Record 20261103-004402-996b7af: 0.442 ps rms, f_c 1.000 MHz, PM 54.8 deg."""
    flt = _load()
    j = lm.jitter(flt, lm.ICP_DESIGN_A, lm.KVCO_DESIGN_HZ_PER_V)
    assert round(j["jitter_rms_s"] * 1e12, 3) == 0.442
    by = j["sigma_phi_sq_rad2_by_term"]
    assert abs(by["vco_target_line"] - 1.4779191719357197e-04) < 1e-18
    assert abs(by["r1_thermal"] - 4.473491479402058e-05) < 1e-18
    f_c = lm.unity_gain_hz(flt, lm.ICP_DESIGN_A, lm.KVCO_DESIGN_HZ_PER_V)
    assert round(f_c / 1e6, 3) == 1.0
    assert round(lm.phase_margin_deg(f_c, flt), 1) == 54.8


def test_all_three_supplied_gives_five_numeric_terms(tmp_path):
    out = tmp_path / "r.json"
    ni = _inputs(tmp_path / "ni.json", lm.NOISE_INPUT_TERMS)
    assert lm.main(["--noise-inputs", ni, "--out", str(out)]) == 0
    res = json.loads(out.read_text())
    assert res["method"]["missing_terms"] == []
    for t in lm.NOISE_INPUT_TERMS:
        assert res["method"]["inputs"][t]["source"] == "test fixture, not a measurement"
        assert res["method"]["inputs"][t]["ssb_dbc_per_hz"] == FLAT
    for p in res["points"]:
        by = p["sigma_phi_sq_rad2_by_term"]
        assert len(by) == 5 and all(isinstance(v, float) for v in by.values())
        assert abs(sum(by.values()) - p["sigma_phi_rad"] ** 2) < 1e-18
        assert "partial" not in p["jitter_label"]
        assert "not measured" in p["jitter_label"]


def test_one_supplied_leaves_the_other_two_missing(tmp_path):
    out = tmp_path / "r.json"
    ni = _inputs(tmp_path / "ni.json", ["pfd_cp_x_N2"])
    assert lm.main(["--noise-inputs", ni, "--out", str(out)]) == 0
    res = json.loads(out.read_text())
    assert res["method"]["missing_terms"] == ["reference_x_N2", "divider_prescaler"]
    for p in res["points"]:
        by = p["sigma_phi_sq_rad2_by_term"]
        assert by["pfd_cp_x_N2"] > 0
        assert by["reference_x_N2"] is None and by["divider_prescaler"] is None
        assert "partial" in p["jitter_label"]
        assert "pfd_cp_x_N2" not in p["jitter_label"].split(";")[0]


def test_input_without_source_is_rejected(tmp_path, capsys):
    f = tmp_path / "ni.json"
    f.write_text(json.dumps({"pfd_cp_x_N2": {"ssb_dbc_per_hz": FLAT}}))
    assert lm.main(["--noise-inputs", str(f)]) != 0
    assert "source" in capsys.readouterr().err


def test_unknown_term_name_is_rejected(tmp_path, capsys):
    f = tmp_path / "ni.json"
    f.write_text(json.dumps({"vco_target_line": {"ssb_dbc_per_hz": FLAT, "source": "x"}}))
    assert lm.main(["--noise-inputs", str(f)]) != 0
    assert "unknown term" in capsys.readouterr().err


@pytest.mark.parametrize("doc", [
    [],                                                            # not an object
    {"pfd_cp_x_N2": {"ssb_dbc_per_hz": [], "source": "x"}},        # empty table
    {"pfd_cp_x_N2": {"ssb_dbc_per_hz": [[0, -140]], "source": "x"}},         # f <= 0
    {"pfd_cp_x_N2": {"ssb_dbc_per_hz": [[1e4, -140], [1e3, -150]], "source": "x"}},  # not increasing
    {"pfd_cp_x_N2": {"ssb_dbc_per_hz": [[1e3, "x"]], "source": "x"}},        # not numbers
    {"pfd_cp_x_N2": {"ssb_dbc_per_hz": FLAT, "source": "   "}},    # blank source
])
def test_bad_noise_input_files_are_rejected(tmp_path, doc):
    f = tmp_path / "ni.json"
    f.write_text(json.dumps(doc))
    with pytest.raises(lm.NoiseInputError):
        lm.load_noise_inputs(str(f))
    assert lm.main(["--noise-inputs", str(f)]) != 0


def test_single_point_table_is_a_flat_floor_over_the_band(tmp_path):
    """A one-point table and a two-point table at the same level must agree."""
    one = _inputs(tmp_path / "a.json", ["pfd_cp_x_N2"])
    two = tmp_path / "b.json"
    two.write_text(json.dumps({"pfd_cp_x_N2": {
        "ssb_dbc_per_hz": [[1.0, -143.0], [1e9, -143.0]], "source": "s"}}))
    flt = _load()
    ja = lm.jitter(flt, lm.ICP_DESIGN_A, lm.KVCO_DESIGN_HZ_PER_V, lm.load_noise_inputs(one))
    jb = lm.jitter(flt, lm.ICP_DESIGN_A, lm.KVCO_DESIGN_HZ_PER_V, lm.load_noise_inputs(str(two)))
    a = ja["sigma_phi_sq_rad2_by_term"]["pfd_cp_x_N2"]
    b = jb["sigma_phi_sq_rad2_by_term"]["pfd_cp_x_N2"]
    assert a > 0 and abs(a - b) / a < 1e-12


def test_supplied_term_scales_as_the_input_power(tmp_path):
    """+10 dB on the input table is x10 on that term's sigma_phi^2 (linear model)."""
    flt, lo = _load(), tmp_path / "lo.json"
    hi = tmp_path / "hi.json"
    lo.write_text(json.dumps({"reference_x_N2": {"ssb_dbc_per_hz": [[1e3, -150.0]], "source": "s"}}))
    hi.write_text(json.dumps({"reference_x_N2": {"ssb_dbc_per_hz": [[1e3, -140.0]], "source": "s"}}))
    v = [lm.jitter(flt, lm.ICP_DESIGN_A, lm.KVCO_DESIGN_HZ_PER_V,
                   lm.load_noise_inputs(str(p)))["sigma_phi_sq_rad2_by_term"]["reference_x_N2"]
         for p in (lo, hi)]
    assert abs(v[1] / v[0] - 10.0) < 1e-9
