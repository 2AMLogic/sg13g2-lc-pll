"""Prescaler cell (/2 CML first stage, then /4-5 dual-modulus).

INP/INN load the VCO tank: the two input devices (the `XCK` emitter followers of
`cml_div23`, bases on INP/INN) are pulled out of the one npn13G2v flavour array
into singleton arrays, one per tank pin, so the integrated top can drop a tank
route on each instead of routing both to one spot (#345). The 240 um
label-to-label span matches vco OUTP/OUTN at x = -120/+120
(`layout/provenance.json`); the vacated array slots are refilled with two dummy
devices so the 129-position 3x43 array keeps its shape (see
`common.plan hbt_split_bases`). The tank-load capacitance is NOT extracted here
(placement only, no routing); that is PEX work on the integrated loop.
"""
import os

from . import common

CELL = "lcpll_prescaler"
SUBCKT = "prescaler"
NETLIST = "design/netlist/prescaler.spice"
INPUT_FIRST = ("INP", "INN")
# Label-to-label span of the split pair: each singleton's base terminal sits
# 3.87 um into its 7.74 um array, so a 240.0 um origin gap is a 240.0 um
# INP-to-INN label span, matching the vco OUTP/OUTN pin span (pins at
# x = -120/+120). Keep in step with PLACE["lcpll_prescaler"] in
# layout/gen_integrated.py.
INPUT_PAIR_SPAN_UM = 240.0


def generate(out_dir):
    return common.build_block(CELL, SUBCKT, os.path.join(common.ROOT, NETLIST), out_dir,
                              input_first=INPUT_FIRST,
                              hbt_split_bases=INPUT_FIRST,
                              explicit_origins={
                                  f"{CELL}_hbt_npn13g2v_base_inp": (0.0, 0.0),
                                  f"{CELL}_hbt_npn13g2v_base_inn": (INPUT_PAIR_SPAN_UM, 0.0),
                              })
