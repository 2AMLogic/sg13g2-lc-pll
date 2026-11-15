"""Netlist-derived logic checks of the M/A counter state sequence (issue #278).

Builds the zero-delay model of `mcounter` + `acounter` from the committed
`design/netlist/divider.spice` (`counter_state_model.py`, no PDK, no simulator) and checks,
for the spec row 3 window N = 90-110 at `N = 8*M + A`:

  - the terminal-count decode the netlist really draws (count 2, not the count 1 that
    design/README.md:147 and :181 state - see the record),
  - the M counter counts DOWN from the loaded M code through 1 and reloads, with output
    period = M code,
  - the divide identity `8*(P-H) + 9*H == N` for every N (P = period, H = MC-high clocks),
    including N = 100 and N = 90, the two ratios the existing count bench grades,
  - the pre-terminal state (count 3) is visited exactly once per period, immediately before
    the terminal-count state, and no load lands on either - so #199's look-ahead decode is
    logic-valid across the whole window,
  - negative controls: M codes 2 and 3 break the look-ahead precondition (teeth), and codes
    0/1 do not produce period = M.

Logic-level only: this is not a timing or corner result and claims nothing about the 125 C
setup failure (#197/#199).
"""
import counter_state_model as csm


def test_terminal_decode_is_count_2():
    # Derived from the parsed DT gate network, not typed in: exactly one q state asserts.
    hits = csm.decode_sweep()
    assert hits == [csm.TERMINAL_Q], "DT asserts for %s" % (hits,)
    assert csm.count_of(hits[0]) == 2


def test_window_counts_down_with_period_m():
    for n in range(csm.N_LO, csm.N_HI + 1):
        r = csm.analyse(n)
        assert r["period"] == r["m"], "N = %d: period %d != M code %d" % (n, r["period"], r["m"])
        assert r["seq"] == list(range(r["m"], 0, -1)), \
            "N = %d: not a down count from the loaded M code through 1: %s" % (n, r["seq"])


def test_divide_identity_every_n_90_110():
    for n in range(csm.N_LO, csm.N_HI + 1):
        r = csm.analyse(n)
        assert r["mc_high"] == r["a"], "N = %d: MC high %d clocks, code A = %d" \
            % (n, r["mc_high"], r["a"])
        assert r["identity"] == n, "N = %d: 8*(P-H) + 9*H = %d" % (n, r["identity"])
        runs = [i for i, s in enumerate(r["cycle"]) if s["mc"]]
        assert (runs == [] if r["a"] == 0 else
                len(runs) == r["a"] and runs == list(range(runs[0], runs[0] + r["a"]))), \
            "N = %d: MC not a single contiguous run of A ones: %s" \
            % (n, [s["mc"] for s in r["cycle"]])


def test_n100_and_n90_explicit():
    # The two ratios the existing count bench grades (scripts/divider_speed_counts.py).
    r100 = csm.analyse(100)
    assert (r100["m"], r100["a"], r100["period"], r100["mc_high"]) == (12, 4, 12, 4)
    r90 = csm.analyse(90)
    assert (r90["m"], r90["a"], r90["period"], r90["mc_high"]) == (11, 2, 11, 2)


def test_lookahead_valid_across_window():
    for n in range(csm.N_LO, csm.N_HI + 1):
        r = csm.analyse(n)
        v = r["verdict"]
        assert v["valid"], "N = %d: look-ahead invalid: %s" % (n, "; ".join(v["why"]))
        k = v["terminal_at"][0]
        assert r["cycle"][k - 1]["q"] == csm.PRE_TERMINAL_Q and r["cycle"][k - 1]["tc2"] == 0, \
            "N = %d: terminal state not reached from count 3 by counting" % n


def test_m_code_2_breaks_lookahead():
    # The load target IS the terminal-count state: count 3 is never visited. This is what
    # shows the check has teeth rather than returning "valid" unconditionally.
    r = csm.analyse(csm.P_MAIN * 2)
    v = r["verdict"]
    assert not v["valid"], "M = 2: look-ahead reported valid"
    assert v["pre_terminal_at"] == [], "M = 2: count 3 unexpectedly on the cycle path"
    assert any(w.startswith("load lands directly on the terminal") for w in v["why"]), \
        "M = 2: no load-lands-on-terminal finding: %s" % v["why"]


def test_m_code_3_loads_onto_pre_terminal():
    r = csm.analyse(csm.P_MAIN * 3)
    v = r["verdict"]
    assert not v["valid"], "M = 3: look-ahead reported valid"
    assert any(w.startswith("load lands directly on the pre-terminal") for w in v["why"]), \
        "M = 3: no load-lands-on-pre-terminal finding: %s" % v["why"]


def test_m_codes_0_and_1_do_not_period_m():
    # Outside the window (spec row 3 needs M >= 7): the wrap does not reload on the
    # terminal-count path, so the output period is not the M code.
    assert csm.analyse(0)["period"] == 16
    assert csm.analyse(csm.P_MAIN)["period"] == 17


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))
