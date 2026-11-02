# sim

Evidence and pins. See the repo README for scope.

- [`pins.json`](pins.json) — PDK, OSDI and simulator pins for the smoke bench.
- [`vco-smoke/`](vco-smoke/README.md) — smoke run of the pinned `sg13g2-vco` (`reuse.lock.json`); records are append-only.
- [`loop-model/`](loop-model/loop_model.py) — method-L linear phase-domain loop model: loop-filter sizing, f_c / PM / partial jitter over the Kvco × I_cp grid (VCO noise input is a target, not measured).
- [`prescaler-g1/`](prescaler-g1/README.md) — gate G1: prescaler first-stage input capacitance / conductance at 5.0 GHz and /2 toggle limit (nominal corner only); records are append-only.
- [`prescaler-g3/`](prescaler-g3/README.md) — gate G3: /4/5 stage in both modulus states and HBT-vs-HV-MOS CML latch comparison (nominal corner only).
