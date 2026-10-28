# Characterization report (T1 item 8)

**Status: skeleton. 0 of 14 spec rows are characterized across the C-grid.**
Rows are keyed by the row number in [`spec/target-spec.md`](../spec/target-spec.md)
§2. Targets are quoted from that file (RATIFIED by DR-001), not restated or
relaxed. Every number below is **simulated, never measured**.

Method codes (spec §2): **A** arithmetic, **L** linear phase-domain model,
**T** ngspice transient, **N** ngspice `.noise`/small-signal. **C-grid** is the
135-point model grid plus 18 supply sub-corners (spec §Corner set).

"Per-corner value" is `not yet measured` wherever no C-grid envelope exists.
**Nominal** means a single typical corner (`mos_tt`, 27 °C, 3.3 V); a nominal
record is evidence of nothing about the other C-grid points and is never
reported as C-grid.

Blocking issues: #39 corner envelopes, #40 Monte Carlo, #41 post-layout.

| # | Parameter | Target (spec §2) | Per-corner value | Pass/fail vs target | Method | Citation |
|---|---|---|---|---|---|---|
| 1 | Output frequency / channel plan | 5.0 GHz, one channel | not yet measured (blocked on #39) | not graded | T (lock), A (plan) | none |
| 2 | Reference frequency | 50 MHz | not yet measured (blocked on #39); PFD re-graded at 50 MHz nominal only, diagnostic variant (gate G5) | not graded | A | `sim/pfd/records/20261023-172447-a47e23f.md` (nominal, diagnostic variant, not the adopted PFD) |
| 3 | Division ratio | N = 100 (P = 8, M = 12, A = 4) | n/a, arithmetic in spec | not graded | A | spec §2 row 3 |
| 4 | Prescaler architecture | ÷2 CML HBT first stage, ÷4/5 second stage; input load ≤ 2.1 fF | not yet measured (blocked on #39); gates G1, G2, G3 open | not graded | A (ratios), sim owed (load, speed) | none |
| 5 | Loop bandwidth, phase margin, loop-filter order | f_c in [0.5, 2.0] MHz, PM ≥ 45°, type-II third order | **Nominal, method L, simulated**: at Kvco 480 MHz/V, I_cp 200 µA, f_c = 1.000 MHz, PM = 54.8°. Over Kvco 381-606 MHz/V at I_cp 200 µA: f_c 0.816-1.227 MHz, PM 52.7-55.6°. Not evaluated per C-grid corner (blocked on #39) | nominal gate passes; C-grid not graded | L | `sim/loop-model/results/loop-model.json` (nominal-only, not C-grid) |
| 6 | Charge-pump current | I_cp 200 µA typ, range 100-400 µA | not yet measured (blocked on #39). Model-only sensitivity at I_cp 100 and 400 µA is in the citation and falls outside the f_c/PM bounds at some Kvco, as spec row 6's ±2× allowance anticipates | not graded | A | `sim/loop-model/results/loop-model.json` (nominal-only, not C-grid) |
| 7 | Charge-pump compliance and mismatch | compliance 1.65 V to V_hi,req; mismatch ≤ 2 % | **Nominal, simulated**: mismatch ≤ 2.0 % over 1.30-2.45 V; 0.274 % at 1.65 V. V_hi,req is unknown until the VCO's graded f(Vctrl) exists (gate G4) | not graded (upper bound undefined) | N (DC sweep) | `sim/cp-dc/records/20261023-171440-2d82c85.md` (nominal-only, not C-grid) |
| 8 | Integrated rms jitter | ≤ 1.0 ps | **Nominal, method L, partial, simulated**: 0.442 ps at Kvco 480 MHz/V, I_cp 200 µA, integrated 10 kHz-10 MHz, 30 points/decade, trapezoid on log f, σ_φ² = 2∫L df. Terms included: VCO target line (−105 dBc/Hz @ 1 MHz, a target, not a measurement) and R1 thermal only. Reference, PFD/CP, divider and prescaler terms are 0 (not modelled). Supply/substrate coupling not modelled. No transient-noise cross-check run | **not graded**: partial sum, so 0.442 ps is not a result against the 1.0 ps target | L | `sim/loop-model/results/loop-model.json` (nominal-only, not C-grid) |
| 9 | Reference spur | ≤ −50 dBc | not yet measured (blocked on #39) | not graded | T | none |
| 10 | Lock time | ≤ 20 µs | not yet measured (blocked on #39) | not graded | T | none |
| 11 | Loop power (excl. VCO core) | ≤ 20 mW | not yet measured (blocked on #39) | not graded | A (allocation), T/DC op | none |
| 12 | Supply plan | spec §5 | not yet measured (review row; coupling graded post-layout, blocked on #41) | not graded | review | none |
| 13 | PVT corner set | spec §Corner set | n/a, definition row | n/a | n/a | spec §Corner set |
| 14 | Signoff | DRC + LVS clean with the VCO in place; post-layout re-verified | not yet measured (blocked on #41) | not graded | tool | none |

## What this report does not claim

- No row has a C-grid envelope, so no row is reported as passing across
  corners. Monte Carlo (#40) and post-layout with the VCO in place (#41) are
  absent; spec rows 8, 9 and 12 depend on both.
- The VCO smoke record (`sim/vco-smoke/records/20261018-024845-17e49a8.md`)
  reports the pinned VCO did not oscillate in that run; it is a toolchain
  check, not a characterization input, and is not cited.
- The attestation inventory
  ([`characterization.inventory.json`](characterization.inventory.json)) cites
  no envelope: the nominal records above are not `klt` envelopes with an
  own `--check` command, so they appear here for context only.

## Filling this in

When #39, #40 and #41 land passing envelopes, replace each `not yet measured`
cell with the per-corner value (or min/typ/max plus binding corner), cite the
envelope path here and in the inventory's `citations` and `envelope_checks`,
re-run `klt signoff --attest 8`, and commit the envelope.
