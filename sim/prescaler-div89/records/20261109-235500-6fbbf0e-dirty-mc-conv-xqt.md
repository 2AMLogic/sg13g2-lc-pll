# mc_conv tail-Vce fix (issue #165): cause check and modulus-control check

All numbers are **simulated, not measured**. Ideal resistors, ideal stimulus (0.4 Vpp differential 5.0 GHz at common mode = supply, IREF = 50 uA).

## Cause (one-corner waveform check, FAST/125 C/3.63 V/MC at the supply, before the change)
Single local `klt sim` unit, `vecmax`/`vecmin` over 10-24 ns of `x1.x89.xmc.*`: `bm` 3.622-3.634 V, `t` 2.946-2.959 V, `teT` 0.114-0.120 V, `vr` 2.539-2.544 V; Vce(XQT) = 2.844 V, Vce(XQM1) = 0.447 V, Vce(XQM2) = 0.684 V. `t` = `bm` - 0.68 V (Vbe, hot FAST) and `bm` sits at the supply, so XQT carries about VDD - Vbe - V(teT). Cause confirmed: a genuine stress of the MC-high state, not a bench artefact beyond the ideal MC level (the real MC comes from the divider on the same VDD).

## Change
`mc_conv`: `RIN` 20k -> 10k and a new `RB` 31k from `bm` to VSS. With MC high, `bm` = 0.756 VDD, i.e. 0.056 VDD above `vr` (0.7 VDD): 0.20 V at 3.63 V, 0.17 V at 2.97 V; MC low still gives `bm` = 0. Only the ratio matters (RB/(RIN+RB) = 0.756), so #164 (PDK resistors) can land in either order.

## Vce record
`sim/prescaler-g1/records/20261109-234716-6fbbf0e-dirty-vce.md`: **PASS, 0 of 36 over 2.2 V**. Worst at 2.97 V: 1.786 V (+0.414 V); worst at 3.63 V: 2.108 V (+0.092 V, `xc23.xck.xqf1`, FAST/125 C, not an mc_conv device). `xmc.xqt` worst: 1.961 V at 3.63 V, FAST/125 C (+0.239 V; was 2.844 V); at 2.97 V it is at most 1.46 V (+0.74 V; was 2.186 V). The 2.2 V limit in `vce_record.py` is unchanged.

## Modulus control
1. Existing `div89_chain.request.json` (108 units, TYP/SLOW/FAST x 3 temps x 3 supplies x 5.0/5.5 GHz x /8,/9; method: output zero-crossing period x fin, `-chain-klt-report`). 90 of 90 units at 2.97 and 3.30 V divide correctly (/8 = 8.000, /9 = 9.000). The 18 units at 3.63 V with the stimulus MC held at an absolute 3.3 V divide by 8, not 9: that stimulus puts MC at 0.909 VDD, below the 0.94 VDD the new input divider needs (below).
2. MC-level sweep (`-mcdroop-klt-report`, 72 units, 5.0 GHz, 9 PVT, 2.97 and 3.63 V, MC = 0.90/0.94/0.97/1.00 VDD): /9 at 0.94, 0.97, 1.00 VDD in every unit at both supplies; /8 (fails to select /9) at 0.90 VDD.

**Consequence / limit**: MC high must be at least ~0.94 VDD (the divider's MC output is on the same VDD, so it is nominally at VDD). Before the change MC high worked at any level above about 0.74 VDD. This is the cost of the fix; a separate MC supply domain or a droop above 6 % would break /9. MC-path load on the prescaler RF input is unchanged (MC drives only `bm`; no RF node touched), so the #160 input-load figure stands.
