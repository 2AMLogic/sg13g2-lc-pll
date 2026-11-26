# spec

- [`target-spec.md`](target-spec.md): the ratified target specification
  (targets, none measured), including the `sg13g2-vco` interface table.
- [`decision-records/`](decision-records/): one record per spec decision.
  `DR-001` ratifies the target spec. Records are append-only: a changed row
  needs a superseding record.
  `DR-002` resolves gate G3 (second-stage flavour: HBT CML).
  `DR-003` proposes the row 11 loop-power fallback (<= 30 mW); proposed, not ratified.
  `DR-005` supersedes row 4's prescaler arrangement with a div-2/3 first stage plus
  a fixed div-4 (P = 8/9), restoring contiguous N; proposed, not ratified.
  `DR-006` states the clock-output interface (row 15: swing and load) as not met; proposed,
  not ratified.
  `DR-008` drops the vendored design-evidence tier checklist and the `--tiers-doc`
  override; the pinned `klt` selects it (operator ruling of 2026-11-23 on #223).
  This index lists only records on `main`. A `DR-NNN` number is claimed by the PR
  that proposes it, so the next free number is read off `main` plus the open PRs,
  not cached here.
