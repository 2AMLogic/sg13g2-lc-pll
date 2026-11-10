import subprocess, os
M = "/home/ubuntu/share/pdk/ihp-sg13g2/libs.tech/ngspice"
geoms = [("1u", "9.05u"), ("2u", "9.05u"), ("1u", "15.3u"), ("1u", "77.7u"), ("1u", "46.4u"), ("1u", "108.8u")]
for sec in ("res_typ", "res_wcs", "res_bcs"):
    for t in (27, 125):
        d = f"/tmp/i168/rext/{sec}-{t}"
        os.makedirs(d, exist_ok=True)
        lines = [f"* rppd extraction", f".lib {M}/models/cornerRES.lib {sec}", f".temp {t}"]
        for i, (w, l) in enumerate(geoms, 1):
            lines.append(f"V{i} a{i} 0 0.1")
            lines.append(f"X{i} a{i} 0 0 rppd w={w} l={l}")
        lines += [".control", f"pre_osdi {M}/osdi/r3_cmc.osdi", "op"]
        lines += [f"print -i(v{i})" for i in range(1, len(geoms) + 1)]
        lines += [".endc", ".end"]
        open(f"{d}/r.cir", "w").write("\n".join(lines) + "\n")
        out = subprocess.run(["ngspice", "-b", "r.cir"], cwd=d, capture_output=True, text=True).stdout
        vals = {}
        for ln in out.splitlines():
            ln = ln.strip()
            if ln.startswith("-i(v") and "=" in ln:
                k, v = ln.split("=")
                vals[k.strip()] = 0.1 / float(v)
        print(sec, t, {f"{g[0]}x{g[1]}": round(vals.get(f"-i(v{i+1})", float('nan')), 1) for i, g in enumerate(geoms)})
