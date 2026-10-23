# sim

Evidence and pins. See the repo README for scope.

- [`pins.json`](pins.json) — PDK, OSDI and simulator pins for the smoke bench.
- [`vco-smoke/`](vco-smoke/README.md) — smoke run of the pinned `sg13g2-vco` (`reuse.lock.json`); records are append-only.
- [`loop-model/`](loop-model/loop_model.py) — method-L linear phase-domain loop model: loop-filter sizing, f_c / PM / partial jitter over the Kvco × I_cp grid (VCO noise input is a target, not measured).
