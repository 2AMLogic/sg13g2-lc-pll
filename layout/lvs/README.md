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

## Re-run after the duplicate port-label fix (#349, 2026-11-21, `klt 0.9.3.dev2575+g6bd18bbc8637`, klayout 0.30.10)

`layout/cells/common.py` no longer keeps `gen-compose`'s own net labels on a routed cell, so the
loop filter carries exactly one label per port at the recorded `port_labels` site (it carried two
per port; the router's copies sat on 10/25 and 30/25). `layout/top.gds` was regenerated
(`sha256:32b79317…`, was `90fecb47…`) and the three per-cell envelopes above were re-run against
it — same commands, same requests, from each cell's directory:

| Cell | Engine | Status | Change vs the run above |
|---|---|---|---|
| `lcpll_loopfilter` | curated `sg13g2` | `mismatch` | none beyond the input hash (same 16 / 16 devices, 0 paired) |
| `lcpll_loopfilter` | `klayout-runset` | `mismatch` | `mismatch_count` 21 -> 18, `pin.unmatched` 6 -> 3: the duplicate labels each produced an extra unmatched named layout net (`VIN`/`VCTRL`/`VSS`) plus a pin warning; with one label per port those nets extract anonymously (`$2`..`$5`) and the phantom entries are gone |
| `lcpll_cp` | curated `sg13g2` | `mismatch` | none beyond the input hash |

Still no match and no new claim: item 4 stays `unmet` with #37, and the tool gaps (#6960, #6961) are
unchanged. The re-run does show the duplication was not extraction-neutral, contrary to the issue's
"believed benign" impact note.
