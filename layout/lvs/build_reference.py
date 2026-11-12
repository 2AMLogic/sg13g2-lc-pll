#!/usr/bin/env python3
"""Build the item-4 LVS reference netlist: design/netlist/pll_top.spice (item 1) plus a `vco`
subckt wrapped around the device cards of the pinned sg13g2-vco netlist.

The pinned .fetched/sg13g2-vco/design/vco.spice is a testbench: its `.subckt vco` header is
commented out and it carries supplies, models and a .control block. Only the device cards
(XL1 .. RRE) are taken, verbatim except that node `0` becomes the port `VSS`; nothing is resized.
Port order matches the `XVCO VCTRL VOP VON VDDV VSS vco` call in pll_top.

    python3 layout/lvs/build_reference.py            # writes layout/lvs/top.reference.spice
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VCO = os.path.join(ROOT, ".fetched", "sg13g2-vco", "design", "vco.spice")
TOP = os.path.join(ROOT, "design", "netlist", "pll_top.spice")
OUT = os.path.join(ROOT, "layout", "lvs", "top.reference.spice")

lines = open(VCO).read().splitlines()
start = next(i for i, l in enumerate(lines) if l.startswith("XL1 "))
end = next(i for i, l in enumerate(lines) if l.startswith("RRE "))
dev = []
for l in lines[start:end + 1]:
    toks = l.split()
    # node tokens only: strip params (contain '=') and the model name (last non-param token)
    out = []
    for t in toks:
        out.append("VSS" if t == "0" else t)
    dev.append(" ".join(out))
body = ["* sg13g2-vco@17e49a8 design/vco.spice device cards, node 0 -> VSS (see build_reference.py)",
        ".subckt vco VCTRL OUTP OUTN VDD VSS"] + dev + [".ends", ""]
top = open(TOP).read()
if not top.endswith("\n"):
    top += "\n"
open(OUT, "w").write(top + "\n" + "\n".join(body))
print("wrote", OUT, "(%d vco device cards)" % len(dev))
