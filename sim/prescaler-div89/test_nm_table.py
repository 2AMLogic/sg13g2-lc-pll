"""Negative controls: the M/A check must FAIL when the range or the prescaler ratio makes a value unreachable."""
import nm_table as t


def test_spec_row3_examples():
    assert t.split(100) == (12, 4) and t.split(90) == (11, 2) and t.split(110) == (13, 6)


def test_all_21_values_reachable():
    rows = t.check()
    assert len(rows) == 21 and all(r[3] for r in rows)


def test_small_n_fails_a_le_m():
    # N = 15 -> M = 1, A = 7: swallow count exceeds main count, must be flagged
    assert not t.check(15, 15)[0][3]


def test_wrong_ratio_fails():
    # P = 16 would need A up to 15 > 7
    assert not all(r[3] for r in t.check(90, 110, p=16))
