# layout

Layout for the LC PLL. `gen_top.py` draws the scaffold `lc_pll_top`: the pinned `sg13g2-vco`
stream placed unmodified at the origin, plus an inductor keep-out marker, an outer
substrate guard ring and metal filler. Loop-block cells are drawn by `gen_cells.py` (below),
and `gen_integrated.py` places them under the VCO and routes the integrated top
(`layout/top.gds`, "Integrated top (#35)" below).

Sign-off state of that stream: DRC is clean on both engines and item 3 reads `met`, clean for
the layers the deck covers — "DRC of the integrated top" below for the verdict and the coverage
it excludes, [`layout/drc/README.md`](drc/README.md) for the run log;
LVS reaches a `mismatch` ([`layout/lvs/README.md`](lvs/README.md), item 4 `unmet`); PEX has not
been run (#41).

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
- Fill is a placeholder; density sign-off is DRC work (#36).
- This section describes `gen_top.py`'s scaffold alone: no DRC, LVS or PEX is run by it. The
  integrated top is the stream that has been checked — see the frame above for where.

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
The digest hashes merged polygons plus label text/position per layer, in sorted `(layer, datatype)`
order rather than KLayout's layer-enumeration order, so it is stable across a re-save of the stream
(#263). Both `digest()` copies -- here and in `gen_integrated.py` -- carry that ordering.

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
(prescaler 209 units, divider 621, in total with HBTs, MOS and caps).

**Not met:**
- The prescaler's INP/INN tank-load capacitance is NOT extracted: the 2.1 fF budget is unverified until PEX on
  the integrated loop (#41). The input group is placed first to keep its geometry compact; that is not a measurement.
- Cells are placement only: no routing, no LVS (#35, #37). Since #202 every `nfet` `mos_array` group carries a
  `mos_array add_guard_ring` pSD substrate tap ring on net `VSS` (see "LU.b substrate taps"); the ring is drawn but
  not tied to anything by a route, and `pfet` groups have no ring. Areas are bounding boxes.
  The loop-filter cell is 131458 um2 because the schematic's `cap_cmim` units (12 x 70.9 um square) are drawn as specified.

## Integrated top (#35)

```
.venv/bin/python layout/gen_integrated.py --write      # -> layout/provenance.json (+ layout/top.gds if the geometry moved)
scripts/test-layout-top.sh                             # reproducibility, attestation pin, VCO byte-match, keep-out record, negatives
```

`gen_integrated.py` runs `gen_top.py` (VCO + keep-out + ring + fill), places the six `gen_cells.py` cells below the VCO,
routes the inter-block signal nets and writes `layout/top.gds`. `layout/provenance.json` holds the generator chain, input
hashes (VCO stream, cells provenance, generators), the output sha256 and geometry digest, placements, per-net route
paths and lengths, collisions, the tank-node estimate and the Metal1 pad-trim record (`metal1_pad_trim`). GDS bytes
carry writer state, so reproducibility is checked on the geometry digest (`--check`), not the file hash. The digest is
writer-independent in both directions: it ignores the byte layout of the stream, and since #263 it also ignores the
layer-enumeration order, so a stream that has merely been re-saved (a clip, a merge, a DRC-prep step) digests to the
same value. T1 item 2 is cited by `manifests/layout.attest.json` (`klt signoff --attest 2 --input layout/top.gds`),
which pins the stream sha256.

**`--write` is geometry-aware, so it is safe to re-run (#257).** KLayout stamps wall-clock time into the GDS
`BGNLIB`/`BGNSTR` records, so regenerating an unchanged design still produces different bytes -- and those bytes are what
the item 2 attestation pins. `--write` therefore writes the fresh stream to `layout/build/top.gds`, compares its geometry
digest against the digest of `layout/top.gds` as it sits on disk, and replaces the committed stream only when the two
differ. Always re-run it after editing a generator: `layout/provenance.json` is rewritten either way (the input hashes
legitimately change), and the attested bytes are left alone unless the geometry actually moved. Each run says which
happened, and `klayout_module` keeps describing whichever module wrote the stream now on disk.

After a run that reports `geometry changed -- replaced`, the attestation pin is stale and must be re-stamped:

```
klt signoff --attest 2 --input layout/top.gds          # refresh manifests/layout.attest.json
```

`scripts/restamp-attest.sh` covers items 1, 9 and 10 only, not item 2. The hash also appears in
`manifests/sg13g2-lc-pll.json` (`evidence.2`/`evidence.3`), `manifests/sg13g2-lc-pll.signoff.json` and the item 3 DRC
evidence (`layout/drc/top.drc.json`, `layout/drc/top.crosscheck.json`), so all of those have to be refreshed with it.
`scripts/test-layout-top.sh` fails until they agree: it checks `layout/top.gds` against the hash
`manifests/layout.attest.json` pins, which the geometry digest (`--check`) cannot see.

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
- **Every Metal1 via-stack pad still covers its own Via1.** `provenance.json` `metal1_pad_trim`: 19 endpoint pads, 1
  trimmed back from foreign Metal1 for native M1.b, 0 left below their Via1. The trim is bounded by construction rather
  than by luck -- Metal1 that *touches* a pad is the pad's own landing polygon and never trims it, so a non-touching
  polygon trims from at best the pad edge and reaches 0.170 um from the pad centre, against the Via1's 0.095 um
  half-width: `via_cover_margin_um` 0.075. The guard is the regression gate on that margin and arms if the pad shrinks,
  the via grows, or M1.b widens; `scripts/test-layout-top.sh` exercises it in both directions. A pad found below its via
  is recorded in `below_via` (with position and uncovered area), never dropped -- dropping it would change geometry to
  hide an open that DRC (#36) and LVS (#37) must see.
- Placeholder fill under routes is removed (5 squares); density sign-off is #36.
- CI pin: `.github/workflows/signoff.yml` stays at `klayout-tools==0.8.0`, which grades item 2 `met` from the attest envelope.
  Moving the pin to 0.9.1 grades item 1 `stale_evidence` (3 met -> 1), so the bump is left out.

## DRC of the integrated top (#36, T1 item 3) — item 3 `met`, clean for covered layers

```
klt drc layout/drc/request.json --format json > layout/drc/top.drc.json   # exit 0 = clean
klt drc --check layout/drc/top.drc.json                                   # re-hash: match
scripts/test-drc-svaricap-liveness.sh                                     # 4 checks, incl. the negative control
```

Current state, run 2026-11-13, `klt 0.9.2.dev964+g02db14ecf46b`, klayout 0.30.13 (klt warns the
build was tested on 0.30.12), PDK `ihp-sg13g2` `fetched:0.3.0`, input `layout/top.gds`
`sha256:92b05723…` (the geometry attested for item 2, byte-identical to the stream the earlier
runs used — **no layout changed**), curated deck `sha256:cf6dfead…`, native deck
`ihp-sg13g2.drc` `sha256:0620b737…`, single local runs, `--engine both`:

| Engine | Result |
|---|---|
| native (`ihp-sg13g2.drc`) | **0 violations, `status: clean`**, 590/590 declared rule categories asserted (`--expect-rule-categories-file layout/drc/native_rule_categories.txt`; `coverage_assertion.satisfied: true`). Carries **no** layer coverage: for an externally-run deck klt leaves `coverage.deck_layers`, `layers_checked`, `layers_in_stream_without_rules`, `rules_skipped` and `deck_scope` empty. |
| curated (`sg13g2`) | **0 violations, `status: clean`**, 63 rules checked. The 64 `nwell.enclosing.pactiv.1` findings the earlier runs recorded (see the run log) are gone because klt now models PDK `NW.c`'s `SVaricap` carve-out (klayout-tools#5442), not because the stream, the rule thresholds or a waiver changed. |

**Coverage, verbatim from the cited report** — "clean" here means **clean for covered layers**:

- `coverage.rules_skipped` = `[]`.
- `coverage.unchecked_rules` = one entry, `NW.b1` (31/0): net-aware PWell width between NWell
  regions of different nets (1.80 um) has no net-aware spacing check in this engine, so only the
  geometric `nwell.space.1` (0.62 um) ran. **A rule in scope that did not run.**
- `coverage.deck_scope` = `['Act','Cnt','Gat','M1','M2','M3','M4','M5','MIM','NW','TM1','TM2','TV1','TV2','V1','V2','V3','V4','pSD','x']` — the only DRM chapters this deck transcribes at all.
- `coverage.unmodeled_rules` = 14 rules the deck declares but does not model: `LU.a`, `LU.c`,
  `LU.c1`, `LU.d`, `LU.d1` (latch-up, other than the `LU.b` tap spacing) and `Pad.a1`, `Pad.aR`,
  `Pad.bR`, `Pad.d`, `Pad.d1R`, `Pad.dR`, `Pad.gR`, `Pad.jR`, `Pad.kR`. **Declared in scope,
  never evaluated.**
- `coverage.voltage_domain_warnings` names the `ThickGateOx` (44/0, '-HV') domain: the deck
  applies the general-case '-LV' thresholds regardless of it (e.g. the `Gat.a1`/`Gat.a2`
  channel-length-specific GatPoly widths, not transcribed).
- `coverage.layers_in_stream_without_rules` is **non-empty**: 39 layers, `1/23, 5/23, 8/2, 8/22,
  8/23, 8/25, 10/2, 10/22, 10/23, 10/25, 26/0, 27/0, 27/2, 27/25, 28/0, 30/22, 30/23, 30/25, 40/0,
  44/0, 46/21, 50/22, 50/23, 51/0, 52/0, 67/22, 67/23, 67/25, 111/0, 126/2, 126/23, 126/25, 128/0,
  129/0, 134/23, 134/25, 148/0, 156/0, 160/0` — drawn in this stream with no rule behind them
  (was 41; `32/0` and `63/0` left the list because the new recogniser reads them).

**The clean verdict is label-gated, not a silenced rule** (`scripts/test-drc-svaricap-liveness.sh`).
A deck change that stopped checking P+ Activ altogether would produce a byte-identical-looking
`clean`, so the discriminating evidence is the negative control: delete the **2** `SVaricap` texts
on `63/0` from a scratch copy of `layout/top.gds` — geometry untouched — and the same **64**
`nwell.enclosing.pactiv.1` findings come back, with no other rule firing. The rule's own
`description` in `klt drc --list-rules` now names the carve-out. The script also fails on klt
`0.9.1` (the current PyPI release, which predates the fix) with exactly those two legs red, which
is what makes it a control rather than a tautology.

**Item 3 is `met`, citing the curated report** (`manifests/sg13g2-lc-pll.signoff.json`, T1 met
4 -> 5; `klt signoff` grades item 3 on `status` alone and reports the `coverage` block above, which
is why the disclosure here is claimant-enforced). Nothing was waived, and no stream, deck or
threshold was edited. Two things this claim does **not** say: the native engine's zero carries no
layer-coverage fields at all, so it cannot substitute for the curated citation; and `NW.b1` plus
the 39 rule-free layers are outside what either engine measured.

**The cited report is reproducible only from a git commit, not a release.** No PyPI
`klayout-tools` carries the `SVaricap` carve-out yet (latest is `0.9.1`, 2026-11-05; the fix merged
2026-11-13), so the report's `provenance.deck.released` is `false` and the reproduction spec is the
`provenance.klt_reinstall_spec` git pin, as it was for the earlier dev-build runs. The signoff
**grader** pin is untouched: `.github/workflows/signoff.yml` stays at `klayout-tools==0.8.0`, which
grades this report item 3 `met` and reproduces the committed record byte-for-byte (the 0.9.1 bump
is still out for the reason recorded above — it grades item 1 `stale_evidence`).

**One manifest correction came with this.** `manifests/sg13g2-lc-pll.json`'s item 3
`content_hash` pinned the **report file's** sha256; `klt signoff` compares that pin against the
envelope's `provenance.input.content_hash` (the layout stream), so the entry had always been a
`stale_evidence` pin — masked while `status: violations` failed the check first. It now pins
`sha256:92b05723…`, the same stream hash item 2 pins.

**G8 keep-out is unchanged and still not clean**: `klt keepout-check` (margin 20 um, `--cells vco`),
`status: violated`, 3 violations, all the VCTRL pin-access stack recorded under "Integrated top
(#35)" (sg13g2-vco#314). It is not part of item 3's verdict. `layout/top.gds` has not been through
LVS (#37) or PEX (#41).

**Full run history** — seven dated runs between 2026-11-10 and 2026-11-13, the native rule-category
derivation, and the tool-friction filings — is in [`layout/drc/README.md`](drc/README.md), beside
the reports. The LVS counterpart is [`layout/lvs/README.md`](lvs/README.md).

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

## Digest re-baseline for the layer-order fix (#263)

Both `digest()` functions hashed their per-layer records in `ly.layer_indexes()` enumeration order, which a
GDS writer does not preserve, so a digest billed as writer-independent moved for a stream whose geometry was
untouched. They now hash in sorted `(layer, datatype)` order. That changes the recorded digest values and
nothing else. Re-baselined 2026-11-14 against `main` @ `da3c610`, `klt 0.9.2.dev1019+g8907ca2d3a87`,
klayout 0.30.13 (venv).

- `layout/top.gds` is **byte-identical**: `gen_integrated.py --write` reported `geometry unchanged -- kept
  ... (attested bytes preserved)`, so `output.sha256` (`92b05723…`) and `manifests/layout.attest.json` are
  untouched and item 2 needs no re-stamp.
- `layout/provenance.json`: `output.geometry_sha256` `38796010…` -> `6abc97d6…`, plus the two input pins that
  follow from the edited files (`inputs.gen_integrated.sha256`, `inputs.cells_provenance.sha256`). The same
  stream round-tripped through KLayout digested to `22b1852d…` before the fix and to `6abc97d6…` after it.
- `layout/cells.provenance.json`: the six per-cell `geometry_sha256` values. `area_um2`, `netlist_sha256`,
  `device_units`, `klt` and `pdk` are unchanged — the host's klt is newer than the recorded
  `0.9.2.dev887+gec7400b7d8e5`, so the `klt` field it rewrote was reverted rather than committed as drift.
- The geometry behind the new cell digests was checked against the attested stream, not assumed: for all six
  cells the per-layer merged-polygon and label record set of the regenerated cell is identical to that of the
  same cell inside the committed `layout/top.gds`. On this host `gen_cells.py --check` mismatched four of the
  six committed digests *before* the fix, with every other field matching — the bug on `main`, not drift.
