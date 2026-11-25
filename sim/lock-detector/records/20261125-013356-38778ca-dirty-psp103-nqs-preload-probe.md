# lock-detector request: psp103_nqs.osdi preload probe (#456)

**Simulated, not measured.** Single corner (`mos_tt`/`typ`, 27 C, 3.3 V), `klt sim --backend local`, klt 0.9.3.dev5546+g3bdec0fe77a4, ngspice-47, host loom-crew-2, 2026-11-25T01:33:56Z, base commit `38778ca` plus this change (`-dirty`).

- **Method**: the request built by `scripts/ld_tool.py request --stage 1` (unmodified body from `ld_tool.py body`), cut to one process bundle and one temperature, backend local, `keep_artifacts`, analysis shortened to `.tran 50p 1n` because the drop is emitted at netlist parse, before the transient. The shortened window leaves the 4 transient measurements without a value (`measurement` diagnostics, identical before and after); that is not a result and no lock-detector number is taken from this probe. A full-length single unit exceeded a 900 s local cap and was killed (no log kept), so it is not used.
- **Count**: lines matching `Unknown model type pspnqs103va - ignored` in the corner's `ngspice.log`.
- **Before** (osdi_preload = psp103.osdi, r3_cmc.osdi): **412** lines ([log](20261125-013356-38778ca-dirty-psp103-nqs-preload-probe-before-ngspice.txt)).
- **After** (osdi_preload adds psp103_nqs.osdi; reported osdi_preload = psp103.osdi, psp103_nqs.osdi, r3_cmc.osdi, sha256 of psp103_nqs.osdi `839b1644...afbdfc7d`): **0** lines ([log](20261125-013356-38778ca-dirty-psp103-nqs-preload-probe-after-ngspice.txt)).
- **Scope of the claim**: the C-grid request itself (45 / 18 corners on the fleet) was not re-run. This probe covers one corner; the preload list is identical for every corner of the request, but other corners were not measured. The archived grid records predate the fix and are unchanged.
