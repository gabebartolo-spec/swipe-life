"""Check hair cuts (body.py HAIRS) for scalp showing and for hair drawn over the arms in a clip.

  python tools/blender/people/hair_check.py <shape> <cut>... [--clip assets/people/clips/wave.json]

Scalp: bare head pixels in the top 40% of the head with hair below them in the same column (a gap
between fringe lumps), plus any bare pixel in the top 12% (the crown). Every hair piece hangs off
the head bone, so the head and its hair turn together: coverage at rest is coverage in every frame.
Arms: replays the clip with the same 2D bones as Person.gd and counts hair_front pixels (z 44) landing on
an arm that is drawn under it (the upper arm always; forearm and hand unless the clip's "front" lifts them).
Prints one line per cut; exits 1 if any cut shows scalp or covers an arm.
"""

import json
import math
import os
import sys

import numpy as np
from PIL import Image

ROOT = "assets/people"
PARENT = {"chest": "pelvis", "head": "chest", "thigh_l": "pelvis", "thigh_r": "pelvis", "shin_l": "thigh_l",
          "shin_r": "thigh_r", "foot_l": "shin_l", "foot_r": "shin_r"}
for s in "lr":
    PARENT |= {f"upper_arm_{s}": "chest", f"forearm_{s}": f"upper_arm_{s}", f"hand_{s}": f"forearm_{s}"}
FRONT_M = 0.35  # Person.gd
BALD = {"bald", "balding_crown", "wisp"}  # scalp is the point of these cuts (wisp: babies)
MIN_PX = 3  # single anti-aliased edge pixels don't count


def load(d):
    m = json.load(open(os.path.join(d, "manifest.json")))
    return m, {n: np.asarray(Image.open(os.path.join(d, n + ".png")))[..., 3] / 255 for n in m["sprites"]}


def layer(res, rect, a):
    c = np.zeros((res, res), np.float32)
    x, y, w, h = rect
    c[y : y + h, x : x + w] = a
    return c


def placed(res, rect, a, pivot, turn, at):
    """The sprite turned `turn` degrees counter-clockwise about its pivot, pivot moved to `at`."""
    img = Image.fromarray((layer(res, rect, a) * 255).astype(np.uint8))
    img = img.rotate(turn, Image.BILINEAR, center=tuple(pivot), translate=(at[0] - pivot[0], at[1] - pivot[1]))
    return np.asarray(img) / 255


def check(shape, cut, clip, dump=None):
    m, body = load(os.path.join(ROOT, shape))
    hm, hair = load(os.path.join(ROOT, shape, "hair", cut))
    res, pv = m["res"], {k: np.array(v) for k, v in m["pivots"].items()}
    head = layer(res, m["sprites"]["body__head"]["rect"], body["body__head"]) > 0.5
    front = [layer(res, hm["sprites"][n]["rect"], a) for n, a in hair.items() if hm["sprites"][n]["layer"] == "hair_front"]
    cover = np.clip(sum(front), 0, 1) if front else np.zeros((res, res))
    ys = np.nonzero(head.any(1))[0]
    span = ys[-1] - ys[0]
    covered = cover >= 0.5
    covered[int(ys[0] + 0.4 * span) :] = False
    below = np.flipud(np.maximum.accumulate(np.flipud(covered), axis=0))  # hair at or below, per column
    bare = head & ~(cover >= 0.5)
    crown = np.zeros_like(head)
    crown[: int(ys[0] + 0.12 * span)] = True
    scalp = int((bare & (below | crown)).sum())

    arms = [n for n, s in m["sprites"].items() if s["piece"].split("_")[0] in ("upper", "forearm", "hand")]
    worst, frames = 0, 0
    for f in range(clip["frames"]):
        turn = {p: clip["bones"][p][f] - m["rest_deg"][p] if p in clip["bones"] else 0.0 for p in pv}
        at = {"pelvis": pv["pelvis"]}
        for p in ["chest", "head"] + [k for k in PARENT if k not in ("chest", "head")]:
            q = PARENT[p]
            t, (dx, dy) = math.radians(turn[q]), pv[p] - pv[q]
            at[p] = at[q] + np.array([dx * math.cos(t) + dy * math.sin(t), -dx * math.sin(t) + dy * math.cos(t)])
        h = sum(placed(res, hm["sprites"][n]["rect"], hair[n], pv["head"], turn["head"], at["head"])
                for n in hair if hm["sprites"][n]["layer"] == "hair_front") if front else 0
        under = 0
        for n in arms:
            p = m["sprites"][n]["piece"]
            if not p.startswith("upper") and clip["front"][p[-1]][f] > FRONT_M:
                continue  # drawn over the head and its hair this frame
            under = under + placed(res, m["sprites"][n]["rect"], body[n], pv[p], turn[p], at[p])
        hit = int(((np.asarray(h) > 0.5) & (np.asarray(under) > 0.5)).sum()) if front else 0
        if dump and hit > worst:
            Image.fromarray(np.stack([np.asarray(under) * 255, np.asarray(h) * 255, head * 0], -1).astype(np.uint8)).save(dump)
        worst = max(worst, hit)
        frames += hit >= MIN_PX
    ok = (scalp < MIN_PX or cut in BALD) and frames == 0
    print(f"{'ok  ' if ok else 'FAIL'} {shape:15} {cut:16} scalp {scalp:4} px   hair on arm: {frames:2} frames, worst {worst} px")
    return ok


args = sys.argv[1:]
clip_path = "assets/people/clips/wave.json"
if "--clip" in args:
    i = args.index("--clip")
    clip_path = args[i + 1]
    del args[i : i + 2]
clip = json.load(open(clip_path))
sys.exit(0 if all([check(args[0], c, clip) for c in args[1:]]) else 1)
