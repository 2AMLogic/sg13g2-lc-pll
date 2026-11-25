# Tank-node floorplan record, 2026-11-20 (#345)

Candidate floorplans for the tank routes VOP/VON (vco `OUTP`/`OUTN` -> prescaler `INP`/`INN`),
tried to find the floor that the pinned VCO's pin positions and the 20 um keep-out impose, and
the shortfall that remains against the 2.1 fF tank-node load budget (spec section 1, I6; DR-001).
Geometric estimate only, method unchanged from `layout/provenance.json` `tank_node_estimate`
(isolated 2 um TopMetal1 wire over substrate, 0.0861 fF/um displayed, magic `extract.tech`
area+perimeter caps); extraction is #41. Everything below was measured with the committed
generators and router (`gen_cells.py`, `gen_integrated.py`), not estimated by hand.

## The geometry that bounds every candidate

With the VCO stream pinned at `17e49a8` (`reuse.lock.json`; verified unchanged for these pins on
upstream `main` as of `e6b0670c`, 2026-11-20 - the only `layout/vco.gds` change since the pin is
`54b72f8c`, the #314 VCTRL edge pin):

- `vco.OUTP` label at (-120.0, -24.0), `vco.OUTN` at (120.0, -32.0), both on TopMetal1 (126/25),
  on the core tank metal whose southern edge is y = -33/-34. The pins are 240 um apart and
  74-82 um inside the bbox bottom edge (-106.03).
- The keep-out (bbox + 20 um, `klt keepout-check --margin 20`) forbids Activ, GatPoly, Cont,
  pSD and Metal1-5 below y = -126.03. TopMetal1 routing is *not* forbidden, so the tank routes
  may cross the keep-out; the prescaler's Metal1-5 input stack may not.
- The guard ring (`gen_top.py`, RING_GAP_UM 5 + RING_W_UM 1 outside the keep-out, pSD sized out
  for Activ enclosure) reaches y = -132.33. With `psd.space.1` = 0.31 um, the closest a clean
  placement holds the cell is y = -133.0 (0.67 um pSD-to-pSD), putting the INP/INN pin stacks
  at y = -134.775 (pin labels 1.775 um below the cell's top edge).

So the straight TopMetal1 run from each pin to the keep-out edge is 102.03 um (OUTP) and
94.03 um (OUTN) - 8.78 / 8.10 fF by the recorded estimate - and to a legal input stack
(clear of the ring) 110.775 / 102.775 um. **That is the floor for any placement of this pinned
stream.** The prescaler cell is 446 um wide with the input pair 9.74 um apart at the cell edge,
so the pair can sit under at most one pin; both pins each need the pair split.

## Candidates tried

All runs: `.venv/bin/python layout/gen_integrated.py --prescaler-origin "<transform>,<x>,<y>"`
(evaluation mode added for this record; regenerates `layout/build/top.gds` and prints routes,
estimate, collisions, commits nothing), then `klt keepout-check layout/build/top.gds
--forbidden <gen_top --forbidden-json> --margin 20 --cells vco`. The estimate method is the
committed one, so the rows compare with the pre-#345 record. "Diff" is the differential
capacitance of the route pair, (C_VOP + C_VON)/2 - the mean, i.e. the capacitance a
differential drive sees (Y_diff = jw(C1+C2)/2); the device-level input capacitance 1.837 fF
(DR-005, already differential) adds to it.

| Candidate | Placement (M0, x, y) | VOP um / fF | VON um / fF | Diff route fF | +1.837 fF | keep-out | collisions |
|---|---|---|---|---|---|---|---|
| committed (pre-#345, `main` `334c3b1`) | (281.0, -185.0) | 850.105 / 73.16 | 611.845 / 52.66 | 62.91 | 64.75 | 3 (VCTRL) | 8 |
| A: pair centred between the pins | (-291.2, -132.5) | 225.405 / 19.40 | 217.405 / 18.71 | 19.06 | 20.90 | 3 (VCTRL) | 8 |
| B: pair under OUTP | (-406.33, -132.5) | 110.275 / 9.49 | 332.535 / 28.62 | 19.06 | 20.90 | 3 (VCTRL) | 8 |
| C: pair split, one device per pin, first try | (-123.87, -132.5) | 110.275 / 9.49 | 102.275 / 8.80 | 9.15 | 10.99 | 3 (VCTRL) | 8 |
| **C adopted: as above, y moved to -133.0** | **(-123.87, -133.0)** | **110.775 / 9.53** | **102.775 / 8.85** | **9.19** | **11.03** | **3 (VCTRL)** | **8** |

Notes on the rows:

- All five rows were re-measured against post-#344 `main` (`334c3b1`, baseline stream
  `sha256:60ad1ed0…`): A and B with the pre-split prescaler cell (`origin/main:layout/cells/prescaler.py`),
  C first try and C adopted with the split prescaler cell.
- A and B have the same differential figure (19.06 fF): the pin pair is colinear with the
  prescaler edge, so Manhattan length is conserved between them - only the split (C) moves the
  differential figure the budget is graded in. A leaves the pair matched within 8 um; B loads
  VON 3x heavier than VOP.
- Candidate C splits the two input devices (the `XCK` emitter followers of `cml_div23`, bases on
  INP/INN) into singleton `bjt_array`s 240 um apart (`layout/cells/prescaler.py`
  `INPUT_PAIR_SPAN_UM`), one under each pin, with the 127 remaining npn13G2v units keeping the
  3x43 array shape refilled by 2 portless dummy devices. The first try at y = -132.5 failed DRC
  (`psd.space.1`: ring pSD to cell pSD 0.17 um < 0.31); y = -133.0 is the closest clean
  placement and is what is committed.
- No candidate adds keep-out violations: every row reports exactly the 3 recorded VCTRL
  pin-access ones (Metal3/4/5 at the VCO's Metal3-only VCTRL pin), and `collisions_total` stays
  8 (FB 1, REF 2, VCP 2, VCTRL 2, VSS 1 — unchanged by the move, matching pre-#345 `main` after
  #344's same-net exclusion; zero collisions on VOP/VON).

## What is committed

`layout/top.gds` sha256 `c897060cf0ca5b10bbcce8d976563a13d6c20f251b102bfcc8268eace0144e7d`
(geometry digest and placements in `layout/provenance.json`): prescaler at M0 (-123.87, -133.0),
input pair split under the pins, VOP 110.775 um / VON 102.775 um of straight TopMetal1.

Two generator changes came with the move, both DRC-driven:

- The cell now sits inside `gen_top.py`'s placeholder fill band (bbox+31..bbox+71), where the
  old placement (top edge y = -185) was clear of it. Native `M1Fil.c`/`M2Fil.c` (filler space
  to metal 0.42 um) fired on 111 filler squares under the cell, so `gen_integrated.py`'s filler
  removal now clears squares near *any* placed geometry on the matching metal layer, not only
  near routes (583 squares removed with #344 supply routes included; the VCO and ring still
  remove none - the band starts 5 um outside the ring, beyond the 2 um removal sizing).
- Filler marker squares (x/22 datatypes) remain under the cell where real metal keeps 2 um
  clearance; density sign-off is still #36.

## The remaining shortfall, stated plainly

Adopted floorplan: route estimate 9.53 fF (VOP) + 8.85 fF (VON), difference 0.68 fF,
**differential route 9.19 fF; with the 1.837 fF device-level input load, 11.03 fF against the
2.1 fF budget - a shortfall of 8.93 fF (5.2x)**. Not met, and not meetable by any placement of
this pinned stream: the floor above (8.78/8.10 fF to the keep-out edge alone) already exceeds
the 0.263 fF routing allowance the budget leaves after the device load (3.06 um of route).

What would have to change, in order:

1. **Expose OUTP/OUTN as top-metal pins at the bbox edge** - requested as
   2AMLogic/sg13g2-vco#420 (same shape of request as #314, whose VCTRL fix `54b72f8c` is on
   upstream `main` but not in the pinned `17e49a8`; a lock bump also clears this repo's 3
   recorded VCTRL keep-out violations, see #279). Residual estimate at the 20 um margin with
   that pin bump and this split floorplan: each route ~29 um (20 um margin + ~8.8 um ring
   clearance to the input stack) = ~2.5 fF per side, differential route ~2.5 fF, total
   ~4.3 fF - closer, still over.
2. **The margin itself bounds any route**: crossing the 20 um keep-out is already 20 um =
   1.72 fF per side by the recorded estimate, so even pins at the bbox edge with the input
   stack hard against the keep-out edge leave 1.72 + 1.837 = 3.56 fF > 2.1 fF. **No route that
   crosses the 20 um margin meets the budget.** Closing it needs the buffer of spec section 6
   Q1 (or a spec decision on the margin/budget) - that goes through `spec/` with a decision
   record, not through layout work; this issue does not edit `spec/`.

## Caveats carried by the adopted floorplan

- The input follower pair is split 240 um apart: Vbe gradient between the two clock followers
  now sets CKP/CKN balance, and the CKP/CKN intra-cell routing (#35; cells are placement-only)
  spans the split. If review prefers the pair intact, candidate A's placement is a one-line
  change (`PLACE` in `layout/gen_integrated.py`) at the recorded cost (19.06 fF differential).
- The 2 dummy HBTs are real geometry with no nets; LVS (#37) must exclude them.
- The estimate excludes sidewall coupling, via-stack pads and the prescaler's own input
  capacitance; PEX delta is #41.

## Reproduce

```
scripts/fetch-vco.sh
uv venv .venv && uv pip install --python .venv/bin/python klayout==0.30.12
.venv/bin/python layout/gen_cells.py --write
.venv/bin/python layout/gen_integrated.py --write        # commits the adopted floorplan
.venv/bin/python layout/gen_integrated.py --prescaler-origin "M0,-291.2,-132.5"    # candidate A
.venv/bin/python layout/gen_integrated.py --prescaler-origin "M0,-406.33,-132.5"   # candidate B
.venv/bin/python layout/gen_integrated.py --prescaler-origin "M0,-123.87,-132.5"   # candidate C first try
.venv/bin/python layout/gen_top.py --out /tmp/b.gds --forbidden-json /tmp/f.json
klt keepout-check layout/build/top.gds --forbidden /tmp/f.json --margin 20 --cells vco --format json
```

Candidates A and B were measured against the pre-split cell (the pair intact, 9.74 um apart);
re-running them today routes them to the split cell's INP/INN unless `layout/cells/prescaler.py`
is reverted to the unsplit build first. Re-run 2026-11-23 against post-#344 `main` (`334c3b1`),
klt 0.9.3.dev3808+g1ad4a837f657, klayout 0.30.12 (both Python module and standalone binary),
PDK ihp-sg13g2 fetched:0.3.0.
