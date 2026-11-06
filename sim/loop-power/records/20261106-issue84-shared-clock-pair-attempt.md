# issue #84: one bounded divider power-reduction attempt (shared clock-bar pair)

**Result (simulated, nominal corner only, not measured; row 11 NOT graded): the attempt cut the M/A divider from 15.78 mW to 13.02 mW and it still divides by 100, but the sum of the existing blocks is 21.14 mW, above the 20 mW budget. The attempt did not reach 20 mW.**

Baseline: `20261106-051958-0503364-dirty.md` (`scripts/run-loop-power.sh` on main at `0503364`): prescaler 6.41 + divider 15.78 + PFD/CP/bias 1.71 = 23.90 mW.

## Where the divider power goes (baseline, split supply rails, nominal)

| part | current (uA) | power at 3.3 V (mW) |
|---|---|---|
| CML-to-CMOS input stage (`cml2cmos`) | 385.0 | 1.27 |
| counters, FB flop and clock tree (everything else) | 4396.1 | 14.51 |
| divider total | 4781.1 | 15.78 (matches the official record) |

Method: the divider's top level flattened into the loop-power deck with `cml2cmos` on its own 3.3 V source (`attempts/issue-84/split-rails.sh`), same stimulus, `tran 4p 120n`, mean over 40n-120n.
The counters and clock tree dominate: about 14 `dff_tg_hv` flops each carry two local clock inverters (`XICLK`, `XICKBB`) switching at the 625 MHz post-CML clock, plus the NAND/NOR decode and the four-inverter clock buffer.

## The attempt

Every `dff_tg_hv` in `mcounter`, `acounter` and the FB flop loses its two local clock inverters; the complementary clocks CLKB and CKBB are generated once, by four parallel `inv_hv` for CLKB (driven from CKL) and four parallel for CKBB (driven from CLKB), and shared by all flops. Flop internals, the decode, M/A codes and the 625 MHz #61 timing fix are untouched. Generated on the committed netlist by `attempts/issue-84/mkvar.py`, not by a schematic edit.

| variant | divider current (uA) | divider (mW) | FB |
|---|---|---|---|
| baseline | 4781.1 | 15.78 | 50 MHz, divides |
| one inverter per shared clock net | 1480.0 | 4.88 | 0 edges, not dividing (drive too weak), not a power number |
| four parallel inverters per shared clock net | 3944.9 | 13.02 | 5 edges, 20 ns mean period, divides |

Sum with the variant: 6.41 + 13.02 + 1.71 = **21.14 mW** against 20 mW, 1.14 mW over, before the lock detector, reference and clock buffering (owed, not zero). Log: `20261106-issue84-shared-clock-pair-ngspice.txt`.

## Limits of this evidence

- **Nominal corner only.** The variant was not run at the 125 C / 2.97 V corners where #97 shows the existing divider already fails to divide; the shared clock pair adds clock skew between flops, so it is likelier to hurt than help there. It is therefore not committed as a schematic change.
- Variant netlist is a text transform of the generated netlist, not an xschem schematic; it is not LVS- or layout-checked.
- One window of 4 FB periods, as the baseline record.
- Stronger shared buffers (more parallel inverters) would give back part of the saving; this was one bounded attempt and that sweep was not run.
- The committed `design/netlist/*.spice` are electrically unchanged; this host's klt (xschem 3.4.7) adds a `** klt-netlist-inputs` header line, so `--check` reports stale. The baseline run regenerated the two netlists locally, and the change was reverted before commit; the netlist hashes in the baseline record are of the regenerated files.

## What limits the divider's power

Dynamic CV^2 f of the CMOS counters at 625 MHz and 3.3 V on the 0.5 um HV-MOS cells: the clock load of about 14 flops and the decode sit on a rail that cannot be lowered, and removing the duplicated local clock inverters recovers only 2.76 mW (17%). Meeting 20 mW by this route would also need the prescaler or PFD/CP share to fall. Fallback proposed in `spec/decision-records/DR-003-loop-power-fallback.md`.
