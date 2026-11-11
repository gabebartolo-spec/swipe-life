"""Which cards have a super swipe ("up"), and which carry death odds. Run from the repo root."""
import collections
import glob
import json
import os

cs = []
for f in glob.glob("data/cards/*.json"):
    for c in json.load(open(f, encoding="utf-8")):
        c["_f"] = os.path.basename(f)
        cs.append(c)
up = [c for c in cs if c.get("up")]
print(len(cs), "cards;", len(up), "have up;", len(cs) - len(up), "don't")
have, tot = collections.Counter(), collections.Counter()
for c in cs:
    tot[c["_f"]] += 1
    have[c["_f"]] += 1 if c.get("up") else 0
for f in sorted(tot):
    print("  %-22s %3d/%d" % (f, have[f], tot[f]))
deaths = [
    (c["id"], s, c[s]["death"]["chance"])
    for c in cs
    for s in ("left", "right", "up")
    if c.get(s, {}).get("death")
]
print("death outcomes:", len(deaths))
for d in deaths:
    print("  ", d)
print("up with death:", sum(1 for c in up if c["up"].get("death")))
print("up with risk:", sum(1 for c in up if c["up"].get("risk")))
