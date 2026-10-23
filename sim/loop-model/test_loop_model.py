"""Tests for the method-L loop model, incl. the C2 = C1 negative control."""
import json

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
