"""Replaces the "up" (super swipe) of cards with hand-written ones.
Input: tools/audit/up_v2/*.jsonl, one JSON object per line:
 {"id": ..., "label": ..., "effects": {...}, "risk": {"chance": .., "effects": {..}, "result": ".."},
  "death": {"chance": .., "cause": ".."}}   (risk and death optional)
Edits data/cards text in place, replacing the existing "up" object.
Run from the repo root: python tools/audit/set_up.py"""
import glob
import json
import re


def span_end(s, start):
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


NEW = {}
for f in glob.glob("tools/audit/up_v2/*.jsonl"):
    for line in open(f, encoding="utf-8"):
        line = line.strip()
        if line:
            o = json.loads(line)
            NEW[o.pop("id")] = o

done = set()
for f in sorted(glob.glob("data/cards/*.json")):
    s = open(f, encoding="utf-8").read()
    for c in json.load(open(f, encoding="utf-8")):
        if c["id"] not in NEW:
            continue
        m = re.search(r'"id"\s*:\s*"%s"' % re.escape(c["id"]), s)
        card_start = s.rfind("{", 0, m.start())
        card_end = span_end(s, card_start)
        card = s[card_start:card_end + 1]
        k = card.find('"up"')
        blob = json.dumps(NEW[c["id"]], ensure_ascii=False)
        if k < 0:
            card = card[:-1] + ', "up": ' + blob + "}"
        else:
            o = card.find("{", k)
            e = span_end(card, o)
            card = card[:o] + blob + card[e + 1:]
        s = s[:card_start] + card + s[card_end + 1:]
        done.add(c["id"])
    open(f, "w", encoding="utf-8", newline="").write(s)
print(len(done), "replaced; unknown ids:", sorted(set(NEW) - done))
