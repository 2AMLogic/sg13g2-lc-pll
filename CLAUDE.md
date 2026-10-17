# sg13g2-lc-pll — agent instructions

Open-source canary block: an integer-N LC PLL on IHP SG13G2, a 130 nm SiGe
BiCMOS open PDK, built around `sg13g2-vco` and designed and verified by AI
agents. **Analog** (RF and mixed-signal loop).

- **PDK**: IHP SG13G2 (open PDK, IHP-GmbH/IHP-Open-PDK). Open-source flow:
  xschem + ngspice for design and simulation; layout, DRC, and LVS through
  klayout-tools (`klt`).
- **Integrating the tank is the point, and the risk.** This block places an
  on-chip spiral inductor and varactor inside a larger layout, next to
  switching circuits. Substrate and supply coupling from the charge pump, loop filter,
  and divider into the tank, the inductor's keep-out and fill rules, and
  extraction of the integrated loop are where the tools will be weakest.
  Grade the loop post-layout with the VCO in place, and file accordingly.
- **The prescaler is the new circuit.** Its first stage runs at the VCO
  frequency and loads a tank that `sg13g2-vco` grades unbuffered. State the
  load it presents, and re-check the VCO's swing and startup margin with
  that load before claiming the loop works.
- **Scope discipline.** The VCO comes from `sg13g2-vco` by a pinned
  reference (`reuse.lock.json`). Do not redesign it, resize it, or fork its
  netlist. Specify the interface — control window, tank-node load, supply,
  phase-noise budget — and stop; a change the VCO needs is an issue on
  `sg13g2-vco`. Below the prescaler, `sg13g2-pll` on this PDK already
  designs a phase-frequency detector, charge pump, loop filter, and divider;
  adopt them or record why not. `sg13g2-pll`'s ring-oscillator PLL is a
  different block, not a duplicate.
- **Noise needs its method.** ngspice has no periodic-noise analysis. Every
  phase-noise, jitter, or spur number states its method (transient noise,
  run length, window, estimator, or a stated linear phase-domain model with
  its inputs) next to the number. A number without its method is not a
  result.
- **Friction protocol (the canary's job)**: every time klayout-tools is
  awkward, missing a capability, or wrong for what you need, file an issue at
  `2AMLogic/klayout-tools` describing the tool gap generically — that tracker
  is scoped to the tool, so keep design-specific detail out of it and describe
  the gap, not the design.
- **Verification is the product**: no claim without a testbench. PVT corners
  on every recorded result; `sim/` results are append-only evidence. A
  simulated number is never called measured.
- Spec changes go through `spec/` with a decision record; agents do not relax
  the ratified spec to make results pass.
- **One integer-N channel at 5.0 GHz is the target.** The full band and
  fractional-N are stretches; do not let them drive the architecture before
  the target closes.

<!-- BEGIN LOOM ORCHESTRATION -->
This repository uses [Loom](https://github.com/rjwalters/loom) for AI-powered development orchestration — see the Loom repository for the full guide (roles, labels, worktrees, configuration). When installed, Loom also writes a locally-substituted copy of that guide to `.loom/CLAUDE.md`.

Work is coordinated through `loom:` labels on issues and pull requests, and the same roles run either under `loom-daemon` or by hand in an attended session — daemon mode is optional. Create the labels once with `.loom/scripts/sync-labels.sh` (an install ships `.github/labels.yml` but does not create the labels on the forge). A pull request ready for review carries `loom:review-requested`; Judge reviews it and applies `loom:pr` (approved) or `loom:changes-requested`; Doctor fixes a `loom:changes-requested` pull request and returns it to `loom:review-requested`. Only a `loom:pr` pull request gets merged, and always via this repo's merge script (`.loom/scripts/merge-pr.sh`) — never a raw forge merge command such as `gh pr merge`. Full state machine: `.loom/docs/label-state-machine.md`.
<!-- END LOOM ORCHESTRATION -->
