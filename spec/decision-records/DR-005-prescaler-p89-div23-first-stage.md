# DR-005: Prescaler P = 8/9 via a ÷2/3 first stage and fixed ÷4 (stage 1: reuse check, architecture, M/A table)

- **Status**: proposed (ratified by the record PR's Judge review plus Champion/operator merge, as DR-001)
- **Date**: 2026-11-06
- **Decided by**: Builder agent (issue #158, operator ruling r7-q31). Part of #158: this record covers the reuse
  check, the architecture and the arithmetic; the simulation criteria are **not** met here (see "Not done").
- **Numbering**: DR-004 is proposed in PR #46 (P = 8/10, even N only). This record supplies the evidence that PR #46
  must be rewritten against; it does not edit DR-004.

## Context

Spec row 3 needs every integer N = 90-110; row 4 assumes P = 8/9. The built prescaler (÷2 then ÷4/5) gives 8/10
(#43), which reaches only even N (#47). r7-q31 reverses option (a) of #43 and restores contiguous N with P = 8/9.

## Reuse check (searched 2026-11-06)

- `2AMLogic/sg13g2-pll` `design/`: `div23_cell.sch` exists. Its header reads "SG13G2 3.3V thick-oxide CMOS
  throughout (sg13_hv_nmos / sg13_hv_pmos)". `sim/prescaler-g3/records/20261103-034036-24cdbb1-dirty.md` records the
  HV-MOS ÷2 failing at 2.5 GHz (12 µm) and 1.5 GHz (24 µm) at the same tail current. A 5 GHz first stage is not
  reachable with it, so it is **not adopted**. The same repo's `divider_chain` is already tracked in the spec's reuse table.
- `2AMLogic/sg13g2-serdes` `design/`: listing filtered for "div" and "23" returns nothing. No sibling builds a
  ≥ 5 GHz HBT ÷2/3.

Evidence commands: `gh api repos/2AMLogic/sg13g2-pll/contents/design --jq '.[].name' | grep -i div` and the same
against `sg13g2-serdes`.

## Decision

Architecture: **÷2/3 first stage (HBT CML, `design/cml_div23.sch` as the starting point), then fixed ÷4 (÷2·÷2)**.
Modulus low gives 2·4 = 8; one swallowed first-stage input cycle per prescaler period gives 9. The modulus signal
comes from the post-prescaler counters and must be retimed to the first stage's clock. `cml_div23` is committed
(`9096754`) but not instantiated by `design/prescaler.sch`, and no record under `sim/` simulates it.

## M, A table

N = 8·M + A (A swallow cycles at ÷9, M − A at ÷8). Generated and checked by `sim/prescaler-div89/nm_table.py`
(negative controls in `test_nm_table.py`); arithmetic, not a simulation.

| N | f_out at 50 MHz ref (GHz) | M | A | A <= M | A <= 7 | 8(M-A)+9A = N |
|---|---|---|---|---|---|---|
| 90 | 4.50 | 11 | 2 | yes | yes | yes |
| 91 | 4.55 | 11 | 3 | yes | yes | yes |
| 92 | 4.60 | 11 | 4 | yes | yes | yes |
| 93 | 4.65 | 11 | 5 | yes | yes | yes |
| 94 | 4.70 | 11 | 6 | yes | yes | yes |
| 95 | 4.75 | 11 | 7 | yes | yes | yes |
| 96 | 4.80 | 12 | 0 | yes | yes | yes |
| 97 | 4.85 | 12 | 1 | yes | yes | yes |
| 98 | 4.90 | 12 | 2 | yes | yes | yes |
| 99 | 4.95 | 12 | 3 | yes | yes | yes |
| 100 | 5.00 | 12 | 4 | yes | yes | yes |
| 101 | 5.05 | 12 | 5 | yes | yes | yes |
| 102 | 5.10 | 12 | 6 | yes | yes | yes |
| 103 | 5.15 | 12 | 7 | yes | yes | yes |
| 104 | 5.20 | 13 | 0 | yes | yes | yes |
| 105 | 5.25 | 13 | 1 | yes | yes | yes |
| 106 | 5.30 | 13 | 2 | yes | yes | yes |
| 107 | 5.35 | 13 | 3 | yes | yes | yes |
| 108 | 5.40 | 13 | 4 | yes | yes | yes |
| 109 | 5.45 | 13 | 5 | yes | yes | yes |
| 110 | 5.50 | 13 | 6 | yes | yes | yes |

21 values, 0 fail

All 21 values satisfy A ≤ M and A ≤ 7; N = 90 / 100 / 110 reproduce row 3 (M = 11, 12, 13; A = 2, 4, 6).

## Not done (criteria of #158 still open; no claim is made for them)

- ÷8 and ÷9 at 5.0 and 5.5 GHz in every `klt sim` corner, including 125 °C and 3.630 V (#97): **not simulated**.
  Until it is, the ÷2/3 stage is unproven and no corner-bounded statement exists.
- First-stage input capacitance against the 2.1 fF budget and the VCO swing/startup re-check with that load: not
  done. **The claim "the loop works" is withheld.**
- Power delta against DR-003 (prescaler allocation ≤ 10 mW): not done.
- Asynchronous modulus retiming (exactly one swallowed cycle per period): not simulated.
- `design/prescaler.sch` is unchanged; the committed netlist still implements ÷8/÷10.

These stay on #158 for follow-on increments (`sim/prescaler-div89/` deck and `klt sim` request with
`--wait-for-capacity 600`).
