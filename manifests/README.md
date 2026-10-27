# Block manifest and tier-verdict record

This directory holds this block's `klt signoff` input and its committed
output, the machine-readable replacement for a hand-maintained gap-to-T1
checklist. The gap-to-T1 tracker (issue #5) points here as the verdict of
record.

## Files

- **`sg13g2-lc-pll.json`**: the block manifest. `block: sg13g2-lc-pll`,
  `kind: analog` (an integer-N LC PLL with no mixed-signal partition decided
  today; if that changes, `kind` may change with it). `evidence` cites only item 10
  (`manifests/repo-hygiene.attest.json`); every other T1 item is `unmet` /
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
  (item 10 `met`, the rest `unmet` / `no_evidence`), `klt` 0.8.0 also lists 3 non-T1 rows
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

## Current verdict

**Not-T1, 1 of 11 T1 items met** (item 10, repo hygiene).

## Item 10 attestation

`repo-hygiene.inventory.json` lists README, LICENSE, the workflows and the checks
(`scripts/ci-harness.sh`, the command CI runs; `design/netlist.sh --check` is `local_only`,
it needs xschem). `repo-hygiene.attest.json` is the tool-produced envelope; the
manifest cites it by the inventory's sha256. The inventory pins the bytes of `README.md`
and the workflows, so editing them means re-attesting in the same PR. `klt`'s tool
environment needs numpy and pytest for the harness command:

```console
uvx --from "klayout-tools==0.8.0" --with numpy --with pytest klt signoff \
    --attest 10 --inventory manifests/repo-hygiene.inventory.json \
    -o manifests/repo-hygiene.attest.json
```

Add `--check manifests/repo-hygiene.attest.json` (instead of `-o`) to verify it still
reproduces. `klayout-tools` 0.7.0 has no `--attest`; the pin was bumped to 0.8.0 for it.
