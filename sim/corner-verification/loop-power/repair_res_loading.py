#!/usr/bin/env python3
"""One-shot repair (issue #452): load a resistor model in the #97 loop-power requests.

Every request-*.json here except the three stage requests and flop-toggle drives a body that instantiates
PDK rppd/rhigh resistors (design/netlist/{prescaler,divider}.spice, PR #169), but the
requests were written before that and load only cornerMOShv/cornerCAP/cornerHBT sections
with at most psp103.osdi preloaded -- so ngspice aborts at parse ("unknown subckt rppd";
rppd is a subcircuit in resistors_mod.lib whose inner devices are r3_cmc OSDI models).

The repair per request, exactly what res_stage2() in make_requests.py (issue #164) and
sim/divider-elab/gen_corner_requests.py already do: each SLOW/TYP/FAST process entry also
selects cornerRES.lib (SLOW=res_wcs, TYP=res_typ, FAST=res_bcs), options.osdi_preload gains
the r3_cmc OSDI, and options.ngspice_init is set to hsa behavior. Idempotent: a second run
changes nothing.

Regenerating any of these files from its make_*_97.py generator would reintroduce the gap
(the generators do not add the res family, deliberately: req() in make_requests.py must not
grow it or the stage requests would double-append). Re-run this script after any such
regeneration. The three stage requests (request-stage1.json, request-stage2.json,
request-stage2-nominal-startup.json) are PR #447/#429 territory and are never touched; any
other process name that is not a DR-004 bundle aborts the repair rather than being skipped.

Run from anywhere: python3 -I sim/corner-verification/loop-power/repair_res_loading.py
(with no arguments it repairs every request-*.json next to this file except the stage
requests; pass explicit FILE arguments to repair just those).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
import corner_set  # noqa: E402  (the spec C-grid, defined once in sim/corner_set.py)

# PR #447 / #429 own these; the stage-1 grid has no resistor axis (res_stage2's note).
# request-flop-toggle-97.json is excluded too: it elaborates only dff_tg_hv/inv_hv, never the
# cml2cmos rppd block, so it parses without a resistor model (its NQS preload is issue #451's).
SKIP = ("request-stage1.json", "request-stage2.json", "request-stage2-nominal-startup.json",
        "request-flop-toggle-97.json")

R3_CMC = "$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/osdi/r3_cmc.osdi"
INIT = ["set ngbehavior=hsa"]
COMMENT = ("RESISTOR LOADING (issue #452): repaired in place -- this deck instantiates PDK rppd/rhigh "
           "resistors (PR #169) but carried no resistor model, so ngspice aborted at parse (unknown "
           "subckt rppd). Added cornerRES.lib (SLOW/TYP/FAST = res_wcs/res_typ/res_bcs) and the r3_cmc "
           "OSDI, as res_stage2() in make_requests.py does (issue #164). Regenerating this file from "
           "its make_* generator reintroduces the gap; re-run repair_res_loading.py afterwards.")


def repair(path):
    """Apply the resistor loading to one request file. True if the file was rewritten."""
    with open(path) as f:
        d = json.load(f)
    changed = False
    for p in d["corners"]["process"]:
        name = p.get("name")
        if name not in corner_set.BUNDLE:
            sys.exit("%s: process name %r is not a DR-004 bundle (one of %s); refusing to guess "
                     "its resistor corner -- repair it by hand" % (path, name, "/".join(corner_set.BUNDLES)))
        if not any(s.get("lib", "").endswith("cornerRES.lib") for s in p["sections"]):
            p["sections"] += corner_set.bundle_sections(name, ("res",))
            changed = True
    opts = d.setdefault("options", {})
    preload = opts.setdefault("osdi_preload", [])
    if R3_CMC not in preload:
        preload.append(R3_CMC)
        changed = True
    if opts.get("ngspice_init") != INIT:
        opts["ngspice_init"] = list(INIT)
        changed = True
    comment = d.setdefault("_comment", [])
    if not any("#452" in c for c in comment):
        comment.append(COMMENT)
        changed = True
    if changed:
        with open(path, "w") as f:
            json.dump(d, f, indent=1)
            f.write("\n")
    return changed


def targets():
    """Every request-*.json next to this file except the three stage requests."""
    return [n for n in sorted(os.listdir(HERE))
            if n.startswith("request-") and n.endswith(".json") and n not in SKIP]


if __name__ == "__main__":
    files = sys.argv[1:] or targets()
    repaired = 0
    for name in files:
        if repair(os.path.join(HERE, name)):
            print("repaired  %s" % name)
            repaired += 1
        else:
            print("already   %s" % name)
    print("%d of %d request(s) rewritten (the rest already carried the resistor loading)" % (repaired, len(files)))
