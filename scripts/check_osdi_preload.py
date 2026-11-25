#!/usr/bin/env python3
"""Guard (#456): a request generator that preloads psp103.osdi must also preload psp103_nqs.osdi.

The PDK's MOS decks instantiate `pspnqs103va` cards; with psp103.osdi alone ngspice drops them
with `Unknown model type pspnqs103va` and the run still "passes". This scans GENERATORS (tracked-style
*.py / *.sh that name `osdi_preload` and `psp103.osdi`), never historical request JSON or anything
under records/ (append-only evidence). Exemptions live in scripts/osdi-preload-allowlist.json, each
with a reason and its evidence. A stale allowlist entry (file gone, or no longer psp103-only) fails
too, so exemptions cannot rot.

  check_osdi_preload.py [--root DIR] [--allowlist FILE]
Exit 0 ok, 1 on violations. PDK-free: pure text scan.
"""
import argparse, json, os, sys

SKIP_DIRS = {".git", ".loom", ".fetched", "records", "node_modules", "__pycache__"}


def code_lines(text):
    return [l for l in text.splitlines() if not l.lstrip().startswith("#")]


def flagged(root):
    """relative paths of generators that preload psp103.osdi without psp103_nqs.osdi"""
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if not f.endswith((".py", ".sh")):
                continue
            p = os.path.join(d, f)
            try:
                code = "\n".join(code_lines(open(p, encoding="utf-8").read()))
            except (UnicodeDecodeError, OSError):
                continue
            if "osdi_preload" in code and "psp103.osdi" in code and "psp103_nqs.osdi" not in code:
                out.append(os.path.relpath(p, root))
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    ap.add_argument("--allowlist", default=None)
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    al = a.allowlist or os.path.join(root, "scripts", "osdi-preload-allowlist.json")
    allow = json.load(open(al))["exempt"] if os.path.exists(al) else {}
    for k, v in allow.items():
        if not v.get("reason") or not v.get("evidence"):
            print(f"FAIL allowlist entry {k} needs both reason and evidence"); return 1
    bad = flagged(root)
    rc = 0
    for p in bad:
        if p not in allow:
            print(f"FAIL {p}: preloads psp103.osdi without psp103_nqs.osdi (pspnqs103va cards would be dropped); add it, or allowlist with evidence"); rc = 1
    for p in allow:
        if p not in bad:
            print(f"FAIL stale allowlist entry {p}: not a psp103-only generator any more or file gone; remove it"); rc = 1
    if rc == 0:
        print(f"ok: {len(bad)} psp103-only generator(s), all allowlisted; every other psp103 preload carries psp103_nqs.osdi")
    return rc


sys.exit(main())
