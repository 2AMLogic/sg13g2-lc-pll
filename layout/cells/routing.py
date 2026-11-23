"""Intra-cell routing plan for routed cells (#343): the legs `klt gen-compose` draws.

`klt gen-compose` does not search: a leg is a via-drop landing pad on each endpoint, an
approach stub one leg-width long out of every port along the port's facing direction, then
a Manhattan polyline through the caller's waypoints, so the caller owns the topology. This
module plans those legs from the generator reports and keeps a rectangle model of the
metal every accepted leg draws, per plane and per net:

  * vertical and horizontal metal are separate planes. Column chains -- a net's pins that
    share an x, split wherever a foreign pin sits between two of them -- are drawn on
    Metal3; a chain leg carries the far pin as its only waypoint, which keeps the wire
    centred on its pads (without it the router lifts it a stub width sideways, onto the
    neighbouring column's pads).
  * everything horizontal -- the link between two of a net's chains, an escape to a block
    edge -- is drawn on Metal2, so it crosses chains without touching them. A link that
    cannot go straight runs through a free strip: the planner only accepts a leg whose
    rectangles keep SPACE_UM from every other net's metal on that plane.
  * between blocks a signal is chained block to block over trunks above the cells, one
    height per trunk, stacked so that a trunk whose escape lines pass under another is
    itself below that one. Which side a leg leaves or enters a block on is chosen to
    leave no two trunks interlocked (each with an escape line inside the other's span).
    Bulk nets -- the nets of the tap rings -- are stars on Metal3 from their westmost end,
    a plane no signal trunk uses.
"""
import collections

from .netlist import PlanError

TOL_UM = 0.3                 # ports closer than this share a column
PAD_UM = 0.42                # side of the via-drop landing pad the router draws on each plane
SPACE_UM = 0.21              # Metal2/Metal3 same-layer minimum spacing (deck metalN.space.1)
W_PAD_UM = 0.42              # in-block leg width: equal to its landing pads, so a stub never overhangs one
W_TRUNK_UM = 0.6             # bulk-net trunk width above the blocks
TRACK_UM = W_TRUNK_UM + SPACE_UM
CORRIDOR0_UM = 1.6           # first corridor line, from the block edge: clear of pin columns
CORRIDOR_PITCH_UM = W_PAD_UM + SPACE_UM
TRUNK_MARGIN_UM = 1.2        # lowest trunk centre above the tallest block
EPS = 1e-6
H_ROLE, V_ROLE = "metal2", "metal3"   # horizontal / vertical planes (ihp-sg13g2 roles)
_DIR = {0: (1.0, 0.0), 90: (0.0, 1.0), 180: (-1.0, 0.0), 270: (0.0, -1.0)}


def _cluster(values, tol):
    out = []
    for v in sorted(values):
        if not out or v - out[-1][-1] > tol:
            out.append([v])
        else:
            out[-1].append(v)
    return [sum(c) / len(c) for c in out]


def _xy(p):
    return (p["x"], p["y"])


def _ref(p):
    return {"block": p["block"], "port": p["port"]}


def _is_tap(p):
    return p["port"].startswith("TAP_")


def _pad(p):
    h = PAD_UM / 2.0
    return (p["x"] - h, p["y"] - h, p["x"] + h, p["y"] + h)


def _seg(p, q, w):
    h = w / 2.0
    return (min(p[0], q[0]) - h, min(p[1], q[1]) - h, max(p[0], q[0]) + h, max(p[1], q[1]) + h)


def _stub_end(p, w):
    dx, dy = _DIR[p["dir"]]
    return (p["x"] + dx * w, p["y"] + dy * w)


def _near(r, o):
    return (r[0] < o[2] + SPACE_UM - EPS and o[0] < r[2] + SPACE_UM - EPS
            and r[1] < o[3] + SPACE_UM - EPS and o[1] < r[3] + SPACE_UM - EPS)


def _aligned(p, q):
    return abs(p[0] - q[0]) < EPS or abs(p[1] - q[1]) < EPS


class _Metal:
    """The rectangles every planned leg draws, per (plane, net). `free` is the same-layer
    spacing test against every other net; a net's own metal may overlap itself."""

    def __init__(self):
        self.rects = collections.defaultdict(list)

    def add(self, plane, net, rects):
        self.rects[(plane, net)].extend(rects)

    def others(self, plane, net, box):
        x0, y0, x1, y1 = box
        return [o for (pl, n), rs in self.rects.items() if pl == plane and n != net for o in rs
                if o[2] > x0 and o[0] < x1 and o[3] > y0 and o[1] < y1]

    def free(self, plane, net, rects):
        xs = [r[0] for r in rects] + [r[2] for r in rects]
        ys = [r[1] for r in rects] + [r[3] for r in rects]
        box = (min(xs) - SPACE_UM, min(ys) - SPACE_UM, max(xs) + SPACE_UM, max(ys) + SPACE_UM)
        return not any(_near(r, o) for r in rects for o in self.others(plane, net, box))


class Block:
    """One placed generator block: the pins it contributes (composed frame, um) and its bbox."""

    def __init__(self, bid, bbox, pins):
        self.id = bid
        self.x0, self.y0, self.x1, self.y1 = bbox
        self.pins = pins

    def nets(self):
        return sorted({p["net"] for p in self.pins})

    def of(self, net):
        return [p for p in self.pins if p["net"] == net]

    def top(self, p):
        """No pin of any net sits above `p` in its column."""
        return not any(abs(q["x"] - p["x"]) <= TOL_UM and q["y"] > p["y"] + EPS for q in self.pins)

    def chains(self, net):
        """Column chains of `net`'s device pins, in x order: pins sharing an x, bottom-up,
        split wherever a pin of another net sits between two of them."""
        pins = sorted((p for p in self.of(net) if not _is_tap(p)), key=lambda p: (p["x"], p["y"]))
        out = []
        for cx in _cluster([p["x"] for p in pins], TOL_UM):
            col = [p for p in pins if abs(p["x"] - cx) <= TOL_UM]
            foreign = [q for q in self.pins if q["net"] != net and abs(q["x"] - cx) <= TOL_UM]
            chain = []
            for a, b in zip(col, col[1:]):
                chain.append(a)
                if any(a["y"] + EPS < q["y"] < b["y"] - EPS for q in foreign):
                    out.append(chain)
                    chain = []
            chain.append(col[-1])
            out.append(chain)
        return out

    def bands(self, metal, plane, net, x0, x1, w):
        """y centres of free horizontal tracks of width w spanning x0..x1: both ends of
        every strip no other net's metal blocks, inside the block and 1 um beyond it."""
        free, y = [], self.y0 - 1.0
        top = self.y1 + 1.0
        box = (min(x0, x1) - w / 2.0 - SPACE_UM, -1e9, max(x0, x1) + w / 2.0 + SPACE_UM, 1e9)
        for o in sorted(metal.others(plane, net, box), key=lambda o: (o[1], o[3])):
            a, b = o[1] - SPACE_UM - w / 2.0, o[3] + SPACE_UM + w / 2.0
            if a > y + EPS:
                free.append((y, min(a, top)))
            y = max(y, b)
        if y < top - EPS:
            free.append((y, top))
        return [y for a, b in free if b - a > EPS for y in (a, b)]


def _leg(metal, net, a, b, mid, w, plane):
    """Plan the leg a -> sa -> mid -> sb -> b, starting on `plane`; a mid point of
    (x, y, role) changes plane there (a via ladder with a landing pad on both planes) and
    the leg continues on `role`. None (nothing drawn) when any rectangle would sit closer
    than SPACE_UM to another net's metal on its plane."""
    sa, sb = _stub_end(a, w), _stub_end(b, w)
    pts = [_xy(a), sa] + list(mid) + [sb, _xy(b)]
    drawn, wp, cur = collections.defaultdict(list), [], plane
    drawn[plane].append(_pad(a))
    for p, q in zip(pts, pts[1:]):
        if not _aligned(p[:2], q[:2]):
            raise PlanError(f"leg {net} {a['port']}->{b['port']}: polyline has a diagonal")
        drawn[cur].append(_seg(p[:2], q[:2], w))
        if len(q) > 2:                       # the plane changes once the route reaches q
            drawn[cur].append(_pad({"x": q[0], "y": q[1]}))
            cur = q[2]
            drawn[cur].append(_pad({"x": q[0], "y": q[1]}))
        wp.append([round(q[0], 3), round(q[1], 3)] + ([q[2]] if len(q) > 2 else []))
    drawn[cur].append(_pad(b))
    if not all(metal.free(pl, net, rs) for pl, rs in drawn.items()):
        return None
    for pl, rs in drawn.items():
        metal.add(pl, net, rs)
    leg = {"from_pin": _ref(a), "to_pin": _ref(b), "width_um": w, "waypoints_um": wp}
    if plane != H_ROLE:
        leg["layer_role"] = plane
    return leg


def _straight(metal, net, a, b, plane, w=W_PAD_UM):
    """a -> b along their shared row or column (stubs aside)."""
    return _leg(metal, net, a, b, [_xy(a), _xy(b)], w, plane)


def _strip(metal, block, net, a, b, plane, w=W_PAD_UM):
    """a -> up or down into a free strip -> across -> b, through the nearest strip that takes
    the whole leg."""
    for y in sorted(block.bands(metal, plane, net, a["x"], b["x"], w), key=lambda y: abs(y - a["y"]) + abs(y - b["y"]))[:6]:
        leg = _leg(metal, net, a, b, [_xy(a), (a["x"], y), (b["x"], y), _xy(b)], w, plane)
        if leg is not None:
            return leg
    return None


def _join(metal, block, net, a, b, planes):
    """Link two pins of one net in one block: straight where they share a row or column
    and nothing foreign lies between, else through a strip; on the first plane that
    takes either."""
    for plane in planes:
        if abs(a["y"] - b["y"]) <= TOL_UM or abs(a["x"] - b["x"]) <= TOL_UM:
            leg = _straight(metal, net, a, b, plane)
            if leg is not None:
                return leg
        leg = _strip(metal, block, net, a, b, plane)
        if leg is not None:
            return leg
    return None


def _link(metal, block, net, new, joined, planes):
    """Join chain `new` to the nearest pin of the already-joined pins `joined`."""
    pairs = sorted(((a, b) for a in new for b in joined),
                   key=lambda ab: abs(ab[0]["x"] - ab[1]["x"]) + abs(ab[0]["y"] - ab[1]["y"]))
    for a, b in pairs:
        leg = _join(metal, block, net, a, b, planes)
        if leg is not None:
            return leg
    raise PlanError(f"{block.id}: no free path joins {net} pins "
                    f"{pairs[0][0]['port']} and {pairs[0][1]['port']}")


def intra(metal, block, rails):
    """Legs inside one block as (net, leg): every column chain on the vertical plane, the
    links that make each net one tree, and the ring ties -- every ring port a device pin
    can still reach, at least one where the net has device pins in the block."""
    out = []
    for net in block.nets():
        pins = block.of(net)
        order = (H_ROLE, V_ROLE)      # Metal3 is the vertical plane: links stay off it where they can
        ch = block.chains(net)
        for c in ch:
            for a, b in zip(c, c[1:]):
                leg = _straight(metal, net, a, b, V_ROLE)
                if leg is None:
                    raise PlanError(f"{block.id}: {net} chain {a['port']}->{b['port']} has no room on {V_ROLE}")
                out.append((net, leg))
        joined = []
        for c in ch:
            if joined:
                out.append((net, _link(metal, block, net, c, joined, order)))
            joined += c
        dev = [p for p in pins if not _is_tap(p)]
        taps = [p for p in pins if _is_tap(p)]
        # A ring tie hugs the ring's own edge, where the vertical plane is empty: prefer it
        # there so a tie never eats a metal2 strip a signal escape needs.
        tie_order = (V_ROLE, H_ROLE)
        tied = False
        for t in taps:
            near = sorted(dev, key=lambda q: abs(q["y"] - t["y"]) + abs(q["x"] - t["x"]))[:4]
            leg = next((leg for p in near for leg in [_join(metal, block, net, p, t, tie_order)] if leg is not None), None)
            tied |= leg is not None
            if leg is not None:
                out.append((net, leg))
        # A ring is one closed conductor: one tied ring port biases all of them, so the star
        # may land on a port no device pin can reach.
        if dev and taps and not tied:
            raise PlanError(f"{block.id}: no free path ties {net} to its ring")
    return out


# --- between blocks -------------------------------------------------------------------------


class _End:
    """One way a between-block leg meets a pin: straight up from it (side None), or through a
    strip to a corridor line beside the block (side "E" or "W"). `mid` is the polyline from
    the pin to that meeting point; `x` its column; `y` where the tall vertical leaves it."""

    def __init__(self, pin, mid, side):
        self.pin, self.mid, self.side = pin, mid, side
        self.x = mid[-1][0]
        self.y = mid[-1][1]


def _options(metal, block, pin):
    """Every feasible way to meet `pin`: straight up on the vertical plane (a top pin),
    else through the nearest free strips out each side on the horizontal plane -- straight
    out of the pin's own column where that column is free, else jogged: along the pin's own
    row to a neighbouring track column (array pin columns pitch 0.46 um, so the pin's own
    column often sits a pad width from the next net's escape), up it to a strip, then out.
    Nothing is drawn."""
    P, net = _xy(pin), pin["net"]
    out = []
    if metal.free(V_ROLE, net, [_seg(P, (pin["x"], block.y1 + 1.0), W_PAD_UM)]):
        out.append(_End(pin, [P], None))
    for side in ("E", "W"):
        sgn = 1.0 if side == "E" else -1.0
        x = block.x1 + CORRIDOR0_UM if side == "E" else block.x0 - CORRIDOR0_UM
        mids = []
        for y in sorted(block.bands(metal, H_ROLE, net, pin["x"], x, W_PAD_UM), key=lambda y: abs(y - pin["y"]))[:5]:
            mids.append([P, (pin["x"], y), (x, y)])
        for k in range(1, 5):
            mx = pin["x"] + sgn * k * CORRIDOR_PITCH_UM
            if sgn * (x - mx) < CORRIDOR_PITCH_UM:
                break
            for y in sorted(block.bands(metal, H_ROLE, net, mx, x, W_PAD_UM), key=lambda y: abs(y - pin["y"]))[:4]:
                mids.append([P, (mx, pin["y"]), (mx, y), (x, y)])
        for mid in mids:
            if metal.free(H_ROLE, net, [_seg(a, b, W_PAD_UM) for a, b in zip(mid, mid[1:])]):
                out.append(_End(pin, mid, side))
    return out


def inter(metal, blocks, order, pins_of, rails):
    """Between-block legs, one record each: a signal is chained west to east between
    consecutive blocks, a bulk net is a star from its westmost end. Each end takes its
    shortest feasible option: with verticals and trunks on different planes no choice of
    side can make two legs interlock."""
    legs = []
    for net in sorted(pins_of):
        by = collections.defaultdict(list)
        for p in pins_of[net]:
            by[p["block"]].append(p)
        bids = [b for b in order if b in by]
        if len(bids) < 2:
            continue
        rail = net in rails
        ends = []   # per block: every feasible way to meet any of the net's pins there
        for b in bids:
            B = blocks[b]
            tap_first = (lambda p: not _is_tap(p)) if rail else (lambda p: not B.top(p))
            opts = [o for p in sorted(by[b], key=lambda p: (tap_first(p), p["x"])) for o in _options(metal, B, p)]
            if not opts:
                raise PlanError(f"{net}: no free way into or out of {b}")
            ends.append(opts)
        idx = [order.index(b) for b in bids]
        for k in range(1, len(ends)):
            i0 = 0 if rail else k - 1
            legs.append({"net": net, "rail": rail, "dep_opts": ends[i0], "arr_opts": ends[k],
                         "bi": (idx[i0], idx[k])})
    return legs


def _corridor(order, i, side):
    """The gap a corridor line lies in: ("first",), ("last",) or the index of its west block."""
    if side == "E":
        return ("last",) if i == len(order) - 1 else i
    return ("first",) if i == 0 else i - 1


def _corridor_base(blocks, order, key):
    if key == ("first",):
        return blocks[order[0]].x0, -1
    if key == ("last",):
        return blocks[order[-1]].x1, 1
    return blocks[order[key]].x1, 1


def finish(metal, blocks, order, legs, y_top):
    """Draw the between-block legs. A leg takes a vertical-plane escape out of each block,
    a horizontal-plane trunk between them, and a vertical-plane approach back in, changing
    plane at a via ladder -- so no two legs can interlock, only share a strip or a corridor
    line. When a leg does not fit, it is retried on its next pair of ends (nearest first),
    with the model rolled back between attempts. Returns [(net, leg)]."""
    def _pair_key(pair, rail):
        # nearest first; a bulk net meets its blocks at ring ports where it can, so the star
        # covers one port and the in-block tie the other -- no pin is left for the router's
        # own nearest-first search to "complete" (it detours outside the metal2/metal3 pair,
        # which the rectangle model does not see)
        return ((0 if (not rail or any(_is_tap(e.pin) for e in pair)) else 1)
                + sum(abs(e.x - e.pin["x"]) + abs(e.y - e.pin["y"]) for e in pair) / 1e6)

    for L in legs:
        L["pairs"] = sorted(((d, a) for d in L["dep_opts"] for a in L["arr_opts"]),
                            key=lambda p: _pair_key(p, L["rail"]))
        L["k"] = 0
    snapshot = {k: list(v) for k, v in metal.rects.items()}
    dead = set()
    result = []
    for _ in range(200):
        metal.rects = {k: list(v) for k, v in snapshot.items()}
        for L in legs:
            L["dep"], L["arr"] = L["pairs"][min(L["k"], len(L["pairs"]) - 1)]
        users = collections.defaultdict(list)
        for L in legs:
            for end, i in ((L["dep"], L["bi"][0]), (L["arr"], L["bi"][1])):
                if end.side:
                    users[_corridor(order, i, end.side)].append(end)
        for key, us in users.items():
            base, sgn = _corridor_base(blocks, order, key)
            for k, end in enumerate(sorted(us, key=lambda e: e.y)):
                x = base + sgn * (CORRIDOR0_UM + k * CORRIDOR_PITCH_UM)
                end.mid[-1] = (x, end.mid[-1][1])
                end.x = x
        tracks = []
        for L in sorted(legs, key=lambda L: (L["rail"], L["net"])):
            lo, hi = sorted((L["dep"].x, L["arr"].x))
            level = 0
            while any(t[0] == level and t[1] - TRACK_UM < hi and lo < t[2] + TRACK_UM for t in tracks):
                level += 1
            tracks.append((level, lo, hi))
            L["h"] = y_top + TRUNK_MARGIN_UM + level * TRACK_UM
        result, failed = [], []
        for L in sorted(legs, key=lambda L: (L["rail"], L["net"])):
            d, a, h = L["dep"], L["arr"], L["h"]
            Pd, Pa = _xy(d.pin), _xy(a.pin)
            # d.mid / a.mid are full pin->corridor polylines (straight, or jogged through a
            # neighbouring track column); the arrival follows its escape in reverse.
            up = [Pd] if d.side is None else list(d.mid) + [(d.x, d.y, V_ROLE)]
            down = [Pa] if a.side is None else [(a.x, a.y, H_ROLE)] + a.mid[::-1][1:]
            mid = up + [(d.x, h), (d.x, h, H_ROLE), (a.x, h), (a.x, h, V_ROLE)] + down
            leg = _leg(metal, L["net"], d.pin, a.pin, mid, W_PAD_UM, H_ROLE if d.side else V_ROLE)
            if leg is None:
                failed.append(L)
            else:
                result.append((L["net"], leg))
        if not failed:
            return result
        adv = next((L for L in failed if id(L) not in dead), None)
        if adv is None:
            return result
        if adv["k"] + 1 < len(adv["pairs"]):
            adv["k"] += 1
        else:
            dead.add(id(adv))
    return result


def plan(blocks, order, rails, y_top):
    """The connectivity plan of a routed cell.

    blocks: {id: Block}; order: block ids west to east; rails: the nets drawn as Metal3
    stars (the tap rings' nets); y_top: the tallest block top. Returns
    ({net: {"pins", "legs"}} in gen-compose's shape, [nets with a leg the model rejected],
    the rectangle model itself -- callers use it to place port labels on clear ground)."""
    metal = _Metal()
    pins_of = collections.defaultdict(list)
    for b in blocks.values():
        for p in b.pins:
            metal.add(H_ROLE, p["net"], [_pad(p)])
            metal.add(V_ROLE, p["net"], [_pad(p)])
            pins_of[p["net"]].append(p)
    conn = {n: {"pins": [_ref(p) for p in ps], "legs": []} for n, ps in pins_of.items()}
    for bid in order:
        for net, leg in intra(metal, blocks[bid], rails):
            conn[net]["legs"].append(leg)
    rejected = []
    for net, leg in finish(metal, blocks, order, inter(metal, blocks, order, pins_of, rails), y_top):
        if leg is None:
            rejected.append(net)
        else:
            conn[net]["legs"].append(leg)
    _cover(metal, blocks, order, rails, conn, pins_of, y_top)
    return conn, rejected, metal


def _cover(metal, blocks, order, rails, conn, pins_of, y_top):
    """Every pin sits on at least one leg. A pin the plan leaves out is fair game for the
    router's own nearest-first completion, which happily detours outside the metal2/metal3
    pair -- geometry the rectangle model never sees. An uncovered pin is wired to the
    nearest covered pin of its net on a fresh trunk above every planned one; the trunk
    level scans upward until the leg fits, so two cover legs never share a level."""
    top = y_top + TRUNK_MARGIN_UM + TRACK_UM * 24
    for net in sorted(pins_of):
        covered = {(l["from_pin"]["block"], l["from_pin"]["port"]) for l in conn[net]["legs"]}
        covered |= {(l["to_pin"]["block"], l["to_pin"]["port"]) for l in conn[net]["legs"]}
        for p in pins_of[net]:
            if (p["block"], p["port"]) in covered:
                continue
            B = blocks[p["block"]]
            opts = _options(metal, B, p)
            near = sorted((q for q in pins_of[net] if (q["block"], q["port"]) in covered),
                          key=lambda q: abs(q["x"] - p["x"]) + abs(q["y"] - p["y"]))
            for q in near:
                BQ = blocks[q["block"]]
                qopts = _options(metal, BQ, q) or [_End(q, [_xy(q)], None)]
                for e in opts:
                    for f in qopts:
                        for k in range(10):
                            ty = top + k * TRACK_UM
                            for line in range(16, 21):
                                # a fresh corridor line beyond every line finish() handed
                                # out, so the metal3 rise clears the escapes already there
                                emid, fmid = list(e.mid), list(f.mid)
                                for end, mid in ((e, emid), (f, fmid)):
                                    if end.side == "E":
                                        mid[-1] = (blocks[end.pin["block"]].x1 + CORRIDOR0_UM
                                                   + line * CORRIDOR_PITCH_UM, mid[-1][1])
                                    elif end.side == "W":
                                        mid[-1] = (blocks[end.pin["block"]].x0 - CORRIDOR0_UM
                                                   - line * CORRIDOR_PITCH_UM, mid[-1][1])
                                ex, fx = emid[-1][0], fmid[-1][0]
                                ey = emid[-1][1]
                                mid = emid + ([(ex, ey, V_ROLE), (ex, ty), (ex, ty, H_ROLE)]
                                              if e.side else [(ex, ty), (ex, ty, H_ROLE)]) \
                                    + [(fx, ty), (fx, ty, V_ROLE)] + fmid[::-1]
                                leg = _leg(metal, net, p, q, mid, W_PAD_UM, H_ROLE if e.side else V_ROLE)
                                if leg is not None:
                                    conn[net]["legs"].append(leg)
                                    covered.add((p["block"], p["port"]))
                                    top = ty + TRACK_UM
                                    break
                            if (p["block"], p["port"]) in covered:
                                break
                        if (p["block"], p["port"]) in covered:
                            break
                    if (p["block"], p["port"]) in covered:
                        break
                if (p["block"], p["port"]) in covered:
                    break
            else:
                raise PlanError(f"{p['block']}.{p['port']} ({net}): no leg covers this pin")
