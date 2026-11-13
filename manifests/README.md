# Block manifest and tier-verdict record

This directory holds this block's `klt signoff` input and its committed
output, the machine-readable replacement for a hand-maintained gap-to-T1
checklist. The gap-to-T1 tracker (issue #5) points here as the verdict of
record.

## Files

- **`sg13g2-lc-pll.json`**: the block manifest. `block: sg13g2-lc-pll`,
  `kind: analog` (an integer-N LC PLL with no mixed-signal partition decided
  today; if that changes, `kind` may change with it). `evidence` cites items 1, 3 (the `klt drc` report `layout/drc/top.drc.json`, graded `unmet` / `check_failed`: 64 violations, #36), 9 and 10
  (`manifests/design-sources.attest.json`, `manifests/testbenches.attest.json`,
  `manifests/repo-hygiene.attest.json`) and item 6 (the `klt yield` report of the
  charge-pump Monte Carlo, `sim/cp-mc/records/`, graded `unmet` / `check_failed`:
  the campaign fails the row-7 mismatch target; `spec_rows."6"` declares the two
  rows' unevidenceable parts as gaps); every other T1 item is `unmet` /
  `no_evidence`. Evidence is added one item at a time, each citation pinning
  the `content_hash` of the artifact it cites.
- **`design-evidence-tiers.md`**: the T1-T4 checklist the grader parses.
  Vendored **byte-identical** (no edits, no newline normalisation) from
  [`2AMLogic/klayout-tools@c6b7e4d`](https://github.com/2AMLogic/klayout-tools/blob/c6b7e4d08a5e6e6475627aba4f90e5bab68d13a7/docs/design-evidence-tiers.md)
  `docs/design-evidence-tiers.md` (2026-10-17; upstream is MIT-licensed, and
  this repo's `LICENSE` does not relicense the vendored copy).
  sha256 `a26b90262320d0fbd32b3f549a02b6300832706041797a559d8bf6bdb62efdc7`.
  When upstream moves, re-vendor and regenerate the record in the same PR.
- **`sg13g2-lc-pll.signoff.json`**: **the verdict of record**, the committed
  output of the command below. Never hand-edit it. Besides the 11 T1 items
  (items 1, 2, 9 and 10 `met`, the rest `unmet` / `check_failed` or
  `no_evidence`), `klt` 0.8.0 also lists 3 non-T1 rows
  (`tier_not_supported`); these are part of its output, not a design claim.

## Regenerate (cold start)

The `klt` pin is `klayout-tools==0.8.0` (PyPI), the same pin as
`.github/workflows/signoff.yml`. Keep the two in step.

```console
uvx --from "klayout-tools==0.8.0" klt signoff \
    --manifest manifests/sg13g2-lc-pll.json \
    --tiers-doc manifests/design-evidence-tiers.md \
    --format json > manifests/sg13g2-lc-pll.signoff.json
```

`klt signoff --manifest` exits `3` when at least one T1 item is `unmet` (a
valid, clean run) and `0` when every item is `met`. Any other exit is a hard
error. Any change that affects the verdict (new evidence, a manifest edit, a
vendored-doc bump, a pin bump) regenerates and commits the record in the same
PR.

## Freshness is CI-enforced

`.github/workflows/signoff.yml` re-runs the command above on every push to
`main`, every pull request and on manual dispatch, treats exit 0 and 3 as
valid and anything else as a failure, then byte-compares the fresh output
against the committed record.

That compare is **not** enough on its own, which is why the same job also
re-checks each attest envelope (next section). The manifest cites items 1, 9
and 10 by their *inventory's* sha256, so editing an inventoried **file** moves
nothing the manifest or the record can notice: the envelope's own per-file
hashes rot in silence. All three envelopes were stale on `main` when the
per-envelope checks were added (#241). An envelope also goes stale with nobody
skipping a re-stamp, when two PRs merge cleanly and neither diff touches the
other's attested files (PR #240 merging after #238) — which is why the checks
run on `push` to `main` and not only on pull requests.

## Current verdict

**Not-T1, 4 of 11 T1 items met** (item 1 design sources, item 2 layout, item 9
testbenches, item 10 repo hygiene).

## Attest envelopes (T1 items 1, 9 and 10)

Three T1 items are evidenced by a `klt signoff --attest` envelope: an inventory
lists the files and the checks, and the tool-produced envelope pins a sha256 per
file plus each check's outcome. The manifest cites each envelope by its
*inventory's* sha256.

| Item | Inventory | Envelope | `local_only` check |
|---|---|---|---|
| 1 Design sources | `design-sources.inventory.json` | `design-sources.attest.json` | six `design/netlist.sh --check <cell>` freshness runs (klt + the PDK) |
| 9 Testbenches | `../sim/testbench-inventory.json` | `testbenches.attest.json` | cold start `bash scripts/run-benches.sh` (PDK + ngspice, 7200 s) |
| 10 Repo hygiene | `repo-hygiene.inventory.json` | `repo-hygiene.attest.json` | `design/netlist.sh --check` (xschem); `harness-tests` is **not** `local_only` and really runs |

**Editing an inventoried file means re-stamping its envelope in the same PR.**
Item 10's inventory pins `README.md`, `LICENSE` and *both workflow files*, so
even a change to `signoff.yml` itself drifts it — re-stamp item 10 **after** your
last edit to either workflow.

### Re-stamp

```console
scripts/restamp-attest.sh 1      # manifests/design-sources.attest.json
scripts/restamp-attest.sh 9      # manifests/testbenches.attest.json  (refuses, see below)
scripts/restamp-attest.sh 10     # manifests/repo-hygiene.attest.json
```

That script is the single re-stamp entry point — the one the CI failure message
names. It runs the pinned `klayout-tools==0.8.0` through `uvx` (never the host
`klt`, which is a different version), prints a `[CARRIED]` line for every
outcome carried and a `[RAN]` line for every command actually run, writes
nothing unless the resulting envelope is `status: pass`, and then verifies the
bytes it wrote reproduce under `--check`.

### The carry rule

A `local_only` check is not run by `--check`: its **committed outcome is carried
forward**. A carried `pass` is not a fresh run, so it may only be carried when
no drifted file can affect that command. `restamp-attest.sh` enforces this
rather than trusting the caller to remember it:

- **item 10** — `design/netlist.sh --check` reads none of the `hygiene` files
  (`README.md`, `LICENSE`, the two workflows), so drift confined to them is
  **carried**. Drift anywhere else is refused.
- **item 1** — a drifted `source` or `derived` file is exactly what the six
  `design/netlist.sh --check <cell>` freshness commands assert, so they are
  **run for real** (needs klt and an `ihp-sg13g2` install, so run it locally,
  not on a bare runner). If any cannot run, or fails, the script writes nothing
  and exits non-zero. With no source/derived drift — an inventory-prose edit,
  say — they are carried instead.
- **item 9** — `scripts/run-benches.sh` executes the inventoried bench scripts
  and decks, so **any** drifted inventoried file means the committed cold-start
  `pass` cannot be carried: it would assert a bench run that never saw those
  files. The script refuses and writes nothing, and it never runs
  `scripts/run-benches.sh`. A real cold start belongs on the Spot batch fleet
  (#242, which waits on #149).

Because of that last rule, item 9's CI step is **warning-only until #242**: its
envelope is stale on `main` today, the drift is reported on every run, and the
job stays green. #242 turns that step into an error once a real passing cold
start is recorded.

### Why a script and not a flag

The pinned `klt` 0.8.0 has no way to refresh an envelope's file hashes without
*running* its `local_only` commands: `--attest N -o` runs them and `--check`
only compares, writing nothing. So the carried re-stamp is a call into the
wheel's own `signoff_attest.check_attestation()`, which is exactly what
`--check` does internally. Host `klt` 0.9.2.dev has
`klt signoff --skip-local-only` for this; no published release does (0.9.1
checked, 2026-11-13), and a pin bump would regenerate the whole record.
Upstream tracks the gap as 2AMLogic/klayout-tools#5209 / #5478 / #5480. **When
the pin moves past a release that ships that flag, delete
`scripts/restamp-attest.sh` and call the flag instead.**

### The raw klt commands

`restamp-attest.sh` is a wrapper, not a replacement — these still work, and the
`--check` form is what CI runs:

```console
# verify one envelope reproduces (exit 0 = fresh, 3 = drifted; what CI runs)
uvx --from "klayout-tools==0.8.0" klt signoff --attest 1 \
    --inventory manifests/design-sources.inventory.json \
    --check manifests/design-sources.attest.json

# item 10 additionally needs numpy and pytest: its harness-tests check really
# runs `bash scripts/ci-harness.sh`
uvx --from "klayout-tools==0.8.0" --with numpy --with pytest klt signoff \
    --attest 10 --inventory manifests/repo-hygiene.inventory.json \
    --check manifests/repo-hygiene.attest.json
```

Swapping `--check <envelope>` for `-o <envelope>` re-attests and writes — but it
**runs every `local_only` command for real**, which for item 9 means the 7200 s
bench cold start and for items 1 and 10 means klt plus the PDK. Prefer
`restamp-attest.sh`, which applies the carry rule above instead.
`klayout-tools` 0.7.0 has no `--attest`; the pin was bumped to 0.8.0 for it.
