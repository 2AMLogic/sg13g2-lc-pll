#!/usr/bin/env bash
# Every tracked .py file must compile on the interpreter this runs under (#234). CI pins
# Python 3.10 (.github/workflows/{harness,signoff}.yml) but ran no layout/*.py, so a
# syntax error that is only legal from 3.12 (PEP 701 nested f-string quotes) sat on main
# unnoticed. Syntax only: compile() never imports, so klayout/numpy are not needed.
#
#   scripts/test-py-compile.sh            # all tracked *.py
#   scripts/test-py-compile.sh a.py b.py  # just these
#
# Writes no bytecode (no __pycache__ in the tree). Needs bash, git, python3.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
PY="${PY_COMPILE_PYTHON:-python3}"

if [ "$#" -gt 0 ]; then printf '%s\0' "$@"; else git ls-files -z '*.py'; fi \
  | xargs -0 --no-run-if-empty "${PY}" -I -c '
import sys
bad = []
for f in sys.argv[1:]:
    try:
        with open(f, encoding="utf-8") as fh:
            compile(fh.read(), f, "exec")
    except SyntaxError as e:
        bad.append(f)
        print(f"FAIL {f}:{e.lineno}: {e.msg}", file=sys.stderr)
    except (OSError, UnicodeDecodeError) as e:
        bad.append(f)
        print(f"FAIL {f}: {e}", file=sys.stderr)
ver = sys.version.split()[0]
print(f"py-compile: {len(sys.argv) - 1} files, {len(bad)} failed (python {ver})")
sys.exit(1 if bad else 0)
'
