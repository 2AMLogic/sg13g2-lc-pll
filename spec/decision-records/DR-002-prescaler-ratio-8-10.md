# DR-002: Prescaler ratio P = 8/10 (supersedes DR-001 Rows 3 and 4)

- **Status**: proposed. Ratified when the operator merges this record after the
  EE and market key reviews have run as input (ratification protocol, as in
  DR-001). Those reviews are not yet recorded here.
- **Date**: 2026-10-28
- **Decided by**: operator ruling on issue #43 (2026-10-28, option a), written
  up by Builder agent.
- **Supersedes**: DR-001 Row 3 (divide ratio) and Row 4 (prescaler ratio).
  DR-001 is append-only and is left unchanged.

## Context

DR-001 Row 4 and `spec/target-spec.md` rows 3 and 4 state a fixed ÷2 CML first
stage followed by a ÷4/5 dual-modulus stage, "so P = 8/9". These do not
compose. The ÷4/5 stage swallows one cycle of *its own* input, which is the
÷2 output at 2.5 GHz; one such cycle is two VCO cycles. The total is therefore
÷8 (stage in ÷4) or ÷10 (stage in ÷5), not ÷8 or ÷9.

Arithmetic: 2 × 4 = 8; 2 × 5 = 10.

Consequence for Row 3: with P = 8/10 the pulse-swallow count is
N = 8·(M − A) + 10·A = 8M + 2A, with A ≤ M. Only even N are reachable.
DR-001's claim that "every integer in 90-110 is reachable" is false for this
architecture.

## Decision

Option (a) of issue #43: keep the fixed ÷2 followed by the ÷4/5 stage and
restate the prescaler as **P = 8/10**, N = 8M + 2A (even N only).

- Row 3: N = 8M + 2A, A ∈ [0, 3] (2A covers every even residue mod 8), A ≤ M,
  M ≥ 7. Target N = 100 is unchanged: M = 12, A = 2 (96 + 4). Stretch band
  90-110 covers even N only: N = 90: M = 11, A = 1; N = 110: M = 13, A = 3.
  Odd N in the band are not reachable.
- Row 4: P = 8/10. The prescaler output at 5.5 GHz is still 5.5/8 =
  687.5 MHz at ÷8 and 5.5/10 = 550 MHz at ÷10, so the 687.5 MHz bound used for
  the `sg13g2-pll` divider closing margin is unchanged (worst case is ÷8).
- **Unchanged**: the architecture, the VCO tank-node load budget, and gates
  G1 and G3.

Options not taken: (b) a ÷2/3 first stage so P = 8/9 holds (contradicts "fixed
÷2", puts swallow logic in the tank-rate stage and risks swing and startup
margin); (c) a different split with the swallow in a stage clocked at the VCO
rate (new architecture, most redesign, nothing gained for N = 100).

## Evidence

Issue #31 measured the whole prescaler at ÷8 (modulus control low) and ÷10
(modulus control high) in `sim/prescaler-g3/`, at the nominal corner only,
**simulated, not measured**. That evidence is in PR #44 and is **not yet on
`main`**; the operator's ruling asks for it to land on `main` and be cited
here. Until PR #44 merges, this record cites it by PR only. Replace this
paragraph with the merged path and commit when it lands.

## Consequences

- Rows 3 and 4 of `spec/target-spec.md`, and the README target table, now read
  P = 8/10 and even N.
- Any downstream counter design (M and A counters) uses A ≤ 3 and the 2-VCO-
  cycle weight per swallowed prescaler cycle.
- Gates are unchanged; no row is measured.
