# DR-004: Prescaler first stage becomes ÷2/3 (finding on DR-001 Rows 3 and 4; stretch value kept)

- **Status**: proposed; **design and evidence pending (#158)**. Ratified only
  when the operator merges this record after #158's design and full-PVT
  evidence land and the EE and market key reviews have run again on the
  resulting head (ratification protocol, as in DR-001).
- **Date**: 2026-10-28; rewritten 2026-11-06 under operator ruling
  r7-q31 (fleet:decide round 20261106-r7).
- **Decided by**: operator ruling on issue #43 (option a, 2026-10-28),
  **replaced** by ruling r7-q31 (2026-11-06) after the keys at `eecb3f8`
  (EE approve, market escalate). Written up by Doctor agent.
- **Supersedes**: nothing yet. DR-001 is append-only and is left unchanged.
  Once #158 lands, this record supersedes DR-001 Row 4 (the prescaler stage
  split) only. DR-001 Row 3's stretch value (every integer N in 90-110) is
  **kept, not relaxed**.

## Finding

DR-001 Row 4 and `spec/target-spec.md` rows 3 and 4 state a fixed ÷2 CML first
stage followed by a ÷4/5 dual-modulus stage, "so P = 8/9". These do not
compose (#31, #43). The ÷4/5 stage swallows one cycle of *its own* input,
which is the ÷2 output at 2.5 GHz; one such cycle is two VCO cycles. The total
is ÷8 (stage in ÷4) or ÷10 (stage in ÷5), not ÷8 or ÷9.

Arithmetic: 2 × 4 = 8; 2 × 5 = 10.

Consequence: with P = 8/10 the pulse-swallow count is N = 8M + 2A, and only
even N are reachable. DR-001's claim that "every integer in 90-110 is
reachable" is false for the fixed-÷2 architecture. This error stays recorded.

## Decision

The first stage becomes a **÷2/3 dual-modulus stage at the VCO rate**, so the
swallowed cycle is one VCO-rate-stage input cycle and the prescaler is
**P = 8/9**, restoring contiguous N over 90-110.

- **Stretch value kept**: DR-001's stretch (4.5-5.5 GHz in 50 MHz steps, every
  integer N = 90-110) is not relaxed. The operator rejected the even-N-only
  alternative (100 MHz steps): the market key rated it `adequate-for-catalog`,
  not `competitive`, against ADF4106-class parts with contiguous N. That
  choice replaces option (a) on #43.
- **Target unchanged**: N = 100 at 5.0 GHz from a 50 MHz reference.
- **Status of rows 3 and 4**: the exact stage split that yields P = 8/9, the
  A/M ranges and the worked N = 90/100/110 decompositions are **pending #158**.
  Until it lands, rows 3 and 4 carry a pending marker, not an even-N value and
  not the DR-001 "÷2 then ÷4/5" text. The composition must be checked
  arithmetically in #158 before it is written into the spec, because the
  DR-001 error was exactly an unchecked composition.
- **Prescaler output bound**: ≤ 687.5 MHz at 5.5 GHz (5.5/8) is unchanged for
  the `sg13g2-pll` divider closing margin, if the final split keeps ÷8 as the
  smallest modulus.
- **Risk to carry into #158**: a ÷2/3 first stage puts swallow gating at the
  VCO rate, so the VCO tank-node load (≤ 2.1 fF, gate G1), swing and startup
  margin, and gate G3 must be re-checked with the new first stage. Any change
  the VCO needs is an issue on `sg13g2-vco`, not an edit here.

Options not taken: (a) keep the fixed ÷2 → ÷4/5 and restate P = 8/10, even N
only (the previous text of this record; rejected by r7-q31); (c) a different
split with the swallow elsewhere (more redesign, nothing gained for N = 100).

## Evidence

None for the new first stage; it is **pending #158** (design and full-PVT
simulation). Everything below concerns the *current* fixed-÷2 netlist and
shows ÷8 and ÷10, not ÷8/9.

Issue #31 simulated the whole prescaler at ÷8 (modulus control low) and ÷10
(modulus control high) at 5.0-12.0 GHz input, nominal corner only,
**simulated, not measured**. The record that matches the netlist on `main` at
the time of writing (`design/netlist/prescaler.spice`, sha256 `326144e4…`,
from commit `8b5e0e2`) is
`sim/prescaler-g3/records/20261103-034036-24cdbb1-dirty.md`. It was run from a
dirty tree on top of `24cdbb1`, and its pin check reads
`ngspice-46 != pinned 47 (mismatch)`, so the simulator was unpinned. The
earlier record `sim/prescaler-g3/records/20261027-022747-9096754.md` is
append-only history for an earlier netlist and is corroboration only. Neither
covers other corners, supply or temperature, so no gate closes here.

## Consequences

- Rows 1, 3 and 4 of `spec/target-spec.md` and the README target table carry
  a pending marker pointing at this record and #158; DR-001's stretch value is
  shown as kept.
- The merged divider (`design/README.md`) implements N = 8M + 2A for the
  current ÷8/÷10 prescaler. It does not match the P = 8/9 decision and will be
  revised with #158; it is not edited beyond correcting its pointer here.
- Gates are unchanged; no row is measured. Re-run both keys and operator
  ratification after #158.
