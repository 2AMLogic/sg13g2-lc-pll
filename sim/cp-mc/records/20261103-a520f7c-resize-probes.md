# cp-mc resize probes for issue #78 (20261103, commit a520f7c)

**Result (simulated, not measured): no resize of the bias branch that was tried reduces the 1.65 V mismatch without breaking the C-grid compliance, so the design is left unchanged and this is acceptance criterion (b).** The `scripts/run-cp-attr.sh` attribution (`20261103-053307-b9dc8bb-dirty-attribution.md`) names XBNS as the dominant random contributor at 1.65 V (66 % of the all-on random mean-square; XBPA a further 8 %). XBNS and XBPA are unmultiplied 4u/1u devices in the cascode-bias branch (`design/cp_bias.sch`: XBPA from IBP down to node px, XBPC diode, XBNS from ICP to ground). Every candidate below enlarged one or both at constant W/L, which at a fixed current should cut their mismatch by about 1/L.

**Why it fails (measured on the probes, mechanism inferred).** XBPA and XBNS are two current sources in series with only the high-impedance node px between them, so the difference in their currents is absorbed by px and appears as a shift of the p-leg cascode gate ICP. Trimming XBPA's width by 0.4 u moves the nominal I_up by about 11 uA (table, last block), i.e. a gain of roughly 14 % of I_cp per micrometre of XBPA width; the 0.6 % nominal offset of the ratified design is a balance point on that slope. Any resize that moves the nominal current of one source relative to the other moves that balance by several percent, and the random mismatch of the same two devices enters through the same gain. Upsizing is therefore not a local fix: it needs a re-balance (as the XBPC retune of 221e27b was) or a topology without two series sources. The re-balance was not found within this issue.

## Method

One local `ngspice -b` per row (`scripts/run-cp-dc.sh`, single nominal TYP / 3.3 V / 27 C corner, `CP_NETLIST` pointing at the variant, files in `probes/`), then, for the one variant that kept the nominal point close, the C-grid on the batch fleet (`sim/corner-verification/cp-dc/request-stage{1,2}.json`, unchanged requests). Deterministic DC, no Monte Carlo; mismatch = |I_up - I_dn| / 200 uA at V_out = 1.65 V. Simulated, not measured.

| variant (changes to the ratified `design/netlist/cp.spice`) | I_up (uA) | I_dn (uA) | mismatch at 1.65 V |
|---|---|---|---|
| ratified design (no change) | 196.4 | 197.6 | 0.599 % |
| XBNS 8u/2u | 199.1 | 197.6 | 0.763 % |
| XBNS 12u/3u | 202.5 | 197.6 | 2.449 % |
| XBNS 16u/4u | 203.0 | 197.6 | 2.731 % |
| XBPA 16u/4u | 203.1 | 197.6 | 2.750 % |
| XBNS and XBPA 8u/2u | 203.1 | 197.6 | 2.763 % |
| XBNS and XBPA 16u/4u | 203.1 | 197.6 | 2.785 % |
| XBNS as two series 4u/1u m=2 (W/L 4, L_eff 2, all in the L = 1 u bin) | 191.6 | 197.6 | 2.967 % |
| ...and XBPA w = 3.2u | 203.1 | 197.6 | 2.778 % |
| ...and XBPA w = 3.6u | 202.8 | 197.6 | 2.635 % |
| ...and XBPA w = 4.4u | 179.0 | 197.6 | 9.296 % |
| ...and XBPA w = 5u | 166.2 | 197.6 | 15.661 % |

(Per-variant records are `probes/probe-*-cp-dc.md`. The series-stack netlist was a hand edit of `cp_bias.sch` that was not kept; its row is reproducible from the description.)

**C-grid for XBNS 8u/2u** (the only probe near the nominal point; commit a520f7c, `klt sim` batch jobs `klt-sim-23ab48797798` stage 1 and `klt-sim-f046358b31e8` stage 2, reports `20261103-a520f7c-xbns8x2-probe-cgrid-stage{1,2}.json`): stage 1 has 10 of 15 corners failing the 2 % row-7 bound at 1.65 V, worst 4.73 % (`mos_fs`, -40 C); stage 2 has 9 of 18 failing, worst 4.53 % (`mos_ff`, 2.97 V, -40 C). The ratified design is 15 of 15 and 18 of 18 passing after the 221e27b retune (worst 0.95 % and 1.57 %). I_up spans 187.6 to 206.0 uA (row 6 range 100 to 400 uA still holds). This variant is **not adopted**.
An earlier probe, XBNS and XBPA both 16u/4u, failed 15 of 15 and 12 of 18 (worst 3.22 % and 5.12 %); its report files were overwritten and are not kept, the row above is its local nominal result.

## What the attribution says a fix must reach

Pooled over 9 corners (MOS tt/ss/ff x T at 3.3 V) at 1.65 V the random part is 1.94 % rms and the deterministic offset another 0.63 % rms. For a zero-mean Gaussian a 2 % limit at the campaign's 0.9973 yield needs a total rms of about 0.67 %, so the sum of every group's random variance plus the offset would have to fall about 9x in mean-square (4.2 to 0.45 %^2). XBNS alone is 66 %; removing it entirely leaves 1.14 % random, still above 0.67 %, and leg_n (15 %), XBPA/XBPS (8 %) and leg_p (4 %) then dominate. Reaching the target takes a redesign of the bias branch and larger legs, not a resize of one device. The 6 % fallback already holds (0.9965 pooled, record `20261103-034036-59b5e16-dirty`).

## Yield target and spec decision

The 0.9973 yield is the campaign's choice (`sim/cp-mc/limits-target.json`); the ratified spec states no yield target for row 7, so this result is graded against a number no ratified record sets. Row 7 and signoff item 6 stay `unmet`. A spec-decision issue with ranked options is filed from this record; `spec/target-spec.md` is not edited.
