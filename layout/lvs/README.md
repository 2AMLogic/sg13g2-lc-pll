# layout/lvs: T1 item 4 (LVS) attempt

**Status: item 4 stays `unmet`.** The top-level compare (`top.lvs.json`) is `status: mismatch` —
the reference-form tool gap is `2AMLogic/klayout-tools#5406`. The two routed cells are matched
against their own `.subckt` references (per-cell section, #343) — a per-cell `match` is not a
top-level verdict and does not move item 4.

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
- Routing is still placement-level at the **top level** (`gen_integrated.py` wires block to block but
  nothing inside a cell counts toward the top-level compare): the two routed cells (#343) change this
  only for `lcpll_loopfilter` and `lcpll_cp` internals, and a top-level `match` would still not be
  expected with the tool gap open — the four placement-only cells are unrouted inside. DRC is no
  longer part of that reason: `layout/drc/top.drc.json` is `clean` as of PR #248.
- `manifests/sg13g2-lc-pll.signoff.json` is not touched **by any run in this file before #343's
  2026-11-23 pass** (that pass re-stamped items 2 and 3 for the new stream; item 4 evidence is
  untouched and stays `unmet`).

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

## Per-cell re-run after the klt fixes (#343, `klt 0.9.3.dev3790+gd901bc795962`, klayout 0.30.12, 2026-11-23)

Both klt issues above are fixed in this build, and `lcpll_cp` is now routed (18 of 18 nets, `layout/README.md`).
Same committed request shape as above — layout `layout/top.gds` (sha256 `2140369c…`, the routed-CP stream) with
`top` set to the cell, reference the cell's own `.subckt`, curated `sg13g2` deck. Reproduce from the cell's
directory with `klt lvs request.json --format json -o <cell>.lvs.json` (the charge pump's request adds
`options.flatten_reference`, below); `klt lvs --check <cell>.lvs.json` re-hashes the inputs.

| Cell | Engine | Status | Counts (layout = reference = matched) | Body check |
|---|---|---|---|---|
| `lcpll_loopfilter` | curated `sg13g2` | **`match`** | 16 / 16 / 16 devices (14 `cap_cmim`, 2 `rppd`), 4 / 4 / 4 nets, 3 / 3 / 3 pins | no MOS in the cell (resistors and caps only) |
| `lcpll_cp` | curated `sg13g2` | **`match`** | 63 / 63 / 63 devices (`nfet` 35, `pfet` 28), 18 / 18 / 18 nets, 6 / 6 / 6 pins | **`verified`**, 0 findings — the `pfet` n-well ties and `nfet` ring ties hold |

Reading the two matches:

- **The `sg13_hv_pmos` census question the issue raised is answered.** The charge pump's
  `device_parameter_coverage` reads `nfet` 35 / 35 and `pfet` 28 / 28 (layout / reference), `W` and `L`
  compared on every MOS, `sg13g2_passive_pairing: all_devices_paired`. The drawn pfets are extracted as
  pfet and pair with the reference cards.
- **How the compare treats `cp`'s hierarchy** (`cp_bias`, `cp_leg_p`, `cp_leg_n`, `cp_dumpbuf`): the
  layout side extracts one flat circuit (63 devices), so the hierarchical reference cannot pair — the
  #347 run read that as `topology.hierarchy_mismatch`. The committed request sets
  `options.flatten_reference: true`: `klt lvs` itself collapses the 5 reference circuits into one
  (substituting every subcircuit call in place; `topology.flattened` is recorded as a warning in the
  envelope) and the compare then pairs all 63 devices. No netlist is written or edited by hand — the
  flattened form is produced by the tool from the committed `.spice`.
- **What the `match` does not verify** (each stated by a warning in the envelope, not silently dropped):
  passive `R`/`C` values are placeholder-excluded on the subckt-call reference side (the loop filter's
  caps and resistors pair on topology alone; the layout-side `R` 7021 Ohm / `C` values are recorded in
  the warnings), and MOS `AS`/`AD`/`PS`/`PD` are secondary parameters KLayout does not compare.
- The `klayout-runset` engine still mismatches for the loop filter (`lcpll_loopfilter.runset.lvs.json`,
  refreshed on the same stream): it counts the `m=12` multiplier card as one device against the drawn
  units, so its device census is not on the same footing as the curated engine's. The curated envelope
  is the per-cell verdict; the runset envelope is committed as the record of that reading.
- **Swapped-net negative controls** (`scripts/test-lvs-cells-negative.sh`): one device card of a scratch
  copy of each reference gets one net swapped (`XC2`'s `VIN` node to `VCTRL`; `XIUP_N`'s gate from `UP`
  to `DN`) and the same request flips to `mismatch` for both cells. A token-for-token net-name swap is
  deliberately not the control: it renames both sides of every connection and the comparer — which pairs
  top-level pins positionally — still matches, which is itself worth knowing about the compare.

Item 4 (top-level LVS) stays `unmet` with #37: these are per-cell compares against per-cell references,
not the integrated-top compare, and the top-level envelope (`top.lvs.json`, runset engine) is unchanged
at `mismatch` for the reference-form reasons recorded above.
