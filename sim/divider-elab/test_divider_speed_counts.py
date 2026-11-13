"""Negative controls for scripts/divider_speed_counts.py (issue #236).

The grader is a CLI with module-level argv handling, so these drive it as a subprocess over
synthetic `wrdata` files built to the layout each deck writes. The point of the COUNT cases is
that the relaxed-clock count check can now FAIL: before #236 the 100 MHz count was printed by a
separate script whose exit status the bench ignored, so a divider that counted 99 produced a
record that looked the same apart from one table cell.
"""
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "divider_speed_counts.py"
DT = 0.05e-9          # sample step of the synthetic data
TCK = 10e-9           # 100 MHz clock, as divider_tran drives it
HI, LO = 3.3, 0.0


def _levels(edges, start=LO):
    """A sampler for a square wave: `edges` is [(time, level), ...], ascending."""
    def at(t):
        v = start
        for x, level in edges:
            if t < x:
                break
            v = level
        return v
    return at


def _ck_edges(n_rise, drop=()):
    """Rising edges at 1.0 ns + k x TCK (falling half a period later); `drop` omits whole cycles."""
    out = []
    for k in range(n_rise):
        if k in drop:
            continue
        out += [(1.0e-9 + k * TCK, HI), (1.0e-9 + k * TCK + TCK / 2, LO)]
    return out


def _fb_edges(m, windows):
    """FB rises just before each window's first CK rise, so the window holds exactly m CK rises."""
    out = []
    for j in range(windows + 1):
        out += [(0.5e-9 + j * m * TCK, HI), (0.5e-9 + j * m * TCK + TCK / 2, LO)]
    return out


def _mc_edges(m, a, windows):
    """MC high over the first `a` CK edges of each window, as sampled 0.3 ns before the edge."""
    out = []
    if a <= 0:
        return out
    for j in range(windows + 1):
        k0 = j * m
        out += [(0.6e-9 + k0 * TCK, HI), (0.8e-9 + (k0 + a - 1) * TCK, LO)]
    return out


def _write(path, signals, stop):
    """One wrdata file: a (t, v) pair per signal, in the order the deck's `wrdata` card lists them."""
    n = int(round(stop / DT)) + 1
    with open(path, "w") as fh:
        for i in range(n):
            t = i * DT
            fh.write(" ".join(f"{t:.12e} {s(t):.6f}" for s in signals) + "\n")


def _count_file(path, codes, windows=3, drop=()):
    """The divider_tran layout: v(xd100.ck) v(mc100) v(fb100) v(mc90) v(fb90) -- one shared CK."""
    m_max = max(m for m, _ in codes)
    stop = (windows + 1) * m_max * TCK + TCK
    ck = _levels(_ck_edges(int(stop / TCK) + 2, drop=drop))
    sig = [ck]
    for m, a in codes:
        sig += [_levels(_mc_edges(m, a, windows)), _levels(_fb_edges(m, windows))]
    _write(path, sig, stop)
    return path


def _speed_file(path, cases, windows=3):
    """The divider_speed layout: ck mc fb per case, cases numbered within their own file."""
    m_max = max(m for m, _ in cases)
    stop = (windows + 1) * m_max * TCK + TCK
    sig = []
    for m, a in cases:
        sig += [_levels(_ck_edges(int(stop / TCK) + 2)), _levels(_mc_edges(m, a, windows)),
                _levels(_fb_edges(m, windows))]
    _write(path, sig, stop)
    return path


def _run(*args):
    p = subprocess.run([sys.executable, "-I", str(SCRIPT), *map(str, args)],
                       capture_output=True, text=True)
    return p.returncode, p.stdout


def _rows(out):
    return [l.split() for l in out.strip().splitlines()]


# --------------------------------------------------------------------------- COUNT mode

def test_count_expected_n_passes(tmp_path):
    rc, out = _run(_count_file(tmp_path / "div.data", ((12, 4), (11, 2))), "COUNT")
    rows = _rows(out)
    assert rc == 0, out
    # one row per full window, per code, with the expected N in the last column
    assert [r[0] for r in rows] == ["N100"] * 3 + ["N90"] * 3
    assert all(r[2:] == [str(m), str(a), str(8 * m + a), str(8 * m + a)]
               for r, (m, a) in zip(rows, [(12, 4)] * 3 + [(11, 2)] * 3)), out


def test_count_dropped_clock_fails(tmp_path):
    """The control the bench was missing: one CK cycle gone from the second N100 window.

    Cycle 17 is not one of the MC-high (swallowed) clocks, so the window loses a clock and keeps
    its 4 MC-high ones: N = 8 x 11 + 4 = 92 instead of 100. The grader must exit nonzero -- while
    still printing the table, so the record keeps the evidence.
    """
    data = _count_file(tmp_path / "div.data", ((12, 4), (11, 2)), drop={17})
    rc, out = _run(data, "COUNT")
    assert rc == 1, out
    ns = [r[4] for r in _rows(out) if r[0] == "N100"]
    assert ns == ["100", "92", "100"], out
    # the N90 lane shares the clock, so it sees the same missing cycle in one window
    assert any(r[4] != "90" for r in _rows(out) if r[0] == "N90"), out


def test_count_wrong_mc_high_fails(tmp_path):
    """A swallow-count error (A = 3 instead of 4) is a wrong N, not a wrong window."""
    rc, out = _run(_count_file(tmp_path / "div.data", ((12, 3), (11, 2))), "COUNT")
    assert rc == 1, out
    assert all(r[4] == "99" and r[5] == "100" for r in _rows(out) if r[0] == "N100"), out


def test_count_no_toggle_fails(tmp_path):
    """FB stuck low: fewer than 3 rising edges, so there is nothing to grade and nothing passes."""
    stop = 200e-9
    sig = [_levels(_ck_edges(22)), _levels([]), _levels([]), _levels([]), _levels([])]
    _write(tmp_path / "div.data", sig, stop)
    rc, out = _run(tmp_path / "div.data", "COUNT")
    assert rc == 1, out
    assert [r[0:3] for r in _rows(out)] == [["N100", "0", "no-toggle"], ["N90", "0", "no-toggle"]], out


# --------------------------------------------------------------------------- speed modes (regression)

def test_speed_mode_still_grades_its_two_files(tmp_path):
    real = _speed_file(tmp_path / "speed.data", ((12, 4), (12, 4)))
    ctrl = _speed_file(tmp_path / "speedC.data", ((12, 4), (12, 4)))
    rc, out = _run(real, ctrl)
    assert rc == 0, out
    assert [r[0] for r in _rows(out)] == ["real-625", "real-687.5", "ideal-clk-625", "ideal-clk-687.5"]
    assert all(r[4] == "100" and r[5] == "100" for r in _rows(out)), out


def test_speed_mode_wrong_n_fails(tmp_path):
    real = _speed_file(tmp_path / "speed.data", ((12, 4), (12, 0)))   # second case swallows nothing
    ctrl = _speed_file(tmp_path / "speedC.data", ((12, 4), (12, 4)))
    rc, out = _run(real, ctrl)
    assert rc == 1, out
    assert _rows(out)[1][4:] == ["96", "100"], out


def test_a_code_mode_grades_four_cases(tmp_path):
    data = _speed_file(tmp_path / "speedA.data", ((12, 0), (12, 0), (12, 7), (12, 7)))
    rc, out = _run(data, "A")
    assert rc == 0, out
    assert [r[4] for r in _rows(out)] == ["96", "96", "103", "103"], out


def test_bad_usage_exits_nonzero(tmp_path):
    rc, _ = _run(_count_file(tmp_path / "div.data", ((12, 4), (11, 2))))
    assert rc != 0
