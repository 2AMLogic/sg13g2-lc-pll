# spec

- [`target-spec.md`](target-spec.md): the ratified target specification
  (targets, none measured), including the `sg13g2-vco` interface table.
- [`decision-records/`](decision-records/): one record per spec decision.
  `DR-001` ratifies the target spec. Records are append-only: a changed row
  needs a superseding record.
  `DR-002` resolves gate G3 (second-stage flavour: HBT CML).
  `DR-003` proposes the row 11 loop-power fallback (<= 30 mW); proposed, not ratified.
  `DR-008` proposes relaxing row 7 (CP mismatch) from 2 % to 6 % through the
  relax-after-measured-FAIL gate; proposed only, row 7 is unchanged until ratified.
