# Issue #212: generated decks removed, regeneration attested

Simulated-evidence housekeeping, no new simulation. Operator ruling r7-q12 (issue #106): results and attestations are append-only; regenerable inputs are not. This record supersedes every citation in the records below of the removed deck files as tracked files. The cited records are unchanged.

## What was removed from tracking (6 files, 543 lines, generator output)

`vco_loaded.spice`, `vco_unloaded.spice`, `vco_loaded_dsubw.spice`, `vco_unloaded_dsubw.spice`, `svar_dsubw125.spice`, `sg13g2_inductor_em.spice` (all in `sim/corner-verification/vco-prescaler-load/`). They are now gitignored. `sg13g2_inductor_em.spice` is a copy of the pinned upstream VCO inductor model (`reuse.lock.json`).

Records that name them as the decks graded: `20261110-125c-probe.md` (line 11), `20261110-dsubw125-stage1.md`, `20261110-dsubw125-stage2.md`. They remain valid: the decks they name are rebuilt byte-for-byte by the command below.

## Regeneration check (byte-for-byte, at the parent commit of this change)

`scripts/fetch-vco.sh` (VCO at 17e49a8f..., 5 files verified), then `python3 -I sim/corner-verification/vco-prescaler-load/make_requests.py` rewrote the tree in place; `git status` stayed clean, so 6 of 6 tracked decks are identical. One run covers both the base path (`main()`) and the `dsubw()` path.

## Digests (sha256)

```
6f24f9857ab7810c91bda5f6307e78f1dfcbe2afd750bb023e28156ded06d6a0  sg13g2_inductor_em.spice
afee8c57d26a1e5b3b8636e33f584226cea62a3593febb7cbff907be582b1743  svar_dsubw125.spice
1a7079938b86084fb73ef556e822dcafd54103e5639608680e12e7370c55bcb5  vco_loaded.spice
3addbbfd399da769749a0fe912c36120d25600da74fc02d662319e7a639a51c7  vco_loaded_dsubw.spice
b4e3587b496fc5625927db525014b372b6c0fd8d2539fe6a6847e068798faf91  vco_unloaded.spice
dc5e7c690fcf249ec6379a7d44542a8597c493c1867ad924395d7656ad1b839a  vco_unloaded_dsubw.spice
```
