# sim/vco-smoke

Toolchain and pin check for the consumed `sg13g2-vco` (see `reuse.lock.json`).
Not a loop result, not a re-grade of the VCO, no noise number.

```bash
scripts/run-vco-smoke.sh        # fetch + verify, render deck, ONE local ngspice, write a record
scripts/test-fetch-vco.sh       # negative controls for the fetch/verify path
```

Prerequisites: `jq`, `curl` or `gh`, an `ihp-sg13g2` install (`PDK_ROOT`) whose
model libraries match `sim/pins.json`, `openvaf-r` (`OPENVAF_R`, plus
`OPENVAF_LD_LIBRARY_PATH` if libLLVM.so.21 is not system-installed), and an
ngspice that loads OSDI v0.4 (`NGSPICE`, ngspice >= 46; ngspice-42 cannot).

- `records/` — dated, append-only. A failed run is recorded too.
- `negative-control-*.txt` — output of `scripts/test-fetch-vco.sh` (tampered
  byte, short commit, ref instead of SHA, wrong mode, wrong sha256, file
  missing at the pinned commit are all refused).

The fetched template is hashed; the substituted deck is a build product and is
not. Besides the four files the lock names for the VCO, it pins the EM-fitted
inductor model (`sim/inductor-model/sg13g2_inductor_em.spice`), because the
template cannot be elaborated without it. The bench runs one corner, so it
stays a local `ngspice -b` rather than a `klt sim` grid (`klt sim` cannot
express an OSDI deck: klayout-tools#2511).
