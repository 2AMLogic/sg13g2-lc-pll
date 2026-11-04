# loop-power row 11: stage 1 complete, 135 of 135 returned (2026-11-04, base `b669786`, issue #70)

**Result (simulated, not measured): `fail`. Stage 1 has 135 of 135 corners returned (7 owed units submitted this increment, all 7 converged). 24 of 135 divide to 50 MHz; those carry 22.41-24.07 mW (min 22.41, max 24.07, binding mos_ff/cap_typ/hbt_bcs -40 C 3.30 V, 24.07 mW) with the nominal PFD + CP + bias constant, against the 20 mW target, before the owed lock detector, reference and clock buffering. 111 of 135 do not divide or did not converge and are not-a-row-11-number. Nothing is relaxed; #97 owns the non-division and #84 the budget.**

## Stage-1 accounting (135 = 5 MOS x 3 MIM x 3 HBT x 3 T at 3.300 V)

| record | returned | divide |
|---|---|---|
| `20261103-133412-ce1d60d-dirty-stage1.md` | 40 | 0 |
| `20261103-193448-b6ec1f3-stage1.md` | 10 | 0 |
| `20261103-215804-0a8000d-stage1.md` | 21 | 5 |
| `20261104-032646-2335505-stage1.md` | 57 | 15 |
| `20261104-083547-b669786-stage1.md` (this increment) | 7 | 4 |
| **total** | **135 of 135** | **24** |

Of the 7 new corners, the 4 that divide (mos_fs/cap_wcs/hbt_bcs -40 and 27 C; mos_fs/cap_wcs/hbt_wcs -40 and 27 C) sum to 22.91-23.32 mW. The 125 C corners (mos_fs/cap_wcs/hbt_bcs, mos_fs/cap_wcs/hbt_wcs, mos_ss/cap_wcs/hbt_bcs) converge but do not divide, consistent with the earlier finding that no stage-1 corner at 125 C divides. Stage 2 (18 supply sub-corners) is unchanged: `20261103-133405-ce1d60d-dirty-stage2.md`, 5 of 18 divide, `fail`.

## Method

- `make_requests.py --missing <the four earlier stage-1 records>` regenerated exactly the 7 owed units (3 requests: `request-stage1-missing{0,1,2}.json`; requests 3-21 in the tree are leftovers from the previous increment and were not submitted). Submitted once with `klt sim --batch-set ... --max-in-flight 3 --capacity-retries 3 --budget-s 1800 --resume` on the batch fleet; all 3 requests passed within the budget. No `--dry-run`. Nothing fell back to a local grid.
- Client history, disclosed: a first client (no `--resume`) submitted jobs `klt-sim-c3cb86cf6c5f`, `klt-sim-96df5f595dc7`, `klt-sim-2be02c670fbf`; I started it detached by mistake and killed it within a minute, and its jobs were not collected. The reported run is the `--resume` client, which started the new jobs `klt-sim-4b4630ab2aff` (missing0), `klt-sim-34fad66c6d16` (missing1), `klt-sim-3a00ca345b4a` (missing2). The per-corner table is in `20261104-083547-b669786-stage1.md`.
- ngspice-46 on the fleet against the pin of 47 (`sim/pins.json`): the pin is not met.
- **Bounded exit**: one submit attempt, no retry. Nothing is owed in stage 1.
- **Owed, not zero**: lock detector, reference and clock buffering. PFD + CP + bias is the nominal constant from `sim/loop-power/records/20261103-065025-67d1431-dirty.md`. All numbers are simulated, not measured.
