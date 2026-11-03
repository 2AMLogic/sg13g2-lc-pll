"""Negative controls for the Vce grader: an out-of-rating Vce must FAIL, a non-converged corner is never a pass."""
import vce_record as vr


def _corner(vdd, vals, status="pass"):
    return {"corner_id": "TYP/27C/%s" % vdd, "process": "TYP", "temperature_c": 27, "params": {"vddv": vdd},
            "status": status, "diagnostics": [],
            "measurements": [{"name": "vce_x%d" % i, "value": v, "status": "pass"} for i, v in enumerate(vals)]}


def test_all_within_rating_passes():
    g = vr.grade({"corners": [_corner(2.97, [1.0, 2.1]), _corner(3.63, [1.2, 2.19])]})
    assert g["verdict"] == "PASS" and g["n_exceeding"] == 0


def test_out_of_rating_vce_fails():
    g = vr.grade({"corners": [_corner(2.97, [1.0, 2.2001])]})
    assert g["verdict"] == "FAIL" and g["rows"][0]["worst_device"] == "x1"


def test_non_converged_corner_is_not_a_pass():
    err = _corner(3.63, [], status="error")
    assert vr.grade({"corners": [_corner(2.97, [1.0]), err]})["verdict"] == "INCOMPLETE"


def test_failure_outranks_non_convergence():
    g = vr.grade({"corners": [_corner(2.97, [2.5]), _corner(3.63, [], status="error")]})
    assert g["verdict"] == "FAIL"
