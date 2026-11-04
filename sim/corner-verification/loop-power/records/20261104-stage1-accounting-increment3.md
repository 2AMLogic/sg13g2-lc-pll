# loop-power row 11: stage-1 accounting after increment 3 (2026-11-04, base `2335505`, issue #70)

**Result (simulated, not measured): INCOMPLETE. Stage 1 has 128 of 135 corners returned, 7 owed (not run locally). 20 of the 128 divide to 50 MHz; those carry 22.41-24.07 mW with the nominal PFD + CP + bias constant, against the 20 mW target, before the owed lock detector, reference and clock buffering. Row 11 stays `fail`; nothing is relaxed.**

## Stage-1 accounting (135 = 5 MOS x 3 MIM x 3 HBT x 3 T at 3.300 V)

| record | returned | divide |
|---|---|---|
| `20261103-133412-ce1d60d-dirty-stage1.md` | 40 | 0 |
| `20261103-193448-b6ec1f3-stage1.md` | 10 | 0 |
| `20261103-215804-0a8000d-stage1.md` | 21 | 5 |
| `20261104-032646-2335505-stage1.md` (this increment) | 57 | 15 |
| **total** | **128 of 135** | **20** |

Over the 20 dividing corners the sum is 22.41 to 24.07 mW (binding: mos_ff/cap_typ/hbt_bcs, -40 C, 3.30 V, 24.07 mW, from the `0a8000d` record). 108 of 128 returned corners do not divide or did not converge and are not-a-row-11-number; this is the same non-division as #97 (design finding), and #84 owns the budget. The dividing corners are all at -40 C or 27 C; none at 125 C.

## Owed (7 units, not run)

`mos_ss/cap_wcs/hbt_bcs` 125 C; `mos_fs/cap_wcs/hbt_bcs` -40, 27, 125 C; `mos_fs/cap_wcs/hbt_wcs` -40, 27, 125 C. `make_requests.py --missing <all four stage-1 records>` regenerates exactly these.

## Method

- `make_requests.py --missing <the three earlier stage-1 records>` wrote 22 per-shard requests (64 units, at most 5 per request; `--max-units-per-job` is not applied under `--batch-set`, klayout-tools #4889 / #4885). Submitted with `klt sim --batch-set request-stage1-missing{0..21}.json --max-in-flight 4 --capacity-retries 3 --budget-s 2400 -o <dir>` on the batch fleet. Nothing fell back to a local grid.
- The first client (launched with `--dry-run` by mistake in my command line, which nevertheless launched real fleet jobs, a tool quirk) was killed by the host's 10-minute background limit after 4 requests had passed; I restarted it with `--resume`. Resume started new jobs for the in-flight requests (job ids in the record). The second client ran its 2400 s budget plus margin (about 48 min, 03:20 UTC) and was then stopped.
- Per request: 17 passed, 2 errored but returned 3 corners each (in request 7 the errored corner is mos_sf/cap_bcs/hbt_bcs -40 C), and 3 requests (19, 20, 21; the small tail requests holding the 7 owed units) had not returned corners when the budget ended (2 launched and running, 1 never launched). The per-corner table and job ids are in `20261104-032646-2335505-stage1.md` (its Method line names `request-stage1.json`; the requests were `request-stage1-missing*.json`).
- ngspice-46 on the fleet against the pin of 47 (`sim/pins.json`): the pin is not met.
- **Bounded exit**: this increment returned 57 new corners (71 -> 128), above the 20-corner stall threshold, so no stall signal. 7 units are owed; a next increment should be the 7 units only (3 requests) and is a small fleet cost.
- **Owed, not zero**: lock detector, reference and clock buffering. PFD + CP + bias is the nominal constant from `sim/loop-power/records/20261103-065025-67d1431-dirty.md`. All numbers are simulated, not measured.
