#!/usr/bin/env bash
# Loop-block cell check: regenerate every cell, compare with layout/cells.provenance.json, and
# check each cell's pin labels against its `.subckt` ports (design/netlist/*.spice).
# `klt interface-check` pairs labels of two placed blocks, so it does not apply to a
# pin-vs-port comparison of one cell; this script is the stated alternative. Cells with
# undrawn devices (tool gaps, recorded in the provenance) may lack labels only for ports
# whose nets touch an undrawn device; that case prints KNOWN-GAP, not PASS.
# Needs .venv/bin/python with `klayout` (override LAYOUT_PY), klt, and an sg13g2 PDK klt resolves.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${LAYOUT_PY:-${ROOT}/.venv/bin/python}"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
bad=0

# plan() unit check (#415): a split-off singleton's id is built from the unit's base net, so
# two units of one HBT flavour on one split base would plan two groups with one id (and
# build_block keys reports/origins by it). The post-assembly uniqueness check must refuse
# that -- and the .lower()-folded spelling of two different base nets -- while the
# one-unit-per-base shape still plans. Pure python + klayout only; runs before the klt parts.
"${PY}" -I - "${ROOT}" <<'PLANEOF' || bad=$((bad+1))
import os, sys
root = sys.argv[1]
sys.path.insert(0, os.path.join(root, "layout"))
from cells import common

def hbt(path, base):
    return {"path": path, "model": "npn13G2v", "nets": ["vcc", base, "vee"],
            "params": {"nx": "1"}}

fail = 0

# Two units of one flavour on one split base: refused, naming the colliding id and the units.
try:
    common.plan("blk", [hbt("xck1", "INP"), hbt("xck2", "INP"), hbt("xd1", "VB")],
                hbt_split_bases=("INP",))
    print("FAIL plan: two units on one split base did not raise"); fail += 1
except common.PlanError as e:
    msg = str(e)
    ok = "blk_hbt_npn13g2v_base_inp" in msg and "xck1" in msg and "xck2" in msg
    print(("PASS" if ok else "FAIL") + f" plan: two units on one split base raise: {msg}")
    fail += 0 if ok else 1

# One unit per split base: still plans, ids unique, both singletons present.
groups = common.plan("blk", [hbt("xck1", "INP"), hbt("xck2", "INN"), hbt("xd1", "VB")],
                     hbt_split_bases=("INP", "INN"))
ids = [g["id"] for g in groups]
ok = len(ids) == len(set(ids)) and {"blk_hbt_npn13g2v_base_inp", "blk_hbt_npn13g2v_base_inn"} <= set(ids)
print(("PASS" if ok else "FAIL") + f" plan: one unit per split base plans {len(ids)} unique-id groups")
fail += 0 if ok else 1

# Nets differing only by case fold to one id: also refused.
try:
    common.plan("blk", [hbt("xck1", "INP"), hbt("xck2", "inp"), hbt("xd1", "VB")],
                hbt_split_bases=("INP", "inp"))
    print("FAIL plan: case-folded split bases did not raise"); fail += 1
except common.PlanError as e:
    print(f"PASS plan: case-folded split bases raise: {e}")

# port_net_label_sites() unit check (#416): every SG13G2 metal terminal (8, 10, 30, 50, 67,
# 126, 134) reported on drawing datatype 0 must resolve to metal text datatype 25, while a
# port terminal on an unmapped layer (e.g. GatPoly 5/0) must raise PlanError loudly.
metal_layers = (8, 10, 30, 50, 67, 126, 134)
syn_groups = [{"id": "g0", "terminals": [
    {"port": f"P{la}", "net": f"N{la}", "unit": "u0"} for la in metal_layers
]}]
syn_reports = {"g0": {"ports": [
    {"name": f"P{la}", "x_um": 1.0, "y_um": 2.0, "layer": {"layer": la, "datatype": 0}}
    for la in metal_layers
]}}
syn_origins = {"g0": {"x": 10.0, "y": 20.0}}
sites = common.port_net_label_sites(syn_groups, syn_reports, syn_origins)
want_sites = {f"N{la}": (11.0, 22.0, la, 25) for la in metal_layers}
if sites == want_sites:
    print("PASS port_net_label_sites: all 7 SG13G2 metal layers map drawing /0 -> text /25")
else:
    print(f"FAIL port_net_label_sites: got {sites}, wanted {want_sites}"); fail += 1

bad_groups = [{"id": "g_poly", "terminals": [{"port": "G0", "net": "IN", "unit": "u0"}]}]
bad_reports = {"g_poly": {"ports": [
    {"name": "G0", "x_um": 0.0, "y_um": 0.0, "layer": {"layer": 5, "datatype": 0}}
]}}
try:
    common.port_net_label_sites(bad_groups, bad_reports, {"g_poly": {"x": 0.0, "y": 0.0}})
    print("FAIL port_net_label_sites: unmapped layer 5/0 did not raise"); fail += 1
except (common.PlanError, RuntimeError) as e:
    ok = "g_poly" in str(e) and "IN" in str(e) and "5/0" in str(e)
    print(("PASS" if ok else "FAIL") + f" port_net_label_sites: unmapped layer 5/0 raises: {e}")
    fail += 0 if ok else 1
sys.exit(1 if fail else 0)
PLANEOF

"${PY}" "${ROOT}/layout/gen_cells.py" --out "${T}/cells" --check || { echo "FAIL regenerate vs provenance"; bad=$((bad+1)); }
[ "${bad}" = 0 ] && echo "PASS regenerated cells match layout/cells.provenance.json"

# layout/gen_cells.py's digest() is billed as writer-independent, so each cell's digest must
# survive a KLayout read->write->read of its stream -- a clip, a merge, a DRC-prep step. It did
# not before #263: digest() hashed per-layer records in ly.layer_indexes() order, and a re-save
# permutes that order, so the digest moved for a stream whose geometry was untouched. On `main`
# before the fix this was live, not hypothetical: the check above mismatched four of the six
# committed digests on a host whose klt writes the layers in a different order, while the cells'
# geometry was identical. Each cell carries its own guards so the case cannot pass vacuously.
# scripts/layout_rt.py compares both streams and the recorded digest for this harness and
# scripts/test-layout-top.sh (#379).
"${PY}" -I - "${ROOT}" "${T}/cells" "${T}/rt" <<'RTEOF' || bad=$((bad+1))
import json, os, sys
import klayout.db as db
root, cells, rtdir = sys.argv[1:4]
sys.path.insert(0, os.path.join(root, "layout"))
sys.path.insert(0, os.path.join(root, "scripts"))
import cells.common as cc
import layout_rt as rt

prov = json.load(open(os.path.join(root, "layout/cells.provenance.json")))
os.makedirs(rtdir, exist_ok=True)
fail = 0

for rec in prov["cells"]:
    if rec["status"] == "undrawn":
        continue
    name = rec["cell"]
    gds = os.path.join(cells, name + ".gds")
    rtp = os.path.join(rtdir, name + ".rt.gds")
    want = rec["geometry_sha256"]
    trip = rt.RoundTrip(gds, rtp, name, want)
    result = trip.compare(cc.digest)
    if not result.order_changed:
        # No permutation to survive on this klayout: say so rather than banking a vacuous PASS.
        print(f"KNOWN-GAP {name}: the re-save did not permute the layer-index order, so this cell cannot discriminate the fix")
    elif not result.digest_survived:
        print(f"FAIL {name}: round-tripped digest {result.resaved_digest} != {result.original_digest}"); fail += 1
    elif trip.compare(rt.enum_digest).digest_survived:
        print(f"FAIL NEG {name}: the pre-#263 enumeration-order digest survived the re-save too, so this cell cannot discriminate the fix"); fail += 1
    else:
        print(f"PASS {name}: digest survives a KLayout re-save that moves the pre-#263 one")
    if not result.matches_record:
        print(f"FAIL {name}: digest {result.original_digest} != recorded {want}"); fail += 1

# Negative control: a real geometry change must still move the digest. The box is placed clear of
# the cell's bounding box so a merge with existing geometry cannot absorb it.
rec = next(r for r in prov["cells"] if r["status"] == "drawn")
name = rec["cell"]
ly = rt.read(os.path.join(cells, name + ".gds"))
b = ly.cell(name).bbox()
ly.cell(name).shapes(ly.layer(8, 0)).insert(db.Box(b.right + 1000, b.top + 1000, b.right + 2000, b.top + 2000))
ed = os.path.join(rtdir, name + ".edited.gds"); ly.write(ed)
if rt.digest_of(ed, name, cc.digest) == rec["geometry_sha256"]:
    print(f"FAIL NEG {name}: an inserted shape did not move the digest"); fail += 1
else:
    print(f"PASS NEG {name}: an inserted shape moves the digest")
sys.exit(1 if fail else 0)
RTEOF

"${PY}" -I - "${ROOT}" "${T}/cells" "${T}/neg" <<'PYEOF' || bad=$((bad+1))
import collections, json, os, sys
import klayout.db as db
root, cells, neg = sys.argv[1:4]
sys.path.insert(0, os.path.join(root, "layout"))
from cells import common
prov = json.load(open(os.path.join(root, "layout/cells.provenance.json")))
fail = 0

def labels(gds, cell):
    """name -> [(layer, x_um, y_um)]: the cell's own labels only (PDK-authored sub-cells such as
    the sg13g2 HBT carry their own B/C/E text below instances). NOT a set of names: the contract
    is one label per port at the recorded site, and a set cannot see a second copy of the same
    string -- routed cells shipped two labels per port through exactly that blind spot (#349)."""
    ly = db.Layout(); ly.read(gds); c = ly.cell(cell)
    out = collections.defaultdict(list)
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        for s in c.shapes(li).each():
            if s.is_text():
                d = s.dtext.trans.disp
                out[s.text_string].append((f"{info.layer}/{info.datatype}", round(d.x, 3), round(d.y, 3)))
    return out

# SG13G2 metal pin/net text layers read by sg13g2.lvs (layers_definitions.lvs +
# general_connections.lvs:57-63) and klt's curated sg13g2 EXTRACTION_DECK.metal_labels (#416).
METAL_TEXT_LAYERS = {f"{la}/25" for la in (8, 10, 30, 50, 67, 126, 134)}

def check(rec, gds):
    ports = common.read_subckts(os.path.join(root, rec["netlist"]))[rec["subckt"]]["ports"]
    got = labels(gds, rec["cell"])
    counts = collections.Counter({n: len(v) for n, v in got.items()})
    extra = [l for l in got if l not in ports]
    missing = [p for p in ports if p not in got]
    allowed = set(rec["undrawn_only_ports"])
    dupes = sorted(f"{n} x{c}" for n, c in counts.items() if c > 1)
    # Every direct text shape on the cell -- and every recorded port_labels entry -- must sit on
    # an SG13G2 */25 metal text layer (#416: sg13g2.lvs ignores drawing */0 texts).
    bad_purpose = sorted(
        [f"{n}:{lay}" for n, v in got.items() for lay, _, _ in v if lay not in METAL_TEXT_LAYERS]
        + [f"recorded {p}:{site['layer']}" for p, site in rec.get("port_labels", {}).items()
           if site["layer"] not in METAL_TEXT_LAYERS])
    # Each stamped port's one label must sit on the layer and at the um site the provenance
    # recorded. The 0.002 um tolerance is 2 dbu: it absorbs float -> 1 nm-dbu quantisation on the
    # GDS round trip, while a foreign copy of the label sits um away or on a router label layer.
    misplaced = sorted(
        f"{p}:{lay},{x},{y} != recorded {site['layer']},{site['x_um']},{site['y_um']}"
        for p, site in rec.get("port_labels", {}).items()
        for lay, x, y in got.get(p, [])
        if lay != site["layer"] or abs(x - site["x_um"]) > 0.002 or abs(y - site["y_um"]) > 0.002)
    return ports, extra, missing, dupes, misplaced, bad_purpose, [m for m in missing if m not in allowed]

for rec in prov["cells"]:
    if rec["status"] == "undrawn":
        print(f"KNOWN-GAP {rec['cell']}: no drawable device ({len(rec['undrawn_devices'])} undrawn); ports {rec['ports']} unlabelled")
        continue
    gds = os.path.join(cells, rec["cell"] + ".gds")
    ports, extra, missing, dupes, misplaced, bad_purpose, unexplained = check(rec, gds)
    if extra or dupes or misplaced or bad_purpose or unexplained:
        print(f"FAIL {rec['cell']}: labels not in subckt ports {extra}; duplicated labels {dupes}; "
              f"labels off the recorded site {misplaced}; labels off */25 metal text purpose {bad_purpose}; "
              f"ports missing without an undrawn-device reason {unexplained}"); fail += 1
    elif missing:
        print(f"KNOWN-GAP {rec['cell']}: ports {missing} reach only undrawn devices; {len(ports)-len(missing)}/{len(ports)} labelled and matching")
    else:
        print(f"PASS {rec['cell']}: {len(ports)} labels == {len(ports)} subckt ports (all on */25)")

# Negative controls on a drawn, complete cell: a dropped label, a renamed label, a duplicated
# label (a second copy of a valid port name -- the exact defect that shipped in #349, invisible
# to a set-based check because the set of names is unchanged), and a port label moved from */25
# to drawing purpose */0 (#416: invisible to sg13g2.lvs) are all detected.
rec = next(r for r in prov["cells"] if r["status"] == "drawn")
gds = os.path.join(cells, rec["cell"] + ".gds")
os.makedirs(neg, exist_ok=True)
for name, mutate in (("drop", lambda _ly, sh, _info, s: sh.erase(s)),
                     ("rename", lambda _ly, sh, _info, s: sh.replace(s, db.DText("BOGUS", s.dtext.trans))),
                     ("duplicate", lambda _ly, sh, _info, s: sh.insert(db.DText(s.text_string, s.dtext.trans)))):
    ly = db.Layout(); ly.read(gds); c = ly.cell(rec["cell"])
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        done = False
        for s in list(c.shapes(li).each()):
            if s.is_text():
                mutate(ly, c.shapes(li), info, s); done = True; break
        if done: break
    p = os.path.join(neg, name + ".gds"); ly.write(p)
    _, extra, _, dupes, misplaced, bad_purpose, unexplained = check(rec, p)
    if extra or dupes or misplaced or bad_purpose or unexplained:
        print(f"PASS NEG {name} label detected")
    else:
        print(f"FAIL NEG {name} label NOT detected"); fail += 1

# Drawing-purpose (/0) negative control (#416): move one port label from <la>/25 to <la>/0 and
# assert check() rejects it via bad_purpose even if port_labels also recorded <la>/0.
ly = db.Layout(); ly.read(gds); c = ly.cell(rec["cell"])
moved = None
for li in ly.layer_indexes():
    info = ly.get_info(li)
    for s in list(c.shapes(li).each()):
        if s.is_text():
            txt, dtrans = s.text_string, s.dtext.trans
            moved = (txt, info.layer, info.datatype)
            c.shapes(li).erase(s)
            c.shapes(ly.layer(info.layer, 0)).insert(db.DText(txt, dtrans))
            break
    if moved is not None:
        break
p_dt0 = os.path.join(neg, "drawing_dt0.gds"); ly.write(p_dt0)
if moved is None or moved[2] != 25:
    print(f"FAIL NEG drawing_dt0: expected a source /25 port label to move to /0, got {moved}"); fail += 1
else:
    _, _, _, _, misplaced, bad_purpose, _ = check(rec, p_dt0)
    forged_rec = dict(rec, port_labels=dict(rec["port_labels"],
                      **{moved[0]: dict(rec["port_labels"][moved[0]], layer=f"{moved[1]}/0")}))
    _, _, _, _, _, forged_bad_purpose, _ = check(forged_rec, p_dt0)
    if bad_purpose and misplaced and forged_bad_purpose:
        print(f"PASS NEG drawing_dt0 ({moved[0]} {moved[1]}/25 -> {moved[1]}/0) label detected")
    else:
        print(f"FAIL NEG drawing_dt0 not cleanly detected: bad_purpose={bad_purpose} "
              f"misplaced={misplaced} forged_bad_purpose={forged_bad_purpose}"); fail += 1
sys.exit(1 if fail else 0)
PYEOF

[ "${bad}" = 0 ] && echo "layout cells: OK" || echo "layout cells: ${bad} failure(s)"
[ "${bad}" = 0 ]
