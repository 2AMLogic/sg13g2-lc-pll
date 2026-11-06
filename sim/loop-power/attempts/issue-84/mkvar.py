#!/usr/bin/env python3
"""scratch: shared-clock-pair variant of the generated divider netlist (experiment only, not committed)."""
import re, sys
src, dst, nbuf = sys.argv[1], sys.argv[2], int(sys.argv[3])
t = open(src).read()
# 1. new flop cell without local clock inverters, CLKB/CKBB are pins
m = re.search(r"\.subckt dff_tg_hv D CLK Q VDD VSS\n.*?\.ends\n", t, re.S)
cell = m.group(0)
new = cell.replace(".subckt dff_tg_hv D CLK Q VDD VSS", ".subckt dff_tg_hv_sc D CLKB CKBB Q VDD VSS")
new = re.sub(r"^XICLK .*\n", "", new, flags=re.M)
new = re.sub(r"^XICKBB .*\n", "", new, flags=re.M)
new = new.replace("*.ipin CLK\n", "*.ipin CLKB\n*.ipin CKBB\n")
t = t.replace(cell, cell + "\n" + new)
# 2. in mcounter/acounter/divider, plain dff_tg_hv instances take shared clock nets
def fix(sub, ck):
    global t
    mm = re.search(r"\.subckt %s .*?\.ends\n" % sub, t, re.S)
    body = mm.group(0)
    b2 = re.sub(r"^(X\w+ \S+) %s (\S+) (VDD VSS) dff_tg_hv$" % ck, r"\1 CLKB CKBB \2 \3 dff_tg_hv_sc", body, flags=re.M)
    b2 = b2.replace(".subckt %s %s " % (sub, ck), ".subckt %s %s CLKB CKBB " % (sub, ck)) if sub != "divider" else b2
    t = t.replace(body, b2)
fix("mcounter", "CK"); fix("acounter", "CK")
mm = re.search(r"\.subckt divider .*?\.ends\n", t, re.S); body = mm.group(0)
b2 = body.replace("XM CKL ", "XM CKL CLKB CKBB ").replace("XA CKL ", "XA CKL CLKB CKBB ")
b2 = re.sub(r"^XFB TC CKL FB VDD VSS dff_tg_hv$", "XFB TC CLKB CKBB FB VDD VSS dff_tg_hv_sc", b2, flags=re.M)
bufs = "".join("XKB%d CKL CLKB VDD VSS inv_hv\n" % i for i in range(nbuf)) + "".join("XKC%d CLKB CKBB VDD VSS inv_hv\n" % i for i in range(nbuf))
b2 = b2.replace(".ends\n", bufs + ".ends\n")
t = t.replace(body, b2)
# subckt pin lists for the counters: instance lines in divider already got the nets; fix pin order on mcounter/acounter (CK first)
open(dst, "w").write(t)
