# DR-006: Retire the prescaler-g3 chain bench; keep and repair the pairs bench

- **Status**: proposed (ratified by the record PR's Judge review plus Champion/operator merge, as DR-001)
- **Date**: 2026-11-10
- **Decided by**: Builder agent (issue #178)
- **Numbering**: DR-004 is reserved by PR #46; DR-006 was the next free number in this repository's
  `spec/decision-records/` when written. It changes no ratified spec row.

## Context

`scripts/run-prescaler-g3.sh` ran two benches. The **chain** deck (`g3_chain.spice.tmpl`) drove the whole prescaler
in both modulus states and passed on f/8 and **f/10** (MC high). That was the /4/5 build. The merged prescaler is
/8 and **/9** (DR-005, `design/netlist/prescaler.spice` instantiates `div89_dm`), so the chain deck's pass rule and
its `.ic` on the old stage names (`x1.hp`, `x1.x2.mp`) no longer describe the circuit. The **pairs** deck
(`g3_pairs.spice.tmpl`) is stage-agnostic (bare HBT `cml_latch` /2 against `mos_latch` /2) and is the evidence DR-005
cites for HV-MOS /2 not reaching 5 GHz.

## Decision

1. **Retire the chain bench.** `g3_chain.spice.tmpl` and the chain half of `run-prescaler-g3.sh` are removed.
   Its successor is `sim/prescaler-div89` (`div89_chain`, 108 units over PVT and supply, PDK resistors,
   `sim/prescaler-div89/records/`), which checks the whole prescaler at 5.0 and 5.5 GHz in both modulus states on the
   right circuit. DR-002's premise (a /4/5 second stage, total /8 or /10) is superseded by DR-005; DR-002 is not
   edited.
2. **Keep the pairs bench** and load the PDK resistor models (`cornerRES.lib res_typ`, `r3_cmc.osdi`), because
   `cml_latch` and `mos_latch` now contain `rppd`/`rhigh` instances (#164).

Rejected: repairing the chain (duplicates div89 with a weaker, nominal-only grid); retiring both (loses the only
HBT-vs-MOS evidence DR-005 relies on).

## Evidence

The pairs bench with PDK resistors is the dated record under `sim/prescaler-g3/records/` (simulated, nominal corner
only, not measured). The older records `20261027-022747-9096754` (chain and pairs) and `20261103-034036-24cdbb1-dirty`
(pairs) predate the PDK resistors (ideal `R`); they are untouched and remain evidence for the circuit as it was then.

## Limits

Nominal corner only for the pairs bench; no corner grid is added (a grid would go through `klt sim`). The MOS latch is
not optimised (fixed L, three widths, ideal clock), so the result is "these HV-MOS variants do not", not "MOS cannot".
