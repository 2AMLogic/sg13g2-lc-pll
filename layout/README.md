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

One table row per block in `layout/gen_cells.py` (`divider`, `charge_pump`, `loop_filter`, `pfd`,
`lock_detector`: cell name, `.subckt`, netlist file), plus `layout/cells/prescaler.py` (its tank-loading input group
is placed first), on shared `cells/common.py`: flatten the `.subckt`, group identical (class, W, L) devices
(`m=` expanded to units), draw each group with `klt gen mos_array|res_array|cap_array|bjt_array`, place groups with
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

**Tool pin.** The HBT (`bjt_array`, klayout-tools#4850 -> #4855) and sub-0.42 um MOS (`dogbone_terminals`,
#4851 -> #4854) fixes are in the installed klt used for the committed provenance (`klt 0.9.2.dev420+gf186e14125ed`;
the provenance records the klt version). An older klt refuses the HBT groups and the generator fails; use
`uvx --from git+https://github.com/2AMLogic/klayout-tools@f94eaa6c00f267e3b58031e6ddaeab0507d2cd9d klt` via `KLT_CMD`
(a throwaway env). `npn13G2v Nx=<n>` is drawn as n unit PDK HBT cells (an approximation of the multi-emitter device).

**Devices drawn (2026-11-10).** Every device of the six blocks is drawn (0 `undrawn_devices`) and every `.subckt`
port is labelled (`scripts/test-layout-cells.sh`: no KNOWN-GAP). The ideal `R` cards were replaced by `rppd`/`rhigh`
in the netlists (#164, PR #169), so the resistors are drawn with `klt gen res_array` at the netlist W/L
(prescaler 208 units, divider 621, in total with HBTs, MOS and caps).

**Not met:**
- The prescaler's INP/INN tank-load capacitance is NOT extracted: the 2.1 fF budget is unverified until PEX on
  the integrated loop (#41). The input group is placed first to keep its geometry compact; that is not a measurement.
- Cells are placement only: no routing, no tap/guard ties, no DRC/LVS (#36, #37). Areas are bounding boxes.
  The loop-filter cell is 131458 um2 because the schematic's `cap_cmim` units (12 x 70.9 um square) are drawn as specified.

## Integrated top (#35)

```
.venv/bin/python layout/gen_integrated.py --write      # -> layout/top.gds + layout/provenance.json
scripts/test-layout-top.sh                             # reproducibility, VCO byte-match, keep-out record, negatives
```

`gen_integrated.py` runs `gen_top.py` (VCO + keep-out + ring + fill), places the six `gen_cells.py` cells below the VCO,
routes the inter-block signal nets and writes `layout/top.gds`. `layout/provenance.json` holds the generator chain, input
hashes (VCO stream, cells provenance, generators), the output sha256 and geometry digest, placements, per-net route
paths and lengths, collisions and the tank-node estimate. GDS bytes carry writer state, so reproducibility is checked on
the geometry digest (`--check`), not the file hash. T1 item 2 is cited by `manifests/layout.attest.json`
(`klt signoff --attest 2 --input layout/top.gds`), which pins the stream sha256.

**Routing (placement-level, not signoff; DRC/LVS/PEX are #36/#37/#41).** Tank nets VOP/VON on TopMetal1 (2 um);
other nets Metal5 horizontal / Metal4 vertical (1 um) with via stacks at each pin. Every route polygon is checked against
foreign geometry on its layer. Not routed: VDD, VDDV, VSS, REF, IREFCP, LOCK, divider M0-M3/A0-A2 tie-offs (supplies: #38).

**Results to read before relying on this layout**
- **Tank-node budget is not met by this floorplan.** Geometric estimate (method in `provenance.json`
  `tank_node_estimate`: isolated TopMetal1 wire over substrate, magic `extract.tech` area/perimeter caps, no coupling, not
  extracted): VOP 850 um = 73 fF, VON 612 um = 53 fF, against the 2.1 fF budget (spec §1, I6). Even the direct distance is far
  above it at 0.086 fF/um, so the budget needs the prescaler input at the tank pins (tens of um), not a route. The floorplan
  was not optimised; PEX delta is #41. Treat I6 as open; the spec is not edited here.
- **Keep-out is violated by exactly one net.** `klt keepout-check` (Metal1-5, margin 20) reports 3 violations, all the VCTRL
  pin-access stack (Metal3/4/5 at the VCO's Metal3-only VCTRL pin, about 57 um inside the bbox). Tank routes are on TopMetal1,
  outside the forbidden set. VCO change requested: sg13g2-vco#314; tool gap: klayout-tools#5198.
- **Route collisions:** `provenance.json` `collisions_total` = 13 overlapping polygons with foreign geometry (nets UP, DN to the
  lock detector and FB at the PFD pin stack). Each is listed per net; none is silently accepted. Cell M4/M5 internals are
  not net-aware here, so some overlaps may be same-net; LVS (#37) decides.
- Placeholder fill under routes is removed (5 squares); density sign-off is #36.
- CI pin: `.github/workflows/signoff.yml` stays at `klayout-tools==0.8.0`, which grades item 2 `met` from the attest envelope.
  Moving the pin to 0.9.1 grades item 1 `stale_evidence` (3 met -> 1), so the bump is left out.

## DRC of the integrated top (#36, T1 item 3) — NOT clean

```
klt drc layout/drc/request.json --format json > layout/drc/top.drc.json   # exit 3 = violations
klt drc --check layout/drc/top.drc.json                                   # re-hash: match
```

Run 2026-11-10, `klt 0.9.2.dev422+g1560fe3aac8d`, klayout 0.30.13 (the build was tested on 0.30.12; klt warns that counts may differ), curated deck `sg13g2`
content hash `sha256:1c95db40596afc5412e216009bcf0b775d1d74895b32738447eccbc76336dd15`, input `layout/top.gds`
(`sha256:b05b0bcb…`, the geometry attested for item 2; re-run 2026-11-10 after the #187 prescaler regeneration, was 747 violations on `b04df5f5…`). Result: **`status: violations`, 783 violations, 12 rules**. Item 3 stays `unmet`
(`check_failed`, `drc__error__count` 783). No waiver was added and no stream was edited. Superseded by the divider placement fix (#202, below): 79 violations on `4a7f8645…`.

Where they sit (`source_path` of each violation):

| Source | Count | Rules |
|---|---|---|
| prescaler `hbt_npn13g2v` (+ divider HBT 2) | 520 `npn13G2V` + others; ~576 under `lcpll_prescaler` | activ/cont/gatpoly/metal1 space and enclosure, nwell.enclosing.pactiv.hv |
| divider pfet/nfet/top, cp nfet, prescaler resistors | ~150 | gatpoly/metal1 width and space, activ.space, cont.space, nwell.enclosing.pactiv.hv |
| **VCO** `BANKP`/`BANKN` varactor banks | 64 (32 `SVaricap` + 32) | `nwell.enclosing.pactiv.1` (32 + 32) |

The 64 VCO findings are in the stream placed unmodified from `sg13g2-vco@17e49a8` and are not waived or edited here; they are reported as sg13g2-vco#315.
Whether the loop-cell findings are real or the curated deck's unconditional approximation of device-internal carve-outs (the HBT and
varactor PCells are foundry-drawn) is not established by this run; `--engine both` against the PDK-native deck was run later (see "Native cross-check"): the findings are real.

**Coverage (verbatim from the report):** `coverage.rules_skipped` = `[]`. `coverage.deck_scope` = `['Act','Cnt','Gat','M1','M2','M3','M4','M5','MIM','NW','TM1','TM2','TV1','TV2','V1','V2','V3','V4','pSD']`.
`coverage.layers_in_stream_without_rules` is **non-empty** (41 layers: 1/23, 5/23, 8/2, 8/22, 8/23, 8/25, 10/2, 10/22, 10/23, 10/25, 26/0, 27/0, 27/2, 27/25, 28/0, 30/22, 30/23, 30/25, 32/0, 40/0, 44/0, 46/21, 50/22, 50/23, 51/0, 52/0, 63/0, 67/22, 67/23, 67/25, 111/0, 126/2, 126/23, 126/25, 128/0, 129/0, 134/23, 134/25, 148/0, 156/0, 160/0), so even a clean result would be clean for covered layers only.

**G8 keep-out** (`klt keepout-check`, margin 20 um, `--cells vco`, forbidden Activ/GatPoly/Cont/pSD/Metal1-5 and their fill): `status: violated`, 3 violations, all the VCTRL
pin-access stack already recorded under "Integrated top (#35)" (tracked at sg13g2-vco#314). Not clean.

### Native cross-check (2026-11-10, `--engine both`)

```
klt drc layout/top.gds --deck sg13g2 --engine both --pdk sg13g2 --pdk-root /home/ubuntu/share/pdk --format json -o layout/drc/top.crosscheck.json   # exit 3
```

`klt 0.9.2.dev457+g5cd6aad7c733`, klayout 0.30.13 (klt warns the build was tested on 0.30.12), PDK `ihp-sg13g2` `fetched:0.3.0`
(host PDK at `~/share/pdk`, not installed or changed by this work), input `sha256:b05b0bcb…`. Curated deck hash
`sha256:0c0014b1…` (the installed klt's deck changed since the earlier run, so `layout/drc/top.drc.json` was re-run and re-stamped:
same 783 violations, `klt drc --check` = match). Native deck `ihp-sg13g2.drc` `sha256:0620b737…`, run with no `--deck-var`
(klt warns the deck's `-rd` globals were not supplied, so gated rule groups may not have run; native coverage is `known: false`).

- **Native engine: `status: violations`, 1798 violations**, 16 rules checked: Cnt.g1 475, Cnt.g2 489, Cnt.c 127, M1.b 288, LU.b 87,
  Act.b 85, Cnt.b 82, M1.a 36, Gat.b 32, Gat.d 29, Cnt.d 23, Gat.a 16, Cnt.e 13, M1.e 10, CntB.h1 5, pSD.c1 1.
  `layers_in_stream_without_rules` is empty for the native deck, but `coverage.unknown` holds `unmeasured_rule_execution`.
- **The loop-cell findings are real, not a curated-deck approximation.** The native deck also flags them. Largest sources: the
  `lcpll_divider_pfet_w5_l0p5` cell (Cnt.g1/g2/c, Act.b, M1.b: about 1250), the prescaler HBT (`npn13G2V`: Act.b, Cnt.b, Cnt.d, M1.b: about 210),
  prescaler `rppd` resistors, and `LU.b` (max N+Activ-to-tap space 20 um) across the nfet cells of the charge pump, PFD and lock detector,
  which have no tap ties yet (see "Not done"). Top-level: M1.a 36, Gat.a 16, M1.e 10, CntB.h1 5.
- **VCO stream:** the native deck reports nothing under the VCO cell. The 64 curated `nwell.enclosing.pactiv.1` hits on `SVaricap` are the
  curated deck's missing carve-out (sg13g2-vco#315), consistent with the closed ruling; not waived, not edited.
- **Comparison:** klt reports `comparison.state: not_comparable` (no rule-id mapping between the curated and native decks), so there is
  no region-level agreement figure.
- Item 3 stays `unmet`. No waiver, deck edit or stream edit was made. The fix is a `layout/gen_cells.py` change (pfet w5 cell first,
  then HBT contact/metal spacing, then tap ties for LU.b) and belongs to a follow-up issue.

### Divider placement fix and native re-run (#202, 2026-11-10)

**Cause of the pfet/prescaler findings: overlapping placement, not the generated cells.** In `layout/gen_integrated.py` the divider
sat at (300.0, -251.0) um while the prescaler occupies x 281..727, y -236.6..-185 um, so the two cells overlapped (879 overlapping
shapes, measured per layer with `klayout.db` Region AND of the two instances). The native deck attributed the resulting Cnt/Act/M1
hits to `lcpll_divider_pfet_w5_l0p5` and the prescaler HBT. The divider is now at (445.0, -310.0) um: clear of the prescaler (7.8 um
below it) and of the loop filter (x <= 430.7 um). VCO stream, VOP/VON routes (850.105 / 611.845 um)
and the tank-load estimate (73.16 / 52.66 fF, not extracted, against 2.1 fF) are unchanged; only the divider-connected routes moved
(FB 995.87 -> 1199.87 um). One cell did change for an unrelated reason: the committed `cells.provenance.json` predated the
current `design/netlist/prescaler.spice` (`gen_cells.py --check` already reported a prescaler geometry/netlist mismatch on `main` before this
change), so regenerating moves one prescaler `rppd` group from L = 8.0 to 7.8 um (`lcpll_prescaler_resrppd_w1_l8` -> `_l7p8`); the pfd/lockdet
provenance only picks up the new `pll_top.spice` hash. The "before" columns below were measured on the stale-cell stream; the divider
placement is what removed the pfet/HBT/resistor findings (both effects are in the "after" numbers). The generator code is unchanged.

```
klt drc layout/top.gds --deck sg13g2 --engine both --pdk sg13g2 --pdk-root /home/ubuntu/share/pdk --format json -o layout/drc/top.crosscheck.json   # exit 3
klt drc layout/drc/request.json --format json > layout/drc/top.drc.json     # curated, exit 3; klt drc --check = match
```

`klt 0.9.2.dev457+g5cd6aad7c733`, klayout 0.30.13, input `sha256:4a7f8645…` (stream), curated deck `sha256:0c0014b1…`, native deck
`ihp-sg13g2.drc` `sha256:0620b737…` (no `--deck-var`, native coverage still `known: false`). Same commands as the 1798 baseline above.

| Engine | Before (`b05b0bcb…`) | After (`4a7f8645…`) | Per rule after |
|---|---|---|---|
| native | 1798 | **348** | LU.b 322, M1.b 22, Cnt.b 4 |
| curated | 783 | **79** | nwell.enclosing.pactiv.1 64 (VCO `SVaricap`, sg13g2-vco#315, not waived), metal1.space.1 11, cont.space.1 4 |

Rules that went to zero natively: Cnt.g1, Cnt.g2, Cnt.c, Cnt.d, Cnt.e, Act.b, Gat.a, Gat.b, Gat.d, M1.a, M1.e, CntB.h1, pSD.c1.

**Residual (item 3 stays `unmet`):**
- **LU.b 322** (divider 235, cp 35, pfd 33, lockdet 19): the nfet cells have no substrate tap. Not fixed: `klt gen` has no pSD P-tap on
  `ihp-sg13g2`. `guard_ring` and `mos_array add_guard_ring` draw an n-well tie with no pSD and off-grid Cont; tried on the nfet groups
  (chunks of <= 96 units), it raised the native count to 559 (176 new `cont_drw_Offgrid`, LU.b not reduced) and was reverted. Tap net would
  be VSS (the nfets' bulk net). Tool gap: 2AMLogic/klayout-tools#5231. Hand-drawn taps were not added.
- **M1.b 22 / Cnt.b 4:** attributed and fixed in the next section (the "5 nm `bjt_array` abutment" attribution recorded here was wrong).
- G8 keep-out is unchanged (3 VCTRL violations, sg13g2-vco#314); `layout/top.gds` has not been through LVS (#37) or PEX (#41).

### M1.b / Cnt.b attribution and fix (#202, 2026-11-10)

**Measured, not assumed.** The 22 `M1.b` hits split by reported cell: 10 in `lc_pll_top` (5 nm x 205 nm), 10 in the prescaler/divider HBT
cells (same 5 nm marker, cell-local frame; the same gaps seen through the hierarchy), 1 + 1 at 160 nm x 864 nm (top and `lcpll_cp_nfet_w6_l0p3__core`).
A flat Metal1 `Region.space_check(180)` on the merged stream gives 11 gaps with everything and **0 with the top-level shapes removed**
(`klayout.db`, instances only), so the gaps are not `bjt_array` unit abutment (the tool pitch is 2.0 um, consistent with the closed
klayout-tools#5232): they are created by the generated top level.

- **M1.b (22 -> 0), `layout/gen_integrated.py`.** The 0.7 um Metal1 via-stack pad at a pin overlaps the pin's own polygon but leaves a 5 nm
  slit to another piece of the same HBT Metal1 polygon (10 sites: prescaler 8, divider 2), and in one place (cp nfet) sits 160 nm from a different
  terminal's strip. The generator now trims each pad to keep 0.18 um from Metal1 polygons it does not touch, then closes notches per merged polygon
  (a closing of 2 x 91 nm applied only to polygons that hold a pad, so it never bridges two polygons). No route, via or placement moved.
- **Cnt.b (4 -> 0), `layout/gen_top.py`.** The guard-ring Cont row is laid out as four straight runs at 0.34 um pitch; at the corners the runs meet
  off-pitch and leave Cont-to-Cont gaps of 30 nm and less. A contact closer than one pitch to an already-kept one is now dropped.

Re-run (`klt 0.9.2.dev514+g65867de9adc8`, klayout 0.30.13, input `sha256:5e184029…`, native deck `ihp-sg13g2.drc` `sha256:0620b737…`,
curated deck `sha256:85a9012a…`; same commands as above, plus `klt drc --check layout/drc/top.drc.json` = match):

| Engine | 1798 baseline | 348 (#202 first pass) | **now** | Per rule now |
|---|---|---|---|---|
| native | 1798 | 348 | **322** | LU.b 322 |
| curated | 783 | 79 | **64** | nwell.enclosing.pactiv.1 64 (VCO `SVaricap`, sg13g2-vco#315, not waived) |

The curated `metal1.space.1` / `cont.space.1` hits (11 / 4) are gone for the same reasons. The curated deck hash differs from the 348 run because the
installed klt moved, so the two columns are not byte-for-byte the same deck. Placements, routes (VOP 850.105 / VON 611.845 um, collisions 13) and the
tank-load geometric estimate are unchanged, and the VCO stream is untouched. **Item 3 of #36 stays `unmet`:** `LU.b` 322 (no P-substrate tap drawable via
`klt gen`; waits on 2AMLogic/klayout-tools#5231, tap net VSS `0`, not hand-drawn) and the 64 VCO curated hits remain. Pins re-stamped: `manifests/layout.attest.json`,
`layout/drc/top.drc.json`, `manifests/sg13g2-lc-pll.json`, signoff record (`klayout-tools==0.8.0`).

## Regeneration after the `cml_dff_latch` resize (#187)

`design/cml_dff.sch` instantiates `cml_dff_latch` (RL1/RL2 `rppd` 1u x 8.0u, #182/#189). Re-run 2026-11-10,
`klt 0.9.2.dev422+g1560fe3aac8d`, klayout 0.30.12 (venv), against `main` @ `42d74d3`; no generator code changed.

- `gen_cells.py --write`: only `lcpll_prescaler` changed. Its `rppd` 1.0 um groups are now 8 units at L = 8.0 um
  (`cml_dff` RL1/RL2) plus 43 units at L = 9.05 um (the `cml_latch` loads of `div2_cml_ls`, which keep 9.05 um; was 51 at
  9.05). Area 27316.5 -> 23027.5 um2 (bbox 529.39 -> 446.27 um wide). `lcpll_divider` has no `cml_dff` in its netlist
  (`grep cml_dff design/netlist/divider.spice` = 0) and its geometry is unchanged; its provenance only picks up the new
  netlist hash and klt version, as do the other cells.
- `gen_integrated.py --write`: `layout/top.gds` (sha256 `b05b0bcb…`) and `provenance.json` regenerated. Placements and
  route paths are unchanged (VOP 850.105 um, VON 611.845 um, collisions 13), so the tank-load geometric estimate
  (73.16 / 52.66 fF, not extracted, against 2.1 fF) is unchanged and still not within budget. PEX stays #41.
- Pins re-stamped to the new stream: `manifests/layout.attest.json` (`klt signoff --attest 2`), `layout/drc/top.drc.json`
  (re-run, 783 violations, see the DRC section), `manifests/sg13g2-lc-pll.json` and the signoff record
  (`klayout-tools==0.8.0`, as CI). The integrated-top DRC/LVS closure itself stays #36/#37.
- Standalone `lcpll_prescaler` (`klt drc`, curated `sg13g2`, `lcpll_prescaler.gds` sha256 `c3f83edc…`): **0 violations**, 19 rules
  checked (Activ/Cont/GatPoly/pSD/Metal1-2/Via1), 43 skipped because their layers (Metal3-5 etc.) are not in the cell; this is clean for
  the checked layers only. It disagrees with the integrated top, which reports ~576 violations under `lcpll_prescaler` (mostly HBT
  `npn13G2V`) from the same device geometry; the cause is not established here (#36).
- Standalone `lcpll_prescaler` `klt lvs` (reference `prescaler`, `form: subckt-call`): **mismatch** (29 `reference.unresolved_subckt_call`,
  14 `topology`, 1 `topology.hierarchy_mismatch`, 1 `device.geometry_not_compared`, 1 `device.placeholder_value`). Expected for a
  placement-only cell with no routing (#35 routes only the integrated top); not a pass and not claimed as one. Other cells were not re-run
  (their geometry did not change).
