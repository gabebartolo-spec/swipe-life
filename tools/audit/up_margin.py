"""Rank super swipes by value margin over the best normal swipe (mirrors feature_audit.gd)."""
import json, glob, sys
VAL = {"stress": -1, "karma": 0.5}
GOOD = {"happiness", "health", "smarts", "looks", "relationships", "career"}
def sc(ch):
    s = 0.0
    for k, v in ch.get("effects", {}).items():
        if k == "money": s += v / 2000
        elif k in GOOD or k in VAL: s += VAL.get(k, 1) * v
    return s
def upv(u):
    v = sc(u)
    if "risk" in u: v += u["risk"]["chance"] * sc(u["risk"])
    if "death" in u: v -= u["death"]["chance"] * 60
    return v
rows = []
for f in glob.glob("data/cards/*.json"):
    for c in json.load(open(f, encoding="utf-8")):
        best = max(sc(c["left"]), sc(c["right"]))
        rows.append((upv(c["up"]) - best, c["id"], upv(c["up"]), best))
rows.sort()
if __name__ == "__main__":
    n = len(rows)
    print("n", n, "median margin", round(rows[n // 2][0], 1))
    print("margin<0:", sum(r[0] < 0 for r in rows), " <3:", sum(r[0] < 3 for r in rows), " >15:", sum(r[0] > 15 for r in rows))
    for r in rows[:int(sys.argv[1]) if len(sys.argv) > 1 else 40]: print(r[1], round(r[0], 1), round(r[2], 1), round(r[3], 1))
