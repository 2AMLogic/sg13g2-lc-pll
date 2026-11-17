# sim/vco-prescaler-load

Gate G2 bench (#87): the pinned `sg13g2-vco` (`reuse.lock.json`, unmodified) with and without the prescaler's
input on the tank nodes. Nominal corner only (`hbt_typ`/`mos_tt`/`cap_typ`, 27 C, 3.3 V), Vctrl = 0, 1.65, 3.3 V.

```bash
scripts/run-vco-prescaler-load.sh     # fetch + verify VCO, two local ngspice runs, write records/<id>.md
```

Prerequisites as for `sim/vco-smoke` (`PDK_ROOT`, `NGSPICE`, `OPENVAF_R`, `OPENVAF_LD_LIBRARY_PATH`; `jq`; `klt` for the
prescaler netlist drift check). `OPENVAF_LD_LIBRARY_PATH` must be a directory that really holds `libLLVM.so.21.1`.

- `load.spice.tmpl` is appended to the fetched `vco.spice` (cut before its own `.control` block); the unloaded and loaded
  decks differ only by the `X1 ... prescaler` instance and its `.ic`.
- `analyze.py` holds the estimators (frequency, Vpp, t90, tank resonance from an AC current probe).
- `records/` is dated and append-only.

**Not covered here**: the C-grid; it ran through `klt sim` on the batch fleet, see
`sim/corner-verification/vco-prescaler-load/` (the mosvar OSDI is preloaded from the PDK on the runner, `options.osdi_preload`).
Routing capacitance is not in the load (the G1 device-level number is 1.373 fF against a
2.1 fF device-plus-routing budget). The row 6 ratio g_m / loss >= 3.0 is not extracted; only startup time is compared.
Simulated, not measured.

**Smoke bench caveat** (observed while building this; fixed since): with ngspice-46, `wrdata` wrote files without a
`.data` suffix, and `scripts/run-vco-smoke.sh` read only `vco_tran_<v>.data`, so it reported "DOES NOT OSCILLATE" for a
VCO that oscillates (4.2 GHz, 0.59 Vpp at Vctrl = 1.65 V in the same deck). Fixed in `27c410c` (issue #90), which
accepts either name; the re-run is `sim/vco-smoke/records/20261103-124045-17e49a8.md`, still on ngspice-46, so it is a
toolchain check off the pinned simulator and not a grade of the VCO. The 20261018 record, run on ngspice-47, is a
different failure (an op/initial-transient non-convergence); that was not reproduced here (no ngspice-47 on this host).
