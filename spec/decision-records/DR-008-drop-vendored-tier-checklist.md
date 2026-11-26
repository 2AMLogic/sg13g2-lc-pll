# DR-008: Drop the vendored design-evidence tier checklist; the pinned klt selects it

- **Status**: accepted (operator ruling)
- **Date**: 2026-11-24
- **Decided by**: Operator ruling of 2026-11-23 on #223 (attended `/fleet:decide` round 20261121-r19, q103), made once for
  the twelve repos that asked the same question. Implemented by Builder agent.

## Context

`manifests/design-evidence-tiers.md` was vendored byte-identical from `2AMLogic/klayout-tools` and passed to
`klt signoff` with `--tiers-doc`, with a hand-followed re-vendor rule at every pin bump. The pinned
`klayout-tools==0.9.1` wheel bundles the same bytes (sha256 `08dcbfd2...`).

## Decision

Delete the vendored copy and drop `--tiers-doc` from every caller (`.github/workflows/signoff.yml`,
`manifests/README.md`). The pinned klayout-tools release alone selects the checklist. This reverses the earlier decision
to vendor the document. The README links the document at the pinned tag (`v0.9.1`).

The CI comparison of a fresh `klt signoff` run against the committed record is kept: it catches a checklist change at a
pin bump, and `source_doc_content_hash` still pins the checklist bytes.

## Effect on the record

Regenerated once with the pinned tool. The only change is `source_doc`
(`manifests/design-evidence-tiers.md` -> `docs/design-evidence-tiers.md`). Every item verdict and the tier result are
unchanged (tier `null`, 4 of 11 T1 items met); `source_doc_content_hash` is unchanged.
