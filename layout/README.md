# layout

Layout scaffold for the LC PLL. `gen_top.py` builds `lc_pll_top`: the pinned `sg13g2-vco`
stream placed unmodified at the origin, plus an inductor keep-out marker, an outer
substrate guard ring and metal filler. Loop-block cells are drawn by `gen_cells.py` (below).

## Regenerate

```
scripts/fetch-vco.sh                                   # pinned VCO files, sha256-verified
uv venv .venv && uv pip install --python .venv/bin/python klayout==0.30.12
.venv/bin/python layout/gen_top.py                     # -> layout/build/lc_pll_top.gds (gitignored)
scripts/test-layout-vco.sh                             # byte-match + checks + negative controls
```

The generator refuses a VCO stream whose sha256 differs from `reuse.lock.json`.
`test-layout-vco.sh` is not in `scripts/ci-harness.sh` (needs the `klayout` module and the
fetch); run it locally.

## What is drawn (um, VCO bbox = `[-305.13,-106.03,305.13,290.26]`)

| Item | Where | Layers |
|---|---|---|
| keep-out | VCO bbox + 20 um; nothing forbidden drawn by the top cell inside; `NoMetFiller` marker covers it | 160/0 |
| guard ring | inner edge VCO bbox + 25 um, 1 um wide, one closed annulus | Activ 1/0, pSD 14/0, Cont 6/0, Metal1 8/0 |
| fill | 4 um squares, 8 um pitch, 40 um band outside the ring | Metal1-5 filler x/22 |

The inductor's own exclusion markers (27/0, x/23, 148/0) are part of the VCO cell and untouched.
Layer numbers: `$PDK_ROOT/ihp-sg13g2/libs.tech/klayout/tech/sg13g2.lyp` and `sg13g2.map`
(IHP-Open-PDK, the release pinned in `sim/pins.json`). The 20 um margin is a design choice
(the VCO's own inductor-to-core gap is 16 um), not a PDK number.

## G8 record (2026-11-03, `klt 0.8.1.dev1163+g340768ea5492`)

- `klt keepout-check --forbidden <Activ,GatPoly,Cont,pSD,Metal1-5,Metal1-5 filler> --margin 20 --cells vco`: clean, 0 violations.
- `klt ring-check --layers '[[1,0]]' --ignore-enclosed` on the ring window: continuous, 0 violations.
- Both fail on injected faults (see `scripts/test-layout-vco.sh`). `keepout-check` guards the
  VCO *bounding box* (it does not read the inductor markers), so it checks the margin around
  the whole VCO, not the spiral footprint alone. `klayout-tools#3849` is the tracker for G8;
  spec Q5 is not edited here.

## Not done / caveats

- The guard ring carries no net label or tie yet; top-level connectivity to `0` comes with the loop-block integration.
- Fill is a placeholder; density sign-off is DRC work (#36). No DRC/LVS/PEX was run here.

## Loop-block cells (#58)

```
.venv/bin/python layout/gen_cells.py --write           # -> layout/build/cells/*.gds + layout/cells.provenance.json
scripts/test-layout-cells.sh                           # regenerate, compare with provenance, pin-vs-port check
```

One generator per block in `layout/cells/` (`prescaler`, `divider`, `charge_pump`, `loop_filter`, `pfd`,
`lock_detector`) on shared `cells/common.py`: flatten the `.subckt`, group identical (class, W, L) devices
(`m=` expanded to units), draw each group with `klt gen mos_array|res_array|cap_array`, place groups with
`klt gen-compose` (placement only; routing is #35), and put one text label per `.subckt` port on a drawn
terminal of that net. `layout/cells.provenance.json` holds the cell list, area (bbox), generator command, klt
version, netlist sha256 and a geometry digest; `gen_cells.py --check` fails on any difference.

**PFD / lock detector: adopted by method, not by stream.** `sg13g2-pll@e71ff61` has no PFD- or
lock-detector-specific layout, only `layout/bin/pll_layout.py`, a generic netlist-to-`klt gen` planner for
its own ring-oscillator netlists. Its method is reused here (attributed in `cells/common.py`) on this repo's
`pfd` and `lock_detector` subckts, whose netlists are the pinned inputs (`reuse.lock.json`). No upstream
layout file exists to hash-pin.

**Pin check.** `klt interface-check` pairs the labels of two placed blocks, so it cannot compare one cell to
its `.subckt`; `scripts/test-layout-cells.sh` compares label set to port list instead, with drop/rename
negative controls. It is not in `scripts/ci-harness.sh` (needs `klayout`, a PDK and klt).

**Not met (tool gaps, recorded per device in the provenance as `undrawn_devices`):**
- `lcpll_prescaler` is not drawn: all 145 devices are SiGe HBTs (95) and ideal resistors (50). No `klt gen`
  generator draws an `sg13g2` HBT (klayout-tools#4850); ideal `R` cards carry only ohms, and choosing a
  physical rppd/rhigh W/L is a schematic decision. The 2.1 fF input-geometry budget is therefore unaddressed;
  `INPUT_FIRST` in `cells/prescaler.py` only orders the input group first for when the cell can be drawn.
- `lcpll_divider` omits 1 HBT (cml2cmos tail) and 5 ideal resistors; port `IREF` is unlabelled (it reaches only the HBT).
- `lcpll_lockdet` omits the `w=0.25u l=12u` pull-down (`mos_array` W floor, klayout-tools#4851).
- Cells are placement only: no routing, no tap/guard ties, no DRC/LVS (#36, #37). Areas are bounding boxes.
  The loop-filter cell is 131458 um2 because the schematic's `cap_cmim` units (12 x 70.9 um square) are drawn as specified.
