# FB edge-time probe, TYP 27 C 3.63 V and TYP 125 C 2.97 V (2026-11-03, base `b2f2875`, issue #97)

**Result (simulated, not measured): PARTIAL. At both corners FB is NOT a 20 ns clock: only one FB rising edge occurs in 40-120 ns, so the divide ratio is not 100. The ratio itself is not determined, the cause is not traced, no design change is made, and the issue's fix and 18-corner ACs are NOT met.**

- **Method**: `.meas tran fbr<k> when v(fb)=1.65 td=40n rise=<k>`, k = 1..8, on the stage-2 body and ramped start-up (unchanged, as `request-diag-97.json`). Run as single-corner requests on the batch fleet (`request-fbcount-97-a.json`, `-b.json`), `timeout_s` 1800. Window and transient stop are 120 ns (`4p 120n 0 4p`), so an edge after 120 ns is not seen.
- **Simulator**: ngspice-46 on the fleet against the pin of 47 (`sim/pins.json`): **the pin is not met.** Nothing was run locally.
- **Run history**: the first request (`request-fbcount-97.json`, all 4 TYP corners, `timeout_s` 600) timed out at 600 s on every unit (job `klt-sim-2183e8475037`): a **non-result**, not used below. Split into single corners with a longer timeout: 27 C 3.63 V job `klt-sim-c37b3013600b`, 125 C 2.97 V job `klt-sim-a35f1f2a7228` (a Spot interruption of the other job in the set was re-submitted once). Each corner ran once; none was repeated.

| corner | converged | fbr1 | fbr2..8 | fb min..max (V) | classification |
|---|---|---|---|---|---|
| TYP 27 C 3.63 V | yes | 83.8 ns | not reached | -0.073..3.737 | converged-no-divide-by-100; one rising edge in an 80 ns window |
| TYP 125 C 2.97 V | yes | 72.8 ns | not reached | -0.038..3.059 | converged-no-divide-by-100; one rising edge in an 80 ns window |

- **Read**: a divide-by-100 output at 5.0 GHz has a 20 ns period, i.e. 3-4 rising edges in the window. One edge means the FB period is at least ~40 ns at both corners (or FB stalls), so the counter runs at a different modulus or hangs. The `fb` swing is rail to rail in both, so FB is not stuck. This **refines** the earlier note that FB "toggles" at these corners (`20261103-issue97-divider-diag.md`): it toggles, but not at 50 MHz.
- **Not determined**: the actual ratio (needs a longer run, or a divider-internal count node), and why. The candidates in the issue (retimed flop / counter timing margin at high VDD and hot, prescaler output threshold) are neither supported nor refuted here.
- **Unchanged from the earlier record**: TYP 125 C 3.63 V is a different mechanism (cml2cmos output never goes low; FB flat).
- **Next**: (1) run these two corners to >= 400 ns with the divider count nodes probed, so the modulus is read directly; (2) fix `cml2cmos` for TYP 125 C 3.63 V; (3) the 18-corner stage-2 grid via `klt sim` on the fleet; (4) re-report nominal row-11 power against #84.
