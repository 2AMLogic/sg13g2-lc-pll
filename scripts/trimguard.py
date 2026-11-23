"""Metal1 pad-trim guard (#245): gen_integrated.trim_pad must stay quiet on a pad whose via
survives the trim and must report a pad cut back past its own Via1, in both directions.

  python trimguard.py <root>

Foreign metal is placed NOT touching the pad, because metal that touches it is the pad's own
landing polygon and trim_pad excludes it by construction.
"""
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
