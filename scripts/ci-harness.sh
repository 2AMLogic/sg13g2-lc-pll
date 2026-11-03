#!/usr/bin/env bash
# The PDK-free harness tests: the one command list CI (.github/workflows/harness.yml),
# `package.json` test and the repo-hygiene inventory (manifests/repo-hygiene.inventory.json)
# all run, so the three cannot drift apart. Needs bash, jq, curl or gh (network, for the
# two fetch tests), python3 with numpy and pytest.
#
#   scripts/ci-harness.sh
#
# Not run here (they need an ihp-sg13g2 install and ngspice; run them locally, see README
# "Reproduce the records"): scripts/test-ngpin.sh, scripts/test-cp-dc-negative.sh,
# design/netlist.sh --check (needs xschem).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
bash scripts/test-fetch-vco.sh 2AMLogic/sg13g2-vco fetch-vco.sh design/vco.spice
bash scripts/test-fetch-vco.sh 2AMLogic/sg13g2-pll fetch-pll.sh design/pfd.sch
python3 scripts/gen_prescaler_vce_request.py --check
python3 -m pytest -q -p no:cacheprovider sim/loop-model sim/prescaler-g1
