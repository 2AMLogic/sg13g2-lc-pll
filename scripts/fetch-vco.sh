#!/usr/bin/env bash
# Fetch the pinned sg13g2-vco files named in reuse.lock.json and verify them.
#
#   scripts/fetch-vco.sh            fetch every file at the pinned commit, verify, install
#   scripts/fetch-vco.sh --verify   verify the already-fetched files only (no network)
#
# `fetched` mode: no VCO bytes are committed here; they land under .fetched/
# (gitignored). Exits non-zero on a malformed lock, a missing file at the pinned
# commit, or any sha256 mismatch. Needs bash, jq, sha256sum, and curl or gh.
# Each file is fetched with up to three curl-then-gh passes (1 s, 2 s backoff) so a
# transient transport failure on one blob cannot fail the gate; the final refusal
# names the last error seen instead of discarding it (#348).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK="${REUSE_LOCK:-${ROOT}/reuse.lock.json}"
FROM_REPO="${FETCH_VCO_REPO:-2AMLogic/sg13g2-vco}"
MODE_ARG="${1:-fetch}"

die() { echo "fetch-vco: error: $*" >&2; exit 1; }

case "${MODE_ARG}" in fetch|--verify) ;; *) die "usage: $0 [--verify]" ;; esac
command -v jq >/dev/null || die "jq is required"
command -v sha256sum >/dev/null || die "sha256sum is required"
[ -f "${LOCK}" ] || die "${LOCK} not found"

# The lock must hold exactly one import of the VCO, in fetched mode.
n="$(jq --arg r "${FROM_REPO}" '[.imports[]? | select(.from == $r)] | length' "${LOCK}")"
[ "${n}" = 1 ] || die "${LOCK} must have exactly one import from ${FROM_REPO} (found ${n})"
entry='.imports[] | select(.from == $r)'
commit="$(jq -r --arg r "${FROM_REPO}" "${entry} | .commit // \"\"" "${LOCK}")"
mode="$(jq -r --arg r "${FROM_REPO}" "${entry} | .mode // \"\"" "${LOCK}")"
[[ "${commit}" =~ ^[0-9a-f]{40}$ ]] || die "commit '${commit}' is not a full 40-hex SHA (short SHAs and refs are refused)"
[ "${mode}" = fetched ] || die "mode is '${mode}', expected 'fetched'"
nfiles="$(jq --arg r "${FROM_REPO}" "[${entry} | .files[]?] | length" "${LOCK}")"
[ "${nfiles}" -gt 0 ] || die "lock lists no files"

# curl's own `--retry 2` covers timeouts and 408/429/5xx only (a permanent 404 is not
# retried); a reset or refused connection is retried by the outer loop below, with
# backoff. A 404 from both legs is a permanent bad pin, so the loop stops at once
# instead of sleeping through retries that cannot change the answer.
fetch_one() { # <upstream path> <dest>  ->  0 on success; sets fetch_err on failure
  local up="$1" dest="$2" attempt backoff=1 gone
  command -v curl >/dev/null || command -v gh >/dev/null ||
    { fetch_err="neither curl nor gh is installed"; return 1; }
  for attempt in 1 2 3; do
    [ "${attempt}" = 1 ] || { sleep "${backoff}"; backoff=$((backoff * 2)); }
    : > "${tmp}/fetch-err"; : > "${tmp}/err-curl"; : > "${tmp}/err-gh"; gone=1
    if command -v curl >/dev/null; then
      curl -fsSL --retry 2 -o "${dest}" \
        "https://raw.githubusercontent.com/${FROM_REPO}/${commit}/${up}" 2>"${tmp}/err-curl" && return 0
      grep -q 'error: 404' "${tmp}/err-curl" || gone=0
    fi
    if command -v gh >/dev/null; then
      gh api -H "Accept: application/vnd.github.raw" \
        "repos/${FROM_REPO}/contents/${up}?ref=${commit}" >"${dest}" 2>"${tmp}/err-gh" && return 0
      grep -q 'HTTP 404' "${tmp}/err-gh" || gone=0
    fi
    cat "${tmp}/err-curl" "${tmp}/err-gh" >"${tmp}/fetch-err"
    [ "${gone}" = 0 ] || break
  done
  fetch_err="$(tr '\n' ' ' <"${tmp}/fetch-err")"
  [ -n "${fetch_err// /}" ] || fetch_err="no error text captured"
  return 1
}

fail=0
tmp="$(mktemp -d)"; trap 'rm -rf "${tmp}"' EXIT
while IFS=$'\t' read -r up local_rel want; do
  [[ "${want}" =~ ^[0-9a-f]{64}$ ]] || { echo "fetch-vco: bad sha256 for ${up}: '${want}'" >&2; fail=1; continue; }
  case "${local_rel}" in /*|*..*) die "unsafe local path '${local_rel}'" ;; esac
  dest="${ROOT}/${local_rel}"
  if [ "${MODE_ARG}" = fetch ]; then
    mkdir -p "${tmp}/$(dirname "${up}")"
    fetch_one "${up}" "${tmp}/${up}" || { echo "fetch-vco: ${up} missing or unreachable at ${commit} (last error: ${fetch_err})" >&2; fail=1; continue; }
    got="$(sha256sum "${tmp}/${up}" | cut -d' ' -f1)"
    if [ "${got}" != "${want}" ]; then
      echo "fetch-vco: MISMATCH ${up}: lock ${want}, fetched ${got}" >&2; fail=1; continue
    fi
    mkdir -p "$(dirname "${dest}")"; cp "${tmp}/${up}" "${dest}"
  fi
  [ -f "${dest}" ] || { echo "fetch-vco: ${local_rel} not fetched (run without --verify)" >&2; fail=1; continue; }
  got="$(sha256sum "${dest}" | cut -d' ' -f1)"
  if [ "${got}" = "${want}" ]; then echo "ok  ${got}  ${up}"
  else echo "fetch-vco: MISMATCH ${local_rel}: lock ${want}, on disk ${got}" >&2; fail=1; fi
done < <(jq -r --arg r "${FROM_REPO}" "${entry} | .files[] | [.upstream, .local, .sha256] | @tsv" "${LOCK}")

[ "${fail}" = 0 ] || die "verification failed; refusing to use the VCO files"
echo "fetch-vco: ${FROM_REPO}@${commit} verified (${nfiles} files)"
