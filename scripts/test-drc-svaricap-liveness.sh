#!/usr/bin/env bash
# The curated `nwell.enclosing.pactiv.1` verdict on layout/top.gds is live, and is clean
# because the PDK varactor is carved out by its own text marker -- not because the rule
# went silent (#36). IHP's NW.c drops P+ Activ interacting with a text-recognised
# SVaricap; klt models that from klayout-tools#5442, which is what turned the 64
# VCO-stream findings into zero. A deck change that silenced the rule outright would look
# identical in the report, so the discriminating check is the negative control below:
# delete the two SVaricap labels from a scratch copy of the stream and the same 64
# findings must come back.
#
#   scripts/test-drc-svaricap-liveness.sh
#
# Needs klt carrying the carve-out (klayout-tools#5442; `klt drc --list-rules` leg below
# fails loudly on an older klt) and a python with the `klayout` module (default
# .venv/bin/python, override with LAYOUT_PY). No PDK and no native deck: the curated deck
# ships inside klt, so this does not run in .github/workflows/harness.yml, which installs
# the 0.8.0 signoff pin and no PDK. Run it locally, like scripts/test-layout-top.sh.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${LAYOUT_PY:-${ROOT}/.venv/bin/python}"
G="${ROOT}/layout/top.gds"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
pass=0; bad=0
ok()   { echo "PASS $1"; pass=$((pass+1)); }
fail() { echo "FAIL $1"; bad=$((bad+1)); }

# The two labels the recogniser reads (one per varactor bank in the pinned VCO stream).
EXPECT_LABELS=2
# What the rule reports on this stream when the recogniser cannot see those labels.
EXPECT_FINDINGS=64
RULE="nwell.enclosing.pactiv.1"

# 1. The deck discloses the carve-out in the rule's own description, so a reader of the
#    clean report can see which geometry it does not measure (klt's listing, not prose).
desc="$(klt drc --list-rules --deck sg13g2 --format json 2>/dev/null \
        | jq -r --arg r "${RULE}" '.rules[] | select(.id==$r) | .description')"
case "${desc}" in
  *SVaricap*) ok "deck discloses the SVaricap carve-out on ${RULE}" ;;
  "")         fail "${RULE} not found in the sg13g2 listing (klt too old, or no jq?)" ;;
  *)          fail "${RULE} description does not mention SVaricap: ${desc}" ;;
esac

# 2. The committed stream is clean on the curated deck.
klt drc "${G}" --deck sg13g2 --engine curated --format json >"${T}/as-built.json" 2>/dev/null
st="$(jq -r '.status' "${T}/as-built.json" 2>/dev/null)"
n="$(jq -r '.violation_count' "${T}/as-built.json" 2>/dev/null)"
if [ "${st}" = "clean" ] && [ "${n}" = "0" ]; then
  ok "as-built curated DRC: status clean, 0 violations"
else
  fail "as-built curated DRC: status '${st}', ${n} violations (expected clean/0)"
  jq -r '.rule_counts // {} | to_entries[] | "    \(.key): \(.value)"' "${T}/as-built.json" 2>/dev/null
fi

# 3. Negative control. Delete every SVaricap text on TEXT_0 (63/0) from a scratch copy --
#    geometry untouched, labels gone -- and the carve-out must stop applying.
"${PY}" -I - "${G}" "${T}/stripped.gds" >/dev/null <<'PYEOF'
import sys

import klayout.db as db

src, dst = sys.argv[1], sys.argv[2]
ly = db.Layout()
ly.read(src)
idx = ly.layer(63, 0)
removed = 0
for cell in ly.each_cell():
    shapes = cell.shapes(idx)
    keep, drop = [], 0
    for sh in shapes.each():
        if sh.is_text() and sh.text_string == "SVaricap":
            drop += 1
        else:
            keep.append(sh.dup())
    if drop:
        shapes.clear()
        for sh in keep:
            shapes.insert(sh)
        removed += drop
ly.write(dst)
PYEOF
rc=$?
labels="$("${PY}" -I -c '
import sys
import klayout.db as db
ly = db.Layout(); ly.read(sys.argv[1])
idx = ly.layer(63, 0)
print(sum(1 for c in ly.each_cell() for s in c.shapes(idx).each()
          if s.is_text() and s.text_string == "SVaricap"))
' "${G}" 2>/dev/null)"
if [ "${rc}" = 0 ] && [ "${labels}" = "${EXPECT_LABELS}" ]; then
  ok "stream carries the ${EXPECT_LABELS} recorded SVaricap labels on 63/0"
else
  fail "SVaricap labels on 63/0 = '${labels}', expected ${EXPECT_LABELS} (strip rc=${rc})"
fi

if [ -s "${T}/stripped.gds" ]; then
  klt drc "${T}/stripped.gds" --deck sg13g2 --engine curated --format json \
      >"${T}/stripped.json" 2>/dev/null
  st="$(jq -r '.status' "${T}/stripped.json" 2>/dev/null)"
  n="$(jq -r --arg r "${RULE}" '.rule_counts[$r] // 0' "${T}/stripped.json" 2>/dev/null)"
  other="$(jq -r --arg r "${RULE}" '.rule_counts // {} | del(.[$r]) | keys | join(",")' \
           "${T}/stripped.json" 2>/dev/null)"
  if [ "${st}" = "violations" ] && [ "${n}" = "${EXPECT_FINDINGS}" ] && [ -z "${other}" ]; then
    ok "NEG labels removed: ${RULE} reports the ${EXPECT_FINDINGS} findings again, and nothing else"
  else
    fail "NEG labels removed: status '${st}', ${RULE} ${n} (expected ${EXPECT_FINDINGS}), other rules '${other}'"
  fi
else
  fail "NEG labels removed: no stripped stream was written"
fi

echo
echo "${pass} passed, ${bad} failed"
[ "${bad}" = 0 ] || exit 1
