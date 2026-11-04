"""Pure (klayout-free) .subckt reading and flattening, shared by layout/cells/common.py and
scripts/gen_prescaler_vce_request.py so one parser reads design/netlist/*.spice."""


class PlanError(Exception):
    pass


# --- netlist reading and flattening (pure) ---------------------------------------------


def read_subckts(path):
    """{subckt: {"ports": [...], "cards": [{name, model, nets, params}]}}; handles `+` lines."""
    joined = []
    with open(path) as f:
        for raw in f.read().splitlines():
            line = raw.rstrip()
            if line.startswith("+") and joined:
                joined[-1] += " " + line[1:].strip()
            else:
                joined.append(line)
    out, cur = {}, None
    for line in joined:
        s = line.strip()
        if s.startswith("**.subckt") or s.startswith("**.ends"):
            s = s[2:]
        if not s or s.startswith("*"):
            continue
        low = s.lower()
        if low.startswith(".subckt"):
            t = s.split()
            cur = t[1]
            out[cur] = {"ports": t[2:], "cards": []}
        elif low.startswith(".ends"):
            cur = None
        elif s.startswith(".") or cur is None:
            continue
        else:
            t = s.split()
            params, pos = {}, []
            for tok in t[1:]:
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    params[k.lower()] = v
                else:
                    pos.append(tok)
            if not pos:
                raise PlanError(f"unparsable card: {s!r}")
            if t[0][0] in "Rr" and len(pos) == 3:      # `Rname n1 n2 value`: ideal resistor
                pos = pos[:2] + ["ideal_res"]
            out[cur]["cards"].append({"name": t[0], "model": pos[-1], "nets": pos[:-1], "params": params})
    return out


def flatten(subckts, top, leaf_models, net_map=None, prefix=""):
    """Leaf devices of `top`: [{path, model, nets, params}], hierarchical nets namespaced.

    `leaf_models` are the models that end the walk. `net_map` optionally pre-maps `top`'s own
    nets (default: each is namespaced by `prefix`); `prefix` is prepended to every path and net."""
    if top not in subckts:
        raise PlanError(f"no .subckt {top!r}")
    out = []

    def walk(name, prefix, net_map):
        for c in subckts[name]["cards"]:
            nets = [n if n.endswith("!") else net_map.get(n, prefix + n) for n in c["nets"]]
            if c["model"] in leaf_models:
                out.append({"path": prefix + c["name"], "model": c["model"], "nets": nets,
                            "params": c["params"]})
            elif c["model"] in subckts:
                ports = subckts[c["model"]]["ports"]
                if len(ports) != len(nets):
                    raise PlanError(f"{prefix}{c['name']}: {c['model']} has {len(ports)} ports, "
                                    f"instantiated with {len(nets)}")
                walk(c["model"], prefix + c["name"] + ".", dict(zip(ports, nets)))
            else:
                raise PlanError(f"{prefix}{c['name']}: no layout primitive for model {c['model']!r}")

    walk(top, prefix, net_map or {})
    return out
