# Testbench inventory, spec rows 1-11 (T1 item 9)

The machine-read list is [`testbench-inventory.json`](testbench-inventory.json), graded by
`klt signoff --attest 9 --inventory sim/testbench-inventory.json`. This file is the per-row map
the JSON cannot express: which bench covers which row, and which rows have no simulation bench and
who owns them. **No row is graded by any bench here**; every bench is nominal corner, simulated,
not measured. Row grading is the C-grid (#39), Monte Carlo (#40) and post-layout (#41) work.

Cold start for the whole list: `scripts/run-benches.sh` (scratch records; a bench's own script writes
the committed record). Pins: [`pins.json`](pins.json).

| Row | Parameter | Bench (script, deck) | What it does today | Missing / owner |
|---|---|---|---|---|
| 1 | Output frequency, channel | `run-loop-tran.sh`, `sim/loop-tran/` | closed loop reaches 5.0 GHz **on a behavioural VCO/divider stand-in** | lock with the real VCO, prescaler and counters: no bench. Needs the VCO's graded f(Vctrl) (gate G4, `sg13g2-vco` #50/#53) and a divider that runs at 625 MHz (#61). Corners: #39 |
| 2 | Reference frequency | none (arithmetic, DR-001) | | no simulation bench by design (method A) |
| 3 | Division ratio | `run-divider-elab.sh`, `sim/divider-elab/` | count check N = 100, 90 at a 100 MHz clock | speed: the divider does **not** divide at 625 MHz (see `sim/loop-power` record); #61 |
| 4 | Prescaler | `run-prescaler-g1.sh`, `run-prescaler-g3.sh`, `sim/prescaler-div89/` (`klt sim`) | G1 load and toggle limit (superseded /8-/10 build), G3 chain /8 and /9 plus flavour pairs, nominal; /8 and /9 at 5.0 and 5.5 GHz over 27 PVT x 3 supplies, async modulus phases, supply power (`sim/prescaler-div89/records/`) | gate G2 (VCO swing and startup with the prescaler load): `run-vco-prescaler-load.sh` (#87), nominal corner only, not yet in the attested cold start; C-grid open (OSDI varactor, klayout-tools#2511) |
| 5 | Loop bandwidth, PM | `sim/loop-model/loop_model.py` (method L), pytest | f_c and PM over Kvco x I_cp | circuit-level check: C-grid, #39 |
| 6 | Charge-pump current | `run-cp-dc.sh` | static I_up and I_dn at 200 uA nominal | trim range, corners: #39 |
| 7 | CP compliance, mismatch | `run-cp-dc.sh`, `run-pfd-sweep.sh` | static window, PFD charge vs phase | V_hi,req needs gate G4; Monte Carlo #40 |
| 8 | Jitter | `run-jitter.sh` | method L, **partial** (VCO target line + R1); method T **not run** (gate G6) | in-band terms by method N, transient-noise cross-check: no bench |
| 9 | Reference spur | `run-loop-tran.sh` | method T on v(Vctrl) at f_ref, stand-in VCO | VCO-output cross-check: no bench; #39, #40 |
| 10 | Lock time | `run-loop-tran.sh` | start at 1.65 V, stand-in VCO, real PFD/CP/filter | real divider in the loop: no bench; #39 |
| 11 | Loop power | `run-loop-power.sh` | prescaler + divider currents at 5.0 GHz in; PFD + CP from the locked `loop-tran` record | lock detector, reference and clock buffering: not in the design; the divider's number is for a chain that does not divide |

Also inventoried, **not** in the cold start: `scripts/run-vco-smoke.sh` (pin and toolchain check of the
consumed VCO; needs `openvaf-r` and the network, and its only record is a failure: the VCO did not
oscillate).

Negative controls: `test-cp-dc-negative.sh`, `test-prescaler-g1-negative.sh`, `test-loop-tran-negative.sh`,
`test-jitter-negative.sh`. `run-pfd-sweep.sh`, `run-prescaler-g3.sh` and `run-divider-elab.sh` have none yet.
