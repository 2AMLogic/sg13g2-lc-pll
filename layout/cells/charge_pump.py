"""Charge-pump cell (subckt `cp`: bias, up/down legs, dump buffer)."""
import os

from . import common

CELL = "lcpll_cp"
SUBCKT = "cp"
NETLIST = "design/netlist/cp.spice"


def generate(out_dir):
    return common.build_block(CELL, SUBCKT, os.path.join(common.ROOT, NETLIST), out_dir)
