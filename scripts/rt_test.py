"""digest() must survive a KLayout re-save of the committed stream (#263).

  python rt_test.py <root> <committed.gds> <tmpdir> [--enumeration-order]

--enumeration-order re-runs the assertion against digest() as it was before #263 (per-layer
records hashed in ly.layer_indexes() order). It must then refuse: that is the negative control
for the ordering fix itself, so a future change that reinstates enumeration order is caught.

scripts/layout_rt.py compares both streams and the recorded digest for this harness and
scripts/test-layout-cells.sh (#379).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(sys.argv[1], "layout"))
sys.path.insert(0, os.path.join(sys.argv[1], "scripts"))
import klayout.db as db
import gen_integrated as gi
import cells.common as cc
import layout_rt as rt

root, committed, t = sys.argv[1], sys.argv[2], sys.argv[3]
enum_order = "--enumeration-order" in sys.argv[4:]


def fail(msg):
    sys.exit("round-trip: " + msg + "; refusing")


fn = rt.enum_digest if enum_order else cc.digest

want = json.load(open(os.path.join(root, "layout/provenance.json")))["output"]["geometry_sha256"]
trip = rt.RoundTrip(committed, os.path.join(t, "rt.gds"), gi.TOP, want)
result = trip.compare(fn)

if not result.order_changed:
    fail("the round trip did not permute the layer-index order, so this case cannot discriminate")
# --enumeration-order must report the writer-dependent hash before a provenance mismatch.
if not result.digest_survived:
    fail(f"the round-tripped stream digests to {result.resaved_digest}, not the committed stream's {result.original_digest}")
if not result.matches_record:
    fail(f"the committed stream digests to {result.original_digest}, not the recorded {want}")

# Negative control in the same run: a real geometry change must still move the digest, or the
# assertions above would hold for a digest() that hashes nothing.
edited = os.path.join(t, "rt_edited.gds")
ly = rt.read(committed)
ly.cell(gi.TOP).shapes(ly.layer(8, 0)).insert(db.Box(-320000, 100000, -315000, 105000))
ly.write(edited)
if rt.digest_of(edited, gi.TOP, fn) == want:
    fail("an inserted shape did not move the digest, so it is not hashing the geometry")

print("round-trip: digest " + want + " survives a KLayout re-save; an inserted shape moves it")
