"""Lock-detector cell: the sg13g2-pll `lock_detector` subckt in design/netlist/pll_top.spice."""
import os

from . import common

CELL = "lcpll_lockdet"
SUBCKT = "lock_detector"
NETLIST = "design/netlist/pll_top.spice"


def generate(out_dir):
    return common.build_block(CELL, SUBCKT, os.path.join(common.ROOT, NETLIST), out_dir)
