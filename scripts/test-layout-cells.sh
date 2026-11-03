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

"${PY}" -I - "${ROOT}" "${T}/cells" "${T}/neg" <<'PYEOF' || bad=$((bad+1))
import json, os, sys
import klayout.db as db
root, cells, neg = sys.argv[1:4]
sys.path.insert(0, os.path.join(root, "layout"))
from cells import common
prov = json.load(open(os.path.join(root, "layout/cells.provenance.json")))
fail = 0

def labels(gds, cell):
    ly = db.Layout(); ly.read(gds); c = ly.cell(cell)
    # The cell's own labels only: PDK-authored sub-cells (the sg13g2 HBT) carry their own B/C/E text.
    return sorted({s.text_string for li in ly.layer_indexes()
                   for s in c.shapes(li).each() if s.is_text()})

def check(rec, gds):
    ports = common.read_subckts(os.path.join(root, rec["netlist"]))[rec["subckt"]]["ports"]
    got = labels(gds, rec["cell"])
    extra = [l for l in got if l not in ports]
    missing = [p for p in ports if p not in got]
    allowed = set(rec["undrawn_only_ports"])
    return ports, extra, missing, [m for m in missing if m not in allowed]

for rec in prov["cells"]:
    if rec["status"] == "undrawn":
        print(f"KNOWN-GAP {rec['cell']}: no drawable device ({len(rec['undrawn_devices'])} undrawn); ports {rec['ports']} unlabelled")
        continue
    gds = os.path.join(cells, rec["cell"] + ".gds")
    ports, extra, missing, unexplained = check(rec, gds)
    if extra or unexplained:
        print(f"FAIL {rec['cell']}: labels not in subckt ports {extra}; ports missing without an undrawn-device reason {unexplained}"); fail += 1
    elif missing:
        print(f"KNOWN-GAP {rec['cell']}: ports {missing} reach only undrawn devices; {len(ports)-len(missing)}/{len(ports)} labelled and matching")
    else:
        print(f"PASS {rec['cell']}: {len(ports)} labels == {len(ports)} subckt ports")

# Negative controls on a drawn, complete cell: a dropped label and a renamed label are detected.
rec = next(r for r in prov["cells"] if r["status"] == "drawn")
gds = os.path.join(cells, rec["cell"] + ".gds")
os.makedirs(neg, exist_ok=True)
for name, mutate in (("drop", lambda sh, s: sh.erase(s)), ("rename", lambda sh, s: sh.replace(s, db.DText("BOGUS", s.dtext.trans)))):
    ly = db.Layout(); ly.read(gds); c = ly.cell(rec["cell"])
    for li in ly.layer_indexes():
        done = False
        for s in list(c.shapes(li).each()):
            if s.is_text():
                mutate(c.shapes(li), s); done = True; break
        if done: break
    p = os.path.join(neg, name + ".gds"); ly.write(p)
    _, extra, _, unexplained = check(rec, p)
    if extra or unexplained:
        print(f"PASS NEG {name} label detected")
    else:
        print(f"FAIL NEG {name} label NOT detected"); fail += 1
sys.exit(1 if fail else 0)
PYEOF

[ "${bad}" = 0 ] && echo "layout cells: OK" || echo "layout cells: ${bad} failure(s)"
[ "${bad}" = 0 ]
