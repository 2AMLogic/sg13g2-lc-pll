# sg13g2-lc-pll

An integer-N LC phase-locked loop on
[IHP SG13G2](https://github.com/IHP-GmbH/IHP-Open-PDK), a 130 nm SiGe BiCMOS
open PDK, built around the program's LC VCO,
[sg13g2-vco](https://github.com/2AMLogic/sg13g2-vco) — designed by AI agents
driving [klayout-tools](https://github.com/2AMLogic/klayout-tools) and the
open-source xschem + ngspice flow.

**Status: just opened, specification phase.** Nothing is designed yet.

**Built agent-native.** Every specification, decision record, testbench, and
line of documentation here is produced by AI agents working from a ratified
spec and an append-only evidence trail — not human-authored work that agents
merely assisted with. Verification is the product: every claim traces to a
recorded result under PVT corners. Where the agents hit friction with the
open-source tooling — most often
[klayout-tools](https://github.com/2AMLogic/klayout-tools) — that friction is
filed as a public issue against the tool itself, so the fix benefits everyone
using SG13G2, not just this repo.

## Why this block, on this PDK

`sg13g2-vco` is a free-running oscillator: a cross-coupled SiGe HBT pair on
an LC tank, tuned by a MOS varactor, ratified for a 4.5–5.5 GHz band. An
oscillator becomes a clock only when a loop locks it. This repo closes that
loop, and in doing so it puts an on-chip spiral inductor and its varactor
inside a larger layout, next to switching circuits.

That integration is the stress. The inductor is drawn in the PDK's thick
top metals; around it the loop adds a charge pump, a loop filter of large
capacitors, a divider, and digital switching, all of which couple into the
tank through the substrate and the supplies. Keep-out zones, guard rings,
fill rules around the inductor, and post-layout extraction of the whole
loop are where the tools will be tested. The other new circuit is the
**prescaler**: the first divider stage runs at the VCO frequency, several
times faster than anything the program's ring-oscillator PLLs divide, and it
loads a tank that `sg13g2-vco` grades without a buffer.

## Scope

- **In scope**: the phase-frequency detector, charge pump, loop filter,
  high-speed prescaler, programmable divider, lock detector, the VCO output
  buffer if one is needed, and the integrated layout with the VCO.
- **Not in scope**: the VCO itself. It is consumed from `sg13g2-vco` by a
  pinned reference. This repo specifies the interface to it — tuning
  window, load on the tank nodes, supply, phase-noise budget — and stops.
  A change the VCO needs is raised there, not patched here.
- **Same-PDK siblings**: `sg13g2-pll` designs a phase-frequency detector,
  charge pump, loop filter, and divider chain on this PDK around a ring
  oscillator. Its sub-blocks are candidates to adopt below the prescaler;
  the two PLLs are different blocks, not duplicates.

## Interface to sg13g2-vco (as ratified there, as targets)

| Item | sg13g2-vco's ratified target | What this loop must provide |
|---|---|---|
| Band | 4.5–5.5 GHz | a divide ratio covering the band from the chosen reference |
| Tuning | ≥ 15% across 0.0–3.3 V; Kvco graded over a 1.65–3.30 V control window | charge-pump output compliance across the control window |
| Core supply | 3.3 V ±10% | a supply plan that keeps loop noise off the core rail |
| Phase noise | ≤ −105 dBc/Hz at 1 MHz offset (target) | a loop bandwidth that suppresses the rest |
| Output | differential at the tank nodes, no output buffer in v1 | a buffer or prescaler input whose load is stated and graded |

These are `sg13g2-vco`'s targets, not measured values. If that repo's
spec changes, this table follows it.

## Target specification (DRAFT — engineering to ratify, see issue #2)

| Parameter | Target | Fallback | Stretch |
|---|---|---|---|
| Output frequency | 5.0 GHz, within the VCO's ratified band | one fixed channel | full 4.5–5.5 GHz band |
| Reference input | 50 MHz | 100 MHz | 25 MHz |
| Division | integer-N, programmable | fixed N | fractional-N |
| Integrated rms jitter (simulated) | ≤ 1 ps, 10 kHz–10 MHz | ≤ 2 ps | ≤ 0.5 ps |
| Reference spur | ≤ −50 dBc | ≤ −40 dBc | ≤ −60 dBc |
| Lock time | ≤ 20 µs | ≤ 50 µs | ≤ 10 µs |
| Power (loop, excluding the VCO core) | ≤ 20 mW | ≤ 30 mW | ≤ 10 mW |
| Signoff | DRC + LVS clean with the VCO in place, post-layout re-verified | — | — |

Maturity ladder: spec ratified → VCO interface agreed with `sg13g2-vco` →
prescaler simulated across PVT → loop simulated across PVT → integrated
layout DRC/LVS-clean → post-layout re-verification → shuttle seat → measured
silicon. **Current position: pre-spec.**

## Repo layout

```
spec/          ratified spec + decision records
design/        schematics / netlists (xschem)
sim/           testbenches + PVT corner results (ngspice)
layout/        GDS + DRC/LVS reports (klayout-tools driven)
measurements/  silicon characterization (empty until tape-out)
```

## License

Apache License 2.0 — see [LICENSE](LICENSE).
