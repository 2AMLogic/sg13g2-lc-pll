# sim

Evidence and pins. See the repo README for scope.

- [`pins.json`](pins.json) — PDK, OSDI and simulator pins for the smoke bench.
- [`vco-smoke/`](vco-smoke/README.md) — smoke run of the pinned `sg13g2-vco` (`reuse.lock.json`); records are append-only.
- [`loop-model/`](loop-model/loop_model.py) — method-L linear phase-domain loop model: loop-filter sizing, f_c / PM / partial jitter over the Kvco × I_cp grid (VCO noise input is a target, not measured). [`records/`](loop-model/records/README.md): the row 5 envelope over the measured I_cp spread of [`cp-dc`](cp-dc/README.md) (`envelope.py`).
- [`corner-verification/`](corner-verification/README.md) — `klt sim` C-grid envelopes for T1 item 5 (first slice: charge pump, rows 6-7; other rows declared gaps).
- [`prescaler-g1/`](prescaler-g1/README.md) — gate G1: prescaler first-stage input capacitance / conductance at 5.0 GHz and /2 toggle limit (nominal corner only); records are append-only. Its [`prescaler_vce.request.json`](prescaler-g1/prescaler_vce.request.json) is the `klt sim` corner request for the HBT Vce check against BVCEO over the 18 supply sub-corners.
- [`prescaler-g3/`](prescaler-g3/README.md) — gate G3: /4/5 stage in both modulus states and HBT-vs-HV-MOS CML latch comparison (nominal corner only).
- [`loop-tran/`](loop-tran/README.md) — closed-loop transient: lock time and reference spur (rows 10, 9) with the real PFD/CP/filter and a behavioural VCO/divider stand-in (nominal corner only).
- [`loop-power/`](loop-power/README.md) — row 11 for the circuits that exist: prescaler + divider supply power at 5.0 GHz in, plus PFD/CP from the loop-tran record.
- [`jitter/`](jitter/README.md) — row 8 method-L jitter record with its section 4 method fields (method T not run).
- [`testbench-inventory.json`](testbench-inventory.json) / [`.md`](testbench-inventory.md) — T1 item 9 inventory (`klt signoff --attest 9`) and the per-row bench map with owner issues.
- [`lock-detector/`](lock-detector/README.md) — gate G5, lock detector half: the pinned `sg13g2-pll` PFD driving the pinned `lock_detector` at 50 MHz; delay window, LOCK trip phase errors, nominal then the C-grid through `klt sim` (batch); records are append-only.
