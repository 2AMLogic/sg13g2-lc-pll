"""Envelope tests, incl. the negative controls: an out-of-range Kvco or I_cp must be flagged."""
import envelope as env
import loop_model as lm


def _icp(a):
    return [("TYP/test", "I_up", a)]


def test_nominal_point_reproduces_loop_model_json():
    import json
    flt = env._flt()
    ref = json.loads((lm.HERE / "results" / "loop-model.json").read_text())["design_point"]
    (r,) = env.envelope(flt, _icp(lm.ICP_DESIGN_A), [lm.KVCO_DESIGN_HZ_PER_V])
    assert abs(r["f_c_hz"] - ref["f_c_hz"]) < 1.0 and abs(r["pm_deg"] - ref["pm_deg"]) < 1e-9


def test_measured_icp_spread_stays_in_row5():
    rows = env.envelope(env._flt(), [("c", "I_up", 191.35e-6), ("c", "I_dn", 205.52e-6)])
    assert not [r for r in rows if r["violations"]]


def test_negative_control_kvco_out_of_range_is_flagged():
    rows = env.envelope(env._flt(), _icp(lm.ICP_DESIGN_A), [3 * lm.KVCO_RANGE_HZ_PER_V[1]])
    assert rows[0]["violations"] and "f_c outside" in rows[0]["violations"][0]


def test_negative_control_icp_out_of_range_is_flagged():
    rows = env.envelope(env._flt(), _icp(20e-6), [lm.KVCO_DESIGN_HZ_PER_V])
    assert rows[0]["violations"]


def test_binding_picks_extremes():
    rows = env.envelope(env._flt(), _icp(lm.ICP_DESIGN_A))
    b = env.binding(rows)
    assert b["f_c_min"]["kvco_hz_per_v"] == min(lm.KVCO_GRID) and b["f_c_max"]["kvco_hz_per_v"] == max(lm.KVCO_GRID)
