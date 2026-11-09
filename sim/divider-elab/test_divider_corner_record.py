"""Negative controls for the divider corner grader: a wrong N fails, an unconverged / truncated / non-toggling run is never a pass."""
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
    assert dr.grade_run(_run([0.0, 12.0, 24.0], ck, [1.0], [2.0], status="error"))["status"] == "not-graded"
    assert dr.grade_run(_run([0.0, 12.0, 24.0], ck, [1.0], [2.0], truncated=True))["status"] == "not-graded"
    assert dr.grade_run(_run([0.0, 12.0, 24.0], ck, [1.0], [2.0]))["status"] == "not-graded"
    assert dr.grade({"corners": [_run([0.0, 12.0], ck, [1.0], [2.0])]})["verdict"] == "INCOMPLETE"


def test_bad_startup_window_is_ignored_but_bad_later_window_fails():
    ck = [i + 0.5 for i in range(80)]
    ok = dr.grade_run(_run([0.0, 7.0, 19.0, 31.0, 43.0], ck, [], [], a=0))   # window 1 is 7 clocks, later ones 12
    assert ok["first_n"] != 100 and ok["status"] == "pass"
    bad = dr.grade_run(_run([0.0, 12.0, 24.0, 35.0, 47.0], ck, [], [], a=0))
    assert bad["status"] == "FAIL"
