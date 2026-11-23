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

def check(rec, gds):
    ports = common.read_subckts(os.path.join(root, rec["netlist"]))[rec["subckt"]]["ports"]
    got = labels(gds, rec["cell"])
    counts = collections.Counter({n: len(v) for n, v in got.items()})
    extra = [l for l in got if l not in ports]
    missing = [p for p in ports if p not in got]
    allowed = set(rec["undrawn_only_ports"])
    dupes = sorted(f"{n} x{c}" for n, c in counts.items() if c > 1)
    # Each stamped port's one label must sit on the layer and at the um site the provenance
    # recorded. The 0.002 um tolerance is 2 dbu: it absorbs float -> 1 nm-dbu quantisation on the
    # GDS round trip, while a foreign copy of the label sits um away or on a router label layer.
    misplaced = sorted(
        f"{p}:{lay},{x},{y} != recorded {site['layer']},{site['x_um']},{site['y_um']}"
        for p, site in rec.get("port_labels", {}).items()
        for lay, x, y in got.get(p, [])
        if lay != site["layer"] or abs(x - site["x_um"]) > 0.002 or abs(y - site["y_um"]) > 0.002)
    return ports, extra, missing, dupes, misplaced, [m for m in missing if m not in allowed]

for rec in prov["cells"]:
    if rec["status"] == "undrawn":
        print(f"KNOWN-GAP {rec['cell']}: no drawable device ({len(rec['undrawn_devices'])} undrawn); ports {rec['ports']} unlabelled")
        continue
    gds = os.path.join(cells, rec["cell"] + ".gds")
    ports, extra, missing, dupes, misplaced, unexplained = check(rec, gds)
    if extra or dupes or misplaced or unexplained:
        print(f"FAIL {rec['cell']}: labels not in subckt ports {extra}; duplicated labels {dupes}; "
              f"labels off the recorded site {misplaced}; ports missing without an undrawn-device reason {unexplained}"); fail += 1
    elif missing:
        print(f"KNOWN-GAP {rec['cell']}: ports {missing} reach only undrawn devices; {len(ports)-len(missing)}/{len(ports)} labelled and matching")
    else:
        print(f"PASS {rec['cell']}: {len(ports)} labels == {len(ports)} subckt ports")

# Negative controls on a drawn, complete cell: a dropped label, a renamed label and a duplicated
# label (a second copy of a valid port name -- the exact defect that shipped in #349, invisible
# to a set-based check because the set of names is unchanged) are all detected.
rec = next(r for r in prov["cells"] if r["status"] == "drawn")
gds = os.path.join(cells, rec["cell"] + ".gds")
os.makedirs(neg, exist_ok=True)
for name, mutate in (("drop", lambda sh, s: sh.erase(s)),
                     ("rename", lambda sh, s: sh.replace(s, db.DText("BOGUS", s.dtext.trans))),
                     ("duplicate", lambda sh, s: sh.insert(db.DText(s.text_string, s.dtext.trans)))):
    ly = db.Layout(); ly.read(gds); c = ly.cell(rec["cell"])
    for li in ly.layer_indexes():
        done = False
        for s in list(c.shapes(li).each()):
            if s.is_text():
                mutate(c.shapes(li), s); done = True; break
        if done: break
    p = os.path.join(neg, name + ".gds"); ly.write(p)
    _, extra, _, dupes, misplaced, unexplained = check(rec, p)
    if extra or dupes or misplaced or unexplained:
        print(f"PASS NEG {name} label detected")
    else:
        print(f"FAIL NEG {name} label NOT detected"); fail += 1
sys.exit(1 if fail else 0)
PYEOF

[ "${bad}" = 0 ] && echo "layout cells: OK" || echo "layout cells: ${bad} failure(s)"
[ "${bad}" = 0 ]
