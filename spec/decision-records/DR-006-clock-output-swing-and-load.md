# DR-006: PLL clock output swing and load: a consumer request, stated as not met

- **Status**: proposed. Adopting 0.8 Vpp differential as a ratified target is a decision for the operator; until
  then row 15 of `spec/target-spec.md` is a request row, not a ratified target.
- **Date**: 2026-11-10
- **Decided by**: Builder agent, issue #206. Docs only: no simulation, no design change.

## Context

A downstream 10 Gb/s half-rate SerDes TX mux (`2AMLogic/sg13g2-serdes`, `spec/decisions/DR-009-mux-clock-swing.md`
and `spec/clock-requirement.md`, Level / load row; cited from the issue, not readable or verified from this repo)
needs the 5.0 GHz clock at **≥ 0.4 V per side (0.8 Vpp differential), common mode ≈ 0.6 V**, into a self-biased,
AC-coupled squarer. The requester reports that at ss / 1.08 V the mux output was not switched with 0.4 V per side, so the
real need is higher; no higher figure was given. Whether DR-009 is ratified there is not known here.

`spec/target-spec.md` had no row for the clock at an output interface. The only swing figure is I6 (VCO row 7): no
output buffer in v1, swing ≥ 0.40 Vpp differential (0.20 Vpp per side, balanced), current-limited, 204.1 µA tail,
at the tank, not graded into any load.

## Decision

1. `spec/target-spec.md` gains **row 15**, a clock-output interface row: node (not yet defined), swing per side and
   differential, common mode, load (self-biased AC-coupled squarer; **load value not provided**), supply, corner set
   (C-grid), and method owed (T). The request is recorded as the requester gave it. Figures are the requester's
   request or the VCO's target; none is simulated or measured here.
2. **Status: not met / not claimed.** I6's 0.40 Vpp differential is half of the requested 0.8 Vpp differential and is
   ungraded into any load. The row must not be read as met.
3. I6 and every other ratified row are **unchanged**. The request is not folded into I6 and I6 is not reworded to fit it.

## Consequences

- Meeting row 15 needs an **output buffer**. Per Q1 (§6) a buffer is designed here, not in the VCO. It supersedes VCO row
  7's "no output buffer" statement and re-grades VCO rows 1 and 2 (and G2's swing and startup re-check), so a record on
  `sg13g2-vco` is required (request R-VCO-3). That issue is a follow-up; this record does not file it on the VCO's behalf
  and edits no VCO file or `reuse.lock.json`.
- The **2.1 fF tank-load budget (§1) is unchanged**. The buffer input counts against it together with the prescaler
  input (the stage-2 first-stage input capacitance is already 1.837 fF at 5.0 GHz and 1.950 fF at 5.5 GHz per DR-005, so
  headroom for a buffer on the same nodes is small and unsimulated).
- Whether the ≥ 0.8 Vpp differential is attainable, with which buffer, at what power, is open: a later design and
  simulation issue, graded over C-grid with the method of §4, including the ss / 1.08 V case the requester names.
- Q1 and the Gates table get an appended entry in `spec/target-spec.md` ("Appended updates"); G1 and G2 stay open.

## Not done

No buffer is designed or simulated. No swing is graded at an output node or into the squarer. The load value is not
known. The consumer's ss / 1.08 V requirement is not quantified. Row 15 is unratified.
