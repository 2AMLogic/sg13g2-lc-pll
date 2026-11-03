"""Prescaler cell (/2 CML first stage, then /4-5 dual-modulus).

INP/INN load the VCO tank: the device group whose gates they drive is placed first, at the
cell origin, so the input geometry sits at the cell edge. The tank-load capacitance is NOT
extracted here (placement only, no routing); that is PEX work on the integrated loop.
"""
import os

from . import common

CELL = "lcpll_prescaler"
SUBCKT = "prescaler"
NETLIST = "design/netlist/prescaler.spice"
INPUT_FIRST = ("INP", "INN")


def generate(out_dir):
    return common.build_block(CELL, SUBCKT, os.path.join(common.ROOT, NETLIST), out_dir,
                              input_first=INPUT_FIRST)
