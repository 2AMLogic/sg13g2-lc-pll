#!/usr/bin/env bash
# Fetch the pinned sg13g2-pll PFD files named in reuse.lock.json and verify them.
#
#   scripts/fetch-pll.sh            fetch every file at the pinned commit, verify, install
#   scripts/fetch-pll.sh --verify   verify the already-fetched files only (no network)
#
# Same lock schema, same checks and same refusals as scripts/fetch-vco.sh (short SHA,
# ref, non-fetched mode, sha256 mismatch, file missing at the commit): it is that script
# pointed at the sg13g2-pll import through its FETCH_VCO_REPO knob, not a fork of it.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export FETCH_VCO_REPO="${FETCH_PLL_REPO:-2AMLogic/sg13g2-pll}"
exec "${ROOT}/scripts/fetch-vco.sh" "$@"
