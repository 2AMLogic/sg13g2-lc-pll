#!/usr/bin/env bash
# sg13g2-lc-pll :: re-stamp one committed `klt signoff --attest` envelope (T1 item 1, 9
# or 10) under the carry rule below, then verify the result reproduces.
#
#   scripts/restamp-attest.sh 1     -> manifests/design-sources.attest.json
#   scripts/restamp-attest.sh 9     -> manifests/testbenches.attest.json  (refuses today)
#   scripts/restamp-attest.sh 10    -> manifests/repo-hygiene.attest.json
#
# This is the one re-stamp entry point: `.github/workflows/signoff.yml` and
# `manifests/README.md` both name it, and it is what the CI failure message tells you to
# run. It writes nothing unless the resulting envelope is `status: pass` and reproduces
# under `--check`.
#
# WHY IT EXISTS (delete it when the pin moves). The pinned klt, 0.8.0, has no way to
# refresh an envelope's file hashes without RUNNING its `local_only` commands: `--attest N
# -o` runs them and `--check` only compares, writing nothing. So carrying a committed
# `local_only` outcome forward is a call into the wheel's own
# `signoff_attest.check_attestation()`, which is exactly what `--check` already does
# internally (it builds the carried envelope, then diffs it against the committed bytes).
# Host klt 0.9.2.dev has `klt signoff --skip-local-only` for this; no published release
# does (0.9.1 checked). When the pin is bumped past a release that ships that flag, DELETE
# this script and call the flag (2AMLogic/klayout-tools#5209 / #5478 / #5480).
#
# THE CARRY RULE. A `local_only` outcome may be carried from the previous envelope only
# when no drifted file can affect that command:
#
#   item 10  `design/netlist.sh --check` reads none of the `hygiene` files (README.md,
#            LICENSE, the two workflows), so drift confined to them is CARRIED.
#   item 1   a drifted `source` or `derived` file is exactly what the six
#            `design/netlist.sh --check <cell>` freshness commands assert, so they are RUN
#            FOR REAL (needs klt and the SG13G2 PDK). If any cannot run, or fails, the
#            script exits non-zero and writes nothing. With no source/derived drift (an
#            inventory-prose edit, say) they are carried instead.
#   item 9   `scripts/run-benches.sh` executes the inventoried bench scripts and decks, so
#            ANY drifted inventoried file means the committed cold-start `pass` cannot be
#            carried: it would assert a bench run that never saw those files. The script
#            refuses and writes nothing. A real cold start belongs on the Spot batch fleet
#            (#242, which waits on #149). This script never runs `scripts/run-benches.sh`.
#
# Every carried outcome is printed as a `[CARRIED]` line and every real run as a `[RAN]`
# line, so the PR that re-stamps can quote them.
set -euo pipefail

KLT_PIN="klayout-tools==0.8.0"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  sed -n '2,41p' "${BASH_SOURCE[0]}"
}

ITEM="${1:-}"
case "${ITEM}" in
  -h|--help) usage; exit 0 ;;
  1)  INVENTORY="manifests/design-sources.inventory.json"
      ENVELOPE="manifests/design-sources.attest.json"
      EXTRA=() ;;
  9)  INVENTORY="sim/testbench-inventory.json"
      ENVELOPE="manifests/testbenches.attest.json"
      EXTRA=() ;;
  # Item 10's `harness-tests` check really runs `bash scripts/ci-harness.sh`, which needs
  # numpy and pytest in klt's own tool environment.
  10) INVENTORY="manifests/repo-hygiene.inventory.json"
      ENVELOPE="manifests/repo-hygiene.attest.json"
      EXTRA=(--with numpy --with pytest) ;;
  *)  echo "restamp-attest.sh: expected a T1 item, one of 1, 9 or 10; got '${ITEM}'" >&2
      echo >&2
      usage >&2
      exit 2 ;;
esac

command -v uvx >/dev/null || {
  echo "restamp-attest.sh: uvx not found on PATH (it runs the pinned ${KLT_PIN}," >&2
  echo "  never the host klt, which is a different version)" >&2
  exit 1
}

cd "${ROOT}"

# `python -I` keeps the repo root off sys.path: the program below imports json, and a
# file named json.py in the tree would otherwise shadow the stdlib module.
uvx --from "${KLT_PIN}" "${EXTRA[@]}" python -I - "${ITEM}" "${INVENTORY}" "${ENVELOPE}" <<'PY'
"""Re-stamp one attest envelope under the carry rule documented in restamp-attest.sh."""

import json
import sys

from klayout_tools import signoff_attest as sa

item = int(sys.argv[1])
inventory = sys.argv[2]
envelope_path = sys.argv[3]


def identity(check):
    """How a command check is named in a [CARRIED] / [RAN] / [FAILED] line."""
    return check.get("name") or check.get("target") or check.get("role") or "command"


def describe(check):
    return "%s %s: %s" % (check.get("role"), identity(check), " ".join(check["argv"]))


def refuse(message):
    print("[REFUSED] %s" % message, file=sys.stderr)
    print("[REFUSED] nothing written; %s is unchanged" % envelope_path, file=sys.stderr)
    raise SystemExit(3)


# check_attestation() builds the carried envelope -- every `local_only` command's
# committed outcome carried forward, the `skipped` marker popped off again -- and diffs
# it against the committed bytes. Its `fresh` payload IS the carried re-stamp, in the
# byte shape `--output` writes. It runs no `local_only` command.
result = sa.check_attestation(item, inventory, envelope_path)
carried = result["fresh"]
with open(envelope_path, "rb") as handle:
    committed = json.loads(handle.read().decode("utf-8"))


def present(envelope):
    return {
        check["path"]: check
        for check in envelope["attestation"]["checks"]
        if check.get("check") == "present"
    }


was, now = present(committed), present(carried)
drifted = sorted(
    [
        (check["role"], path, "changed" if path in was else "added")
        for path, check in now.items()
        if was.get(path, {}).get("content_hash") != check.get("content_hash")
    ]
    + [
        (check["role"], path, "removed from the inventory")
        for path, check in was.items()
        if path not in now
    ]
)
inventory_moved = committed.get("provenance", {}).get("input", {}).get(
    "content_hash"
) != carried["provenance"]["input"]["content_hash"]

print("item %d: %s (inventory %s)" % (item, envelope_path, inventory))
print(
    "  committed vs re-attested: %s; carried envelope status: %s"
    % (result["status"], result["fresh_status"])
)
print("  inventory bytes: %s" % ("CHANGED" if inventory_moved else "unchanged"))
if drifted:
    for role, path, how in drifted:
        print("  [DRIFT] %s %s (%s)" % (role, path, how))
else:
    print("  [DRIFT] none: every inventoried file still matches its committed hash")

# ------------------------------------------------------------------ the carry rule
run_for_real = False
if item == 9:
    if drifted:
        refuse(
            "item 9 carries a `local_only` cold start (bash scripts/run-benches.sh) that "
            "executes the inventoried bench scripts and decks, and %d inventoried file(s) "
            "above have drifted. Carrying the committed `pass` forward would assert a "
            "bench run that never saw them. A real cold start is required, on the Spot "
            "batch fleet per the host rules -- tracked in #242, which waits on #149. This "
            "script never runs scripts/run-benches.sh." % len(drifted)
        )
elif item == 10:
    offenders = [entry for entry in drifted if entry[0] != "hygiene"]
    if offenders:
        refuse(
            "the carry rule only covers item 10 drift confined to its `hygiene` files "
            "(design/netlist.sh --check reads none of them). Drifted outside that: %s"
            % ", ".join("%s %s" % (role, path) for role, path, _ in offenders)
        )
elif item == 1:
    run_for_real = any(role in ("source", "derived") for role, _, _ in drifted)

# ------------------------------------------------------------------ build the envelope
if run_for_real:
    print(
        "  a drifted source/derived file is exactly what the freshness commands assert:\n"
        "  running every local_only command FOR REAL (needs klt and the SG13G2 PDK)"
    )
    # committed_checks=None: build_attestation runs the local_only commands itself.
    envelope = sa.build_attestation(item, inventory)
    for check in envelope["attestation"]["checks"]:
        if check.get("check") == "command":
            print(
                "  [RAN] %s -> exit %s%s"
                % (
                    describe(check),
                    check.get("exit_status"),
                    " (%s)" % check["error"] if check.get("error") else "",
                )
            )
else:
    envelope = carried
    for check in result["skipped_checks"]:
        print(
            "  [CARRIED] %s -> committed outcome %s, NOT re-run"
            % (describe(check), "pass" if check.get("passed") else "FAIL")
        )

if envelope["status"] != "pass":
    for check in envelope["attestation"]["checks"]:
        if not check.get("passed"):
            print("  [FAILED] %s" % json.dumps(check), file=sys.stderr)
    refuse(
        "the re-attested envelope is status %r, not 'pass' (the [FAILED] check(s) above). "
        "Fix the failing check and re-run. If a failing envelope is genuinely what you "
        "mean to commit, write it with `klt signoff --attest` directly and say so in the "
        "PR -- this script will not stamp one." % envelope["status"]
    )

if sa.write_attestation(envelope, envelope_path):
    print("  wrote %s" % envelope_path)
else:
    print("  %s already reproduces byte-for-byte; left untouched" % envelope_path)
PY

# The serialization is confirmed by the thing that grades it, not by inspection: the
# envelope just written has to reproduce under the same `--check` CI runs.
echo "verifying: klt signoff --attest ${ITEM} --check ${ENVELOPE}"
rc=0
uvx --from "${KLT_PIN}" "${EXTRA[@]}" klt signoff --attest "${ITEM}" \
    --inventory "${INVENTORY}" --check "${ENVELOPE}" || rc=$?
if [ "${rc}" -ne 0 ]; then
  echo "restamp-attest.sh: the envelope just written does NOT reproduce (--check exited" >&2
  echo "  ${rc}, expected 0). Treat ${ENVELOPE} as untrustworthy: inspect the drift above" >&2
  echo "  and restore it with 'git checkout -- ${ENVELOPE}'." >&2
  exit 1
fi
echo "restamp-attest.sh: item ${ITEM} re-stamped and reproducing (${ENVELOPE})"
