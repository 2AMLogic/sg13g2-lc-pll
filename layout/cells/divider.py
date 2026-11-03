"""Divider cell: cml2cmos + M counter + A counter (subckt `divider`)."""
import os

from . import common

CELL = "lcpll_divider"
SUBCKT = "divider"
NETLIST = "design/netlist/divider.spice"


def generate(out_dir):
    return common.build_block(CELL, SUBCKT, os.path.join(common.ROOT, NETLIST), out_dir)
