"""Zero-delay logic model of the divider counters in design/netlist/divider.spice (issue #278).

Parses the committed netlist (klt netlist output, generated - do not edit by hand) into gate
networks for the `mcounter` and `acounter` subcircuits and evaluates them as a synchronous
zero-delay boolean model: every flop (M counter q0-q3, borrow flags b1-b3, registered terminal
count TC/TCN/TC2; A counter s0-s2 and MC) samples its D network at the same CKL edge. Load
value, count direction, terminal-count decode and reload behaviour all come from the parsed
netlist, not from a typed equation list.

For every N in 90-110 (spec row 3, N = 8*M + A, P = 8/9) the model free-runs from the
all-zero power-on state, finds the joint limit cycle of mcounter + acounter by state-repeat
detection, and reports:

  - the M-counter state sequence over one full output period,
  - whether the state immediately before the terminal-count state is visited exactly once
    per period, and whether any load lands directly on the terminal-count state,
  - whether a look-ahead decode of that pre-terminal state, registered one CKL cycle, would
    be logic-valid for #199.

This is a logic-level result: no PDK, no ngspice, no timing. It says nothing about the
setup failure at 125 C that motivates it (#197/#199; trace record in unmerged PR #200). It
decides only whether the look-ahead state is on the counter's path for every modulus the
M/A programming allows in the target window, which is the precondition no simulator was
needed for.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NETLIST = os.path.join(HERE, "..", "..", "design", "netlist", "divider.spice")

P_MAIN, P_ALT = 8, 9            # prescaler second-stage modulus, MC low / MC high (spec row 4)
N_LO, N_HI = 90, 110            # spec row 3 stretch band; target N = 100 sits inside
MSB_FIRST = ("q3", "q2", "q1", "q0")
TERMINAL_Q = (0, 0, 1, 0)       # asserted by test against the parsed DT network (count 2)
PRE_TERMINAL_Q = (0, 0, 1, 1)   # count 3, the state #199 would look ahead to

GATE_INPUTS = {"inv_hv": 1, "nand2_hv": 2, "nand3_hv": 3, "nor2_hv": 2}


def _read():
    with open(NETLIST) as f:
        return f.read().splitlines()


def subckts(lines):
    """{name: (pins, [instance token lists])} for every .subckt in the netlist."""
    out, cur = {}, None
    for ln in lines:
        t = ln.split()
        if not t or t[0].startswith(("*", "**")):
            continue
        if t[0].lower() == ".subckt":
            cur = (t[1], t[2:], [])
        elif t[0].lower() == ".ends" and cur:
            out[cur[0]] = (cur[1], cur[2])
            cur = None
        elif cur and t[0][0] in "Xx":
            cur[2].append(t)
    return out


def _gate(kind, ins):
    if kind == "inv_hv":
        return int(not ins[0])
    if kind in ("nand2_hv", "nand3_hv"):
        return int(not all(ins))
    if kind == "nor2_hv":
        return int(not any(ins))
    raise AssertionError("cell kind not modelled as zero-delay logic: " + kind)


class Cell:
    """Gate + flop network of one .subckt, synchronous zero-delay semantics.

    All flops latch their settled D inputs on the same edge. A `dff_tg_hv_qn` stores Q and
    exposes its complementary output QN combinationally (one inverter inside the cell).
    """

    def __init__(self, subs, name):
        self.name = name
        self.pins, insts = subs[name]
        self.flops, self.gates, self.qn_of = [], [], {}
        for t in insts:
            kind, nets = t[-1], t[1:-1]
            if kind == "dff_tg_hv":
                self.flops.append((nets[0], nets[2]))
            elif kind == "dff_tg_hv_qn":
                self.flops.append((nets[0], nets[2]))
                self.qn_of[nets[3]] = nets[2]
            else:
                assert kind in GATE_INPUTS, "unexpected cell in %s: %s" % (name, kind)
                n = GATE_INPUTS[kind]
                self.gates.append((kind, nets[:n], nets[n]))
        assert self.flops, "no flops parsed from " + name
        self.state = {q: 0 for _, q in self.flops}

    def settle(self, ext):
        v = dict(ext)
        v.update(self.state)
        v["VDD"], v["VSS"] = 1, 0
        for qn, q in self.qn_of.items():
            v[qn] = 1 - v[q]
        for _ in range(len(self.gates) + 2):
            for kind, ins, out in self.gates:
                if all(i in v for i in ins):
                    v[out] = _gate(kind, [v[i] for i in ins])
        for d, _q in self.flops:
            assert d in v, "%s: D net %s never settled" % (self.name, d)
        return v

    def latch(self, v):
        self.state = {q: v[d] for d, q in self.flops}


class DividerCounters:
    """mcounter + acounter of the divider, clocked together on CKL.

    TC/TCN are mcounter flop outputs feeding acounter's D network, so one tick is one CKL
    edge: settle both D networks from the current state, then latch both.
    """

    def __init__(self, subs, m_code, a_code):
        self.m = Cell(subs, "mcounter")
        self.a = Cell(subs, "acounter")
        self.ext = {}
        for i in range(4):
            self.ext["M%d" % i] = (m_code >> i) & 1
        for i in range(3):
            self.ext["A%d" % i] = (a_code >> i) & 1

    def _key(self):
        return (tuple(sorted(self.m.state.items())), tuple(sorted(self.a.state.items())))

    def snapshot(self):
        """The counter state as present during this CKL cycle (before its sampling edge)."""
        return {
            "q": tuple(self.m.state[b] for b in MSB_FIRST),
            "b": tuple(self.m.state[b] for b in ("b3", "b2", "b1")),
            "tc": self.m.state["TC"],
            "tc2": self.m.state["TC2"],
            "mc": self.a.state["MC"],
        }

    def tick(self):
        vm = self.m.settle(self.ext)
        va = self.a.settle(dict(self.ext, TC=vm["TC"], TCN=vm["TCN"]))
        self.m.latch(vm)
        self.a.latch(va)

    def limit_cycle(self, max_clocks=200):
        """The periodic joint state cycle reached from the all-zero power-on state."""
        seen, hist = {}, []
        key = self._key()
        for _ in range(max_clocks):
            if key in seen:
                return hist[seen[key]:]
            seen[key] = len(hist)
            hist.append(self.snapshot())
            self.tick()
            key = self._key()
        raise AssertionError("no repeated joint state within %d CKL cycles" % max_clocks)


def count_of(q):
    """Counter value of a q-flop state tuple (MSB first; q0 is the LSB, M0 loads into it)."""
    v = 0
    for bit in q:
        v = (v << 1) | bit
    return v


def decode_sweep():
    """The q states that assert DT, derived from the parsed mcounter gate network."""
    m = Cell(subckts(_read()), "mcounter")
    hits = []
    ext = {"M%d" % i: 0 for i in range(4)}
    for code in range(16):
        m.state = {b: (code >> (3 - i)) & 1 for i, b in enumerate(MSB_FIRST)}
        m.state.update({k: 0 for k in ("TC", "TCN", "TC2", "b1", "b2", "b3")})
        if m.settle(ext)["DT"]:
            hits.append(tuple(m.state[b] for b in MSB_FIRST))
    return hits


def lookahead_verdict(cycle, m_code):
    """Whether #199's option - decode the pre-terminal state one count early and register
    it - is logic-valid for this M code.

    Valid requires all of: the output period equals the M code; the terminal-count state
    and the pre-terminal state each occur exactly once per period; the terminal state's
    predecessor is the pre-terminal state, reached by counting and not by a load; and no
    load lands directly on either state (a load onto either would pulse the registered
    look-ahead at the wrong time or swallow the pulse entirely).
    """
    def hits(q):
        return [k for k, s in enumerate(cycle) if s["q"] == q]

    term, pre = hits(TERMINAL_Q), hits(PRE_TERMINAL_Q)
    why = []
    ok = True
    if len(cycle) != m_code:
        ok = False
        why.append("period %d != M code %d" % (len(cycle), m_code))
    if len(term) != 1:
        ok = False
        why.append("terminal state visited %d times per period" % len(term))
    if len(pre) != 1:
        ok = False
        why.append("pre-terminal state visited %d times per period" % len(pre))
    if len(term) == 1:
        src = cycle[term[0] - 1]
        if src["q"] != PRE_TERMINAL_Q:
            ok = False
            why.append("terminal predecessor is count %d, not the pre-terminal state"
                       % count_of(src["q"]))
        elif src["tc2"] == 1:
            ok = False
            why.append("terminal state is reached by a load edge, not by counting")
    for k, s in enumerate(cycle):
        nxt = cycle[(k + 1) % len(cycle)]["q"]
        if s["tc2"] == 1 and nxt in (TERMINAL_Q, PRE_TERMINAL_Q):
            ok = False
            which = "terminal" if nxt == TERMINAL_Q else "pre-terminal"
            why.append("load lands directly on the %s state (count %d)"
                       % (which, count_of(nxt)))
    return {"valid": ok, "why": why, "terminal_at": term, "pre_terminal_at": pre}


def analyse(n):
    """Model one N of the window: M code, A code, joint limit cycle, and the verdicts."""
    m_code, a_code = n // P_MAIN, n % P_MAIN
    d = DividerCounters(subckts(_read()), m_code, a_code)
    cycle = d.limit_cycle()
    for k in range(len(cycle)):
        if cycle[k - 1]["tc2"] == 1:
            cycle = cycle[k:] + cycle[:k]
            break
    h = sum(s["mc"] for s in cycle)
    return {
        "n": n, "m": m_code, "a": a_code,
        "cycle": cycle,
        "seq": [count_of(s["q"]) for s in cycle],
        "period": len(cycle),
        "mc_high": h,
        "identity": P_MAIN * (len(cycle) - h) + P_ALT * h,
        "verdict": lookahead_verdict(cycle, m_code),
    }


def _fmt_sequence(res):
    parts = []
    for k, s in enumerate(res["cycle"]):
        c = res["seq"][k]
        tag = "*" if s["q"] == TERMINAL_Q else ("+" if s["q"] == PRE_TERMINAL_Q else "")
        parts.append("%d%s" % (c, tag))
    return " -> ".join(parts) + " -> load(%d)" % res["m"]


def main():
    hits = decode_sweep()
    assert len(hits) == 1, "DT decode asserts for %d q states: %s" % (len(hits), hits)
    print("netlist: %s" % os.path.relpath(NETLIST, HERE))
    print("logic-level zero-delay model of mcounter + acounter; no PDK, no simulator,")
    print("no timing - this is not a timing or corner result.")
    print("")
    print("terminal-count decode DT (parsed from the netlist) asserts only for")
    print("q (q3 q2 q1 q0) = %s, count %d with q0 = LSB; TC/TCN/TC2 register it."
          % (" ".join(str(b) for b in hits[0]), count_of(hits[0])))
    m_codes = sorted({n // P_MAIN for n in range(N_LO, N_HI + 1)})
    print("N = %d*M + A maps every N in [%d, %d] onto just %d M codes: %s"
          % (P_MAIN, N_LO, N_HI, len(m_codes), m_codes))
    print("")
    print("M-counter state sequence over one full output period, per M code in the window")
    print("(* = terminal-count state, + = pre-terminal state):")
    for m in m_codes:
        res = analyse(P_MAIN * m)
        print("  M = %2d: %s" % (m, _fmt_sequence(res)))
    print("")
    print("  N   M   A  period  MC-high  8*(P-H)+9*H  pre-terminal  load-on-terminal  look-ahead")
    for n in range(N_LO, N_HI + 1):
        r = analyse(n)
        v = r["verdict"]
        pre_ok = len(v["pre_terminal_at"]) == 1
        load_on_term = any(w.startswith("load lands directly on the terminal")
                           for w in v["why"])
        print("  %3d %3d %3d  %5d  %7d  %11d  %13s  %17s  %s%s"
              % (n, r["m"], r["a"], r["period"], r["mc_high"], r["identity"],
                 "once" if pre_ok else "no",
                 "yes" if load_on_term else "no",
                 "valid" if v["valid"] else "INVALID",
                 "" if v["valid"] else " (" + "; ".join(v["why"]) + ")"))


if __name__ == "__main__":
    main()
