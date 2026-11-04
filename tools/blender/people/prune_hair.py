"""Keep only the hair sprites of a hair-only render (build_hair.sh)."""

import json
import os
import sys

out = sys.argv[1]
path = os.path.join(out, "manifest.json")
m = json.load(open(path))
for name, s in list(m["sprites"].items()):
    if not s["layer"].startswith("hair"):
        os.remove(os.path.join(out, name + ".png"))
        del m["sprites"][name]
json.dump({"sprites": m["sprites"]}, open(path, "w"), indent=1)
