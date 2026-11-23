"""The spec C-grid corner set, in one place.

`spec/target-spec.md` §"How to read this file" says the corner set "is defined
once in §Corner set"; `spec/target-spec.md` §Corner set defines it. This module
is that one definition for the `klt sim` request generators: the stage-1 device
axes, the temperature axis, the stage-1 and stage-2 supplies, and the DR-004
`SLOW`/`TYP`/`FAST` bundles together with the corner `.lib` file and section
name each device family uses.

A generator states only which device families its circuit contains — the charge
pump holds HV MOS alone, the prescaler chain HBT plus poly resistors, the
loop-power body MOS + MIM + HBT — and keeps its own `models.pdk` string, lib
path prefix, stages, shards, measurements and options. Nothing about the
*content* of a request is decided here beyond the corner names themselves.

Several generators run under `python3 -I`, which does not put the script's own
directory on `sys.path`, so import this with an explicit entry (the pattern of
`layout/gen_integrated.py` and `scripts/gen_prescaler_vce_request.py`):

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the sim/ dir
    import corner_set  # noqa: E402
"""

# --- Stage 1: 135 model-grid points at V_STAGE1 (spec/target-spec.md §Corner set).
MOS = ["tt", "ss", "ff", "sf", "fs"]    # cornerMOShv.lib, 5 points
MIM = ["typ", "bcs", "wcs"]             # cornerCAP.lib, 3 points
HBT = ["typ", "bcs", "wcs"]             # cornerHBT.lib, 3 points (VCO + prescaler stage 1 use npn13G2v)

# --- Axes shared by both stages.
TEMPS = [-40, 27, 125]                  # degrees C (VCO row 11: -40 to +125)
V_STAGE1 = 3.3                          # nominal supply, V
V_STAGE2 = [2.97, 3.63]                 # the 18 stage-2 supply sub-corners' two rails, V

# --- Device family -> (corner .lib file name, .lib section-name prefix).
FAMILY = {
    "mos": ("cornerMOShv.lib", "mos_"),
    "mim": ("cornerCAP.lib", "cap_"),
    "hbt": ("cornerHBT.lib", "hbt_"),
    "res": ("cornerRES.lib", "res_"),
}

# PDK-relative prefix for those lib files. Pass an absolute prefix to the
# helpers below instead when a request needs absolute paths; either way it must
# end in the path separator.
LIB = "libs.tech/ngspice/models/"

# --- DR-004 stage-2 bundles, in spec order. The "res" entry is the
# "poly-resistor corner of the grid point they are on" of
# spec/target-spec.md §Corner set (loop-side crossing); it reaches a request
# only for a circuit that asks for the "res" family.
BUNDLES = ["SLOW", "TYP", "FAST"]
BUNDLE = {
    "SLOW": {"mos": "ss", "mim": "wcs", "hbt": "wcs", "res": "wcs"},
    "TYP": {"mos": "tt", "mim": "typ", "hbt": "typ", "res": "typ"},
    "FAST": {"mos": "ff", "mim": "bcs", "hbt": "bcs", "res": "bcs"},
}


def lib_path(family, lib=LIB):
    """FAMILY's corner .lib path under the prefix LIB.

    lib_path("mos") == "libs.tech/ngspice/models/cornerMOShv.lib"
    """
    return lib + FAMILY[family][0]


def section(family, corner):
    """FAMILY's .lib section name at the short corner name CORNER.

    section("mos", "tt") == "mos_tt"
    """
    return FAMILY[family][1] + corner


def sections(families, lib=LIB, **corners):
    """A request's `corners.process[].sections` list for FAMILIES, in that order.

    FAMILIES names the device families the circuit contains (keys of FAMILY);
    each needs its short corner name as a keyword. Extra keywords are ignored,
    so a caller may pass a family it only sometimes asks for:

        sections(["mos", "mim", "hbt"], mos="ss", mim="wcs", hbt="wcs")
    """
    return [{"lib": lib_path(f, lib), "section": section(f, corners[f])} for f in families]


def bundle(name, families):
    """The short corner names of FAMILIES for DR-004 bundle NAME, in that order.

    bundle("SLOW", ("mos", "mim", "hbt")) == ["ss", "wcs", "wcs"]
    """
    return [BUNDLE[name][f] for f in families]


def bundle_sections(name, families, lib=LIB):
    """sections() for DR-004 bundle NAME ("SLOW" / "TYP" / "FAST")."""
    return sections(families, lib=lib, **{f: BUNDLE[name][f] for f in families})


def bundle_corners(family):
    """FAMILY's short corner names across SLOW / TYP / FAST, in spec order.

    bundle_corners("mos") == ["ss", "tt", "ff"]
    """
    return [BUNDLE[b][family] for b in BUNDLES]
