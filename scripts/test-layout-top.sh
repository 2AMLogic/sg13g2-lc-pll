#!/usr/bin/env bash
# Integrated layout check (#35): committed layout/top.gds reproduces, still matches the stream hash
# manifests/layout.attest.json pins (#257), holds the pinned VCO unmodified, keep-out intrusions are
# exactly the recorded VCTRL pin-access ones, and the checks can fail.
# Needs .fetched/ (scripts/fetch-vco.sh), klt, a python with `klayout` (default .venv/bin/python; LAYOUT_PY).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${LAYOUT_PY:-${ROOT}/.venv/bin/python}"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
# expect()/expect_summary and the pass/bad tally, including when `refuse:<ERE>` is required
# over a bare `refuse`: see the contract in scripts/lib-expect.sh.
# shellcheck source=lib-expect.sh
source "${ROOT}/scripts/lib-expect.sh"
VCO="${ROOT}/.fetched/sg13g2-vco/layout/vco.gds"; G="${ROOT}/layout/top.gds"
# layout/gen_top.py's refusal on a VCO stream whose sha256 differs from reuse.lock.json.
REFUSAL='gen_top: .* sha256 [0-9a-f]{64} != pinned [0-9a-f]{64}; refusing'

expect "fetched VCO files verify" ok "${ROOT}/scripts/fetch-vco.sh" --verify
expect "regenerated geometry == committed provenance" ok "${PY}" "${ROOT}/layout/gen_integrated.py" --check
klt clip "${G}" --cell vco -o "${T}/placed.gds" >/dev/null 2>&1
klt clip "${VCO}" --cell vco -o "${T}/pinned.gds" >/dev/null 2>&1
expect "placed VCO subtree == pinned stream" ok klt diff "${T}/placed.gds" "${T}/pinned.gds"
expect "committed stream sha256 == provenance" ok bash -c \
  "[ \"\$(sha256sum '${G}' | cut -d' ' -f1)\" = \"\$(jq -r .output.sha256 '${ROOT}/layout/provenance.json')\" ]"
expect "attestation envelope passes" ok jq -e '.status=="pass" and .t1_item==2' "${ROOT}/manifests/layout.attest.json"

# T1 item 2's envelope pins the stream BYTES, not the geometry digest, so a timestamp-only rewrite
# of layout/top.gds invalidates the attestation while --check keeps passing (#257). Compare the
# stream on disk against the hash the envelope pins -- the file is what is attested.
PIN="$(jq -r '.provenance.input.content_hash' "${ROOT}/manifests/layout.attest.json" | sed 's/^sha256://')"
pin_check() { local f="$1" h
  [ -n "${PIN}" ] && [ "${PIN}" != "null" ] || { echo "pin-check: manifests/layout.attest.json has no provenance.input.content_hash; refusing"; return 1; }
  h="$(sha256sum "${f}" | cut -d' ' -f1)"
  [ "${h}" = "${PIN}" ] || { echo "pin-check: ${f} sha256 ${h} != attested ${PIN}; refusing"; return 1; }
  echo "pin-check: ${f} matches the attested stream ${PIN}"; }
expect "committed stream == attestation pin" ok pin_check "${G}"
expect "attestation pin == provenance output.sha256" ok bash -c \
  "[ \"${PIN}\" = \"\$(jq -r .output.sha256 '${ROOT}/layout/provenance.json')\" ]"

# The churn this guards against is the GDS timestamp fields and nothing else, so the fixture for it
# is a byte-level edit of the seconds in every BGNLIB/BGNSTR record -- same size, same geometry,
# different sha256. Re-saving the stream through KLayout would NOT be an equivalent fixture: it also
# permutes the layer-index order, and layout/gen_integrated.py's digest() hashes layers in
# enumeration order, so a re-save moves the geometry digest too.
cat >"${T}/gds_restamp.py" <<'STAMPEOF'
"""Shift the seconds field of every GDS BGNLIB/BGNSTR timestamp: a byte churn with no geometry."""
import sys

src, dst = sys.argv[1], sys.argv[2]
data = bytearray(open(src, "rb").read())
i, n, hits = 0, len(data), 0
while i + 4 <= n:
    rlen = int.from_bytes(data[i:i + 2], "big")
    if rlen < 4:
        break
    # record type 0x01 = BGNLIB, 0x05 = BGNSTR; data type 0x02 = INT2; 12 int2 = mod/access y m d h m s
    if data[i + 3] == 0x02 and data[i + 2] in (0x01, 0x05) and rlen >= 28:
        for off in (i + 14, i + 26):            # the two seconds fields
            data[off:off + 2] = ((int.from_bytes(data[off:off + 2], "big") + 7) % 60).to_bytes(2, "big")
        hits += 1
    i += rlen
if hits == 0:
    sys.exit("gds-restamp: no BGNLIB/BGNSTR record found in " + src + "; refusing")
open(dst, "wb").write(bytes(data))
print("gds-restamp: re-stamped " + str(hits) + " records")
STAMPEOF
expect "timestamp-churn fixture builds" ok "${PY}" -I "${T}/gds_restamp.py" "${G}" "${T}/restamped.gds"

# --write must keep the attested bytes when the geometry is unchanged and replace them when it is
# not. Exercises layout/gen_integrated.py's publish_stream() on copies under ${T}; nothing in the
# checkout is written. Both halves carry a guard that fails if the fixture cannot discriminate.
cat >"${T}/pub_test.py" <<'PUBEOF'
import hashlib
import os
import shutil
import sys

sys.path.insert(0, os.path.join(sys.argv[1], "layout"))
import klayout.db as db
import gen_integrated as gi

committed, restamped, t = sys.argv[2], sys.argv[3], sys.argv[4]


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def dig(path):
    ly = db.Layout()
    ly.read(path)
    return gi.digest(ly, ly.cell(gi.TOP))


def fail(msg):
    sys.exit("publish-stream: " + msg + "; refusing")


# 1. timestamp churn only: the destination must keep its committed bytes
dest = os.path.join(t, "pub_dest.gds")
shutil.copyfile(committed, dest)
if sha(restamped) == sha(committed):
    fail("the re-stamped fixture is byte-identical, so this control cannot discriminate")
if dig(restamped) != dig(committed):
    fail("the re-stamped fixture moved the geometry digest, so it is not a timestamp-only churn")
if gi.publish_stream(restamped, dest, dig(restamped)) is not False:
    fail("replaced a stream whose geometry is unchanged")
if sha(dest) != sha(committed):
    fail("churned the bytes of a stream whose geometry is unchanged")

# 2. a real geometry change must be published. Both fixtures are KLayout saves, so they differ by
#    the inserted box alone -- not by the layer-order permutation a save also introduces.
plain = os.path.join(t, "pub_plain.gds")
ly = db.Layout()
ly.read(committed)
ly.write(plain)
edited = os.path.join(t, "pub_edited.gds")
ly = db.Layout()
ly.read(committed)
ly.cell(gi.TOP).shapes(ly.layer(8, 0)).insert(db.Box(-320000, 100000, -315000, 105000))
ly.write(edited)
if dig(edited) == dig(plain):
    fail("the inserted shape did not move the geometry digest, so this control cannot discriminate")
shutil.copyfile(plain, dest)
if gi.publish_stream(edited, dest, dig(edited)) is not True:
    fail("kept a stale stream after the geometry changed")
if dig(dest) != dig(edited):
    fail("the published stream does not carry the new geometry")

# 3. an absent destination is created
missing = os.path.join(t, "pub_missing.gds")
if gi.publish_stream(restamped, missing, dig(restamped)) is not True or not os.path.exists(missing):
    fail("did not create an absent destination")

print("publish-stream: timestamp churn kept the attested bytes, geometry change replaced them")
PUBEOF
expect "--write keeps attested bytes on churn, replaces them on a geometry change" ok \
  "${PY}" -I "${T}/pub_test.py" "${ROOT}" "${G}" "${T}/restamped.gds" "${T}"

# keep-out: the only intrusions are the VCTRL pin-access stack (3 shapes, Metal3/4/5), recorded in layout/README.md
"${PY}" "${ROOT}/layout/gen_top.py" --out "${T}/b.gds" --forbidden-json "${T}/f.json" >/dev/null 2>&1
klt keepout-check "${G}" --forbidden "${T}/f.json" --margin 20 --cells vco --format json >"${T}/ko.json" 2>/dev/null
n="$(jq '[.. | objects | select(has("kind"))] | length' "${T}/ko.json" 2>/dev/null)"
[ -n "${n}" ] && [ "${n}" = 3 ] && { echo "PASS keep-out: 3 recorded VCTRL intrusions"; pass=$((pass+1)); } \
  || { echo "FAIL keep-out intrusions = '${n}', expected the 3 recorded VCTRL ones"; bad=$((bad+1)); }

# negative controls
"${PY}" -I - "${G}" "${T}" <<'PYEOF'
import sys, klayout.db as db
g, t = sys.argv[1], sys.argv[2]
ly = db.Layout(); ly.read(g)
ly.cell("vco").shapes(ly.layer(8, 0)).insert(db.Box(0, 0, 1000, 1000)); ly.write(t + "/edited.gds")
ly = db.Layout(); ly.read(g)
ly.cell("lc_pll_top").shapes(ly.layer(8, 0)).insert(db.Box(-320000, 100000, -315000, 105000)); ly.write(t + "/intr.gds")
PYEOF
klt clip "${T}/edited.gds" --cell vco -o "${T}/edited_clip.gds" >/dev/null 2>&1
expect "NEG edited VCO cell detected" refuse klt diff "${T}/edited_clip.gds" "${T}/pinned.gds"
klt keepout-check "${T}/intr.gds" --forbidden "${T}/f.json" --margin 20 --cells vco --format json >"${T}/ko2.json" 2>/dev/null
n2="$(jq '[.. | objects | select(has("kind"))] | length' "${T}/ko2.json" 2>/dev/null)"
[ "${n2}" = 4 ] && { echo "PASS NEG extra keep-out intruder detected (4)"; pass=$((pass+1)); } || { echo "FAIL NEG intruder count '${n2}'"; bad=$((bad+1)); }
mkdir -p "${T}/s/.fetched/sg13g2-vco/layout"; cp "${VCO}" "${T}/s/.fetched/sg13g2-vco/layout/vco.gds"
printf 'X' | dd of="${T}/s/.fetched/sg13g2-vco/layout/vco.gds" bs=1 seek=100 conv=notrunc 2>/dev/null
# Must carry gen_top.py's own sha256 refusal (reached through gen_integrated's build_base
# subprocess), not merely exit non-zero: see the expect() note above.
expect "NEG tampered stream: generator refuses" "refuse:${REFUSAL}" \
  "${PY}" "${ROOT}/layout/gen_integrated.py" --vco "${T}/s/.fetched/sg13g2-vco/layout/vco.gds" --check
# Metal1 pad-trim guard (#245). Drives gen_integrated.trim_pad over synthetic Metal1 so the guard
# is exercised in BOTH directions: it must stay quiet on a pad whose via survives the trim, and must
# report a pad cut back past its own Via1. A check that cannot fail is not a check (same reasoning as
# the refuse:<ERE> note above). Foreign Metal1 is placed NOT touching the pad, because metal that
# touches it is the pad's own landing polygon and trim_pad excludes it by construction.
cat >"${T}/trimguard.py" <<'TRIMEOF'
import sys
sys.path.insert(0, sys.argv[1] + "/layout")
import klayout.db as db
import gen_integrated as g

dbu = 0.001
PAD, VIA, SP = g.PAD_UM[0], g.VIA_UM[0], g.M1B_SP_UM
pad = g.box(dbu, 0, 0, PAD, PAD)
edge = PAD / 2


def run(foreign_boxes, sp_um):
    base = db.Region(pad)
    for b in foreign_boxes:
        base.insert(b)
    base = base.merged()
    keep, trimmed, unc = g.trim_pad(dbu, pad, base, round(sp_um / dbu))
    return trimmed, not unc.is_empty()


# a 1 um square whose near edge sits `gap` outside the pad, on the +x side
def near(gap):
    return g.box(dbu, edge + gap + 0.5, 0, 1.0, 1.0)


# (name, foreign shapes, spacing um, expect_trimmed, expect_below_via)
cases = [
    ("no foreign metal",        [],                      SP,   False, False),
    ("foreign clear of M1.b",   [near(SP + 0.02)],       SP,   False, False),
    ("worst-case 1 nm gap",     [near(0.001)],           SP,   True,  False),
    ("foreign both sides",      [near(0.001),
                                 g.box(dbu, -(edge + 0.501), 0, 1.0, 1.0)], SP, True, False),
    # The guard must arm if the pad/via/spacing relationship ever regresses. At the shipped constants
    # the trim reaches edge-SP = %.3f um from centre, clear of the via's %.4f um half-width; widening
    # the spacing past %.3f um takes it past the via and MUST be reported.
    ("wider spacing cuts via",  [near(0.001)],           0.30, True,  True),
    ("wider spacing, 2 sides",  [near(0.001),
                                 g.box(dbu, -(edge + 0.501), 0, 1.0, 1.0)], 0.40, True, True),
]

print("  pad=%.2fum via=%.2fum M1.b=%.2fum -> trim reaches %.3fum from centre, via half-width %.4fum"
      % (PAD, VIA, SP, edge - SP, VIA / 2))
bad = 0
for name, foreign, sp_um, want_trim, want_below in cases:
    trimmed, below = run(foreign, sp_um)
    if (trimmed, below) != (want_trim, want_below):
        print("  FAIL %-24s sp=%.2f trimmed=%s below_via=%s, want %s/%s"
              % (name, sp_um, trimmed, below, want_trim, want_below))
        bad += 1
    else:
        print("  ok   %-24s sp=%.2f trimmed=%-5s below_via=%s" % (name, sp_um, trimmed, below))
sys.exit(1 if bad else 0)
TRIMEOF
expect "pad-trim guard discriminates" ok "${PY}" -I "${T}/trimguard.py" "${ROOT}"

# The committed layout must carry the trim record and have no pad cut below its via (#245).
expect "committed layout records the pad trim" ok jq -e \
  '.metal1_pad_trim | .pads_total >= 1 and .pads_trimmed_below_via == 0
   and (.below_via | length) == 0 and .via_cover_margin_um > 0' \
  "${ROOT}/layout/provenance.json"

# The churned stream keeps the geometry digest (so --check still passes) but breaks the attestation
# pin, which is the whole trap in #257: the pin check must refuse it, with its own refusal text.
expect "NEG timestamp-churned stream fails the attestation pin" \
  "refuse:pin-check: .* sha256 [0-9a-f]{64} != attested [0-9a-f]{64}; refusing" \
  pin_check "${T}/restamped.gds"
expect_summary || exit 1
