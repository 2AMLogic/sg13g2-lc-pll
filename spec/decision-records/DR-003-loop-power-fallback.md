# DR-003: Loop power (spec row 11) - propose the named <= 30 mW fallback

- **Status**: proposed. **Not ratified.** Needs the EE and market keys and the operator. Agents do not relax the ratified spec; `spec/target-spec.md` is unchanged by this record.
- **Date**: 2026-11-06
- **Decided by**: Builder agent (issue #84)

## Context

Row 11 sets loop power (excluding the VCO core) at <= 20 mW with a named fallback of <= 30 mW. Once the divider really divided (#61), its power rose from 8.48 to 14.89 mW (15.78 mW on main at `0503364`), and the sum of the circuits that exist went over budget. Issue #84 was ruled "fix the design, not the spec" with one bounded power-reduction attempt, and this record only if the attempt failed.

## Evidence

`sim/loop-power/records/20261106-051958-0503364-dirty.md` (baseline, 23.90 mW) and `sim/loop-power/records/20261106-issue84-shared-clock-pair-attempt.md` (best attempt, 21.14 mW). Both simulated, nominal corner only, row 11 not graded.

## Proposal

Ratify row 11 at <= 30 mW (the fallback the row already names), keeping the 20 mW target as the stretch. The attempted reduction is 2.76 mW at nominal, leaves the sum 1.14 mW over 20 mW, is untested at the 125 C corners, and the lock detector, reference and clock buffering (allocated <= 4 mW) are still owed on top.

## Limits

One bounded attempt, nominal corner, text-transformed netlist. It shows that this attempt fell short, not that 20 mW is unreachable (a lower-swing or lower-frequency clock tree, or re-splitting the prescaler share, were not tried).

## Not decided here

Any change to the allocation split, and any other row.
