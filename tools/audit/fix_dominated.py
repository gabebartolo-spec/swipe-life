"""Gives the always-better swipe of each dominated card a risk, so the choice is safe vs gamble.
Edits data/cards text in place (keeps each file's layout). Run: python tools/audit/fix_dominated.py"""
import json, math, re, zlib
from dominated import find

LINES = ["It didn't go to plan.", "Not everything went your way.", "Then it went a bit wrong.",
         "Mostly fine. Mostly.", "There was a catch.", "You paid for it later."]
files = {}
n = 0
for f, c, better, worse in find():
    if f not in files:
        files[f] = open(f, encoding="utf-8").read()
    s = files[f]
    gains = {k: v for k, v in c[better]["effects"].items() if k not in ("stress", "karma") and v > 0}
    if gains:
        top = max(gains, key=lambda k: gains[k] / (2000 if k == "money" else 1))
        cost = -max(2 if top != "money" else 100, round(gains[top] * 0.8))
    else:
        top, cost = "happiness", -3
    eff = {top: cost}
    if c["ages"][0] >= 6:
        eff["stress"] = 2
    line = LINES[zlib.crc32(c["id"].encode()) % len(LINES)]
    risk = ', "risk": ' + json.dumps({"chance": 0.3, "effects": eff, "result": line}, ensure_ascii=False)
    i = re.search(r'"id"\s*:\s*"%s"' % re.escape(c["id"]), s).end()
    j = re.compile(r'"%s"\s*:\s*\{' % better).search(s, i)
    k = re.compile(r'"effects"\s*:\s*\{[^{}]*\}').search(s, j.end())
    files[f] = s[:k.end()] + risk + s[k.end():]
    n += 1
for f, s in files.items():
    open(f, "w", encoding="utf-8", newline="").write(s)
print(n, "cards given a risk")
