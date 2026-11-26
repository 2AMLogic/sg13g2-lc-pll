"""Check the integrated stream hash in every committed LVS report (#413, #419)."""

import json
import sys
from decimal import Decimal
from pathlib import Path


def reject_constant(token):
    # Python's decoder accepts NaN and infinities by default.
    raise ValueError(f"{token} is not a JSON number")


def read_envelope(path):
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip(" \t\r\n"):
            sys.exit(f"lvs-fresh: {path} is empty; refusing")
        # The hash check does not depend on the interpreter's integer digit limit.
        return json.loads(text, parse_constant=reject_constant, parse_int=Decimal)
    except (ValueError, RecursionError) as error:
        sys.exit(f"lvs-fresh: {path} is not valid JSON; refusing ({error})")
    except OSError as error:
        sys.exit(f"lvs-fresh: cannot read {path}; refusing ({error})")


def names_stream(layout, report, root):
    if isinstance(layout, str):
        try:
            return (report.parent / layout).resolve() == root / "layout/top.gds"
        except (OSError, ValueError, RuntimeError):
            # This string cannot resolve to the integrated GDS.
            return False
    return (isinstance(layout, dict) and layout.get("scope") == "repo"
            and layout.get("path") == "layout/top.gds")


def check(root, stream):
    found = 0
    for path in sorted((root / "layout/lvs").rglob("*.lvs.json")):
        envelope = read_envelope(path)
        if not isinstance(envelope, dict) or not names_stream(envelope.get("layout"), path, root):
            continue
        environment = envelope.get("environment")
        pin = environment.get("layout_sha256") if isinstance(environment, dict) else None
        if not pin:
            sys.exit(f"lvs-fresh: {path} records no environment.layout_sha256; refusing")
        if pin != stream:
            sys.exit(f"lvs-fresh: {path} pins layout sha256 {pin} != stream {stream}; refusing")
        found += 1
    if not found:
        sys.exit(f"lvs-fresh: no *.lvs.json under {root}/layout/lvs names the integrated GDS; refusing")
    print(f"lvs-fresh: {found} committed report(s) pin the shipped stream {stream}")


if __name__ == "__main__":
    check(Path(sys.argv[1]).resolve(), sys.argv[2])
