# cp-mc attribution 20261103-053307-b9dc8bb-dirty

**Simulated, not measured.** Method: `klt sim` Monte Carlo (vary: mismatch, seed 20261103, n = 100 per corner, none-control n = 10) on 9 corners (MOS tt/ss/ff x T -40/27/125 C at 3.3 V), one cp instance per sample, static op (UP on / DN on at each V_out). Each run leaves mismatch on in one device group (`mm_ok=0` on every other MOS instance, sim/cp-mc/attribute.py); `all` is every instance on; `none` (mismatch off everywhere, n = 10) measures the deterministic P/N offset, which adds in quadrature and is subtracted. Groups add in mean-square if independent; the table's last columns test that. Values are rms of mm = |I_up - I_dn| / 200 uA x 100 over all samples and corners pooled (mean of the square, so the sign drops out); the percentage is the group's share of the all-on mean-square. Groups: ok: 23 MOS instances partitioned into {'bn_ref': 1, 'bn_xbn2': 1, 'bn_xbns': 1, 'bn_casc': 2, 'bp_ref': 1, 'bp_copy': 2, 'bp_casc': 1, 'leg_p': 2, 'leg_n': 2, 'switches': 10}.

| measurement | systematic (none) | bn_ref | bn_xbn2 | bn_xbns | bn_casc | bp_ref | bp_copy | bp_casc | leg_p | leg_n | switches | sum of groups | all-on random | sum / all-on |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mm_v165_pct | 0.632 | 0.062 (0 %) | 0.331 (3 %) | 1.579 (66 %) | 0.080 (0 %) | 0.154 (1 %) | 0.547 (8 %) | 0.031 (0 %) | 0.380 (4 %) | 0.751 (15 %) | 0.000 (0 %) | 1.909 | 1.944 | 0.96 |
| mm_v200_pct | 1.088 | 0.079 (0 %) | 0.140 (1 %) | 1.632 (69 %) | 0.000 (0 %) | 0.077 (0 %) | 0.548 (8 %) | 0.034 (0 %) | 0.371 (4 %) | 0.754 (15 %) | 0.010 (0 %) | 1.924 | 1.965 | 0.96 |
| mm_v225_pct | 1.487 | 0.154 (1 %) | 0.192 (1 %) | 1.643 (71 %) | 0.000 (0 %) | 0.087 (0 %) | 0.533 (7 %) | 0.034 (0 %) | 0.359 (3 %) | 0.751 (15 %) | 0.028 (0 %) | 1.935 | 1.950 | 0.99 |
| mm_v245_pct | 3.118 | 0.369 (4 %) | 0.000 (0 %) | 1.658 (81 %) | 0.000 (0 %) | 0.000 (0 %) | 0.447 (6 %) | 0.024 (0 %) | 0.319 (3 %) | 0.736 (16 %) | 0.076 (0 %) | 1.932 | 1.844 | 1.10 |

All entries are rms of mm in %; the percentage is the group's share of the all-on random mean-square (all-on minus the `none` systematic). n per run: all=900, bn_ref=900, bn_xbn2=900, bn_xbns=900, bn_casc=900, bp_ref=900, bp_copy=900, bp_casc=900, leg_p=900, leg_n=900, switches=900, none=90

Commit `b9dc8bb-dirty`, host loom-worker-1, klt 0.8.1.dev1256+g56544971269c.
