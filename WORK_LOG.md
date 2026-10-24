# Work Log

Chronological record of merged PRs and closed issues, maintained by the Guide triage agent.

### 2026-10-24

- **PR #6**: ci: grade T1 tier state with klt signoff against a committed verdict
- **Issue #4** (closed): Commit a T1 block manifest and a klt signoff CI job (T1 item 10)

### 2026-10-23

- **PR #27**: refactor: source shared lib-pdk.sh in the VCO smoke bench
- **PR #25**: feat: warn and record when ngspice differs from the pinned version
- **Issue #26** (closed): Consolidate run-vco-smoke.sh PDK/pin check into lib-pdk.sh (copy has drifted: no thread cap)
- **Issue #22** (closed): sim/pins.json ngspice pin says 47; CP/PFD records ran on ngspice-46
- **PR #21**: feat: charge-pump design sources, CP/PFD benches, and the PFD pin with its failed 50 MHz re-grade
- **PR #20**: feat(sim): method-L loop model and loop-filter sizing over Kvco and I_cp
- **Issue #18** (closed): Linear phase-domain loop model: size the type-II 3rd-order loop filter and grade f_c / PM over the Kvco and I_cp range (spec rows 5, 6, 8 method L)

### 2026-10-21

- **PR #14**: Bump Repo Skills 0.24.3 -> 0.24.7

### 2026-10-20

- **PR #11**: fix: wire package.json gate scripts to fetch-vco negative controls
- **Issue #10** (closed): Replace always-green stub check scripts in package.json with the repo's real checks

### 2026-10-18

- **PR #9**: feat: pin sg13g2-vco with hash-verified fetch and a smoke bench

### 2026-10-17

- **PR #7**: docs(spec): ratify LC-PLL target spec, VCO interface table and DR-001
- **PR #1**: chore(loom): Install Loom 0.19.1181
- **Issue #2** (closed): Draft and ratify the target spec
