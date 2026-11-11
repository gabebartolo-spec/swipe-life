"""Replaces card "text" with the richer versions in tools/audit/text_v2/*.jsonl ({"id", "text"} per line).
Edits data/cards in place (only the text string). Run from the repo root."""
import glob, json, re
NEW = {}
for f in glob.glob("tools/audit/text_v2/*.jsonl"):
    for line in open(f, encoding="utf-8"):
        if line.strip():
            o = json.loads(line)
            NEW[o["id"]] = o["text"]
done = set()
for f in glob.glob("data/cards/*.json"):
    s = open(f, encoding="utf-8").read()
    for cid in [c["id"] for c in json.loads(s)]:
        if cid not in NEW:
            continue
        i = re.search(r'"id": ?"%s"' % re.escape(cid), s).start()
        m = re.compile(r'"text": ?("(?:[^"\\]|\\.)*")').search(s, i)
        s = s[:m.start(1)] + json.dumps(NEW[cid], ensure_ascii=False) + s[m.end(1):]
        done.add(cid)
    json.loads(s)
    open(f, "w", encoding="utf-8", newline="\n").write(s)
print(len(done), "replaced; unknown:", sorted(set(NEW) - done))
