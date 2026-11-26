#!/usr/bin/env python3
"""Per-node activity summary of an ngspice ASCII rawfile (issue #197 hot-corner stall trace). Stdlib only.

  trace_raw.py RAW --list [PATTERN]          list node names (regex PATTERN)
  trace_raw.py RAW NODE [NODE...] [--t0 NS --t1 NS]
      sample min/max (blank if the window contains no samples), rising/falling crossings of 1.65 V, time of the last crossing.
  trace_raw.py RAW --table CLK NS0 NS1 NODE [NODE...]
      logic level (1 above 1.65 V, else 0; X if between 0.8 and 2.5 V) of each NODE 0.15 ns before each rising CLK edge in [NS0, NS1].
  trace_raw.py RAW --cross NS0 NS1 NODE [NODE...]
      time (ns) of every 1.65 V crossing (r/f) of each NODE in [NS0, NS1].
  trace_raw.py RAW --at NS NODE [NODE...]    node voltages at the sample nearest NS.
Node names are as printed by --list (e.g. v(xd.ck)). Simulated, not measured.
"""
import re
import sys
from itertools import pairwise

LEVEL = 1.65


def load(path):
    """Header only; the values are read on demand by column() (ASCII `Values:` rawfile, as klt sim writes it)."""
    with open(path, "rb") as f:
        data = f.read()
    i = data.index(b"Values:\n")
    hdr = data[:i].decode().splitlines()
    nv = int(next(l for l in hdr if l.startswith("No. Variables")).split(":")[1])
    npt = int(next(l for l in hdr if l.startswith("No. Points")).split(":")[1])
    k = hdr.index("Variables:")
    names = [hdr[k + 1 + j].split("\t")[2] for j in range(nv)]
    return names, npt, nv, data[i + 8:].split()


def column(body, nv, npt, j):
    """Column j: the table is whitespace tokens, per point `<index> <time> <v1> ... <v(nv-1)>`, i.e. nv + 1 tokens."""
    return [float(body[p * (nv + 1) + 1 + j]) for p in range(npt)]


def crossings(times, volts, start, stop):
    """Yield (time in ns, direction) for threshold crossings in the closed window."""
    for (ta, va), (tb, vb) in pairwise(zip(times, volts)):
        if (va < LEVEL) == (vb < LEVEL):
            continue
        when = ta + (tb - ta) * (LEVEL - va) / (vb - va)
        if start <= when <= stop:
            yield when, "r" if vb >= LEVEL else "f"


def main(argv):
    raw, args = argv[1], argv[2:]
    names, npt, nv, body = load(raw)
    if args and args[0] == "--list":
        pat = re.compile(args[1]) if len(args) > 1 else re.compile(".")
        print("\n".join(n for n in names if "#" not in n and pat.search(n)))
        return
    t = [seconds * 1e9 for seconds in column(body, nv, npt, 0)]
    if args and args[0] == "--cross":
        n0, n1 = float(args[1]), float(args[2])
        for n in args[3:]:
            v = column(body, nv, npt, names.index(n))
            print(n, " ".join(f"{edge}{when:.3f}" for when, edge in crossings(t, v, n0, n1)))
        return
    if args and args[0] == "--table":
        clk, n0, n1, nodes = args[1], float(args[2]), float(args[3]), args[4:]
        c = column(body, nv, npt, names.index(clk))
        cols = [column(body, nv, npt, names.index(n)) for n in nodes]
        print("t_ns\t" + "\t".join(n[2:-1].replace("xd.", "") for n in nodes))
        for te, edge in crossings(t, c, n0, n1):
            if edge == "r":
                p = max(i for i in range(npt) if t[i] <= te - 0.15)
                lv = lambda v: "X" if 0.8 < v < 2.5 else str(int(v > LEVEL))
                print(f"{te:.2f}\t" + "\t".join(lv(col[p]) for col in cols))
        return
    if args and args[0] == "--at":
        ns = float(args[1])
        p = min(range(npt), key=lambda q: abs(t[q] - ns))
        print(f"t = {t[p]:.3f} ns")
        for n in args[2:]:
            print(f"{n}\t{column(body, nv, npt, names.index(n))[p]:.3f}")
        return
    t0, t1 = float("-inf"), float("inf")
    nodes = []
    it = iter(args)
    for a in it:
        if a == "--t0":
            t0 = float(next(it))
        elif a == "--t1":
            t1 = float(next(it))
        else:
            nodes.append(a)
    print("node\tmin\tmax\trises\tfalls\tlast crossing (ns)")
    for n in nodes:
        v = column(body, nv, npt, names.index(n))
        vs = [voltage for when, voltage in zip(t, v) if t0 <= when <= t1]
        rises = falls = 0
        last = None
        for when, edge in crossings(t, v, t0, t1):
            last = when
            if edge == "r":
                rises += 1
            else:
                falls += 1
        low = f"{min(vs):.3f}" if vs else ""
        high = f"{max(vs):.3f}" if vs else ""
        last_ns = f"{last:.3f}" if last is not None else ""
        print(f"{n}\t{low}\t{high}\t{rises}\t{falls}\t{last_ns}")


if __name__ == "__main__":
    main(sys.argv)
