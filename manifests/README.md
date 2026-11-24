# Block manifest and tier-verdict record

This directory holds this block's `klt signoff` input and its committed
output, the machine-readable replacement for a hand-maintained gap-to-T1
checklist. The gap-to-T1 tracker (issue #5) points here as the verdict of
record.

## Files

- **`sg13g2-lc-pll.json`**: the block manifest. `block: sg13g2-lc-pll`,
  `kind: analog` (an integer-N LC PLL with no mixed-signal partition decided
  today; if that changes, `kind` may change with it). `evidence` cites items 1, 2, 9 and 10 (the four `klt signoff --attest` envelopes `manifests/design-sources.attest.json`, `manifests/layout.attest.json`, `manifests/testbenches.attest.json`, `manifests/repo-hygiene.attest.json`), item 3 (the `klt drc` report `layout/drc/top.drc.json`, graded `met`: `status: clean`, clean for the layers the curated deck covers, #36), item 5 (two passing `klt sim` corner records `sim/corner-verification/cp-dc/records/20261103-221e27b-stage{1,2}.json` for row 6 — also passing row-7 mismatch at 1.65 V after #67 — and the passing method-L `model-run` record `sim/loop-model/records/20261115-101634-6a08197-row5-envelope.json` for row 5; graded `unmet` / `partial_coverage`: every cited envelope passes, while `spec_rows."5"` declares rows 1, 7 (upper edge `V_hi,req`), 8, 9, 10 and 11 as gaps) and item 6 (the `klt yield` report of the
  charge-pump Monte Carlo, `sim/cp-mc/records/`, graded `unmet` / `check_failed`:
  the campaign fails the row-7 mismatch target; `spec_rows."6"` declares the two
  rows' unevidenceable parts as gaps); item 9's envelope is `unmet` /
  `stale_evidence` at the 0.9.1 pin (see **Current verdict**); every other T1
  item is `unmet` / `no_evidence`. Evidence is added one item at a time, each
  citation pinning the `content_hash` of the artifact it cites.
- **`design-evidence-tiers.md`**: the T1-T4 checklist the grader parses.
  Vendored **byte-identical** (no edits, no newline normalisation) from
  [`2AMLogic/klayout-tools@4d0d29be`](https://github.com/2AMLogic/klayout-tools/blob/4d0d29be4fd991f499d59e783a908082d5e24c56/docs/design-evidence-tiers.md)
  `docs/design-evidence-tiers.md` — the build commit of the pinned
  `klayout-tools==0.9.1` wheel (tag `v0.9.1`, 2026-11-05), byte-identical to the
  copy bundled in that wheel at `klayout_tools/data/design-evidence-tiers.md`.
  Upstream is MIT-licensed, and this repo's `LICENSE` does not relicense the
  vendored copy.
  sha256 `08dcbfd2c3f2df152868d86c0ad2aa6a43d393b1d266f0b1e914cd8f0a329c58`.
  When upstream moves, re-vendor and regenerate the record in the same PR.
- **`sg13g2-lc-pll.signoff.json`**: **the verdict of record**, the committed
  output of the command below. Never hand-edit it. Besides the 11 T1 items
  (items 1, 2, 3 and 10 `met`, the rest `unmet` / `partial_coverage`, `check_failed`,
  `stale_evidence` or `no_evidence`), `klt` 0.9.1 also lists 3 non-T1 rows
  (`tier_not_supported`); these are part of its output, not a design claim.

## Regenerate (cold start)

The `klt` pin is `klayout-tools==0.9.1` (PyPI), the same pin as
`.github/workflows/signoff.yml`. Keep the two in step.

```console
uvx --from "klayout-tools==0.9.1" klt signoff \
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
re-checks each inventory-backed attest envelope (next section). At 0.8.0 the manifest cited items 1, 9
and 10 by their *inventory's* sha256, so editing an inventoried **file** moved
nothing the manifest or the record could notice: the envelope's own per-file
hashes rotted in silence. At the 0.9.1 pin this still holds for items 9 and 10
(their envelopes bind the inventory alone), but item 1's envelope now records a
digest over its whole input set, so a drifted design source moves its manifest
pin and the record too (#304). The per-envelope `--check` steps stay for all
three: they are what actually reports *which* file drifted. All three envelopes were stale on `main` when the
per-envelope checks were added (#241). An envelope also goes stale with nobody
skipping a re-stamp, when two PRs merge cleanly and neither diff touches the
other's attested files (PR #240 merging after #238) — which is why the checks
run on `push` to `main` and not only on pull requests.

## Current verdict

**Not-T1, 4 of 11 T1 items met** (item 1 design sources, item 2 layout, item 3 DRC — clean
for covered layers, see [`layout/README.md`](../layout/README.md) for the coverage the verdict
excludes — item 10 repo hygiene). Item 9 testbenches reads `unmet` / `stale_evidence` at the
0.9.1 pin: its envelope was already stale on `main` before the bump (member files such as
`scripts/run-benches.sh` and `scripts/lib-pdk.sh` drifted after the committed cold start),
but `klt` 0.8.0 did not detect member-level drift and graded it `met`; 0.9.1 does. The
honest re-stamp needs a real `scripts/run-benches.sh` cold start on the Spot batch fleet
(#242, which waits on #149) — `scripts/restamp-attest.sh 9` refuses by design, and the
envelope was not faked to hold the tally at 5.

## Attest envelopes (T1 items 1, 2, 9 and 10)

Four T1 items are evidenced by a `klt signoff --attest` envelope, and all four
envelopes are tool-produced. Items 1, 9 and 10 are inventory-backed: an
inventory lists the files and the checks, and the envelope pins a sha256 per
file plus each check's outcome; the manifest cites each of those envelopes by
the envelope's `provenance.input.content_hash` — at 0.8.0 that was the
*inventory's* own sha256; item 1's envelope at the 0.9.1 pin instead records a
digest over the envelope's whole input set (the inventory plus every listed
source, derived netlist, `reuse.lock.json` and `sim/loop-model/loop-filter.json`),
and its manifest pin moved with it (#304). Item 2 has no inventory — its envelope is produced
from the layout stream (`--attest 2 --input layout/top.gds`, klt >= 0.9.x) and
pins the stream's own sha256, which is what the manifest cites.

| Item | Inventory | Envelope | `local_only` check |
|---|---|---|---|
| 1 Design sources | `design-sources.inventory.json` | `design-sources.attest.json` | six `design/netlist.sh --check <cell>` freshness runs (klt + the PDK) |
| 2 Layout | — (no inventory; produced from `--input layout/top.gds`, cited by the GDS's own sha256) | `layout.attest.json` | none — its three checks (`stream_readable`, `top_cell_non_empty`, `dbu_on_grid`) are evaluated at attest time from the stream |
| 9 Testbenches | `../sim/testbench-inventory.json` | `testbenches.attest.json` | cold start `bash scripts/run-benches.sh` (PDK + ngspice, 7200 s) |
| 10 Repo hygiene | `repo-hygiene.inventory.json` | `repo-hygiene.attest.json` | `design/netlist.sh --check` (xschem); `harness-tests` is **not** `local_only` and really runs |

**Editing an inventoried file means re-stamping its envelope in the same PR.**
Item 10's inventory pins `README.md`, `LICENSE` and *both workflow files*, so
even a change to `signoff.yml` itself drifts it — re-stamp item 10 **after** your
last edit to either workflow. Item 2 has no inventoried files — its envelope
pins `layout/top.gds` itself, so it only goes stale when that GDS changes.

### Item 2 is off-pin (disposition: left as produced, recorded 2026-11-15, #304)

The committed envelope was produced out-of-band by a 0.9.2 dev build
(`provenance.klt_version` records `0.9.2.dev887+gec7400b7d8e5`). Up to the #304
pin bump the pinned `klayout-tools==0.8.0` could neither produce nor re-check
it — `--attest 2 --input` first ships in 0.9.x — which made the off-pin
producer version unavoidable. **The #304 bump (0.8.0 → 0.9.1) does NOT
re-produce item 2's envelope**; it stays at its recorded dev-build version,
and that is the recorded disposition. Why that is acceptable:

- The three checks it carries (`stream_readable`, `top_cell_non_empty`,
  `dbu_on_grid`) read the GDS stream alone — `provenance.pdk` is `null`, no
  PDK is involved — so their outcomes do not depend on the producer version.
- The manifest binds the citation by `layout/top.gds`'s own sha256, which the
  bump does not touch; item 2 grades `met` identically at 0.8.0 and 0.9.1
  (measured, #304 curation), and its envelope file is byte-unchanged here.
- The producer version is recorded, not hidden — nothing about the envelope
  claims it came from the pin.

What would close the gap: a deliberate re-attest at the pinned release —
`klt signoff --attest 2 --input layout/top.gds` with `-o`, on a host with
`layout/top.gds` and **KLayout** — re-stamping the envelope and regenerating
the verdict in one PR. That is a layout-host task, out of scope for a pin
bump; it is left unfiled so it does not masquerade as a dependency of the
verdict (item 2 grades `met` as-is).

`scripts/restamp-attest.sh` refuses item 2 by design, and
`signoff.yml`'s per-envelope `--check` steps cover items 1, 10 and 9 only:
item 2's envelope is guarded locally by `scripts/test-layout-top.sh`, which no
workflow runs.

### README.md and the Guide docs tick

`README.md` is in item 10's `hygiene` inventory, so **any** PR that edits it
re-stamps `manifests/repo-hygiene.attest.json` in the same PR — the rule in the
paragraph above has no exception for it.

The Guide's document-maintenance tick cannot do that re-stamp: its staging set
is fixed at `WORK_LOG.md WORK_PLAN.md README.md` by its Loom-managed role prompt
(`.loom/roles/guide.md:2369`, verified 2026-11-14 against `c8df23d`), and both
copies of that prompt (`.loom/roles/guide.md`, `.claude/commands/loom/guide.md`)
are listed in `.loom/install-metadata.json` and overwritten by
`.loom/scripts/resync-installed.sh` at every resync (loom 0.19.1294,
`last_resync` 2026-11-12). A local edit teaching the tick to re-stamp — or to
stay out of `README.md` — would not survive it, so the fix belongs upstream:
rjwalters/loom#13892 (filed 2026-11-14) tracks the generic staging-set /
integrity-check conflict. **`README.md` is therefore not the Guide's to own in
this repo.** README status corrections go through a normal issue → Builder PR,
which re-stamps as a matter of course (#277 is the worked instance).

When a Guide docs PR edits `README.md` anyway (PR #274, the only occurrence as
of 2026-11-14): Doctor runs `scripts/restamp-attest.sh 10`, stages
`manifests/repo-hygiene.attest.json`, and quotes the script's `[CARRIED]` /
`[RAN]` lines in the PR. The carry rule permits the re-stamp: item 10's
`local_only` `design/netlist.sh --check` reads none of the `hygiene` files, so
drift confined to them is carried (see **The carry rule** below). The PR then
falls off the docs-only fast path — the Judge's `docs_only_fast_path_check()`
(`.loom/roles/judge.md:1683`, verified 2026-11-14) re-derives eligibility from
the PR's own file list, so the added envelope is `NOT ELIGIBLE` and the PR takes
a full review. That is the intended outcome, not a regression.

### Re-stamp

```console
scripts/restamp-attest.sh 1      # manifests/design-sources.attest.json
scripts/restamp-attest.sh 9      # manifests/testbenches.attest.json  (refuses, see below)
scripts/restamp-attest.sh 10     # manifests/repo-hygiene.attest.json
```

That script is the single re-stamp entry point — the one the CI failure message
names. It covers the inventory-backed envelopes only — items 1, 9 and 10 — and
refuses item 2 (see **Item 2 is off-pin** above). It runs the pinned
`klayout-tools==0.9.1` through `uvx` (never the host
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

The pinned `klt` 0.9.1 has no way to refresh an envelope's file hashes without
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
uvx --from "klayout-tools==0.9.1" klt signoff --attest 1 \
    --inventory manifests/design-sources.inventory.json \
    --check manifests/design-sources.attest.json

# item 10 additionally needs numpy and pytest: its harness-tests check really
# runs `bash scripts/ci-harness.sh`
uvx --from "klayout-tools==0.9.1" --with numpy --with pytest klt signoff \
    --attest 10 --inventory manifests/repo-hygiene.inventory.json \
    --check manifests/repo-hygiene.attest.json
```

Swapping `--check <envelope>` for `-o <envelope>` re-attests and writes — but it
**runs every `local_only` command for real**, which for item 9 means the 7200 s
bench cold start and for items 1 and 10 means klt plus the PDK. Prefer
`restamp-attest.sh`, which applies the carry rule above instead.
`klayout-tools` 0.7.0 has no `--attest`; the pin was bumped to 0.8.0 for it.
