# DR-002: Gate G3 - second-stage device flavour (HBT CML)

- **Status**: proposed (ratified by the record PR's Judge review plus Champion/operator merge, as DR-001)
- **Date**: 2026-10-27
- **Decided by**: Builder agent (issue #31)

## Context

Spec row 4 leaves the /4/5 stage's device flavour (HBT vs HV MOS CML at 2.5-2.75 GHz) to "design time"
(gate G3). This record resolves that gate only; it changes no ratified row.

## Decision

The /4/5 stage is built from `npn13G2v` CML (`design/div45_dm.sch` and its cells).

## Evidence

`sim/prescaler-g3/records/20261027-022747-9096754.md` (simulated, **nominal corner only**: `hbt_typ`/`mos_tt`,
27 C, 3.3 V; ideal resistors). The whole prescaler divides by 8 (MC low) and by 10 (MC high) at every swept
VCO-side frequency from 5.0 to 12.0 GHz, i.e. the /4/5 stage works at the 2.5 and 2.75 GHz clocks with
margin. A bare two-latch /2 at the same 100 uA tail and 2.4 kohm loads divides to at least 6 GHz in HBT, and
only to 2.0 GHz (W = 12 um), 1.0 GHz (24 um) and not at all (48 um) in `sg13_hv_nmos` at fixed L = 0.45 um.

## Limits

One corner. The MOS circuit was not optimised (no peaking, fixed L, three widths, ideal clock) and a MOS stage at a
multiple of the current may reach 2.75 GHz; the record does not test that. The choice is therefore "HBT meets
the row at the same current; the HV-MOS variants tried do not", not "MOS cannot". C-grid margin is owed to #39.

## Not decided here

The ratio: a fixed /2 then /4/5 gives /8 or /10, not /8 or /9 (issue #43).
