"""Gives every card without a super swipe ("up") one, from tools/audit/up_text/*.txt.
Each line is id|label|setback line|death cause (optional). Numbers: the better swipe doubled, a 50%
setback undoing its top gain (1.5x) plus Stress, and a death chance where a cause is written.
Edits data/cards text in place. Run from the repo root: python tools/audit/add_up.py"""
import glob
import json
import os
import re

GOOD = ("happiness", "health", "smarts", "looks", "relationships", "career")
TEXT = {}
for f in glob.glob("tools/audit/up_text/*.txt"):
    for line in open(f, encoding="utf-8"):
        p = line.rstrip("\n").split("|")
        if len(p) >= 3:
            TEXT[p[0]] = p[1:]


def score(ch):
    s = 0.0
    for k, v in ch.get("effects", {}).items():
        if k == "money":
            s += v / 2000.0
        elif k == "stress":
            s -= v
        elif k in GOOD or k == "karma":
            s += (0.5 if k == "karma" else 1.0) * v
    return s


def amp(v, money):
    return int(round(v * 2))


def build(c, label, line, cause):
    base = c["left"] if score(c["left"]) >= score(c["right"]) else c["right"]
    eff = {k: amp(v, k == "money") for k, v in base.get("effects", {}).items()}
    gains = {k: v for k, v in eff.items() if k not in ("stress", "karma") and v > 0}
    adult = c["ages"][0] >= 6
    if gains:
        top = max(gains, key=lambda k: gains[k] / (2000 if k == "money" else 1))
        cost = -max(300 if top == "money" else 3, round(gains[top] * 0.75))
    else:
        top, cost = "happiness", -4
    if not eff:
        eff = {"happiness": 3}
    rk = {top: cost}
    if adult:
        rk["stress"] = 3
    up = {"label": label, "effects": eff}
    up["risk"] = {"chance": 0.5, "effects": rk, "result": line}
    if cause:
        up["death"] = {"chance": 0.04 if c["ages"][0] >= 13 else 0.02, "cause": cause}
    return up


def span_end(s, start):
    """Index of the '}' closing the object that opens at s[start]."""
    depth, i, instr = 0, start, False
    while i < len(s):
        ch = s[i]
        if instr:
            if ch == "\\":
                i += 1
            elif ch == '"':
                instr = False
        elif ch == '"':
            instr = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced")


n, missing = 0, []
for f in sorted(glob.glob("data/cards/*.json")):
    s = open(f, encoding="utf-8").read()
    for c in json.load(open(f, encoding="utf-8")):
        if c.get("up"):
            continue
        t = TEXT.get(c["id"])
        if t is None:
            missing.append(c["id"])
            continue
        up = build(c, t[0], t[1], t[2] if len(t) > 2 and t[2] else "")
        m = re.search(r'"id"\s*:\s*"%s"' % re.escape(c["id"]), s)
        start = s.rfind("{", 0, m.start())
        end = span_end(s, start)
        s = s[:end] + ', "up": ' + json.dumps(up, ensure_ascii=False) + s[end:]
        n += 1
    open(f, "w", encoding="utf-8", newline="").write(s)
print(n, "cards given a super swipe; missing text:", missing)
