#!/usr/bin/env bash
# PDK-free test of scripts/check_osdi_preload.py (#456): passes on this tree, and fails on a
# scratch tree where an unlisted generator preloads psp103.osdi without psp103_nqs.osdi.
#   scripts/test-osdi-preload.sh
set -uo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CK=(python3 -I "${SRC}/scripts/check_osdi_preload.py")
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
bad=0
ok()  { echo "ok   $1"; }
bd()  { echo "FAIL $1"; bad=1; }

"${CK[@]}" --root "${SRC}" >/dev/null && ok "this tree passes" || { bd "this tree"; "${CK[@]}" --root "${SRC}"; }

mk() { mkdir -p "${T}/$1/scripts" "${T}/$1/sim/g"; echo '{"exempt":{}}' > "${T}/$1/scripts/osdi-preload-allowlist.json"; }
OS='$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/osdi/'
mk neg; printf 'o = {"osdi_preload": ["%spsp103.osdi", "%sr3_cmc.osdi"]}\n' "${OS}" "${OS}" > "${T}/neg/sim/g/make_requests.py"
"${CK[@]}" --root "${T}/neg" >/dev/null && bd "negative: psp103-only generator must fail" || ok "negative: psp103-only generator fails"

mk pos; printf 'o = {"osdi_preload": ["%spsp103.osdi", "%spsp103_nqs.osdi"]}\n' "${OS}" "${OS}" > "${T}/pos/sim/g/make_requests.py"
"${CK[@]}" --root "${T}/pos" >/dev/null && ok "psp103 + psp103_nqs passes" || bd "psp103 + nqs must pass"

mk rec; mkdir -p "${T}/rec/sim/g/records"; printf 'osdi_preload psp103.osdi\n' > "${T}/rec/sim/g/records/x.sh"
"${CK[@]}" --root "${T}/rec" >/dev/null && ok "records/ is not scanned" || bd "records/ must be skipped"

mk stale; echo '{"exempt":{"sim/g/gone.py":{"reason":"r","evidence":"e"}}}' > "${T}/stale/scripts/osdi-preload-allowlist.json"
"${CK[@]}" --root "${T}/stale" >/dev/null && bd "stale allowlist entry must fail" || ok "stale allowlist entry fails"
exit "${bad}"
