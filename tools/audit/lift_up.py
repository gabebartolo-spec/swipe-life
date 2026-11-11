"""Lifts small-gap ups: grows their positive good-stat effects (x1.15 steps) until margin >= 2. Then run set_up.py."""
import glob, json, sys
sys.argv = ["x", "0"]
sys.path.insert(0, "tools/audit")
import up_margin as m
need = {r[1] for r in m.rows if r[0] < 2}
best = {}
for f in glob.glob("data/cards/*.json"):
    for c in json.load(open(f, encoding="utf-8")):
        if c["id"] in need: best[c["id"]] = max(m.sc(c["left"]), m.sc(c["right"]))
n = 0
for f in glob.glob("tools/audit/up_v2/*.jsonl"):
    out, ch = [], False
    for line in open(f, encoding="utf-8"):
        s = line.strip()
        if not s: continue
        o = json.loads(s)
        if o["id"] in need:
            for _ in range(12):
                if m.upv(o) - best[o["id"]] >= 2: break
                for k, v in o["effects"].items():
                    if v > 0 and (k in m.GOOD or k == "money") : o["effects"][k] = max(v + 1, round(v * 1.15)) if k != "money" else round(v * 1.15)
            ch = True; n += 1
        out.append(json.dumps(o, ensure_ascii=False, separators=(",", ":")))
    if ch: open(f, "w", encoding="utf-8").write("\n".join(out) + "\n")
print("lifted", n)
