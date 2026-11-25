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
"${PY}" -I "${ROOT}/scripts/layout_cells_check.py" plan "${ROOT}" || bad=$((bad+1))

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
"${PY}" -I "${ROOT}/scripts/layout_cells_check.py" roundtrip "${ROOT}" "${T}/cells" "${T}/rt" || bad=$((bad+1))

"${PY}" -I "${ROOT}/scripts/layout_cells_check.py" labels "${ROOT}" "${T}/cells" "${T}/neg" || bad=$((bad+1))

[ "${bad}" = 0 ] && echo "layout cells: OK" || echo "layout cells: ${bad} failure(s)"
[ "${bad}" = 0 ]
