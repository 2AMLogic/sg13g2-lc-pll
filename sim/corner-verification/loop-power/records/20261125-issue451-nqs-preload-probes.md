# Issue #451: NQS preload probes for the 42 loop-power requests (measured)

Method: for each request, a scratch copy reduced to its first declared corner (first temperature, first value of each param), `options.timeout_s=60`, run with `klt sim <scratch> --backend local` (ngspice-47, `PDK_ROOT=~/share/pdk`, pins per `sim/pins.json` not hash-checked on this host). Count = lines `Unknown model type pspnqs103va - ignored` in that corner's `ngspice.log`. Model parsing completes before the transient starts, so the 60 s cap truncates the transient only; every run's log reached model parsing (0 `unknown subckt`). Decks and model sections unchanged.

Before = request as on main (`psp103.osdi` + `r3_cmc.osdi`); After = `psp103_nqs.osdi` appended.

| request | before | after |
|---|---|---|
| request-bittrace-97-FAST-125-2.97.json | 2432 | 0 |
| request-bittrace2-97-SLOW-125-2.97.json | 2432 | 0 |
| request-bittrace2-97-TYP-125-2.97.json | 2432 | 0 |
| request-bittrace3-97-SLOW-125-2.97.json | 2432 | 0 |
| request-clock-97-a.json | 2432 | 0 |
| request-clock-97-b.json | 2432 | 0 |
| request-d2settle-97-FAST-125-2.97.json | 2432 | 0 |
| request-d2settle-97-TYP-27-2.97.json | 2432 | 0 |
| request-diag-97.json | 2432 | 0 |
| request-diag125-97-FAST-2.97.json | 2432 | 0 |
| request-diag125-97-SLOW-2.97.json | 2432 | 0 |
| request-diag125-97-SLOW-3.63.json | 2432 | 0 |
| request-diag125-97-TYP-2.97.json | 2432 | 0 |
| request-dtgate-97-SLOW-125-2.97-n34.json | 2432 | 0 |
| request-dtgate-97-SLOW-125-2.97.json | 2432 | 0 |
| request-edge-97-FAST-125-2.97.json | 2432 | 0 |
| request-edge-97-TYP-27-2.97.json | 2432 | 0 |
| request-fbcount-97-a.json | 2432 | 0 |
| request-fbcount-97-b.json | 2432 | 0 |
| request-fbcount-97.json | 2432 | 0 |
| request-forced-97-SLOW-125-2.97.json | 2432 | 0 |
| request-forcedprobe-97-FAST-125-2.97.json | 2432 | 0 |
| request-forcedprobe-97-SLOW-125-2.97.json | 2432 | 0 |
| request-forcedprobe-97-TYP-125-2.97.json | 2432 | 0 |
| request-forcedprobe2-97-SLOW-125-2.97.json | 2432 | 0 |
| request-modulus-97-a.json | 2432 | 0 |
| request-modulus-97-a2.json | 2432 | 0 |
| request-modulus-97-b.json | 2432 | 0 |
| request-modulus-97-b2.json | 2432 | 0 |
| request-probe-97-b.json | 2432 | 0 |
| request-probe-nominal.json | 2432 | 0 |
| request-probe-ramp.json | 2432 | 0 |
| request-slew-97-SLOW-125-2.97.json | 2432 | 0 |
| request-slew-97-TYP-125-2.97.json | 2432 | 0 |
| request-slew-97-TYP-27-2.97.json | 2432 | 0 |
| request-stage2-97-fix1.json | 2432 | 0 |
| request-state-97-a.json | 2432 | 0 |
| request-state-97-b.json | 2432 | 0 |
| request-state-97-c.json | 2432 | 0 |
| request-statesnap-97-FAST-125-2.97.json | 2432 | 0 |
| request-tclevels-97-SLOW-125-2.97.json | 2432 | 0 |
| request-tclevels-97-TYP-125-2.97.json | 2432 | 0 |
