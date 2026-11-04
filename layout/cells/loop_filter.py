"""Loop-filter cell (subckt `loopfilter`: rppd resistors + cap_cmim network)."""
import os

from . import common

CELL = "lcpll_loopfilter"
SUBCKT = "loopfilter"
NETLIST = "design/netlist/loopfilter.spice"


def generate(out_dir):
    return common.build_block(CELL, SUBCKT, os.path.join(common.ROOT, NETLIST), out_dir)
