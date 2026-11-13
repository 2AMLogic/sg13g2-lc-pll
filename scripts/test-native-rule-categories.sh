#!/usr/bin/env bash
# Check layout/drc/native_rule_categories.txt -- the independently derived list of RDB rule
# categories the IHP SG13G2 native DRC runset declares, which `klt drc
# --expect-rule-categories-file` is given so a zero-violation native run can be graded
# `clean` instead of `coverage_unknown` (#36, T1 item 3).
#
# The committed list is only valid for the deck revision it was read from and for the switch
# set the DRC run uses, so this script re-derives it and asserts the invariants the
# derivation relies on:
#   1. regeneration reproduces the committed list byte-for-byte;
#   2. every file in the committed include chain still hashes to the recorded value;
#   3. chip area (the deck's `en_tiles`) does not move the declared set;
#   4. the two layout-dependent categories in the include chain stay undeclared *for this
#      layout*, with the premise measured from layout/top.gds rather than assumed:
#        - MIM.gR  : total MIM (36/0) area must stay under the 174800 um2 recommended max,
#                    and feeding a larger area to the generator must add MIM.gR back;
#        - Seal.l  : the layout must have no EdgeSeal boundary (39/4);
#   5. the deck does not splice in the geometry-gated rule files (density, antenna), whose
#      rules emit a category only when a measured density is out of range;
#   6. negative controls: each switch the run leaves at its default actually moves the set,
#      so a list that silently matched a crippled deck would be caught.
#
# Needs `ruby` and an IHP SG13G2 PDK (PDK_ROOT or --pdk-root; default ~/share/pdk).
# The layout premise checks need a python with `klayout` (override LAYOUT_PY).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PDK_ROOT="${PDK_ROOT:-${HOME}/share/pdk}"
DECK="${PDK_ROOT}/ihp-sg13g2/libs.tech/klayout/tech/drc/ihp-sg13g2.drc"
GEN="${ROOT}/layout/drc/native_rule_categories.rb"
LIST="${ROOT}/layout/drc/native_rule_categories.txt"
PROV="${ROOT}/layout/drc/native_rule_categories.provenance.json"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
bad=0

if [ ! -f "${DECK}" ]; then
  echo "SKIP no IHP SG13G2 native deck at ${DECK} (set PDK_ROOT)"
  exit 0
fi
command -v ruby >/dev/null || { echo "SKIP no ruby on PATH"; exit 0; }

run_gen() { ruby "${GEN}" --deck "${DECK}" --pdk-root "${PDK_ROOT}" "$@"; }

# 1. regeneration reproduces the committed list
run_gen --out "${T}/regen.txt" >/dev/null 2>&1 || { echo "FAIL generator errored"; exit 1; }
if cmp -s "${T}/regen.txt" "${LIST}"; then
  echo "PASS regenerated list matches ${LIST#"${ROOT}"/} ($(wc -l < "${LIST}" | tr -d ' ') categories)"
else
  echo "FAIL regenerated list differs from the committed one"; diff "${LIST}" "${T}/regen.txt" | head -20; bad=$((bad+1))
fi

# 2. include-chain hashes still match the recorded provenance
python3 -I - "${PROV}" "${PDK_ROOT}" <<'PYEOF' || bad=$((bad+1))
import hashlib, json, sys
prov_path, pdk_root = sys.argv[1], sys.argv[2]
prov = json.load(open(prov_path))
drift = []
for entry in prov["include_chain"]:
    path = f"{pdk_root}/{entry['path']}"
    try:
        got = "sha256:" + hashlib.sha256(open(path, "rb").read()).hexdigest()
    except OSError as exc:
        drift.append(f"{entry['path']}: {exc}")
        continue
    if got != entry["content_hash"]:
        drift.append(f"{entry['path']}: {entry['content_hash']} -> {got}")
if drift:
    print("FAIL deck include chain drifted from the recorded provenance:")
    for line in drift:
        print("  " + line)
    sys.exit(1)
print(f"PASS all {len(prov['include_chain'])} deck files match their recorded sha256")
PYEOF

# 3. the declared set does not depend on chip area (en_tiles switches run mode only)
run_gen --chip-area 2000000 --out "${T}/tiled.txt" >/dev/null 2>&1
if cmp -s "${T}/tiled.txt" "${LIST}"; then
  echo "PASS declared set unchanged with chip area above the 1e6 um2 en_tiles threshold"
else
  echo "FAIL en_tiles changes the declared set"; diff "${LIST}" "${T}/tiled.txt" | head -20; bad=$((bad+1))
fi

# 4a. MIM.gR: undeclared at the derived area, declared above the recommended maximum
if grep -qx 'MIM.gR' "${LIST}"; then
  echo "FAIL MIM.gR is in the committed list but the derivation assumes it is not declared"; bad=$((bad+1))
fi
run_gen --region-area 200000 --out "${T}/mim.txt" >/dev/null 2>&1
if [ "$(comm -13 "${LIST}" "${T}/mim.txt" | tr -d ' \n')" = "MIM.gR" ]; then
  echo "PASS MIM.gR is declared only above the recommended total MIM area"
else
  echo "FAIL feeding a large MIM area did not add exactly MIM.gR"; comm -13 "${LIST}" "${T}/mim.txt" | head; bad=$((bad+1))
fi

# 4b. the layout premises behind 4a and Seal.l, measured rather than assumed
LAYOUT_PY="${LAYOUT_PY:-${ROOT}/.venv/bin/python}"
if [ -x "${LAYOUT_PY}" ] && "${LAYOUT_PY}" -c 'import klayout.db' 2>/dev/null; then
  "${LAYOUT_PY}" -I - "${ROOT}/layout/top.gds" "${LIST}" <<'PYEOF' || bad=$((bad+1))
import sys
import klayout.db as db
gds, list_path = sys.argv[1], sys.argv[2]
declared = {line.strip() for line in open(list_path) if line.strip()}
ly = db.Layout(); ly.read(gds); dbu = ly.dbu
def area_um2(layer, datatype):
    li = ly.find_layer(layer, datatype)
    if li is None:
        return 0.0
    r = db.Region(ly.top_cell().begin_shapes_rec(li)); r.merge()
    return r.area() * dbu * dbu
MIM_GR_MAX = 174800.0          # rule_decks/sg13g2_tech_default.json, Mim_gR
mim = area_um2(36, 0)          # mim_drw
seal = area_um2(39, 4)         # edgeseal_bound
fail = 0
if mim >= MIM_GR_MAX:
    print(f"FAIL total MIM area {mim:.1f} um2 reaches the MIM.gR maximum {MIM_GR_MAX} um2: "
          "the deck would declare MIM.gR and the committed list is stale")
    fail += 1
else:
    print(f"PASS total MIM area {mim:.1f} um2 is under the MIM.gR maximum {MIM_GR_MAX} um2")
if seal > 0.0 or "Seal.l" in declared:
    print(f"FAIL EdgeSeal boundary (39/4) area {seal:.1f} um2: the deck would declare Seal.l")
    fail += 1
else:
    print("PASS no EdgeSeal boundary (39/4) in the stream, so Seal.l stays undeclared")
sys.exit(1 if fail else 0)
PYEOF
else
  echo "SKIP layout premise checks (no python with klayout at ${LAYOUT_PY})"
fi

# 5. the geometry-gated rule files are not part of this deck's include chain
python3 -I - "${PROV}" <<'PYEOF' || bad=$((bad+1))
import json, sys
prov = json.load(open(sys.argv[1]))
paths = [e["path"] for e in prov["include_chain"]]
gated = [p for p in paths if p.endswith(("density.drc", "antenna.drc", "sg13g2_maximal.drc"))]
if gated:
    print(f"FAIL geometry-gated rule file(s) now in the include chain: {gated}")
    sys.exit(1)
print(f"PASS include chain ({len(paths)} files) carries no density/antenna/maximal rule file")
PYEOF

# 6. negative controls -- each switch must actually move the set
neg() {  # name, expected-direction, grep-pattern that must disappear, --set args...
  local name="$1"; local pattern="$2"; shift 2
  run_gen --out "${T}/neg.txt" "$@" >/dev/null 2>&1
  local before after
  before="$(wc -l < "${LIST}" | tr -d ' ')"
  after="$(wc -l < "${T}/neg.txt" | tr -d ' ')"
  if [ "${after}" -ge "${before}" ]; then
    echo "FAIL negative control ${name}: ${before} -> ${after} categories (expected fewer)"; bad=$((bad+1)); return
  fi
  if [ -n "${pattern}" ] && grep -qE "${pattern}" "${T}/neg.txt"; then
    echo "FAIL negative control ${name}: ${pattern} still declared"; bad=$((bad+1)); return
  fi
  echo "PASS negative control ${name}: ${before} -> ${after} categories"
}
neg "no_feol=true"      '^(NW|Act|Gat|Cnt|pSD|TGO)\.' --set no_feol=true
neg "no_beol=true"      '^(M1|M5|TM1|TV1|V1|MIM)\.'   --set no_beol=true
neg "no_pin=true"       '^Pin\.'                      --set no_pin=true
neg "no_forbidden=true" '^forbidden\.'                --set no_forbidden=true
neg "no_offgrid=true"   '_Offgrid$'                   --set no_offgrid=true
neg "no_angle=true"     '_(Acute|Angle45|Angle90)$'   --set no_angle=true
neg "precheck_drc=true" '^NW\.b$'                     --set precheck_drc=true
neg "tables=nwell only" '^(M1|Cnt|Act|Pin|forbidden)\.' \
    --set tables=nwell --set no_feol=true --set no_beol=true --set no_pin=true \
    --set no_forbidden=true --set no_offgrid=true --set no_angle=true

if [ "${bad}" = 0 ]; then echo "ALL PASS"; else echo "${bad} CHECK(S) FAILED"; fi
exit "${bad}"
