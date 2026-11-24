# layout/lvs: T1 item 4 (LVS) attempt

**Status: item 4 stays `unmet`. No `klt lvs` envelope exists; both engines stop before a compare.**
Tracker for the current tool gap: `2AMLogic/klayout-tools#5407` (earlier gap #5402 is fixed). Nothing here is a `match`.

**DRC state changed after the runs below were written.** `layout/drc/top.drc.json` went
`status: clean` in PR #248 (commit `28cbf88`, 2026-11-13); the dated run sections below keep their
findings as history and say so in the past tense. Item 4 is unaffected and stays `unmet`.

## Inputs

- `build_reference.py` -> `top.reference.spice`: `design/netlist/pll_top.spice` (item 1) plus a `vco`
  subckt made from the device cards of the pinned `sg13g2-vco@17e49a8` `design/vco.spice` (the
  pinned file is a testbench whose `.subckt vco` header is commented out). Cards are verbatim except
  node `0` -> port `VSS`; port order follows the `XVCO VCTRL VOP VON VDDV VSS vco` call. Nothing is resized.
- `request.json`: curated-deck request, `layout/top.gds` (`lc_pll_top`) vs `top.reference.spice` (`pll_top`).

## Result (2026-11-12, `klt 0.9.2.dev868+g937ab1c98ca5`, single local runs)

| Run | Outcome |
|---|---|
| `klt lvs layout/lvs/request.json` (curated `sg13g2`, `form: subckt-call`) | exit 1 before compare: `subcircuits 'inductor', 'sg13_hv_svaricap' are not known devices for the requested deck`. `device_map` only maps onto curated classes, none exist for these. |
| `engine: klayout-runset`, PDK `sg13g2.lvs`, `form: subckt-call` | same conversion error (curated device list consulted for the runset engine too). |
| `engine: klayout-runset`, no `form` (xschem `X` cards passed raw) | runset aborts: `Can't find a schematic counterpart for the top cell lc_pll_top - use 'same_circuit'`; `klt lvs` has no way to pair `lc_pll_top` with `pll_top`. |

So the inductor, varactor and `npn13G2v` recognition question the issue names is not reached:
no `device_census` or `coverage.declared_not_recognized` was produced. `power_connectivity` is
`unchecked` for any non-gate-level reference (its `expected_nets` option is refused otherwise).

## Re-run 2026-11-13 (`klt 0.9.2.dev879+gd0673a77ebba`, includes klayout-tools PR 5404)

| Run | Outcome |
|---|---|
| `klt lvs layout/lvs/request.json` (curated `sg13g2`, `form: subckt-call`) | unchanged: exit 1, `inductor` / `sg13_hv_svaricap` not known devices for the curated deck. |
| `engine: klayout-runset`, PDK `sg13g2.lvs` as `deck_file`, no `form`, `lc_pll_top` vs `pll_top` | past the earlier errors: the compare runs, then `klt` raises `ValueError: invalid coverage: checked: work identity must be a nonempty string` in `_build_coverage` (`lvs_runset.py`) and writes no envelope. Filed as `2AMLogic/klayout-tools#5407`. |

Still no `device_census`, no `coverage.declared_not_recognized`, no `power_connectivity` verdict, so
`npn13G2v` recognition remains unobserved. Item 4 stays `unmet`; `layout/drc/top.drc.json` was still
`violations` at the time of this run, so a `match` would not have been expected even without the
crash (DRC went `clean` later, in PR #248 — see the note at the top). The runset request used
absolute paths in a scratch file (`/tmp`) and is not committed; a committed runset request is added
once the tool produces an envelope.

## Not done

- No hand-written plain-element reference in the runset's dialect: that is a second, unreviewed
  netlist, and a `match` against it would not be evidence about the item-1 netlist.
- Routing is still placement-level (`gen_integrated.py`), so a `match` would not be expected even
  with the tool gap closed. DRC is no longer part of that reason: `layout/drc/top.drc.json` is
  `clean` as of PR #248, and this bullet now rests on the placement-level routing alone.
- `manifests/sg13g2-lc-pll.signoff.json` is not touched.

Re-run once `klayout-tools#5407` lands; then commit the envelope as `top.lvs.json` and check it with
`klt lvs --check layout/lvs/top.lvs.json`.

## Run 2026-11-13 (`klt 0.9.2.dev883+gd109c11dce60`, klayout 0.30.13): first envelope, `status: mismatch`

Committed: `request.runset.json` (relative paths) and `top.lvs.json` (the envelope).
Reproduce from this directory with
`klt lvs request.runset.json --deck-file <PDK>/libs.tech/klayout/tech/lvs/sg13g2.lvs --format json -o top.lvs.json`
(single local run; the PDK `sg13g2.lvs` runset, `engine: klayout-runset`, deck sha256 `e01bcb1e...`).
`klt lvs --check top.lvs.json`, run from `layout/lvs/`, exits 0: that re-hashes the inputs only and is
**not** an LVS verdict. The LVS verdict is `status: mismatch`.

| Field | Value |
|---|---|
| `status` | `mismatch` (1787 net, 677 device, 16 pin errors; 0 nets / devices / pins matched) |
| `power_connectivity` | `unchecked`: the runset's extracted netlist has no instance-level power pins. This is "does not apply", not "verified". |
| layout `device_census` | `sg13_hv_nmos` 391, `npn13G2v` 137, `rppd` 85, `sg13_hv_svaricap` 32, `cap_cmim` 20, `rhigh` 6, `inductor` 2, `ptap1` 1 |
| reference `device_census` | empty (3 top-level devices, 2 pins) |
| `coverage.checked` | `cap_cmim, inductor, npn13G2v, ptap1, rhigh, rppd, sg13_hv_nmos, sg13_hv_svaricap` |
| `declared_not_recognized` | 35 deck classes absent from this layout (e.g. `npn13G2`, `npn13G2l`, `inductor3`, `ntap1`, `sg13_hv_pmos`) |

Reading it:

- **`npn13G2v` is recognized** on the layout side (137 devices, in `coverage.checked`), as are the
  inductor and the HV varactor. Recognition is no longer the blocker the issue feared.
- **The compare itself is not meaningful yet.** The reference top (`pll_top`) reaches the runset as
  3 subcircuit-call cards (`XPFD`, `XCP`, ...), not primitive devices, so nothing can pair with the
  1782-net flat layout extraction. The 0-matched counts say the two sides were not on the same footing,
  not that 674 devices are individually wrong. How the compare treats the VCO (flat vs black box):
  flat on the layout side, unexpanded on the reference side.
- The ~1.1 MB envelope is committed as evidence of this state, not as a pass. Item 4 stays `unmet`;
  `manifests/sg13g2-lc-pll.signoff.json` is not touched. `layout/drc/top.drc.json` was also still
  `violations` at the time of this run (it went `clean` later, in PR #248 — see the note at the top).
- Needed next (not done here; a hand-flattened reference would be a second, unreviewed netlist):
  a runset-compatible path for a hierarchical subcircuit-call reference. Tracked upstream as `2AMLogic/klayout-tools#5406` (open).

## Per-cell compares (#343, `klt 0.9.3.dev2575+g6bd18bbc8637`, klayout 0.30.12)

Committed under `cells/<cell>/` (request + envelope; `klt lvs --check` re-hashes them). The layout is
the committed `layout/top.gds` with `top` set to the cell, the reference is the cell's own `.subckt` in
`design/netlist/` (`form: subckt-call`; nothing hand-written). **No cell is matched; item 4 stays `unmet` with #37.**

| Cell | Engine | Status | Reading |
|---|---|---|---|
| `lcpll_loopfilter` (routed) | curated `sg13g2` | `mismatch` | equal 16 / 16 devices (14 `cap_cmim`, 2 `rppd`), 0 paired; layout has a `vsubs` net/pin the converted reference lacks, reference classes upper-case |
| `lcpll_loopfilter` (routed) | `klayout-runset` | `mismatch` | layout 4 devices vs reference 2 (`m=12` multiplier vs drawn units), 0 paired |
| `lcpll_cp` (placement only) | curated `sg13g2` | `mismatch` | 63 flat layout devices vs 4 reference devices in `cp_bias`/`cp_leg_*`/`cp_dumpbuf` hierarchy (`topology.hierarchy_mismatch`); unrouted, so no match expected |

Tool gaps filed generically: `2AMLogic/klayout-tools#6960` (subckt-call reference pairs 0 devices), `#6961`
(gen-compose router cannot wire the charge pump). The curated envelopes carry no `device_census` field and no
`coverage` block in this klt, so the `sg13_hv_pmos` census question stays open for the charge pump; the
`device_classes` list does include `pfet`. The swapped-net negative control is not run: it needs a `match`
baseline to flip, and neither cell has one. It becomes meaningful once the two issues above are fixed.

## Per-cell compares, all six cells (#346, `klt 0.9.3.dev2575+g6bd18bbc8637`, klayout 0.30.12)

The four remaining cells get the #343 treatment: committed request + envelope under `cells/<cell>/`, layout =
committed `layout/top.gds` with `top` set to the cell, reference = the cell's own `.subckt` (`form: subckt-call`,
nothing hand-written). These envelopes pin the `layout/top.gds` stream `90fecb47...`, which is what `main` held when they were produced
(the five #346 routing trials, four remaining cells plus a charge-pump repeat, all came back partial and none
shipped; the loop filter is separate, shipped fully routed 4/4). `main` has since moved to `60ad1ed0...`
(#344, `c1e1155`, supply / external-pin / divider tie-off routing), so on this head `klt lvs --check` reports
`environment.layout_sha256` drift for all seven #346 envelopes and for #347's `lcpll_cp` envelope, which is cited
rather than re-run. This is provenance staleness, not changed readings: the `lcpll_pfd` and `lcpll_lockdet`
requests were re-run against `60ad1ed0...` and gave byte-identical verdicts, device/net counts and category
counts (the top-level routing sits above these cells); the other cells' readings were not re-run. Refreshing the
envelopes is tracked in #413. The charge pump's flatten retry below is new evidence. **Every cell
mismatches; item 4 stays `unmet` with #37 and the swapped-net negative control stays pending everywhere (it needs a
`match` baseline to flip; none exists).**

| Cell | Engine | Status | Reading |
|---|---|---|---|
| `lcpll_pfd` (placement only) | curated `sg13g2` | `mismatch` | 66 layout devices (33 `nfet`, 33 `pfet`), 0 paired, 0 of 201/14 nets matched; flat layout vs 6-circuit reference hierarchy (`EDGEDET`, `SRLATCH`, … appear as reference circuits); 2 `device.body_unverified` (tap conductors unlabelled — the cell is unrouted) |
| `lcpll_pfd` | curated + `flatten_reference` | no envelope | exits 1: `top cell/subcircuit 'pfd' not found in reference netlist` — the flatten path only selects the file's first `.subckt` (`pll_top`), `2AMLogic/klayout-tools#6988`; `request.flatten.json` is committed so the diagnostic reproduces |
| `lcpll_lockdet` (placement only) | curated `sg13g2` | `mismatch` | 40 layout devices (19 `nfet`, 18 `pfet`, 2 `cap_cmim`, 1 `rhigh`), 0 paired, 0 of 120/11 nets matched; hierarchy mismatch + `device.placeholder_value` on 2 reference `CAP_CMIM` instances and 1 `RHIGH` instance |
| `lcpll_lockdet` | curated + `flatten_reference` | no envelope | same #6988 failure (`'lock_detector' not found`) |
| `lcpll_divider` (placement only) | curated `sg13g2` | `mismatch` | 617 layout devices (304 `nfet`, 304 `pfet`, 1 `rppd`, 5 `rhigh`, 3 `cap_cmim`) vs 0 paired, 0 of 1846/19 nets matched; the 4 HBT units drawn by the generator are **not** a curated-deck device class (absent from `device_classes`), so they are invisible to this engine; 1 unresolved reference `NPN13G2V` call |
| `lcpll_divider` | curated + `flatten_reference` | `mismatch` | reference flattens to 617 devices — census equal — but 0 pair: 1234 `device.unmatched`, 2130 `net.unmatched` (unrouted layout), 3 nets / 26 pins matched; envelope committed as `<cell>.flatten.lvs.json` |
| `lcpll_prescaler` (placement only) | curated `sg13g2` | `mismatch` | 80 layout `rppd` (the 129 HBT units are not a curated-deck class — prescaler HBT recognition is **not observed** by this engine, matching the #343 note that the curated envelopes carry no `device_census`/`coverage`); 29 reference `NPN13G2V` calls unresolved (`reference.unresolved_subckt_call`); `device.placeholder_value` applies to 24 reference `RPPD` instances; 0 devices paired |
| `lcpll_prescaler` | curated + `flatten_reference` | `mismatch` | census 80 / 80 `rppd` and the compare engages — 25 devices, 52 nets, 12 pins matched — then `net.split` 110 / `net.merged` 54 (the layout is unrouted, so extracted connectivity cannot agree); envelope committed |
| `lcpll_cp` | curated + `flatten_reference` | `mismatch` | census 63 / 63 devices (the #347 flat-vs-hierarchy asymmetry gone), 0 paired: 63 `device.unmatched`, 212 `net.unmatched`; envelope committed beside #347's plain curated envelope |

What the flatten retries establish: the `topology.hierarchy_mismatch` note's own recommendation (`options.flatten_reference:
true`) is the right shape — divider and charge pump reach an equal device census with it — but no device pairs yet
(#6960 pairing still applies), it cannot even be requested for `pfd`/`lock_detector` whose reference subckt is not the
first of `pll_top.spice` (#6988), and a placement-only layout can at best half-match (prescaler: splits/merges on
unrouted nets). Fields this klt does not emit for these envelopes: `device_census`, `coverage` (only the `klayout-runset` top-level envelope, the committed `top.lvs.json`, carries both; replaying
the curated top-level request exits 1 during conversion on `inductor` and `sg13_hv_svaricap`, so no curated top-level envelope
exists, and the curated per-cell envelopes do not carry them) — the HBT recognition statements above rest on
`device_classes` + `device_parameter_coverage` + the unresolved-call counts, not a census.

Reproduce (needs `klt`, the KLayout Python module and an IHP-SG13G2 PDK; the committed requests use relative paths, so run
from each `cells/<cell>/` directory): `klt lvs request.json --format json -o <cell>.lvs.json`
and `klt lvs request.flatten.json --format json -o <cell>.flatten.lvs.json`. `klt lvs --check` re-hashes the
inputs and currently reports `environment.layout_sha256` drift (`90fecb47...` recorded, `60ad1ed0...` on this head)
for all seven #346 envelopes; it is an input-freshness check, not a verdict.

## Re-run after the duplicate port-label fix (#349, 2026-11-23, `klt 0.9.3.dev3910+g8703ad519ff7`, klayout 0.30.12)

`layout/cells/common.py` no longer keeps `gen-compose`'s own net labels on a routed cell, so the
loop filter carries exactly one label per port at the recorded `port_labels` site (it carried two
per port; the router's copies sat on 10/25 and 30/25). `layout/top.gds` was regenerated on top of
`main` after the #344/#345/#346 merges (`sha256:4b8e6867...`, was `c897060c...` on `main`) and the
three per-cell envelopes above were re-run against it — same commands, same requests, from each
cell's directory. Counts below are measured from `mismatches[]` / `counts` in the committed
envelopes, compared with `main`'s copies:

| Cell | Engine | Status | Change vs `main` |
|---|---|---|---|
| `lcpll_loopfilter` | curated `sg13g2` | `mismatch` | none beyond the input hash (same 16 / 16 devices, 0 paired, `mismatch_count` 31) |
| `lcpll_loopfilter` | `klayout-runset` | `mismatch` | `mismatch_count` 21 -> 18; `counts.pins.layout` 3 -> **0**; `pin.unmatched` 6 -> 3 (the 3 layout-side warnings gone, the 3 reference-side entries remain); `counts.nets` unchanged (layout 5, reference 4, matched 0) and `net.unmatched` unchanged at 9 — three layout nets lost their names (`VIN`/`VCTRL`/`VSS` -> anonymous `$n`), none was added or removed |
| `lcpll_cp` | curated `sg13g2` | `mismatch` | none beyond the input hash |

No net was added or removed: the whole `21 -> 18` delta is the three layout-side pin warnings
disappearing because the runset now recognises no layout pin at all.

**The routed loop filter now presents zero layout pins to the PDK runset.** `counts.pins.layout`
fell 3 -> 0 and all three reference pins (`VCTRL`/`VIN`/`VSS`) remain unmatched, so this is *further*
from an eventual `match`, even though `mismatch_count` fell. Mechanism, inferred from the
before/after pair (the runset deck was not read): the pins the runset recognised came from the
router's texts on the label purposes 10/25 and 30/25 (no-rule label layers, `layout/drc/README.md`);
the surviving stamp writes text on drawing purposes (`126/0` / `67/0` / `8/0`, per `port_labels`),
which the runset evidently does not read as pin text. "One label per port" as implemented is
therefore a label the PDK LVS runset cannot use. This matters beyond #349: item 4 / #37 needs layout
pins to match, and #346 routes the other cells onto the same stamp path. Tracked in #416.

Still no match and no new claim: item 4 stays `unmet` with #37, and the tool gaps (#6960, #6961) are
unchanged. The re-run does show the duplication was not extraction-neutral, contrary to the issue's
"believed benign" impact note.

## Envelope refresh 2026-11-23 (#413, `klt 0.9.3.dev3934+g049acce7a82b`, klayout 0.30.12)

Every committed envelope whose layout input is the integrated `layout/top.gds` is now pinned to the
stream on `main` after #349: `sha256:4b8e6867...`, the same bytes `manifests/layout.attest.json` pins. Before this
refresh (on `main` at `ce39102`) the eleven envelopes pinned three different earlier streams (`90fecb47...` for seven cell
reports, `5e184029...` for `top.lvs.json`; the three loop-filter / charge-pump reports re-run by #349 already pinned
`4b8e6867...`), so
`klt lvs --check` reported `[DRIFTED] environment.layout_sha256` -- provenance staleness, not wrong verdicts.
The eight stale requests (seven cell reports plus top) were re-run once each from their directories (same requests, same commands as above;
`top.lvs.json` with `--deck-file <PDK>/libs.tech/klayout/tech/lvs/sg13g2.lvs`, deck `sha256:e01bcb1e...`, unchanged).
The three #349 envelopes were not re-run: they already record `4b8e6867...`.

| Report | Status | vs the previous envelope |
|---|---|---|
| `top.lvs.json` | `mismatch` | layout side moved with the stream (previous committed run at `ce39102` -> now): nets 1782 -> 1746, devices 674 -> 666, pins 14 -> 19 (layout-side `counts`), still 0 matched; `mismatch_count` 2480 -> 2441. Layout device census: `npn13G2v` 137 -> 139, `rppd` 85 -> 86, `cap_cmim` 20 -> 9 (three classes moved; the 2026-11-13 section's `rppd` 85 / `cap_cmim` 20 are the older values). These are layout-side `counts`, not the error counts the 2026-11-13 section quotes (there 1787 / 677 / 16; the current error-count figures, `category_counts`, are 1751 / 669 / 21). Reference-side pairing limitation (#5406) unchanged. |
| `cells/lcpll_pfd/lcpll_pfd.lvs.json`, `lcpll_lockdet.lvs.json`, `lcpll_divider.lvs.json`, `lcpll_divider.flatten.lvs.json`, `lcpll_prescaler.lvs.json`, `lcpll_prescaler.flatten.lvs.json`, `lcpll_cp.flatten.lvs.json` | `mismatch` | status, `counts` (nets / devices / pins) and `mismatch_count` identical to the previous envelope on all seven. The re-run used a newer `klt` (`0.9.3.dev2575+g6bd18bbc8637` -> `0.9.3.dev3934+g049acce7a82b`), so each of the seven also gained tool-version diagnostics: `device_classes` gained `inductor`; `ignored_layers`, `pin_set_difference` (`deck_synthesized_layout_pins: ["vsubs"]`), `sg13g2_passive_pairing` (`insufficient_evidence`), `mismatches_omitted` (`false`) and `warnings` (top cell has no text on the deck's pin label layers; looks like the already-tracked #416) went from `null` to populated. `lcpll_prescaler.flatten.lvs.json` additionally changed `mismatches` and `net_correspondence` (auto-generated net names). This is tool-version drift, not stream drift. |
| `cells/lcpll_loopfilter/lcpll_loopfilter.lvs.json`, `.runset.lvs.json`, `cells/lcpll_cp/lcpll_cp.lvs.json` | `mismatch` | not re-run; see the #349 section below (already on `4b8e6867...`) |

No verdict changed and item 4 stays `unmet`. The earlier statement in the #346 section that these envelopes pin
`90fecb47...` describes the state when they were produced; this section supersedes it for the pins.
The refreshed `top.lvs.json` records its layout input in the repo-scope form
(`{"scope":"repo","path":"layout/top.gds"}`) instead of the report-relative `../top.gds` string the 2026-11-13
envelope carried.

`scripts/test-layout-top.sh` now enforces the pin (#413): it discovers every committed `*.lvs.json` under
`layout/lvs/` whose recorded layout input is the integrated GDS -- either path form -- and refuses when a
report's `environment.layout_sha256` is stale or missing, naming the file and both hashes, so the next
stream bump fails the layout test at the commit that causes it instead of silently stranding the evidence.
The string-form negative control compares against the unmodified tree's own count, so adding an envelope
does not break it.

## Re-run after moving stamped cell port labels to `/25` (#416, 2026-11-23, `klt 0.9.3.dev4116+ga9885c2c7fa3`, klayout 0.30.12)

Both the PDK LVS runset (`sg13g2.lvs`: `rule_decks/layers_definitions.lvs` +
`general_connections.lvs:57-63`) and `klt`'s curated `sg13g2` `EXTRACTION_DECK.metal_labels` attach
metal pin/net text exclusively from datatype `25` (`8/25`, `10/25`, `30/25`, `50/25`, `67/25`,
`126/25`, `134/25`) and ignore drawing-purpose `*/0` text. `layout/cells/common.py` now maps every
cell's `.subckt` port terminal from `<layer>/0` onto `<layer>/25` (uniformly across routed and
placement-only cells, failing with `PlanError` on any unmapped layer), still stamping strictly one
direct text shape per port. `layout/top.gds` was regenerated (`sha256:1c49ad5d...`, was
`4b8e6867...` on `main`), and all eleven committed `*.lvs.json` envelopes pinning `layout/top.gds`
were re-run from their directories and verified with `klt lvs --check`:

| Report | Engine | Status | Change vs `main` (`4b8e6867...`) |
|---|---|---|---|
| `cells/lcpll_loopfilter/lcpll_loopfilter.runset.lvs.json` | `klayout-runset` (`sg13g2.lvs`) | `mismatch` | **`counts.pins.layout` `0 -> 3`** (matches `counts.pins.reference == 3`); layout nets recover their port names (`VCTRL`, `VIN`, `VSS`, leaving only internal `$1` and `$4` anonymous); `mismatch_count` `18 -> 21` (`pin.unmatched` `3 -> 6`: the 3 layout-side pin entries reappear alongside the 3 reference-side entries, with the runset's own compare grading each pin pair `Match`, while device/net mismatch keeps circuit pairing at 0) |
| `cells/lcpll_loopfilter/lcpll_loopfilter.lvs.json`, `cells/lcpll_cp/{lcpll_cp,lcpll_cp.flatten}.lvs.json`, `cells/lcpll_divider/{lcpll_divider,lcpll_divider.flatten}.lvs.json`, `cells/lcpll_lockdet/lcpll_lockdet.lvs.json`, `cells/lcpll_pfd/lcpll_pfd.lvs.json`, `cells/lcpll_prescaler/{lcpll_prescaler,lcpll_prescaler.flatten}.lvs.json` (9 reports) | curated `sg13g2` | `mismatch` | `counts` (nets / devices / pins), `mismatch_count` and `category_counts` unchanged on all nine; **`warnings` cleared (`[... has no text on the deck's pin label layers. Text is drawn on .../0 ...]` -> `[]`)** on all nine |
| `top.lvs.json` | `klayout-runset` (`sg13g2.lvs`) | `mismatch` | `counts.nets` (`1746 / 5 / 0`) and `counts.devices` (`666 / 3 / 0`) unchanged; `counts.pins.layout` `19 -> 20` (`pin.unmatched` `21 -> 22`, `mismatch_count` `2441 -> 2442`): the `PSP` route (`lcpll_prescaler.OUTP` -> `lcpll_divider.INP`), whose top-level `67/25` label sat over a Metal4-only segment, is now named `'INP,OUTP'` by its `/25` cell port labels, and existing routed islands pick up their connected cell port names (`VSS` -> `'A0,A1,M0,M1,VSS'`, `VDD` -> `'A2,M2,M3,VDD'`, `VCP` -> `'VCP,VIN,VOUT'`, etc.) |

No LVS verdict moved to `match`; item 4 stays `unmet` with #37 and `2AMLogic/klayout-tools#6960` / `#6961`.
