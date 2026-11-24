# cp-dc I_cp request psp103_nqs preload probe 20261124-235121-d0a486d-dirty

**Result (probe, simulated not measured): the standalone I_cp corner request `sim/cp-dc/cp_icp_corners.request.json` dropped `pspnqs103va` model cards: one declared corner (TYP, 27 C, paired VDD/VHI 2.97 V) logged 92 `Unknown model type pspnqs103va - ignored` lines before the fix and 0 after adding `psp103_nqs.osdi` to `options.osdi_preload` (the only change to the request). Both runs completed (`ngspice-47 done`, measurements returned).**

- **Scope**: issue #451 accounting for the CP candidate `sim/cp-dc/cp_icp_corners.request.json`. One corner of the request's declared grid, chosen per the issue test plan (TYP at 27 C, paired VDD/VHI = 2.97 V); no other corner, netlist, measurement or option changed.
- **Method**: scratch copy of the tracked request written beside it (relative `cp_icp.cir` path preserved), `corners` trimmed to that one unit and `options.keep_artifacts` set, then `klt sim <scratch> --backend local -o <fresh dir>`. Baseline ran the request as tracked (preload `psp103.osdi` only); the repeat ran the tracked request after the one-line preload fix. Count = `Unknown model type` lines in the fresh per-corner `ngspice.log`.
- **Simulator**: `ngspice-47` (`/home/ubuntu/.local/bin/ngspice`, binary sha256 `39ca1adb826660324c3626f72bd946ec40704f0f3fc8e243c623f76e24b3eee2`), one local `klt sim` per run, `OMP_NUM_THREADS=2`.
- **PDK**: IHP-Open-PDK v0.3.0, `PDK_ROOT=/home/ubuntu/share/pdk`; model libraries, `psp103.osdi` (sha256 `2e4299c4683997e26469410dc1ab36b02ced924b1ac0972d6c4eae360e1fc796`) and `psp103_nqs.osdi` (sha256 `839b164483205601c09032951f6c41d3580f15e506dc40a7202950d3afbdfc7d`) all hash-match `sim/pins.json`.
- **Commit**: `d0a486d-dirty` of this repository (worktree of issue #451; the tracked request differs from HEAD only by this fix)
- **Host**: loom-crew-1, 2026-11-24

| run | osdi_preload | Unknown-model-type lines | run outcome |
|---|---|---|---|
| baseline | `psp103.osdi` | 92 | completed, measurements returned |
| fixed | `psp103.osdi` + `psp103_nqs.osdi` | 0 | completed, measurements returned |

The 92-line baseline count equals the archived cp-dc bench count (`20261023-171440-2d82c85-ngspice.txt`, same netlist family); it is measured here for this request, not assumed from that run.

ngspice logs: [`20261124-235121-d0a486d-dirty-icp-nqs-preload-base-ngspice.txt`](20261124-235121-d0a486d-dirty-icp-nqs-preload-base-ngspice.txt), [`20261124-235121-d0a486d-dirty-icp-nqs-preload-fixed-ngspice.txt`](20261124-235121-d0a486d-dirty-icp-nqs-preload-fixed-ngspice.txt)
