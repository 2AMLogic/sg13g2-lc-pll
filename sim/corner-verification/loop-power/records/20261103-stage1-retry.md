# loop-power C-grid stage 1, retry attempt (2026-11-03, base `7ad7c83`)

**Result (simulated, not measured): no new corners. Stage 1 is still INCOMPLETE (40 of 135 from `20261103-133412-ce1d60d-dirty-stage1.md`); no row 11 number comes from stage 1.**

- **Method**: `klt sim request-stage1.json --backend batch --max-units-per-job 5 --max-concurrent-jobs 4 --wait-for-capacity 120 --budget-s 520`, ngspice-46 on the fleet (pin is 47, `sim/pins.json`: **the pin is not met**). Nothing ran on the dispatch host; no local fallback.
- **Outcome**: 4 of 27 shards launched in the 520 s budget (`klt-sim-01278d6b2fca`, `klt-sim-9fc584fa7604`, `klt-sim-8382612509df`, `klt-sim-5425bb8a7701`). Two were `interrupted` by the Spot fleet (`01278d6b2fca` after 277 s, `5425bb8a7701` after 431 s); the other two were still `running` when the budget ended, and no corner artifacts came back. `klt sim` reported a launch rate of 0.3 jobs/min and an ETA of 1 h 8 m for the remaining 23 shards, beyond this session.
- **Not a pass**: the row 11 verdict stays that of `20261103-133405-ce1d60d-dirty-stage2.md` (`fail`, 5 of 18 corners divide, 18.63-19.96 mW before the owed lock detector, reference and clock buffering). Owed, not zero.
- The remaining stage 1 corners are owed to a later fleet attempt (`--resume`), not run locally.
