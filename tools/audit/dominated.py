"""Lists strictly dominated cards with an age class, for tools/audit/fix_dominated.py."""
import glob, json, os, re

def vec(ch):
    e = dict(ch.get("effects", {}))
    if "stress" in e: e["stress"] = -e["stress"]
    return e

def pareto(a, b):
    ks = set(a) | set(b)
    return all(a.get(k, 0) >= b.get(k, 0) for k in ks) and any(a.get(k, 0) > b.get(k, 0) for k in ks)

def find():
    out = []
    for f in sorted(glob.glob("data/cards/*.json")):
        for c in json.load(open(f, encoding="utf-8")):
            for n, m in (("left", "right"), ("right", "left")):
                x, y = c[n], c[m]
                if pareto(vec(x), vec(y)) and not x.get("risk") and not x.get("death") and not x.get("set_flags"):
                    out.append((f, c, n, m))
    return out

if __name__ == "__main__":
    import collections
    cls = collections.Counter()
    for f, c, better, worse in find():
        age = c["ages"][0]
        relax = c[better].get("effects", {}).get("stress", 0) < 0
        k = ("adult" if age >= 18 else "kid" if age >= 6 else "baby") + ("-relax" if relax else "")
        cls[k] += 1
    print(cls)
