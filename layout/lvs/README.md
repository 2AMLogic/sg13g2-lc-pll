# layout/lvs: T1 item 4 (LVS) attempt

**Status: item 4 stays `unmet`. No `klt lvs` envelope exists; both engines stop before a compare.**
Tracker for the current tool gap: `2AMLogic/klayout-tools#5407` (earlier gap #5402 is fixed). Nothing here is a `match`.

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
`npn13G2v` recognition remains unobserved. Item 4 stays `unmet`; `layout/drc/top.drc.json` is still
`violations`, so a `match` would not be expected even without the crash. The runset request used
absolute paths in a scratch file (`/tmp`) and is not committed; a committed runset request is added
once the tool produces an envelope.

## Not done

- No hand-written plain-element reference in the runset's dialect: that is a second, unreviewed
  netlist, and a `match` against it would not be evidence about the item-1 netlist.
- Layout state is unchanged: `layout/drc/top.drc.json` is `violations` and routing is placement-level
  (`gen_integrated.py`), so a `match` would not be expected even with the tool gap closed.
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
  `manifests/sg13g2-lc-pll.signoff.json` is not touched. `layout/drc/top.drc.json` is also still `violations`.
- Needed next (not done here; a hand-flattened reference would be a second, unreviewed netlist):
  a runset-compatible path for a hierarchical subcircuit-call reference. Tracked upstream as `2AMLogic/klayout-tools#5406` (open).
