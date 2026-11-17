"""Negative controls for the /8-/9 grader: a wrong ratio, a collapsed swing, a glitchy modulus sequence, a unit that
did not run must each fail or be incomplete; only a clean series passes."""
import div89_record as d

TIN = 1 / 5.5e9


def _x(times):
    return {"times": times, "edges": ["rise"] * len(times), "truncated": False}


def _series(periods_in_tin, t0=8e-9):
    t, out = t0, [t0]
    for n in periods_in_tin:
        t += n * TIN
        out.append(t)
    return out


def _corner(periods, hi_drop=0, status="pass", mcv=0.0, phi=None):
    z = _series(periods)
    params = {"vddv": 3.3, "fin": 5.5e9, "mcv": mcv}
    if phi is not None:
        params = {"vddv": 3.3, "fin": 5.5e9, "phi": phi}
    ms = [{"name": "x_zero", "crossings": _x(z)},
          {"name": "x_hi", "crossings": _x(z[hi_drop:])},
          {"name": "x_lo", "crossings": _x(z[hi_drop:])}]
    return {"corner_id": "TYP/27C", "process": "TYP", "temperature_c": 27, "params": params, "status": status,
            "diagnostics": [], "measurements": ms}


def test_clean_div8_and_div9_pass():
    assert d.grade_chain_corner(_corner([8] * 10))["ok"]
    assert d.grade_chain_corner(_corner([9] * 10, mcv=1.0))["ok"]


def test_wrong_ratio_fails():
    assert not d.grade_chain_corner(_corner([9] * 10, mcv=0.0))["ok"]          # /9 where /8 was asked
    assert not d.grade_chain_corner(_corner([8] * 9 + [10]))["ok"]             # one /10 hiccup


def test_collapsed_swing_fails():
    r = d.grade_chain_corner(_corner([8] * 10, hi_drop=5))
    assert not r["ok"] and "swing" in r["why"]


def test_too_few_edges_or_error_is_not_a_pass():
    assert not d.grade_chain_corner(_corner([8] * 3))["ok"]
    r = d.grade_chain_corner(_corner([8] * 10, status="error"))
    assert not r["ran"] and not r["ok"]
    assert d.verdict([r]) == "INCOMPLETE"
    assert d.verdict([r, dict(r, ran=True, ok=False)]) == "FAIL"


def test_async_clean_sequence_passes():
    assert d.grade_async_corner(_corner([8] * 3 + [9] * 5 + [8] * 4, phi=3e-10))["ok"]


def test_async_glitches_fail():
    for seq in ([8] * 3 + [10] + [9] * 4 + [8] * 3,          # /10 in the sequence
                [8] * 3 + [17] + [8] * 4,                     # two swallows in one period
                [8, 8, 9, 8, 9, 9, 9, 8, 8, 8, 8, 8],         # 8 9 8 9 hiccup: more than two changes
                [9] * 4 + [8] * 8,                            # starts on 9
                [8] * 12):                                    # MC pulse never swallowed
        assert not d.grade_async_corner(_corner(seq, phi=3e-10))["ok"], seq
