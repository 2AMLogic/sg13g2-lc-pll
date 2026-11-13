# spec

- [`target-spec.md`](target-spec.md): the ratified target specification
  (targets, none measured), including the `sg13g2-vco` interface table.
- [`decision-records/`](decision-records/): one record per spec decision.
  `DR-001` ratifies the target spec. Records are append-only: a changed row
  needs a superseding record.
  `DR-002` resolves gate G3 (second-stage flavour: HBT CML).
  `DR-003` proposes the row 11 loop-power fallback (<= 30 mW); proposed, not ratified.
  `DR-007` states the reference phase-noise requirement (R-REF-1), splits DR-001's
  in-band share three ways, and defines method N (charge pump only); proposed.
