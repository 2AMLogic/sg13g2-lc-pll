# prescaler-div89 run 20261109-234530-6fbbf0e-pdk-resistors

**Result (simulated, not measured): /8 and /9 at 5.0 and 5.5 GHz over 108 chain corners (SLOW/TYP/FAST x -40/27/125 C x 2.970/3.300/3.630 V): FAIL (102 of 108 pass); modulus toggled at 16 phases of the output period over 288 async corners (5.5 GHz, 2.970 and 3.630 V): FAIL (256 of 288 pass). 38 unit(s) failed, 0 did not run and are not counted as passes. Overall: FAIL.**

- **Netlist**: `design/netlist/prescaler.spice` sha256 `41c32b6c2224936dfdbe7b1eab13efd6c16c0e27d85d360a54c5af94ebbead52` (checked against its schematic with `design/netlist.sh --check`)
- **Stimulus**: 0.4 Vpp differential sine (0.1 V per side, antiphase) on INP/INN at a common mode equal to the supply; supply, IREF (50 uA ideal) and MC ramp 0 -> final in 1 ns, the inputs follow v(vdd) (power-up start; see the comment in `div89_chain.cir`). PDK rppd/rhigh resistors (r3_cmc OSDI, end resistance and parasitic C included), process-tied to the HBT corner. No VCO, no routing parasitics.
- **Pass rule (chain)**: transient 24 ns; rising zero crossings of v(OUTP)-v(OUTN) from 6 ns; at least 8; every period within +-0.25 input periods of N x T_in (N = 8 for MC low, 9 for MC high); crossing counts at +0.1 V (rise) and -0.1 V (fall) within one of the zero-crossing count, i.e. the output swings at least 0.2 Vpp at every cycle. Nominal-only numbers are never labelled corner-bounded here.
- **Pass rule (async)**: transient 34 ns; MC is one 8 ns CMOS-level pulse rising at 8 ns + phi, phi = 0..1500 ps in 100 ps steps (the output period is 1.45-1.64 ns, so every phase of the S1/S2 swallow window is hit); every output period 8 or 9 input periods (+-0.25), the 8/9 sequence 8..8 9..9 8..8 with at most two changes and starting and ending on 8, 9-periods count within 8 ns / (9 T_in) - 1 .. 8 ns / (8 T_in) + 1, and the swing rule above. This is the asynchronous-modulus retiming check: one swallowed input cycle per prescaler period, no /10 or /17 or /8-hiccup.
- **Simulator**: `ngspice-46` on the Spot batch fleet (`environment.engine_host` = worker, c7i.8xlarge), against sim/pins.json pin 47: **mismatch (fleet ran 46)**. Jobs: `klt-sim-0f4cad8039d6`, `klt-sim-628889e3fbaf`, `klt-sim-ccec43287dae`.
- **Requests / reports**: `div89_chain.request.json` sha256 `c910fda94818ba04d2b7f5c55243ea18e356b58342af804a2dfe1c2685d4793b`, report [`20261109-234530-6fbbf0e-pdk-resistors-div89_chain.json.gz`](20261109-234530-6fbbf0e-pdk-resistors-div89_chain.json.gz) sha256 `5e98f9d331292b31a9375d554aca5ce9b1cd37e20378c6d7474ea4ea05b433a2`; `div89_async_2p97.request.json` sha256 `3a34ac585838f04c8a622d619fb544716a7e3910090801669a326038e7de9f12`, report [`20261109-234530-6fbbf0e-pdk-resistors-div89_async_2p97.json.gz`](20261109-234530-6fbbf0e-pdk-resistors-div89_async_2p97.json.gz) sha256 `45813e54ba2d36d4a6ac0554d6e450f017fa6afda1b02a85bfa2f44337ec14d7`; `div89_async_3p63.request.json` sha256 `66b705b0d684bdb8d25849bd2b326e21db02a7989eb169fd1bef90ada7a509d1`, report [`20261109-234530-6fbbf0e-pdk-resistors-div89_async_3p63.json.gz`](20261109-234530-6fbbf0e-pdk-resistors-div89_async_3p63.json.gz) sha256 `6f12cb86b22fb046c754a34ccfceda60dab9d5bee4feefb07c40b0e379106ed0`
- **PDK**: `models.pdk` sg13g2 on the fleet image; `cornerHBT.lib` staged from this host's IHP-Open-PDK v0.3.0 install (`environment.staged_model_inputs`). SLOW = hbt_wcs + res_wcs, TYP = hbt_typ + res_typ, FAST = hbt_bcs + res_bcs.
- **Commit**: `6fbbf0e-dirty` of this repository
- **Jitter / phase-noise numbers**: none (functional division only).

## Chain: ratio per corner (cells: mean output period / T_in, verdict)

| process | T (C) | vdd (V) | 5.0 GHz /8 | 5.0 GHz /9 | 5.5 GHz /8 | 5.5 GHz /9 |
|---|---|---|---|---|---|---|
| FAST | -40 | 2.970 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| FAST | -40 | 3.300 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| FAST | -40 | 3.630 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| FAST | 27 | 2.970 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| FAST | 27 | 3.300 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| FAST | 27 | 3.630 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| FAST | 125 | 2.970 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| FAST | 125 | 3.300 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| FAST | 125 | 3.630 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| SLOW | -40 | 2.970 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| SLOW | -40 | 3.300 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| SLOW | -40 | 3.630 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| SLOW | 27 | 2.970 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| SLOW | 27 | 3.300 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| SLOW | 27 | 3.630 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| SLOW | 125 | 2.970 | 8.00 pass | 9.00 pass | 10.00 FAIL: ratio 10.00..10.00 | 10.00 FAIL: ratio 9.98..10.00 |
| SLOW | 125 | 3.300 | 8.00 pass | 9.00 pass | 9.89 FAIL: ratio 9.31..9.99 | 9.97 FAIL: ratio 9.74..10.00 |
| SLOW | 125 | 3.630 | 8.00 pass | 9.00 pass | 9.78 FAIL: ratio 9.24..9.97 | 10.00 FAIL: ratio 10.00..10.01 |
| TYP | -40 | 2.970 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| TYP | -40 | 3.300 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| TYP | -40 | 3.630 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| TYP | 27 | 2.970 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| TYP | 27 | 3.300 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| TYP | 27 | 3.630 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| TYP | 125 | 2.970 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| TYP | 125 | 3.300 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |
| TYP | 125 | 3.630 | 8.00 pass | 9.00 pass | 8.00 pass | 9.00 pass |

## Async modulus: phases passing per corner (16 phases phi = 0..1500 ps; each phase is one 34 ns run graded by the async rule above)

| process | T (C) | vdd (V) | phases passing | worst phase | note |
|---|---|---|---|---|---|
| FAST | -40 | 2.970 | 16/16 | - |  |
| FAST | -40 | 3.630 | 16/16 | - |  |
| FAST | 27 | 2.970 | 16/16 | - |  |
| FAST | 27 | 3.630 | 16/16 | - |  |
| FAST | 125 | 2.970 | 16/16 | - |  |
| FAST | 125 | 3.630 | 16/16 | - |  |
| SLOW | -40 | 2.970 | 16/16 | - |  |
| SLOW | -40 | 3.630 | 16/16 | - |  |
| SLOW | 27 | 2.970 | 16/16 | - |  |
| SLOW | 27 | 3.630 | 16/16 | - |  |
| SLOW | 125 | 2.970 | 0/16 | phi=0 ps | period of 9.96,10.87,11.03,11.01,11.12,10.01,10.00,10.00,10.00,10.00,1 input periods; sequence not 8..9..8 (2 changes); 0 nine-periods outside 3..7 |
| SLOW | 125 | 3.630 | 0/16 | phi=0 ps | period of 9.91,10.20,9.90,10.06,10.01,9.98,9.94,9.95,9.97,9.83,9.28,9. input periods; sequence not 8..9..8 (2 changes); 1 nine-periods outside 3..7 |
| TYP | -40 | 2.970 | 16/16 | - |  |
| TYP | -40 | 3.630 | 16/16 | - |  |
| TYP | 27 | 2.970 | 16/16 | - |  |
| TYP | 27 | 3.630 | 16/16 | - |  |
| TYP | 125 | 2.970 | 16/16 | - |  |
| TYP | 125 | 3.630 | 16/16 | - |  |

## Supply power (prescaler + 50 uA reference)

Mean supply current over 8-24 ns (`.meas AVG i(vdd)`), power = |I| x vddv. Baseline: the pre-change /8-/10 prescaler, 6.41 mW at TYP / 27 C / 3.3 V (`sim/loop-power/records/20261106-051958-0503364-dirty.md`, window 40-120 ns, so the delta is indicative to a few hundredths of a mW). Spec row 11 allocation: <= 10 mW.

| corner | fin (GHz) | ratio | power (mW) | delta vs baseline (mW) |
|---|---|---|---|---|
| TYP / 27 C / 3.300 V | 5.5 | /8 | 6.417 | +0.007 |
| TYP / 27 C / 3.300 V | 5.0 | /8 | 6.417 | +0.007 |
| TYP / 27 C / 3.300 V | 5.0 | /9 | 6.423 | +0.013 |
| TYP / 27 C / 3.300 V | 5.5 | /9 | 6.423 | +0.013 |

Over all 108 chain corners: minimum 5.238 mW (`SLOW/novdd/125C/params:fin=5000000000,mcv=3.3,vddv=2.97`), **maximum 7.377 mW** (`FAST/novdd/-40C/params:fin=5000000000,mcv=3.3,vddv=3.63`); within the 10 mW allocation at every corner.

## Units not passing

| unit | reason |
|---|---|
| `SLOW/novdd/125C/params:fin=5500000000,mcv=0,vddv=2.97` | ratio 10.00..10.00 |
| `SLOW/novdd/125C/params:fin=5500000000,mcv=3.3,vddv=2.97` | ratio 9.98..10.00 |
| `SLOW/novdd/125C/params:fin=5500000000,mcv=0,vddv=3.3` | ratio 9.31..9.99 |
| `SLOW/novdd/125C/params:fin=5500000000,mcv=3.3,vddv=3.3` | ratio 9.74..10.00 |
| `SLOW/novdd/125C/params:fin=5500000000,mcv=0,vddv=3.63` | ratio 9.24..9.97 |
| `SLOW/novdd/125C/params:fin=5500000000,mcv=3.3,vddv=3.63` | ratio 10.00..10.01 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=0,vddv=2.97` | period of 9.96,10.87,11.03,11.01,11.12,10.01,10.00,10.00,10.00,10.00,1 input periods; sequence not 8..9..8 (2 changes); 0 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=1e-10,vddv=2.97` | period of 9.98,10.86,11.03,11.01,11.13,10.00,10.00,10.00,10.00,10.00,1 input periods; sequence not 8..9..8 (2 changes); 0 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=2e-10,vddv=2.97` | period of 9.98,10.85,11.03,11.01,11.13,10.00,10.00,10.00,10.00,10.00,1 input periods; sequence not 8..9..8 (2 changes); 0 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=3e-10,vddv=2.97` | period of 9.97,10.84,11.04,11.02,11.12,10.01,10.00,10.00,10.00,10.00,1 input periods; sequence not 8..9..8 (2 changes); 0 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=4e-10,vddv=2.97` | period of 9.97,10.81,11.06,11.03,11.09,10.03,10.01,10.00,10.00,10.00,1 input periods; sequence not 8..9..8 (2 changes); 0 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=5e-10,vddv=2.97` | period of 9.97,10.77,11.07,11.05,11.07,10.02,9.97,9.97,9.97,9.94,9.55, input periods; sequence not 8..9..8 (2 changes); 0 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=6e-10,vddv=2.97` | period of 9.97,10.70,11.10,11.08,11.05,10.04,9.97,9.97,9.97,9.94,9.53, input periods; sequence not 8..9..8 (2 changes); 0 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=7e-10,vddv=2.97` | period of 9.98,10.71,11.08,11.08,11.03,10.06,9.97,9.97,9.97,9.94,9.55, input periods; sequence not 8..9..8 (2 changes); 0 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=8e-10,vddv=2.97` | period of 9.99,10.64,11.09,11.11,11.07,10.06,9.96,9.97,9.97,9.96,9.79, input periods; sequence not 8..9..8 (2 changes); 0 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=9e-10,vddv=2.97` | period of 10.00,10.58,10.79,10.52,11.01,10.12,10.00,10.00,10.00,10.00, input periods; sequence not 8..9..8 (2 changes); 0 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=1e-09,vddv=2.97` | period of 10.00,10.52,9.77,9.89,9.98,10.46,9.60,9.93,9.99,10.00,10.00, input periods; sequence not 8..9..8 (2 changes); 0 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=1.1e-09,vddv=2.97` | period of 10.00,10.40,9.76,10.00,10.00,10.38,9.66,9.95,9.99,10.00,10.0 input periods; sequence not 8..9..8 (0 changes); 0 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=1.2e-09,vddv=2.97` | period of 10.00,10.30,9.84,10.01,10.00,10.56,10.05,9.49,9.89,9.99,10.0 input periods; sequence not 8..9..8 (4 changes); 1 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=1.3e-09,vddv=2.97` | period of 10.00,10.24,9.90,10.01,10.00,10.66,10.08,9.98,9.96,9.82,9.51 input periods; sequence not 8..9..8 (2 changes); 0 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=1.4e-09,vddv=2.97` | period of 10.00,10.19,9.94,10.01,10.01,10.74,10.03,9.97,9.97,9.96,9.82 input periods; sequence not 8..9..8 (2 changes); 0 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=1.5e-09,vddv=2.97` | period of 10.00,9.89,10.92,11.05,11.01,11.02,10.02,9.98,9.97,9.94,9.53 input periods; sequence not 8..9..8 (2 changes); 0 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=0,vddv=3.63` | period of 9.91,10.20,9.90,10.06,10.01,9.98,9.94,9.95,9.97,9.83,9.28,9. input periods; sequence not 8..9..8 (2 changes); 1 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=1e-10,vddv=3.63` | period of 9.91,10.17,9.93,10.06,9.98,9.98,9.94,9.96,9.97,9.77,9.34,9.9 input periods; sequence not 8..9..8 (2 changes); 1 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=2e-10,vddv=3.63` | period of 9.90,10.15,9.95,10.06,9.96,9.99,9.95,9.97,9.94,9.28,9.84,9.9 input periods; sequence not 8..9..8 (2 changes); 1 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=3e-10,vddv=3.63` | period of 9.91,10.06,9.94,10.05,10.79,9.32,9.83,9.95,9.97,9.86,9.94,9. input periods; sequence not 8..9..8 (7 changes) |
| `SLOW/novdd/125C/params:fin=5500000000,phi=4e-10,vddv=3.63` | period of 9.91,10.13,9.88,10.05,10.74,9.26,9.93,9.96,9.97,9.82,9.29,9. input periods; sequence not 8..9..8 (7 changes) |
| `SLOW/novdd/125C/params:fin=5500000000,phi=5e-10,vddv=3.63` | period of 9.92,10.15,9.93,10.07,9.93,10.10,9.90,9.95,9.97,9.93,9.92,9. input periods; sequence not 8..9..8 (2 changes); 1 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=6e-10,vddv=3.63` | period of 9.94,10.13,9.94,10.07,9.93,10.10,9.91,9.95,9.97,9.93,9.90,9. input periods; sequence not 8..9..8 (2 changes); 1 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=7e-10,vddv=3.63` | period of 9.94,10.12,9.94,10.07,9.93,10.10,9.91,9.95,9.97,9.94,9.88,9. input periods; sequence not 8..9..8 (2 changes); 1 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=8e-10,vddv=3.63` | period of 9.94,10.10,9.96,10.07,9.93,10.10,9.91,9.95,9.97,9.94,9.26,9. input periods; sequence not 8..9..8 (2 changes); 1 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=9e-10,vddv=3.63` | period of 9.94,10.09,9.97,10.06,9.94,10.35,9.67,9.94,9.97,9.95,9.30,9. input periods; sequence not 8..9..8 (2 changes); 1 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=1e-09,vddv=3.63` | period of 9.95,10.08,9.99,10.03,9.96,10.81,9.41,9.77,9.95,9.97,9.88,9. input periods; sequence not 8..9..8 (5 changes); 2 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=1.1e-09,vddv=3.63` | period of 9.95,10.06,10.02,9.98,10.04,10.19,9.79,9.94,9.97,9.95,9.31,9 input periods; sequence not 8..9..8 (2 changes); 1 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=1.2e-09,vddv=3.63` | period of 9.95,10.05,10.10,9.91,10.06,10.58,9.40,9.94,9.96,9.97,9.78,9 input periods; sequence not 8..9..8 (5 changes); 2 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=1.3e-09,vddv=3.63` | period of 9.95,10.01,10.25,9.80,10.06,10.76,9.68,9.51,9.94,9.97,9.94,9 input periods; sequence not 8..9..8 (4 changes); 1 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=1.4e-09,vddv=3.63` | period of 9.95,9.95,10.09,9.91,10.72,9.72,9.57,9.95,9.97,9.94,9.25,9.8 input periods; sequence not 8..9..8 (6 changes); 2 nine-periods outside 3..7 |
| `SLOW/novdd/125C/params:fin=5500000000,phi=1.5e-09,vddv=3.63` | period of 9.95,9.96,10.09,9.92,10.29,9.76,9.94,9.95,9.97,9.84,9.27,9.9 input periods; sequence not 8..9..8 (4 changes); 2 nine-periods outside 3..7 |
