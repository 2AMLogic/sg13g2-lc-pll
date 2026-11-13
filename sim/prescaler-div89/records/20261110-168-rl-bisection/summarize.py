import json, sys
base = sys.argv[1]
man = json.load(open(f"{base}/set-manifest.json"))
for r in man["requests"]:
    rep = json.load(open(f"{r['dir']}/report.json"))
    name = r["request"].split("/")[-2]
    cells = []
    for c in rep["corners"]:
        x = [m for m in c["measurements"] if m["name"] == "x_zero"][0]
        t = x.get("crossings", {}).get("times", [])
        p = [b - a for a, b in zip(t, t[1:])]
        fin = c["params"]["fin"]; v = c["params"]["vddv"]
        if p:
            rat = [q * fin for q in p]
            cells.append(f"{v}V mc={c['params']['mcv']}: n={len(t)} ratio {min(rat):.2f}..{max(rat):.2f}")
        else:
            cells.append(f"{v}V mc={c['params']['mcv']}: no crossings")
    print(f"{name:18s}", " | ".join(cells))
