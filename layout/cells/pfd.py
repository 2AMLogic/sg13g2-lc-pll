"""PFD cell: the sg13g2-pll `pfd` subckt as carried in design/netlist/pll_top.spice.

Adopted at the netlist level (pinned sg13g2-pll@e71ff61, see reuse.lock.json); drawn with the
same netlist-to-device-group method sg13g2-pll uses. See layout/README.md for why no upstream
layout stream is imported.
"""
import os

from . import common

CELL = "lcpll_pfd"
SUBCKT = "pfd"
NETLIST = "design/netlist/pll_top.spice"


def generate(out_dir):
    return common.build_block(CELL, SUBCKT, os.path.join(common.ROOT, NETLIST), out_dir)
