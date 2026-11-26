"""--write must keep the attested bytes when the geometry is unchanged and replace them when
it is not: layout/gen_integrated.py's publish_stream() under test.

  python pub_test.py <root> <committed.gds> <restamped.gds> <tmpdir>

Exercises publish_stream() on copies under <tmpdir>; nothing in the checkout is written. Both
halves carry a guard that fails if the fixture cannot discriminate.
"""
import hashlib
import os
import shutil
import sys

sys.path.insert(0, os.path.join(sys.argv[1], "layout"))
import klayout.db as db
import gen_integrated as gi
import cells.common as cc

committed, restamped, t = sys.argv[2], sys.argv[3], sys.argv[4]


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def dig(path):
    ly = db.Layout()
    ly.read(path)
    return cc.digest(ly, ly.cell(gi.TOP))


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
#    the inserted box alone; since #263 a save does not move the digest either way.
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
