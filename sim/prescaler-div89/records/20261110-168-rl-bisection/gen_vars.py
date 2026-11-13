"""Scratch generator for the #168 bisection variants (not committed)."""
import json, os, re, sys

WT = "/home/ubuntu/GitHub/sg13g2-lc-pll/.loom/worktrees/issue-168"
SRC = f"{WT}/design/netlist/prescaler.spice"
CIR = f"{WT}/sim/prescaler-div89/div89_chain.cir"
REQ = f"{WT}/sim/prescaler-div89/div89_chain.request.json"
OUT = "/tmp/i168/vars"

# instance-name prefix -> class
CLS = {
    "XRL": "RL", "XRT": "RT", "XRTC": "RTC", "XRF": "EF", "XRDF": "EF",
    "XRREF": "BIAS", "XRIN": "BIAS", "XRD1": "BIAS", "XRD2": "BIAS",
}
# nominal ideal values of the pre-#164 netlist, keyed by (w, l)
IDEAL = {("1u", "9.05u"): 2400, ("2u", "9.05u"): 1200, ("1u", "15.3u"): 4000,
         ("1u", "77.7u"): 20000, ("1u", "46.4u"): 12000, ("1u", "108.8u"): 28000}
# SLOW (res_wcs) / 125 C rppd values extracted with a single DC op (rext.py)
WCS125 = {("1u", "9.05u"): 2673.5, ("2u", "9.05u"): 1344.5, ("1u", "15.3u"): 4476.0,
          ("1u", "77.7u"): 22472.4, ("1u", "46.4u"): 13445.4, ("1u", "108.8u"): 31441.7}


def classify(name):
    # longest prefix first so XRTC is not read as XRT
    for p in sorted(CLS, key=len, reverse=True):
        if name == p or (name.startswith(p) and name[len(p):].isdigit()) or name == p:
            return CLS[p]
    return None


def make(groups, table, subckts=None):
    """Replace rppd instances of the given classes (inside optional subckts) with ideal R from table."""
    out, cur = [], None
    for ln in open(SRC).read().splitlines():
        m = re.match(r"\.subckt\s+(\S+)", ln)
        if m:
            cur = m.group(1)
        mm = re.match(r"(X\w+)\s+(\S+)\s+(\S+)\s+(\S+)\s+rppd\s+w=(\S+)\s+l=(\S+)", ln)
        if mm and (subckts is None or cur in subckts):
            nm, a, b, _, w, l = mm.groups()
            if classify(nm) in groups:
                out.append(f"R{nm[1:]} {a} {b} {table[(w, l)]}")
                continue
        out.append(ln)
    return "\n".join(out) + "\n"


VARIANTS = {
    "pdk": (set(), None, None),
    "ideal_all_nom": ({"RL", "RT", "RTC", "EF", "BIAS"}, IDEAL, None),
    "ideal_all_wcs125": ({"RL", "RT", "RTC", "EF", "BIAS"}, WCS125, None),
    "ideal_RL_nom": ({"RL"}, IDEAL, None),
    "ideal_RT_nom": ({"RT"}, IDEAL, None),
    "ideal_RTC_nom": ({"RTC"}, IDEAL, None),
    "ideal_EF_nom": ({"EF"}, IDEAL, None),
    "ideal_BIAS_nom": ({"BIAS"}, IDEAL, None),
}


def write_variant(name, groups, table, subckts, vdd=(2.97,), fin=(5.5e9,), mcv=(0, 3.3)):
    d = f"{OUT}/{name}"
    os.makedirs(d, exist_ok=True)
    open(f"{d}/prescaler.spice", "w").write(make(groups, table, subckts) if groups else open(SRC).read())
    cir = open(CIR).read().replace(".include ../../design/netlist/prescaler.spice", ".include prescaler.spice")
    open(f"{d}/div89_chain.cir", "w").write(cir)
    r = json.load(open(REQ))
    r["netlist"] = "div89_chain.cir"
    r["corners"]["process"] = [p for p in r["corners"]["process"] if p["name"] == "SLOW"]
    r["corners"]["temperature_c"] = [125]
    v, f, m = [], [], []
    for a in vdd:
        for b in fin:
            for c in mcv:
                v.append(a); f.append(b); m.append(c)
    r["corners"]["params"] = {"vddv": v, "fin": f, "mcv": m}
    json.dump(r, open(f"{d}/req.json", "w"), indent=1)
    return f"{d}/req.json"


if __name__ == "__main__":
    names = sys.argv[1:] or list(VARIANTS)
    for n in names:
        g, t, s = VARIANTS[n]
        print(write_variant(n, g, t, s))
