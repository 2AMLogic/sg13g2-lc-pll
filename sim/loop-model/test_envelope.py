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


def _doc(rows):
    verdict = "PASS" if not [r for r in rows if r["violations"]] else "FAIL"
    b = env.binding(rows)
    return env.model_run_doc(verdict, env._flt(), b, rows, "icp-corners-klt-report.json.gz",
                             "ab" * 32, "sim/cp-dc/records/icp-corners-klt-report.json.gz")


def test_model_run_doc_carries_required_keys():
    doc = _doc(env.envelope(env._flt(), _icp(lm.ICP_DESIGN_A)))
    assert {"schema_version", "kind", "status", "method", "measurements"} <= set(doc)
    assert doc["kind"] == "model-run"
    assert isinstance(doc["schema_version"], int) and not isinstance(doc["schema_version"], bool)
    assert doc["schema_version"] == 1
    assert doc["status"] == "pass" and doc["verdict"] == "PASS"
    assert {"verdict", "points", "binding", "loop_filter"} <= set(doc)


def test_model_run_doc_status_is_lowercase_not_the_verdict():
    rows = env.envelope(env._flt(), _icp(20e-6), [lm.KVCO_DESIGN_HZ_PER_V])
    doc = _doc(rows)
    assert doc["verdict"] == "FAIL" and doc["status"] == "fail"


def test_model_run_doc_measurements_carry_row5_limits():
    doc = _doc(env.envelope(env._flt(), _icp(lm.ICP_DESIGN_A)))
    limited = [m for m in doc["measurements"] if isinstance(m, dict) and m.get("limits")]
    assert limited, "no limits-bearing measurement: the grader's no_limits_checked refusal applies"
    for m in limited:
        assert set(m["limits"]) <= {"min", "max"}
    assert {"f_c_mhz", "pm_deg"} <= {m["name"] for m in limited}
    fc = {m["name"]: m for m in limited}["f_c_mhz"]
    assert fc["limits"] == {"min": 0.5, "max": 2.0} and fc["unit"] == "MHz"
    assert {m["name"]: m for m in limited}["pm_deg"]["limits"] == {"min": 45.0}


def test_no_limits_measurement_would_fail_the_limits_guard():
    doc = _doc(env.envelope(env._flt(), _icp(lm.ICP_DESIGN_A)))
    stripped = [dict(m, limits=None) for m in doc["measurements"]]
    assert not [m for m in stripped if isinstance(m, dict) and m.get("limits")]


def test_model_run_doc_corners_carry_point_status():
    rows = env.envelope(env._flt(), _icp(lm.ICP_DESIGN_A))
    doc = _doc(rows)
    assert len(doc["corners"]) == len(rows)
    assert all(c["status"] == "pass" for c in doc["corners"])
    assert all((c["status"] == "pass") == (not r["violations"]) for c, r in zip(doc["corners"], rows))
    assert doc["corners"][0]["f_c_hz"] == rows[0]["f_c_hz"]


def test_model_run_doc_failing_point_is_flagged_in_corners():
    rows = env.envelope(env._flt(), _icp(lm.ICP_DESIGN_A), [3 * lm.KVCO_RANGE_HZ_PER_V[1]])
    doc = _doc(rows)
    assert doc["status"] == "fail"
    assert [c for c in doc["corners"] if c["status"] == "fail"]
    assert not [c for c in doc["corners"] if c["status"] == "pass"]


def test_model_run_doc_method_states_method_and_inputs():
    doc = _doc(env.envelope(env._flt(), _icp(lm.ICP_DESIGN_A)))
    m = doc["method"]
    assert "Method L" in m and "spec section 3" in m and "spec section 4" in m
    assert "icp-corners-klt-report.json.gz" in m and "nominal" in m


def test_model_run_doc_worst_case_matches_binding():
    doc = _doc(env.envelope(env._flt(), _icp(lm.ICP_DESIGN_A)))
    b = doc["binding"]
    fc = {m["name"]: m for m in doc["measurements"]}["f_c_mhz"]
    vals = {b["f_c_min"]["f_c_hz"] / 1e6, b["f_c_max"]["f_c_hz"] / 1e6}
    assert fc["worst_case"]["corner_id"] in (b["f_c_min"]["corner_id"], b["f_c_max"]["corner_id"])
    assert fc["worst_case"]["value"] in vals
    assert fc["worst_case"]["margin"] >= 0.0
    pm = {m["name"]: m for m in doc["measurements"]}["pm_deg"]
    assert pm["worst_case"]["corner_id"] == b["pm_min"]["corner_id"]
    assert abs(pm["worst_case"]["value"] - b["pm_min"]["pm_deg"]) < 1e-12


def test_model_run_doc_provenance_names_the_icp_input():
    doc = _doc(env.envelope(env._flt(), _icp(lm.ICP_DESIGN_A)))
    inp = doc["provenance"]["input"]
    assert inp["path"] == "sim/cp-dc/records/icp-corners-klt-report.json.gz"
    # `klt signoff` binds a manifest citation through provenance.input.content_hash
    # (sha256:-prefixed); a bare-hex key would make every pinned citation
    # unverifiable_provenance (#304).
    assert inp["content_hash"] == "sha256:" + "ab" * 32
    assert "sha256" not in inp or inp.get("sha256") is None
