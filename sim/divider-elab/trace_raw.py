#!/usr/bin/env python3
"""Per-node activity summary of an ngspice binary rawfile (issue #197 hot-corner stall trace). Stdlib only.

  trace_raw.py RAW --list [PATTERN]          list node names (regex PATTERN)
  trace_raw.py RAW NODE [NODE...] [--t0 NS --t1 NS]
      min/max over the window, rising/falling crossings of 1.65 V, time of the last crossing.
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


def main(argv):
    raw, args = argv[1], argv[2:]
    names, npt, nv, body = load(raw)
    if args and args[0] == "--list":
        pat = re.compile(args[1]) if len(args) > 1 else re.compile(".")
        print("\n".join(n for n in names if "#" not in n and pat.search(n)))
        return
    t = column(body, nv, npt, 0)
    if args and args[0] == "--cross":
        n0, n1 = float(args[1]), float(args[2])
        for n in args[3:]:
            v = column(body, nv, npt, names.index(n))
            out = []
            for i in range(1, npt):
                if n0 <= t[i] * 1e9 <= n1 and (v[i - 1] < LEVEL) != (v[i] < LEVEL):
                    tx = t[i - 1] + (t[i] - t[i - 1]) * (LEVEL - v[i - 1]) / (v[i] - v[i - 1])
                    out.append(("r" if v[i] >= LEVEL else "f") + f"{tx * 1e9:.3f}")
            print(n, " ".join(out))
        return
    if args and args[0] == "--table":
        clk, n0, n1, nodes = args[1], float(args[2]) * 1e-9, float(args[3]) * 1e-9, args[4:]
        c = column(body, nv, npt, names.index(clk))
        cols = [column(body, nv, npt, names.index(n)) for n in nodes]
        print("t_ns\t" + "\t".join(n[2:-1].replace("xd.", "") for n in nodes))
        for q in range(1, npt):
            if c[q - 1] < LEVEL <= c[q]:
                te = t[q - 1] + (t[q] - t[q - 1]) * (LEVEL - c[q - 1]) / (c[q] - c[q - 1])
                if n0 <= te <= n1:
                    p = max(i for i in range(npt) if t[i] <= te - 0.15e-9)
                    lv = lambda v: "X" if 0.8 < v < 2.5 else str(int(v > LEVEL))
                    print(f"{te * 1e9:.2f}\t" + "\t".join(lv(col[p]) for col in cols))
        return
    if args and args[0] == "--at":
        ns = float(args[1])
        p = min(range(npt), key=lambda q: abs(t[q] - ns * 1e-9))
        print(f"t = {t[p] * 1e9:.3f} ns")
        for n in args[2:]:
            print(f"{n}\t{column(body, nv, npt, names.index(n))[p]:.3f}")
        return
    t0 = t1 = None
    nodes = []
    it = iter(args)
    for a in it:
        if a == "--t0":
            t0 = float(next(it)) * 1e-9
        elif a == "--t1":
            t1 = float(next(it)) * 1e-9
        else:
            nodes.append(a)
    print("node\tmin\tmax\trises\tfalls\tlast crossing (ns)")
    for n in nodes:
        v = column(body, nv, npt, names.index(n))
        sel = [(a, b) for a, b in zip(t, v) if (t0 is None or a >= t0) and (t1 is None or a <= t1)]
        rises = falls = 0
        last = None
        for (ta, va), (tb, vb) in pairwise(sel):
            if va < LEVEL <= vb:
                rises += 1
                last = ta + (tb - ta) * (LEVEL - va) / (vb - va)
            elif va >= LEVEL > vb:
                falls += 1
                last = ta + (tb - ta) * (va - LEVEL) / (va - vb)
        vs = [b for _, b in sel]
        print(f"{n}\t{min(vs):.3f}\t{max(vs):.3f}\t{rises}\t{falls}\t{'' if last is None else f'{last * 1e9:.3f}'}")


if __name__ == "__main__":
    main(sys.argv)
