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

## Update, stage 2 (issue #158, appended; the sections above are unchanged)

The "Not done" list above is updated here by appending. Records are under `sim/prescaler-div89/records/`, id
`20261106-222812-0ffb789` (commit `0ffb789`); all results are simulated, not measured.

- **Design**: `design/div89_dm.sch` (new) puts `cml_div23` on the tank inputs, then two `div2_cml_ls` /2 stages;
  `M = MC AND S1 AND S2` (`S1` level-shifted by a `cml_ef`, two `cml_and2` levels, then the existing `mc_conv` +
  `cml_ef` for MC). `design/prescaler.sch` instantiates it in place of `div2_cml` + `div45_dm`; both are left in the
  tree, unused. `design/netlist/prescaler.spice` and `pll_top.spice` regenerated with `klt netlist`
  (`design/netlist.sh --check` passes). No device was resized: the cells are the committed ones.
- **/8 and /9 at 5.0 and 5.5 GHz in every `klt sim` corner**: 108 of 108 units pass (SLOW/TYP/FAST x -40/27/125 C x
  2.970/3.300/3.630 V, so 125 C / 3.630 V of #97 and -40 C are in), measured period 7.999-9.000 input periods against
  8 or 9. Stimulus, pass rule and swing threshold (>= 0.2 Vpp at every cycle) are in the record. Corner-bounded for
  this grid, ideal stimulus and ideal resistors, **no VCO and no layout**.
- **Modulus retiming**: MC pulsed at 16 phases (100 ps steps) of the output period at 5.5 GHz, 288 units (9 PVT x
  2 supplies x 16): 288 of 288 give an 8..8 9..9 8..8 period sequence, no /10, /17 or hiccup.
  **Limit of that statement**: the stimulus is an ideal CMOS-level pulse. In the PLL the MC comes from counters
  clocked by this prescaler's own output, so its edges sit at a fixed delay after an output edge; the run covers
  every phase, so it covers that delay, but it does not model the counter's own timing.
- **Input capacitance**: 1.837 fF at 5.0 GHz and 1.950 fF at 5.5 GHz differential, nominal corner, device level
  (`...-cin.md`), against 2.1 fF device plus routing. It is **0.46 fF (34 %) higher** than the /8-/10 build (1.373 fF)
  because the followers drive four latch clock pairs, not two. Under the budget at device level; only 0.15 fF is left
  for routing at 5.5 GHz. Corners not simulated.
- **VCO swing and startup with this load: not re-checked here.** `sim/vco-prescaler-load` needs `openvaf-r`, which
  the worker host does not have. Filed as a follow-up (#160); **the claim "the loop works" stays withheld.**
- **Power**: 6.435 mW (/8) and 6.441 mW (/9) at TYP / 27 C / 3.3 V against 6.41 mW for the /8-/10 prescaler in
  `sim/loop-power/records/20261106-051958-0503364-dirty.md` (+0.03 mW, different averaging windows); maximum over the
  108 corners 7.355 mW (FAST, -40 C, 3.630 V, 5.5 GHz, /9), inside the 10 mW prescaler allocation of row 11. DR-003 is
  unaffected: the prescaler share does not move.
- **Failed run kept in the trail**: the first corner run (job `klt-sim-3a33c3ccd28e`, decks with the sources applied at
  t = 0) errored on 4 of 108 units, FAST / 125 C / 3.630 V ("timestep too small" in the operating point). A local probe
  showed the same failure at 110 C but not at 100 or 120 C, and the pre-change netlist converged at that corner:
  a start-up convergence artefact. The decks now ramp supply, IREF and MC over 1 ns and the divider divides from the
  ramped start at that corner. This is a bench change, not a circuit change.

Still not done: the VCO re-check above; the routing capacitance in the tank load; Monte Carlo; noise and jitter of
the first stage; layout.

## Update, stage 3 (PR #161 ratification send-back, appended; the sections above are unchanged)

Appended after both hand-run ratification keys at `b31d51ee` asked for changes (EE `request-changes`, market
`uncompetitive`). All results are simulated or logic-level, not measured.

- **Swallow counter widened to 3 bits (the blocking finding).** At stage 2 `acounter` was still 2 bits (A in [0, 3])
  and `pll_top` still tied M = 12, A = 2, the P = 8/10 code. With P = 8/9, N = 8 M + A, so that tie gave **N = 98
  (4.90 GHz)**, not 100, and only 10 of the 21 values in 90-110 were reachable (N = 100 and 110 were not). The stage-2
  text above ("the design swap is done") covered the prescaler only; it did not cover the counter. Now:
  `design/acounter.sch` is a 3-bit saturating down counter (A0..A2, state s0..s2, registered MC), `divider` gains an
  `A2` pin, and `pll_top` ties **M = 12, A = 4 (N = 100)**. `design/netlist/{divider,pll_top}.spice` are regenerated
  with `klt netlist` (`design/netlist.sh --check` passes). The adopted `sg13g2-pll` cells are unchanged (one extra
  `dff_tg_hv`, `inv_hv`, `nand3_hv`, `nor2_hv` and `nand2_hv` instances).
- **Evidence for the counter, at logic level.** `sim/prescaler-div89/test_divider_code.py` reads the committed
  `pll_top.spice` and checks, from the netlist: the tied code is M = 12, A = 4; every N in 90-110 has a legal code
  (A <= M) with the widths present in the netlist; and a zero-delay boolean model of the `acounter` gates, parsed from
  the netlist, holds MC high for exactly A clocks after a load for every A in 0..7 from every pre-state, then holds at
  zero. This is **not a timing or corner result**. Divider decks (`sim/divider-elab/`) are re-tied for the new pin
  list and codes (N = 100: A = 4; 90: A = 2; 110: A = 6; extremes A = 0 and A = 7, N = 96 and 103) and the count
  scripts now use N = 8 x clocks + MC-high. Re-run, record `sim/divider-elab/records/20261108-044535-b31d51e-dirty.md` (simulated, **nominal corner only**, ideal
  stimulus, no layout, no prescaler in the loop): FB divides to the expected N at 625 and 687.5 MHz through the real
  `cml2cmos` for N = 100 (A = 4), A = 0 (N = 96) and A = 7 (N = 103), and the ideal-clock control for N = 100; the 100 MHz
  count check gives N = 100 and N = 90 (A = 2). Other codes in 90-110 (N = 110 is elaborated only) rest on the
  logic-level test. The record is stamped `-dirty` (run before the commit). **No corner other than nominal**, so the
  stage-2 corner evidence for the counters is not extended to the 3-bit one. Three-bit next-state logic is three gates deep, as the 2-bit logic was.
- **HBT Vce-versus-BVCEO stress check: not graded for the new netlist.** The re-run
  (`sim/prescaler-g1/records/20261106-224822-cf0dede-dirty-vce.md`) did not converge in 18 of 18 corners, because
  the bench `.ic` in `sim/prescaler-g1/prescaler_vce.cir` still names `x1.x2.mp` / `x1.x2.mn`, instances that the
  `div89_dm` hierarchy removed. It is a stale bench, not a circuit finding, and no stress number exists for this
  netlist: **the stage-2 power and swing statements above say nothing about |Vce| against the 2.2 V BVCEO minimum.**
  Tracked in #162 (bench fix and re-grade). Not done.
- **Spec row 4** is brought into line by an appended update in `spec/target-spec.md` (see its "Appended updates"
  section), not by editing the ratified text.

Still not done, in addition to the list above: corner evidence (anything but nominal) for the 3-bit `acounter`, the
Vce stress grade (#162).
