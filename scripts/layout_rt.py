"""Shared stream round-trip machinery for the layout test harnesses (test-only).

`scripts/test-layout-cells.sh` and `scripts/test-layout-top.sh` both assert that the
production geometry digest (`layout/cells/common.py` `digest()`, writer-independent since
#263) survives a KLayout read->write->read of a stream, while the digest as it was before
#263 -- the same per-layer records hashed in `ly.layer_indexes()` enumeration order, which
a re-save permutes -- does not. RoundTrip.compare checks the layer order, the two stream
digests and the recorded digest for both harnesses. Each caller reports its own outcomes: the per-cell
KNOWN-GAP/PASS/FAIL lines in test-layout-cells.sh, the scored `round-trip: ...; refusing`
exits in test-layout-top.sh, and each harness's own inserted-shape control.

`enum_digest` applies the instance transform to label positions -- the production
convention documented on `cells.common.digest()` (the cell helper's pre-#379 copy hashed
the child cell's own coordinates; the two positions coincide for the six generated cells,
and the injected fault this module exists to keep is layer order alone).
"""
import hashlib
from dataclasses import dataclass

import klayout.db as db


def read(path):
    ly = db.Layout()
    ly.read(path)
    return ly


def _layer_order(ly):
    """(layer, datatype) pairs in `ly.layer_indexes()` enumeration order: the writer
    artefact a re-save permutes and digest() must not depend on."""
    return [(ly.get_info(i).layer, ly.get_info(i).datatype) for i in ly.layer_indexes()]


@dataclass(frozen=True)
class Comparison:
    order_changed: bool
    original_digest: str
    resaved_digest: str
    digest_survived: bool
    matches_record: bool


class RoundTrip:
    """An original stream and its re-read KLayout save, reusable across digest functions."""

    def __init__(self, src, dst, cell, recorded):
        self.original = read(src)
        self.original.write(dst)
        self.resaved = read(dst)
        self.cell = cell
        self.recorded = recorded

    def compare(self, digest):
        original = digest(self.original, self.original.cell(self.cell))
        resaved = digest(self.resaved, self.resaved.cell(self.cell))
        return Comparison(
            order_changed=_layer_order(self.original) != _layer_order(self.resaved),
            original_digest=original,
            resaved_digest=resaved,
            digest_survived=original == resaved,
            matches_record=original == self.recorded,
        )


def digest_of(path, cell, fn):
    """Digest `cell` from the stream at `path` with `fn`: `cells.common.digest` for the
    production value, `enum_digest` for the pre-#263 one."""
    ly = read(path)
    return fn(ly, ly.cell(cell))


def enum_digest(ly, cell):
    """digest() before #263: identical records, hashed in layer_indexes() enumeration order."""
    h = hashlib.sha256()
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        r = db.Region(cell.begin_shapes_rec(li))
        r.merge()
        polys = sorted(str(p) for p in r.each())
        txt = sorted(f"{s.text_string}@{(it.trans() * s.text_trans.disp).x},{(it.trans() * s.text_trans.disp).y}"
                     for it in cell.begin_shapes_rec(li) for s in [it.shape()] if s.is_text())
        if polys or txt:
            h.update(f"{info.layer}/{info.datatype}|{';'.join(polys)}|{';'.join(txt)}\n".encode())
    return h.hexdigest()
