# DR-006: PLL clock output swing and load: a consumer request, stated as not met

- **Status**: proposed. Adopting 0.8 Vpp differential as a ratified target is a decision for the operator; until
  then row 15 of `spec/target-spec.md` is a request row, not a ratified target.
- **Date**: 2026-11-10
- **Decided by**: Builder agent, issue #206. Docs only: no simulation, no design change.

## Context

A downstream 10 Gb/s half-rate SerDes TX mux (`2AMLogic/sg13g2-serdes`, `spec/decisions/DR-009-mux-clock-swing.md`
and `spec/clock-requirement.md`, Level / load row; cited via the issue and read at `f72fa11`; the consumer's own grading, not re-verified here)
needs the 5.0 GHz clock at **≥ 0.4 V per side (0.8 Vpp differential), common mode ≈ 0.6 V**, into a self-biased,
AC-coupled squarer. In the consumer's pinned bench (`sim/tx/tx_mos_mux2to1_cml.sp` at `f72fa11`, lines 70–71) `ckp` is
driven 0.4 → 0.8 V and `ckn` 0.8 → 0.4 V (0.4 Vpp per pin, 0.8 Vpp differential, 0.6 V common mode) at the mux's `ckp/ckn`
input pins, which sit on the external side of the coupling capacitors `XCca/XCcb` (lines 46 and 52) and connect to the
mux instance (line 77). The receiver is a circuit load whose equivalent 5 GHz input impedance is unspecified. The requester reports that at ss / 1.08 V the mux output was not switched with 0.4 V per side, so the
real need is higher; no higher figure was given. DR-009 is proposed there, not ratified (read at `f72fa11`).

`spec/target-spec.md` had no row for the clock at an output interface. I6 (VCO row 7) is a **target**: no output buffer
in v1, swing ≥ 0.40 Vpp differential (0.20 Vpp per side, balanced), current-limited, 204.1 µA tail, at the tank. It is a
minimum with no upper bound, so comparing it with the request does not establish a required gain or a buffer.

Historical simulations (method T, not measured) did grade tank swing with the prescaler attached: nominal 0.549–0.620 Vpp
differential (`sim/vco-prescaler-load/records/20261110-nominal-batch.md`) and 0.451–0.814 Vpp over 36 converged of 54
loaded C-grid points (`sim/corner-verification/vco-prescaler-load/records/20261110-stage2.md`). All converged points are
at f_osc 3.686–4.298 GHz, none at 5.0 GHz; the 125 °C points did not converge; the prescaler snapshot was sha256
`41c32b6c…` and the current netlist hashes `add4d3b3…`. None of this is swing at a 5 GHz output into the squarer.

## Decision

1. `spec/target-spec.md` gains **row 15**, a clock-output interface row: node (not yet defined), swing per side and
   differential, common mode, load (the consumer's self-biased AC-coupled squarer circuit; its **5 GHz input impedance is not specified**), supply, corner set
   (C-grid), and method owed (T). The request is recorded as the requester gave it. Figures are the requester's
   request or the VCO's target; none is simulated or measured here.
2. **Status: not met / not claimed.** No swing at a 5 GHz output into the squarer is graded, so no pass and no measured
   failure is claimed. The row must not be read as met. The consumer applies the swing at its mux `ckp/ckn` pins, outside the coupling capacitors, so the driver
   side owns the ≈ 0.6 V common mode (the coupling blocks DC). **Open:** the future PLL output pins, the common mode this
   block's driver must provide, and the swing it delivers into the mux input; `VOP/VON` are connected only internally
   (`XVCO` to `XPS`, `design/netlist/pll_top.spice`). The requester's 1.08 V is the receiver's supply in a coupled
   test, separate from this block's own 2.97–3.63 V grid (§5).
3. I6 and every other ratified row are **unchanged**. The request is not folded into I6 and I6 is not reworded to fit it.

## Consequences

- A buffer is a **candidate** for isolating the tank, not a demonstrated need. If adopted, per Q1 (§6) it is designed here,
  not in the VCO. It would supersede VCO row
  7's "no output buffer" statement and re-grades VCO rows 1 and 2 (and G2's swing and startup re-check), so a record on
  `sg13g2-vco` is required (request R-VCO-3). That issue is a follow-up; this record does not file it on the VCO's behalf
  and edits no VCO file or `reuse.lock.json`.
- The **2.1 fF tank-load budget (§1) is unchanged**. The buffer input counts against it together with the prescaler
  input (DR-005 records 1.837 fF at 5.0 GHz and 1.950 fF at 5.5 GHz, **historical nominal device-level estimates** from
  Im(Ydiff)/(2πf) at the prescaler's DC operating point on netlist `334d242e…`; the current netlist, `add4d3b3…`, models
  the input-stage bias resistors. The 0.263 / 0.150 fF left from 2.1 fF is for that snapshot only and is shared by routing
  and any new input. A fresh simulation is needed before it is used as design margin.)
- Whether the ≥ 0.8 Vpp differential is attainable, with which buffer, at what power, is open: a later design and
  simulation issue, graded over C-grid with the method of §4, including the ss / 1.08 V case the requester names.
- Q1 and the Gates table get an appended entry in `spec/target-spec.md` ("Appended updates"); G1 and G2 stay open.

## Not done

No buffer is designed or simulated. No swing is graded at an output node or into the squarer. The receiver's equivalent 5 GHz input
impedance is not specified, nor is its sufficient input swing (consumer DR-009 is proposed, pinned `f72fa11`). The consumer's ss / 1.08 V requirement is not quantified. Row 15 is unratified.
