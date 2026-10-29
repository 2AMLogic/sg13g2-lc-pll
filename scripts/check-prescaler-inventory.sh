#!/usr/bin/env bash
# Writes or checks design/netlist/prescaler.inventory.json (path + sha256 of the committed prescaler netlist),
# the prescaler's entry for the item-1 `klt signoff --inventory` file that #32 assembles.
#   scripts/check-prescaler-inventory.sh           check (exit 1 if stale)
#   scripts/check-prescaler-inventory.sh --write   rewrite
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
F="${ROOT}/design/netlist/prescaler.inventory.json"
want="$(jq -n --arg p design/netlist/prescaler.spice --arg s "$(sha256sum "${ROOT}/design/netlist/prescaler.spice" | cut -d' ' -f1)" \
  --arg src design/prescaler.sch '{item: 1, block: "prescaler", files: [{path: $p, sha256: $s, derived_from: $src}]}')"
if [ "${1:-}" = "--write" ]; then printf '%s\n' "${want}" > "${F}"; echo "wrote ${F#"${ROOT}/"}"; exit 0; fi
[ -f "${F}" ] && [ "$(jq -S . "${F}")" = "$(printf '%s' "${want}" | jq -S .)" ] && echo "ok  ${F#"${ROOT}/"} current" || { echo "STALE: run scripts/check-prescaler-inventory.sh --write" >&2; exit 1; }
