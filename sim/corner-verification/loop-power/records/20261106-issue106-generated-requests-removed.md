# Issue #106: generated request JSONs removed, regeneration attested

Simulated-evidence housekeeping, no new simulation. Operator ruling r7-q12 (issue #106): results and attestations are append-only; regenerable inputs are not. This record supersedes every citation below of the removed request files. The cited records are unchanged.

## What was removed (56 tracked files, all generator output)

| Family | Files | Generator |
|---|---|---|
| `loop-power/request-stage1-missing{0..21}.json` | 22 (the earlier note of 29 was a stale count; main tracked 22) | `make_requests.py --missing <records>` |
| `loop-power/request-stage2-97-s-<PROC>-<T>-<VDD>.json` | 18 | `make_stage2_shards_97.py` (reads the tracked `request-stage2-97-fix1.json`) |
| `vco-prescaler-load/request-{loaded,unloaded}-stage{1,2}[-<shard>].json` | 16 | `make_requests.py` (after `scripts/fetch-vco.sh`) |

Result and report files under `records/` were not touched.

## Regeneration check (byte-for-byte, `cmp`, at the parent commit of this change)

- **stage2-97-s (18)**: `cd <dir with request-stage2-97-fix1.json + make_stage2_shards_97.py> && python3 -I make_stage2_shards_97.py` rebuilds all 18; 18 of 18 identical.
- **vco-prescaler-load (16)**: `scripts/fetch-vco.sh && python3 -I sim/corner-verification/vco-prescaler-load/make_requests.py` rewrote the tree in place; `git status` stayed clean, so 16 of 16 identical (the circuit bodies were identical too).
- **stage1-missing (22)**: the recorded set rebuilds, but from two invocations, because the tree held a mix of two runs. Let `R` = `records/`:
  - indices 3..21 (19 files): `make_requests.py --missing R/20261103-133412-ce1d60d-dirty-stage1.md R/20261103-193448-b6ec1f3-stage1.md R/20261103-215804-0a8000d-stage1.md` (64 units, 22 requests, the run `20261104-stage1-accounting-increment3.md` cites as "the three earlier stage-1 records"); 19 of 19 identical.
  - indices 0..2 (3 files): the same command with `R/20261104-032646-2335505-stage1.md` added (7 units, 3 requests, the run `20261104-stage1-complete-135.md` cites). That run overwrote indices 0..2 of the first run, which is why the three-record command alone reproduces only 19 of the 22 (indices 0..2 differ). 3 of 3 identical.
  - Net: 22 of 22 rebuild. Why 22 and not 29: 29 is the count `make_requests.py --missing` gives for the first two records only (133412 + 193448); the later three-record run wrote 22 and the tree never held more.
  - Citation `20261104-083547-b669786-stage1.md:5` names `request-stage1-missing{0,1,2}` for the 7-unit run; those three are the four-record output above.

## Digests of the removed files (sha256, for later byte checks)

```
98d1f62d0f035e64c18b088e2d7eb85790d1d93d9c3c858fa65fc7fcb17a52be  loop-power/request-stage1-missing0.json
87b297ef586094f465ef34a19f776df776fd6daa3dcb98101ecf9c8a5c358730  loop-power/request-stage1-missing1.json
c1f02ed551c4607f82c6cf379abac36ea757a360bcc7cedbbf1c26b11f60addc  loop-power/request-stage1-missing10.json
afe4b9c29fbe1fb46c2c175cd1fb631bc5f272ee2d18a4553cc5cb7f3105e03b  loop-power/request-stage1-missing11.json
cfbe286f641f9327f13bf1a1b614cd39b1043216a9879cca48a8cbb420cf5a9a  loop-power/request-stage1-missing12.json
e5a2519779b89446757c88280e1b051f0cd4fba75b9ae489efe17d1ccbb169db  loop-power/request-stage1-missing13.json
911c89ddf03140a926e0958e04e94b31614acdb89db2b4666c094c1b5b8a3341  loop-power/request-stage1-missing14.json
c3e2146d314d240de621d874da2ff5b9295dffea3a28db0155fd9a85e2694b9c  loop-power/request-stage1-missing15.json
9e0c05469dc4a4a5f92486b9d54c9aaebbe820a09912a35a26691499923e9d58  loop-power/request-stage1-missing16.json
02bd72eb2686f277b5bc57a6f0fe4db31b587d057fa900f835b1a72013d5372e  loop-power/request-stage1-missing17.json
0d107188e6acce8827dbe95a33edc0dbdc05a3e58124ba0188a92c8984ab6fa1  loop-power/request-stage1-missing18.json
a10c4103a9bd07396eb5f315745b15280edcc80c265a9d162e52fe80fe8120c1  loop-power/request-stage1-missing19.json
6d33c42be73706b94f72aa4b64493e83a7593f8cffcbd01a4215d62bad6384da  loop-power/request-stage1-missing2.json
1c138178f562830a0bf3317913d14fabcd01a1644450c7ce3c69466300d80974  loop-power/request-stage1-missing20.json
6e4454bb394df104f63948d3ce373e522c3a4458ca4ba841ca9f61d47bb65101  loop-power/request-stage1-missing21.json
f067a698c18a3dedf8769e2aa0439b7f0a4158aff270ddfa9978640a18c07256  loop-power/request-stage1-missing3.json
c8c7f9cf3552cee8c57b34b5fe72f9f1963c2ddc07cf74b7960c851c8cb31b86  loop-power/request-stage1-missing4.json
98f5e9c6ca11b4857372074b14981c38c753a6a0f618701bd5c43ff232b439f9  loop-power/request-stage1-missing5.json
cd820e2fb7f5acddaa7788a43bf2feb57665d4f073b4c2fd339ffcdfcab97995  loop-power/request-stage1-missing6.json
cb1cc662a54f948834c1040f4a9a1a7145493b32f7ff84c9732127158acc4551  loop-power/request-stage1-missing7.json
f3d60a085252b6a911eea8288a1f3117ba345928e369d6e78d129714cb3192df  loop-power/request-stage1-missing8.json
d88b949382622199fd49461fd099044e9435102b7bda76e809415c21e1ec21bc  loop-power/request-stage1-missing9.json
b8ba6d3bc10131bc32b0c65d8902cc7ea34dc087bd2f416e679ccdba8c62a55e  loop-power/request-stage2-97-s-FAST--40-2.97.json
322ff28b34f77008db8824f3a2d80e7e1e476b4317dcc6c763627cb903a640c4  loop-power/request-stage2-97-s-FAST--40-3.63.json
b772a460c35b34db051cdf24f35fa10df3b3c1fb7c3167b103995398515c6a6f  loop-power/request-stage2-97-s-FAST-125-2.97.json
37b57da00cf1aa51812e49e64af3deb95e18e1d83d7ecc4bd224bf299c66bb4d  loop-power/request-stage2-97-s-FAST-125-3.63.json
095997aa139216ad65eeab5e30ee55144e5623ed2d13a31f8a1315f109d24060  loop-power/request-stage2-97-s-FAST-27-2.97.json
867516845952a5835d90a326063791f7fb928eea96a38ddf0285ec770b881845  loop-power/request-stage2-97-s-FAST-27-3.63.json
a65427be1a0afbbab8a0eaff5449e8c6244d51d56d73bed792b648c310b3bf19  loop-power/request-stage2-97-s-SLOW--40-2.97.json
3a774dbd9bf8118b8c6f8a335028686208ce0ea638d3b2512dcbf91f0deee185  loop-power/request-stage2-97-s-SLOW--40-3.63.json
715efa6da823b4cb46c4c2237ed21e522be7100fefc913143ae9da3b3aaf6b76  loop-power/request-stage2-97-s-SLOW-125-2.97.json
a2bac551984d3953e5f28e087bdefd330f49de1ceedc9839ff1f8007ec584e36  loop-power/request-stage2-97-s-SLOW-125-3.63.json
bc7ce8a0b3f6b82dfc9003fe19c51e577697c3057b73e402d2f372b61ce7cb2a  loop-power/request-stage2-97-s-SLOW-27-2.97.json
44f945b4b8576619d8afade8cfbb7e726e6f57530206a500ebd0a0632f4bedba  loop-power/request-stage2-97-s-SLOW-27-3.63.json
f5961a91ea0e78e9e7941aa9282f89ef0bc7ce64a0d1f38ab625cfa39b60c30f  loop-power/request-stage2-97-s-TYP--40-2.97.json
bc935de4c1ff93e9fbe311a8db8f93ff8a88c3928cf92cbf6cd0824e71735883  loop-power/request-stage2-97-s-TYP--40-3.63.json
cc215cca04267a8553800dfc975e045390ac93a3f2ffb3739030dbc5f29ae57d  loop-power/request-stage2-97-s-TYP-125-2.97.json
1dd18b07e934f57c31df53b37609cb12ad244af9e66a90ebd473be1e0098e13d  loop-power/request-stage2-97-s-TYP-125-3.63.json
91fcae53333485d716b412223f12d335a1f39b1c0e9d0ee3d059c0eeb2f0d231  loop-power/request-stage2-97-s-TYP-27-2.97.json
f36c7f66a2cb1495610ac81a54314780f8e8e925e1ba091a37a887c427ad809b  loop-power/request-stage2-97-s-TYP-27-3.63.json
9289ea144c9a9c25d4de1868c76ec4d6a83f15aad24421dd8d524b511fee64bc  vco-prescaler-load/request-loaded-stage1-ff.json
a00560f89fc9af42aee55f02c17f2ea37115f3b26c23c82f4daa05f79b6cc00a  vco-prescaler-load/request-loaded-stage1-fs.json
2410dc9a80ea1c39f2ca70033e8be77f7eb8de9ca8ac50d520b137b88bfbde76  vco-prescaler-load/request-loaded-stage1-sf.json
2969d06f01636d66083b901a739ff02afec8e33a1d1d6d3eddb223e040a8118c  vco-prescaler-load/request-loaded-stage1-ss.json
b51875da7e13d43f9903614e916147ca8e9a366fa9e994f4612206ac99aef1cd  vco-prescaler-load/request-loaded-stage1-tt.json
f61167c993bc6b5044bbbba4011fdd6d59473e33e40e66382402010d86265bcd  vco-prescaler-load/request-loaded-stage1.json
fe03cf3fbffaa7e7303ed546c856516f58d7d7100067a7b175e882a69a2f3f01  vco-prescaler-load/request-loaded-stage2-125C.json
b70611ecd28674a554dd36fb6d2959ad824648da07db1de4a2ca1cc59d1af557  vco-prescaler-load/request-loaded-stage2-FAST.json
29f884d0b12d444e105a4858a2f05a2d1d2c26420f4de7e88afedc66dda09bdc  vco-prescaler-load/request-loaded-stage2-SLOW.json
8f4d25febcea3a36a41c3e53b4aa4e3990010e91890bda2a559a8dbf57423de9  vco-prescaler-load/request-loaded-stage2-TYP.json
2a2cc82f292afb034a181e5db83b1300b7ce71bfa0207c580512dd3303ae2383  vco-prescaler-load/request-loaded-stage2.json
8158d12dfae0adbccf894e9b86e59d793c198b7b18df28f46c66c5372a454931  vco-prescaler-load/request-unloaded-stage2-125C.json
a8f413a8f9747133a1d28d04454ad9e912dddf5796b43ab2091ac40f85380e62  vco-prescaler-load/request-unloaded-stage2-FAST.json
520bd45977a13f136972b727dce2c010c11490e1c61d17364924b2735dbf262e  vco-prescaler-load/request-unloaded-stage2-SLOW.json
cd9a393ee5f6f4ccc1d63a961869ebfa8d91e54feb86427161c539476fb8ccce  vco-prescaler-load/request-unloaded-stage2-TYP.json
bbd9f6a0177e431f988728324e773c0c537271415122cb253da007c4dc8808de  vco-prescaler-load/request-unloaded-stage2.json
```

## Citations affected

`loop-power/records/` files that name the removed requests by filename or glob: `20261104-083547-b669786-stage1.md`, `20261104-stage1-accounting-increment3.md`, `20261104-stage1-complete-135.md`, `20261104-issue97-125c-diagnosis.md`, `20261105-issue97-mcounter-qn-tc2-in-tree.md`, `20261105-issue97-tc-from-tcn-inverter-trial.md`, `20261105-issue97-tc-own-flops-from-dtn-trial.md`. Read each as pointing at the generator command in this record. `vco-prescaler-load/records/` cites none.
