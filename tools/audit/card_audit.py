"""Static balance audit of data/cards: dominated choices, extreme deltas, dead flags, death odds.
Run: python tools/audit/card_audit.py"""
import glob, json, collections

cards = []
for f in sorted(glob.glob("data/cards/*.json")):
    for c in json.load(open(f, encoding="utf-8")):
        c["_f"] = f.split("\\")[-1].split("/")[-1]
        cards.append(c)
print(len(cards), "cards")
sides = ("left", "right", "up")
VAL = {"happiness": 1, "health": 1, "smarts": 1, "looks": 1, "relationships": 1, "karma": .5,
       "career": 1, "stress": -1, "money": 0}


def score(ch):
    e = ch.get("effects", {})
    s = sum(VAL.get(k, 0) * v for k, v in e.items())
    r = ch.get("risk")
    if r:
        s += r["chance"] * sum(VAL.get(k, 0) * v for k, v in r["effects"].items())
    return s, e.get("money", 0)


dom, big, nodelta = [], [], []
for c in cards:
    l, r = c["left"], c["right"]
    (sl, ml), (sr, mr) = score(l), score(r)
    if sl >= sr and ml >= mr and (sl > sr or ml > mr) or sr >= sl and mr >= ml and (sr > sl or mr > ml):
        if abs(sl - sr) >= 2 or abs(ml - mr) >= 200:
            dom.append((c["id"], c["_f"], round(sl, 1), ml, round(sr, 1), mr))
    for s in sides:
        ch = c.get(s)
        if not ch:
            continue
        for k, v in ch.get("effects", {}).items():
            lim = 40000 if k == "money" else 25
            if abs(v) > lim:
                big.append((c["id"], s, k, v))
    if not l.get("effects") and not r.get("effects"):
        nodelta.append(c["id"])
print("\nDOMINATED choices (one side better on all, gap>=2 pts or $200):", len(dom))
for d in dom[:40]:
    print("  ", d)
print("\nBIG deltas:", len(big))
for b in big[:30]:
    print("  ", b)
print("\nNo effects at all:", len(nodelta), nodelta[:20])

# flags
setf, clrf, need, forbid = set(), set(), set(), set()
for c in cards:
    for s in sides:
        ch = c.get(s) or {}
        setf |= set(ch.get("set_flags", []))
        clrf |= set(ch.get("clear_flags", []))
    rq = c.get("requires", {})
    need |= set(rq.get("flags", []))
    forbid |= set(rq.get("not_flags", []))
print("\nflags required but never set by any card:", sorted(need - setf))
print("flags set but never read:", sorted(setf - need - forbid)[:40])

# uncovered ages and per-age weight
cov = collections.Counter()
for c in cards:
    if "set" in c:
        continue
    for a in range(c["ages"][0], c["ages"][1] + 1):
        cov[a] += 1
thin = [a for a in range(0, 101) if cov[a] < 12]
print("\nages with <12 non-locked cards:", thin)

# death odds
dd = collections.defaultdict(float)
for c in cards:
    for s in sides:
        d = (c.get(s) or {}).get("death")
        if d:
            for a in range(c["ages"][0], c["ages"][1] + 1):
                dd[a] = max(dd[a], d["chance"])
print("cards with death chance:", sum(1 for c in cards for s in sides if (c.get(s) or {}).get("death")))
hi = [(c["id"], s, c[s]["death"]["chance"]) for c in cards for s in sides if (c.get(s) or {}).get("death") and c[s]["death"]["chance"] >= .15]
print("death chance >=15%:", hi)

# mean money / stats per band, by choice average
band = collections.defaultdict(lambda: collections.Counter())
cnt = collections.Counter()
for c in cards:
    if "set" in c:
        continue
    b = (c["ages"][0] // 10) * 10
    cnt[b] += 1
    for s in ("left", "right"):
        for k, v in c[s].get("effects", {}).items():
            band[b][k] += v / 2
print("\nmean per-card avg effect by age decade (sum of both sides /2 / cards):")
for b in sorted(band):
    print(b, cnt[b], {k: round(v / cnt[b], 2) for k, v in sorted(band[b].items())})

# strict Pareto: one side is >= on every stat (stress lower is better) and > on one, no risk/death on the better side
def vec(ch):
    e = dict(ch.get("effects", {}))
    for k in list(e):
        if k == "stress":
            e[k] = -e[k]
    return e


def pareto(a, b):
    ka = set(a) | set(b)
    return all(a.get(k, 0) >= b.get(k, 0) for k in ka) and any(a.get(k, 0) > b.get(k, 0) for k in ka)


strict = []
for c in cards:
    l, r = c["left"], c["right"]
    for x, y, n in ((l, r, "left"), (r, l, "right")):
        if pareto(vec(x), vec(y)) and not x.get("risk") and not x.get("death") and not x.get("set_flags"):
            strict.append((c["id"], n + " always better"))
print("\nSTRICT pareto-dominated (no real choice):", len(strict))
for s in strict:
    print("  ", s)
