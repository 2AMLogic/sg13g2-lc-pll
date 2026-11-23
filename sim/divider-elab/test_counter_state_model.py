"""Netlist-derived logic checks of the M/A counter state sequence (issue #278).

Builds the zero-delay model of `mcounter` + `acounter` from the committed
`design/netlist/divider.spice` (`counter_state_model.py`, no PDK, no simulator) and checks,
for the spec row 3 window N = 90-110 at `N = 8*M + A`:

  - the combinational decode `DT` the netlist really draws asserts at count 2, one CKL cycle before
    the registered `TC`/`TC2` fire at count 1 - the phase `design/README.md` states for the
    load and the TC flops (both phases correct; see the record's appended correction),
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


def _dt_at(d, snap):
    # DT is a gate network, not a flop, so snapshot() does not carry it: settle it combinationally
    # from one cycle state (same construction as decode_sweep, with that state's TC/TC2/b flags
    # restored). settle() does not mutate state, but restore anyway so the counter stays reusable.
    saved = dict(d.m.state)
    d.m.state = {b: snap["q"][i] for i, b in enumerate(csm.MSB_FIRST)}
    d.m.state.update({"b3": snap["b"][0], "b2": snap["b"][1], "b1": snap["b"][2],
                      "TC": snap["tc"], "TCN": 1 - snap["tc"], "TC2": snap["tc2"]})
    dt = d.m.settle(d.ext)["DT"]
    d.m.state = saved
    return dt


def test_dt_registered_phase_separation():
    # The conflation issue #297 was filed on: DT (combinational, XT1..XT4) asserts at count 2 while
    # the registered TC/TC2 flops (XFT/XFTN/XFT2 = DFF(DT)) are high one CKL cycle later at count 1,
    # so design/README.md's Q = 0001 for the TC/load phase and the netlist's count-2 decode are both
    # correct. Asserted on the model's own limit cycle, per M code the target window reaches.
    assert csm.decode_sweep() == [csm.TERMINAL_Q]
    for m in (11, 12, 13):
        d = csm.DividerCounters(csm.subckts(csm._read()), m, 0)
        cycle = d.limit_cycle()
        for k, snap in enumerate(cycle):
            assert _dt_at(d, snap) == (snap["q"] == csm.TERMINAL_Q), \
                "M = %d: DT not asserted exactly at count 2 (cycle step %d)" % (m, k)
        for name, at in (("TC", [k for k, s in enumerate(cycle) if s["tc"]]),
                         ("TC2", [k for k, s in enumerate(cycle) if s["tc2"]])):
            assert len(at) == 1, "M = %d: %s high %d times per period" % (m, name, len(at))
            assert csm.count_of(cycle[at[0]]["q"]) == 1, \
                "M = %d: %s registered at count %d, not 1" % (m, name, csm.count_of(cycle[at[0]]["q"]))
            assert cycle[at[0] - 1]["q"] == csm.TERMINAL_Q, \
                "M = %d: %s does not follow the DT count-2 cycle state" % (m, name)


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
