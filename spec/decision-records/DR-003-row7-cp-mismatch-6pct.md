# DR-003: Row 7 - charge-pump up/down mismatch, proposal to relax 2 % to 6 %

- **Status**: proposed. This is a **relax-after-measured-FAIL** proposal (`2AMLogic/2am` `ratification/protocol.md` §2-3).
  It changes no ratified row until it is ratified: the PR takes the EE key (Step 5 re-derivation) and the market key,
  and only then goes to the operator. `spec/target-spec.md` is **not edited** by this PR as proposed.
- **Date**: 2026-11-06
- **Decided by**: none yet. Drafted by a Builder agent (issue #82) on the operator ruling r7-q10 (2026-11-05); the
  author session cannot hold either key.

## Context

Row 7 binds up/down mismatch to **≤ 2 %** of I_cp across [1.65 V, V_hi,req], fallback ≤ 6 %. The ratified design was
graded against that row and does not meet it (`sim/cp-mc/records/20261103-034036-59b5e16-dirty.md`). Issue #78 tried
to close it by resizing; PR #81 recorded that it cannot be closed that way. The operator ruled that 6 % goes through
the market gate rather than being settled as a preference.

## Proposal

Row 7 up/down mismatch becomes **≤ 6 % of I_cp** across [1.65 V, V_hi,req] (the compliance clause and gate G4 are
unchanged), **at a stated yield of 0.9973 (3 sigma), pooled over the C-grid**, estimator `klt yield`
(Clopper-Pearson, 95 % confidence), Monte Carlo of per-instance device mismatch only, n = 200 per corner.

On the yield target: the ratified spec states none. 0.9973 is the campaign's own choice
(`sim/cp-mc/limits-target.json`) and is kept here so that the number is not tuned to the result. **It is not met by
the point estimate today** (below). If either key wants a different target it is a change to this proposal, to be
made before the keys are applied, not after the data are read again.

## Evidence (simulated, not measured)

| | 2 % bound | 6 % bound |
|---|---|---|
| Pooled yield at 1.65 V, 33 corners x 200 samples (n = 6600) | **0.7179** [0.7069, 0.7287] | **0.9965** [0.9948, 0.9978] |
| Pooled yield at 2.00 V | 0.7353 | 0.9992 [0.9982, 0.9998] |
| Pooled yield at 2.25 V / 2.45 V | 0.6076 / 0.4391 | 0.9150 / 0.7318 |

Source: `sim/cp-mc/records/20261103-034036-59b5e16-dirty.md` and its `-yield-target.json` / `-yield-fallback.json`.
Read it as follows.

- **Measured FAIL at 2 %**: yield 0.718 at 1.65 V against a 0.9973 target; the negative control was detected.
- **At 6 % the 1.65 V point estimate (0.9965) is below 0.9973**, and the CI [0.9948, 0.9978] straddles it. The row
  would be graded `target, not met` at that yield, not closed. The record's `klt yield` fallback status is `fail`
  overall because of the 2.25 V and 2.45 V probes; those are probes above 2.00 V, not the requirement, because
  V_hi,req is unresolved (gate G4). This proposal does not close G4.
- **Why resizing failed** (`sim/cp-mc/records/20261103-a520f7c-resize-probes.md`, PR #81): XBNS and XBPA are two
  current sources in series with only the high-impedance node px between them. Their current difference lands on px
  and shifts the p-leg cascode gate, a gain of about 14 % of I_cp per micrometre of XBPA width. Every enlargement
  tried moved the nominal balance by several percent (XBNS 12u/3u: 2.449 %; XBNS 8u/2u fails 10 of 15 stage-1
  corners, worst 4.73 %). Reaching 2 % at 0.9973 needs about a 9x cut in mean-square (4.2 to 0.45 %^2), which is a
  bias-branch topology change, not a resize.

## Expected effect on row 9 (reference spur)

Row 9's ripple budget is V_r ≤ 0.52 mV peak at −50 dBc (DR-001 §Row 9). Two estimates, which disagree, both
stated:

1. **DR-001's allowance model** (V_r = 26 mV·δ, built on t_rst = 0.1·T_ref and a filter attenuation a = 0.1 that DR-001
   marks as *stated allowances, not derived*): δ = 6 % gives 1.56 mV, 3.0x the budget, i.e. about **−40.5 dBc** for
   this contribution. That is the row 9 fallback (−40 dBc), not the target.
2. **The simulated filter**: `sim/loop-model/loop-filter.json` gives |Z(50 MHz)| = 83.10 ohm (unloaded R3-C3 pole
   included), so V_r = 2·ΔI·0.1·83.10 ohm = 0.199 mV at δ = 6 % (12 µA), 0.066 mV at 2 %. Scaling the −50 dBc /
   0.52 mV point linearly (small-index FM) puts the mismatch contribution near **−58 dBc**. The largest simulated
   sample at 1.65 V was 0.259 mV, inside the budget.

The two differ by 8x because the allowance model assumed a 655 ohm effective impedance. Neither is the locked-loop
spur: that is method T on the closed loop (row 9) and remains owed. Static DC mismatch only; leakage, charge
sharing and pulse-width effects are not in either estimate. So the proposal says only that **6 % does not by itself
break the row 9 target on the simulated filter, and would on DR-001's allowance model**. The loop-closed pass decides.

## What each key rules

- **EE key**: Step 5 re-derivation of the 2 % to 6 % relaxation, including the yield statement above and the row 9
  disagreement. Tokens: `approve` / `request-changes`.
- **Market key**: whether 6 % up/down mismatch is competitive against **named public parts**. This record names
  none and does not guess; the key supplies them. Tokens: `competitive` / `adequate-for-catalog` / `uncompetitive` /
  `escalate`.

## Outcomes

- **Market key `competitive`** (EE key `approve`): the PR goes to the operator to ratify. On ratification a commit to
  this PR edits `spec/target-spec.md` row 7 (target ≤ 6 %, yield statement, fallback line removed or replaced) and
  the README index; row 7 stays `target, not met` until graded at that yield.
- **Market key `adequate-for-catalog`, `uncompetitive` or `escalate`**: **do not relax.** Row 7 stays at 2 %. Open the
  bounded CP redesign instead: single-source cascode bias, mirrors sized for 2 %, a fresh C-grid and a cp-mc re-run.
  This PR is then closed unmerged.

## Alternatives considered (from the operator's ruling, history only)

- Bounded redesign first, then this record: rejected by the operator in favour of the market gate.
- Ratify 6 % now without the keys: not available; agents do not relax a ratified row.
- Keep 2 % and state a lower yield: would be a different spec change, also a relaxation, so it needs the same gate.

## Not decided here

V_hi,req and gate G4; the loop-closed row 9 spur; the 0.9973 yield, if the keys prefer another value.
