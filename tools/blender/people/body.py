"""Modular people, vertical slice (docs/PEOPLE.md ยง10 step 1): child_f_skinny as 15 rigid clay pieces,
plus garment and hair recipes, all in neutral clay for tinting in game.

Run headless:
  blender -b --factory-startup --python tools/blender/people/body.py -- <out.glb>

Every object is named "<layer>|<piece>|<mask>":
  layer  body, face (fixed colours, not tinted), tee, sweater, trousers, hair_back, hair_front
  piece  pelvis, chest, head, upper_arm_l/r, forearm_l/r, hand_l/r, thigh_l/r, shin_l/r, foot_l/r
  mask   R (main colour c1), G (trim, c2), B (detail, c3)
Each piece's pivot (joint it turns about, Godot axes: x right, y up, z to camera) is a glTF extra.
"_l" is the character's left, which is screen right (+x) from the front.
Proportions come from the approved chibi girl (tools/blender/build_clay_girl.py, child, non-cutout).
"""

import os
import sys

import bpy
from mathutils import Vector

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from build_clay_room import g2b, hexc  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1 :]
OUT = ARGS[0]
AGE = ARGS[1] if len(ARGS) > 1 else "child"
SEX = ARGS[2] if len(ARGS) > 2 else "f"
OPTS = dict(a.split("=", 1) if "=" in a else (a, "1") for a in ARGS[3:])
HAIR = OPTS.get("hair", "")  # hair=<cut>: one cut of HAIRS; no hair= builds the body without hair
HAIR_ONLY = "hair_only" in OPTS  # only the cut, the head (occluder) and the chest (render.py's light level)
ARGS = [a for a in ARGS if "=" not in a and a != "hair_only"]
# approved age bands (build_clay_girl.py --age, clay_sets_front.png): the child is modelled, other ages
# rescale the body below the neck (sx width, sy height) and the head (h) about the neck
SX, SY, H = {"baby": (1.12, 0.55, 0.95), "child": (1, 1, 1), "teen": (0.86, 1.35, 0.9), "adult": (0.9, 1.5, 0.86)}[AGE]
NECK = 1.27  # points above this belong to the head
# director 2026-11-03: a short neck on everyone but babies (no neck read as hunched); about a quarter head
NECK_UP = {"baby": 0.0, "child": 0.08, "teen": 0.2}.get(AGE, 0.32)  # director: kid shortest neck, adult longest


def T(p):
    """Age transform of a modelled point -> (point, radius factor, per-axis stretch); copied from build_clay_girl."""
    x, y, z = p
    y += NECK_UP * min(max((y - 1.36) / 0.1, 0), 1)  # neck stub: the head rises above the collar line
    if y > NECK:
        return (x * H, NECK * SY + (y - NECK) * H, z * H), H, (1, 1, 1)
    f = (SX + SY) / 2
    if y < 0.15:  # feet keep their shape
        return (x * SX, y * SY, z * SX), f, (1, 1, 1)
    return (x * SX, y * SY, z * SX), f, (SX / f, SY / f, SX / f)

NEUTRAL = "cccccc"  # tinted pieces: grey clay, colour comes from the shader
FACE = {"eyes": "2b2024", "blush": "f0a0a0", "mouth": "8a3a3a"}

# joints (child girl, metres, Godot axes)
J = {
    "waist": (0, 0.86, 0), "neck": (0, 1.34, 0), "head_c": (0, 1.68, 0),
    "shoulder": (0.33, 1.24, 0), "elbow": (0.39, 1.02, 0.01), "wrist": (0.45, 0.8, 0.02), "hand_c": (0.47, 0.68, 0.03),
    "hip": (0.16, 0.72, 0), "knee": (0.16, 0.44, 0), "ankle": (0.17, 0.16, 0), "toe": (0.17, 0.08, 0.05),
}
# sex shape (director 2026-11-03, "triangle theory", not literal): men broad shoulders, women narrower
# shoulders, a pinched waist and wider hips (hourglass). Teens and adults only; children stay unisex.
GROWN = AGE in ("teen", "adult")
SHOULDER_W = {"m": 1.12, "f": 0.94}[SEX] if GROWN else 1.0  # shoulder span and upper chest
WAIST_W = {"m": 1.04, "f": 0.88}[SEX] if GROWN else 1.0  # ribs-to-waist width
HIP_W = {"m": 1.0, "f": 1.1}[SEX] if GROWN else 1.0  # pelvis width
for _n in ("shoulder", "elbow", "wrist", "hand_c"):  # the whole arm moves out, keeping its angle
    J[_n] = (J[_n][0] + 0.33 * (SHOULDER_W - 1), *J[_n][1:])
if GROWN:  # shoulder caps sat level with the chest top and poked up (director): drop the joint
    J["shoulder"] = (J["shoulder"][0], J["shoulder"][1] - 0.04, J["shoulder"][2])
    # arms angled a little away from the body, so a gap shows under the arm (director: arms looked fused)
    for _n, _dx in (("elbow", 0.035), ("wrist", 0.07), ("hand_c", 0.08)):
        J[_n] = (J[_n][0] + _dx, *J[_n][1:])
for _n in ("hip", "knee", "ankle", "toe"):
    J[_n] = (J[_n][0] + 0.16 * (HIP_W - 1), *J[_n][1:])
PIVOT = {"pelvis": "waist", "chest": "waist", "head": "neck", "upper_arm": "shoulder", "forearm": "elbow",
         "hand": "wrist", "thigh": "hip", "shin": "knee", "foot": "ankle"}
END = {"pelvis": "hip", "chest": "neck", "head": "head_c", "upper_arm": "elbow", "forearm": "wrist", "hand": "hand_c",
       "thigh": "knee", "shin": "ankle", "foot": "toe"}  # the piece's rest direction runs pivot -> end
PARTS = {}  # (layer, piece, mask) -> [sphere objects]


def j(name, s=1):
    x, y, z = J[name]
    return (x * s, y, z)


def sphere(key, at, r, scale=(1, 1, 1), segs=32):
    at, f, st = T(tuple(at))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r * f, location=g2b(*at), segments=segs, ring_count=segs // 2)
    ob = bpy.context.object
    ob.scale = (scale[0] * st[0], scale[2] * st[2], scale[1] * st[1])
    PARTS.setdefault(key, []).append(ob)


def chain(key, a, b, r, n=5):
    a, b = Vector(a), Vector(b)
    if key[0].startswith("hair"):  # hair only: approved clothes keep their bead count
        n = max(n, int((b - a).length / (0.3 * r)) + 2)  # beads 0.3 r apart: the remesh fuses them into a smooth tube, not sausages
    for i in range(n):
        sphere(key, a.lerp(b, i / (n - 1)), r)


def ring(key, centre, rx, rz, r, n=14):
    """A band of beads round the y axis (collar, cuff, hem); the remesh fuses it into a rolled edge."""
    import math

    for i in range(n):
        t = 2 * math.pi * i / n
        sphere(key, (centre[0] + rx * math.cos(t), centre[1], centre[2] + rz * math.sin(t)), r, segs=16)


def limb_ring(key, a, b, t, rad, n=12, r=0.03):
    """Ring of beads round a limb at fraction t from joint a to joint b (cuffs on a hanging arm)."""
    import math

    a, b = Vector(a), Vector(b)
    c = a.lerp(b, t)
    d = (b - a).normalized()
    u = d.cross(Vector((0, 0, 1))).normalized()
    w = d.cross(u)
    for i in range(n):
        ang = 2 * math.pi * i / n
        sphere(key, tuple(c + (u * math.cos(ang) + w * math.sin(ang)) * rad), r, segs=16)


# Sockets (director 2026-11-03): every piece meeting at a joint ends in a sphere of exactly that joint's
# radius centred on its pivot, so a turn never shows an edge, gap or bulge where the pieces overlap.
JR = {"neck": 0.09, "waist": 0.2, "shoulder": 0.1, "elbow": 0.09, "wrist": 0.075, "hip": 0.115, "knee": 0.105,
      "ankle": 0.085}
WAIST = ARGS[3] if len(ARGS) > 3 else "loose"  # loose: the top hangs over the pelvis; tucked: waistband over the top


def socket(layer, piece, joint, s=1, grow=0.0, mask="R"):
    scale = (1.0, 0.9, 0.7) if joint == "waist" else (1, 1, 1)
    sphere((layer, piece, mask), j(joint, s), JR[joint] + grow, scale)


def bone(layer, piece, a, b, s, r, grow=0.0, n=5):
    """Limb piece from joint a to joint b: a chain no thicker than the sockets, a socket at each end."""
    chain((layer, piece, "R"), j(a, s), j(b, s), r + grow, n)
    socket(layer, piece, a, s, grow)
    socket(layer, piece, b, s, grow)


def top_w(y):
    """Width of a top's sides at height y (director: fitted tops). Women: in at the waist, out at the hips;
    men: broad at the ribs, tapering to the hem; children: straight."""
    if not GROWN:
        return 1.0
    if SEX == "f":
        pts = ((1.05, 0.94), (0.97, 0.86), (0.9, 0.96), (0.84, HIP_W))
    else:
        pts = ((1.05, 1.06), (0.84, 0.96))
    for (y0, w0), (y1, w1) in zip(pts, pts[1:]):
        if y1 <= y <= y0:
            return w1 + (w0 - w1) * (y - y1) / (y0 - y1)
    return pts[0][1] if y > pts[0][0] else pts[-1][1]


def torso(layer, grow, mask="R"):
    # slim: widest at the ribs, narrowing to the waist (director: the one-ball belly read as fat)
    sphere((layer, "chest", mask), (0, 1.1, 0), 0.29 + grow, (WAIST_W, 0.8, 0.62))
    sphere((layer, "chest", mask), (0, 1.27, 0), 0.22 + grow, (1.05 * SHOULDER_W, 0.42, 0.7))
    if GROWN:  # flat yoke out to the shoulder: a squared shoulder line, not a ball (director: too rounded)
        sphere((layer, "chest", mask), (0, 1.3, 0), 0.22 + grow, (1.4 * SHOULDER_W, 0.3, 0.65))
    socket(layer, "chest", "waist", grow=grow, mask=mask)
    if SEX == "f" and AGE in ("teen", "adult"):  # chest beads (PEOPLE.md ง2, director: women need breasts)
        # undo the age stretch (tall bodies stretched round beads into vertical footballs): k/SY, k/SX
        k = (SX + SY) / 2
        for s in (-1, 1):
            # one round bead per side, a clear gap between them (director: "just make them normal")
            r = 0.075 if AGE == "adult" else 0.06
            sphere((layer, "chest", mask), (0.1 * s, 1.14, 0.09), r + grow, (k / SX, k / SY, 0.8 * k / SX))
    if layer != "body":  # tops hang straight past the hips, wider than the trousers (director)
        for y in (1.05, 1.02, 0.99, 0.96, 0.93, 0.9, 0.87, 0.84):  # sides from the ribs to the hem: no round belly
            sphere((layer, "chest", mask), (0, y, 0), 0.3 + grow, (top_w(y), 0.35, 0.62))
        sphere((layer, "chest", mask), (0, 0.8, 0), 0.24 + grow, (1.3 * HIP_W, 0.28, 0.74))
    socket(layer, "chest", "neck", grow=grow, mask=mask)


def pelvis(layer, grow):
    socket(layer, "pelvis", "waist", grow=grow)
    sphere((layer, "pelvis", "R"), (0, 0.78, 0), 0.24 + grow, (1.05 * HIP_W, 0.55, 0.75))
    for s in (-1, 1):
        socket(layer, "pelvis", "hip", s, grow)


def legs(layer, grow, to_ankle=True):
    for s, side in ((1, "l"), (-1, "r")):
        bone(layer, "thigh_" + side, "hip", "knee", s, 0.11, grow)
        if to_ankle:
            bone(layer, "shin_" + side, "knee", "ankle", s, 0.1, grow)
        else:  # trouser leg ends above the shoe
            chain((layer, "shin_" + side, "R"), j("knee", s), (0.17 * s, 0.2, 0), 0.1 + grow)
            socket(layer, "shin_" + side, "knee", s, grow)


def arms(layer, grow, forearm=True):
    for s, side in ((1, "l"), (-1, "r")):
        bone(layer, "upper_arm_" + side, "shoulder", "elbow", s, 0.095, grow)
        if forearm:  # sleeve ends at the wrist cuff (no socket there: the hand turns under it)
            chain((layer, "forearm_" + side, "R"), j("elbow", s), j("wrist", s), 0.085 + grow)
            socket(layer, "forearm_" + side, "elbow", s, grow)


def body():
    torso("body", 0)
    pelvis("body", 0)
    legs("body", 0)
    sphere(("body", "head", "R"), J["head_c"], 0.47, (1.05, 0.95, 1.0))
    chain(("body", "head", "R"), (0, 1.3, 0), (0, 1.46, 0), 0.09, 5)
    socket("body", "head", "neck")
    for s, side in ((1, "l"), (-1, "r")):
        bone("body", "upper_arm_" + side, "shoulder", "elbow", s, 0.095)
        bone("body", "forearm_" + side, "elbow", "wrist", s, 0.085)
        hand(side, s)
        socket("body", "hand_" + side, "wrist", s)
        sphere(("body", "foot_" + side, "R"), j("toe", s), 0.13, (0.85, 0.6, 1.25))
        socket("body", "foot_" + side, "ankle", s)
        # face beads ride on the head piece
        sphere(("face", "head", "eyes"), (0.14 * s, 1.64, 0.43), 0.05, (0.8, 1.15, 0.5), 16)
        if AGE in ("baby", "child"):  # director: blush only on babies and children
            sphere(("face", "head", "blush"), (0.25 * s, 1.55, 0.38), 0.06, (1, 0.55, 0.35), 16)
    sphere(("face", "head", "mouth"), (0, 1.52, 0.44), 0.04, (1.2, 0.5, 0.4), 16)
    if AGE == "adult":  # elderly face lines, copied from the director's sketch (2026-11-03): own sprite,
        # Person shows it when elderly. Continuous strokes of overlapping thin beads, not dots.
        def stroke(pts, r=0.011):
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                n = max(2, int(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / (r * 0.6)))
                for i in range(n + 1):
                    t = i / n
                    sphere(("wrinkles", "head", "lines"), (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 0.5), r, segs=8)

        stroke([(-0.11, 1.872), (0.1, 1.872)], 0.011)  # forehead: a straight line over a wavy one
        stroke([(-0.11, 1.8), (0, 1.808), (0.1, 1.8)], 0.011)
        for s in (1, -1):
            stroke([(0.095 * s, 1.562), (0.185 * s, 1.562)], 0.009)  # under-eye line: eye-wide, at the sketch's eye-to-mouth ratio
            stroke([(0.082 * s, 1.494), (0.1 * s, 1.466)], 0.01)  # fold down and out from the mouth corner


def hand(side, s):
    """Relaxed hand (director: not a limp fish): palm faces the thigh, so the front view sees its narrow edge;
    the wrist turns it in toward the leg and the fingers curl in, with a thumb in front. The joint (hand_c)
    is unchanged, so clips keep their angles."""
    h, w = Vector(j("hand_c", s)), Vector(j("wrist", s))
    key = ("body", "hand_" + side, "R")
    k = SX / SY  # undo each age's height stretch on the hand: teen/adult hands came out as long pointed claws,
    # the baby's squash flattened the fist into a sideways tab
    if AGE == "baby":  # a small round fist hanging straight down out of the cuff (director: not massive)
        sphere(key, tuple(w + Vector((-0.01 * s, -0.08 * k, 0.01))), 0.062, (1, k, 1))
        sphere(key, tuple(w + Vector((-0.02 * s, -0.13 * k, 0.015))), 0.068, (0.95, 0.95 * k, 1))
        return
    sphere(key, tuple(w + Vector((0, -0.03 * k, 0))), 0.064, (1, k, 1))  # wrist, narrower than the forearm
    sphere(key, tuple(w + Vector((-0.02 * s, -0.11 * k, 0))), 0.07, (0.8, 1.2 * k, 0.9))  # palm, edge-on
    sphere(key, tuple(w + Vector((-0.05 * s, -0.18 * k, 0.01))), 0.058, (0.85, k, 0.9))  # round curled fingers, in
    sphere(key, tuple(w + Vector((-0.06 * s, -0.08 * k, 0.04))), 0.034, (0.9, 1.3 * k, 0.9))  # thumb, inner edge


def sleeve_top(layer, side, s, end, r):
    """Grown sleeve top (director: clothes must follow the flat yoke): the chain starts below the joint and
    a flat cap hides the socket, so no ball stands above the shoulder line."""
    a = Vector(j("shoulder", s))
    chain((layer, "upper_arm_" + side, "R"), tuple(a.lerp(Vector(end), 0.2)), tuple(end), r, 4)
    # cap as wide as the sleeve (wider bulged as a separate ball, director: seamless); its top, 0.8 r above the
    # joint, still covers the body's shoulder socket (r 0.1), so no skin shows
    sphere((layer, "upper_arm_" + side, "R"), tuple(a), r, (1, 0.87, 1))  # top 0.87 r ~ 0.1 above the joint


def tee():
    torso("tee", 0.025)
    ring(("tee", "chest", "G"), (0, 1.36, 0.0), 0.12, 0.1, 0.035)
    for s, side in ((1, "l"), (-1, "r")):
        mid = Vector(j("shoulder", s)).lerp(Vector(j("elbow", s)), 0.65)
        if GROWN:
            sleeve_top("tee", side, s, mid, 0.115)  # arm 0.095 + 0.02: close fit, no puff
        else:
            chain(("tee", "upper_arm_" + side, "R"), j("shoulder", s), tuple(mid), 0.115, 4)
            socket("tee", "upper_arm_" + side, "shoulder", s, 0.015)


def sweater():
    torso("sweater", 0.035)
    ring(("sweater", "chest", "G"), (0, 1.36, 0.0), 0.13, 0.11, 0.04)
    if GROWN:
        for s, side in ((1, "l"), (-1, "r")):
            sleeve_top("sweater", side, s, j("elbow", s), 0.115)
            socket("sweater", "upper_arm_" + side, "elbow", s, 0.025)
            chain(("sweater", "forearm_" + side, "R"), j("elbow", s), j("wrist", s), 0.11)  # same as the upper sleeve: no step at the elbow
            socket("sweater", "forearm_" + side, "elbow", s, 0.025)
    else:
        arms("sweater", 0.025)


def trousers():
    pelvis("trousers", 0.03)
    legs("trousers", 0.03, to_ankle=False)


def onesie():
    """Full-body item (baby, as approved in clay_sets_front): top, legs and feet in one colour."""
    torso("onesie", 0.035)
    pelvis("onesie", 0.03)
    legs("onesie", 0.03)
    arms("onesie", 0.04)
    for s, side in ((1, "l"), (-1, "r")):
        sphere(("onesie", "foot_" + side, "R"), j("toe", s), 0.15, (0.85, 0.6, 1.25))
        socket("onesie", "foot_" + side, "ankle", s, 0.025)


def cap(r=0.5, y=1.82, sy=0.92):
    """Back of the hair: drawn behind the head and body, so it can never cover an arm."""
    sphere(("hair_back", "head", "R"), (0, y, -0.1), r, (1.03, sy, 0.95))


def shell(r=0.47, y=2.02, sy=0.6, sx=1.0):  # top 2.3 covers the cap dome; the deeper sy rounds the crown ridge (teen beret), lower edge 1.74
    """Crown shell (PEOPLE.md: no scalp between fringe lumps); the head occluder trims it to the top."""
    sphere(("hair_front", "head", "R"), (0, y, 0.02), r, (sx, sy, 1.0))


def front(at, r, scale=(1, 1, 1)):
    sphere(("hair_front", "head", "R"), at, r, scale)


def back(at, r, scale=(1, 1, 1)):
    sphere(("hair_back", "head", "R"), at, r, scale)


def temples():
    """Closes the sliver of scalp at the head's edge between the crown shell and the side hair (hair_check)."""
    for s in (-1, 1):
        front((0.46 * s, 1.74, 0.1), 0.11, (1.0, 2.6, 1.0))
        front((0.45 * s, 1.77, 0.0), 0.11, (0.8, 1.8, 0.9))


# Cuts (director 2026-11-03: 34, any cut on anyone). Rules that keep them clean in motion:
# - every piece hangs off the head bone, so whatever covers the scalp at rest covers it in every frame;
# - hair_front stays above the shoulder tops (y 1.36) outside |x| 0.2, so it never covers an arm;
#   anything longer goes on hair_back, which draws behind the body.
def wisp():
    """Baby hair: a wisp on top (build_clay_girl.py --age baby)."""
    front((0.05, 2.1, 0.12), 0.14, (1.3, 0.5, 1.0))


def bob():
    """Chin-length bob: smooth straight sides to a blunt line at the jaw, a straight fringe, no layers."""
    from math import cos, sin

    cap()
    shell()
    temples()
    for i in range(11):  # blunt fringe across the brow, sitting on the skin so it fuses into the shell
        x = -0.3 + 0.06 * i
        front((x, 1.89, skin_z(x, 1.89) - 0.03), 0.08, (1.0, 1.1, 0.8))
    for s in (-1, 1):
        # one smooth slab per side from the temple to the jaw
        front((0.41 * s, 1.77, 0.04), 0.13, (0.75, 1.7, 1.0))
        front((0.41 * s, 1.56, 0.02), 0.12, (0.78, 1.4, 1.05))
        for i in range(6):  # a level bar along the jaw squares the bottom off (blunt line, no flick)
            front((0.41 * s, 1.45, -0.18 + 0.065 * i), 0.07, (1.0, 0.8, 1.0))
    # the back falls to the same level, behind the neck
    back((0, 1.66, -0.2), 0.44, (1.12, 0.62, 0.92))
    for i in range(9):  # level lower edge round the back, inside the side slabs
        a = -1.4 + 0.35 * i
        back((0.38 * sin(a), 1.46, -0.04 - 0.36 * cos(a)), 0.09, (1, 0.8, 1))


def crop():
    """Short crop: a close rounded crown, a short soft-pointed fringe and tapered sides."""
    cap(0.48, 1.84, 0.8)
    shell(0.45, 2.0, 0.5)  # top 2.225 covers the cap dome (a lower shell shows its edge across the crown)
    for i in range(9):  # a short smooth fringe, a touch lower in the middle, sunk in the skin so no lip
        x = -0.28 + 0.07 * i
        y = 1.91 + 0.25 * x * x
        front((x, y, skin_z(x, y) - 0.02), 0.07, (1.0, 1.0, 0.6))
    for s in (-1, 1):  # short sideburn tapering to the top of the ear
        front((0.42 * s, 1.84, 0.08), 0.08, (0.7, 1.4, 0.9))
        front((0.43 * s, 1.76, 0.1), 0.06, (0.65, 1.5, 0.8))


def crew_cut():
    """Crew cut: nearly flat to the scalp, high clean hairline, short sides, no fringe."""
    cap(0.47, 1.84, 0.78)
    shell(0.45, 1.99, 0.49)  # top 2.21 covers the cap dome


def pixie():
    """Pixie: short all over, a side-swept fringe tapering to the temple, short wisps in front of the ears."""
    cap(0.49, 1.84, 0.84)
    shell(0.46, 2.0, 0.55)  # top 2.25 covers the cap dome; closer to the skull than the long cuts
    n = 9
    for i in range(n):  # the sweep narrows as it crosses the brow, so it ends in the side hair without a step
        t = i / (n - 1)
        x, y = 0.26 - 0.6 * t, 2.02 - 0.18 * t
        front((x, y, skin_z(x, y) + 0.01), 0.13 - 0.06 * t, (1.0, 0.8, 0.8))
    for s in (-1, 1):
        front((0.43 * s, 1.78, 0.1), 0.08, (0.62, 1.5, 0.8))
        front((0.42 * s, 1.67, 0.15), 0.05, (0.6, 1.5, 0.7))
    front((-0.38, 1.88, 0.14), 0.08)  # closes the notch where the sweep ends at the temple


def long_straight():
    """Long straight, middle part: thin flat side panels stop above the shoulders in front; one flat sheet falls behind."""
    cap()
    # round crown no wider than the cap: a flat wide shell plus flat fringe pads read as a beret (director)
    shell()
    for s in (-1, 1):
        # curtains sweep from the middle part down the sides of the forehead, following the skull
        sheet(HF, (0.03 * s, 2.15, 0.17), (0.38 * s, 1.84, 0.12), 0.12, (1.0, 0.8, 0.8))
        # straight, flat panels framing the face: thin in x, so the edge reads as a hanging sheet, not a tube
        sheet(HF, (0.39 * s, 1.94, 0.0), (0.38 * s, 1.6, -0.02), 0.15, (0.55, 1.0, 1.2))
        # the same panel carries on straight down behind the shoulder
        sheet(HB, (0.39 * s, 1.66, -0.04), (0.37 * s, 0.98, -0.1), 0.15, (0.55, 1.0, 1.2))
    # one wide flat sheet down the back, dead straight sides
    sheet(HB, (0, 1.72, -0.2), (0, 0.98, -0.22), 0.3, (1.4, 1.0, 0.6))


def high_ponytail():
    """High ponytail: pulled back off the forehead and tied on top of the crown; the tail arcs over and falls beside the head."""
    cap(0.5, 1.84, 0.9)
    shell()
    for s in (-1, 1):  # sleek sides: thin, flat against the skull (no bob lobes)
        front((0.44 * s, 1.8, 0.04), 0.1, (0.6, 1.6, 1.0))
    front((0, 2.3, -0.12), 0.1)  # the tie, on top of the crown
    pts = [(0, 2.34, -0.16), (0.06, 2.41, -0.32), (0.26, 2.34, -0.48), (0.46, 2.1, -0.5), (0.54, 1.8, -0.46),
           (0.56, 1.5, -0.42)]
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        chain(HB, a, b, 0.15 - 0.014 * i, 4)
    back((0.56, 1.46, -0.42), 0.07)


def afro():
    """Afro: a big round mass of clumped curls, wider and taller than the head; curls right down to the hairline."""
    import math

    C, R = (0, 2.02, -0.06), (0.72, 0.68, 0.66)
    back(C, 0.62, (1.08, 1.0, 0.98))
    shell(0.47, 2.12, 0.45, 1.05)
    n = 110
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        rr = math.sqrt(1 - y * y)
        t = math.pi * (3 - math.sqrt(5)) * i
        x, z = rr * math.cos(t), rr * math.sin(t)
        p = (C[0] + R[0] * x, C[1] + R[1] * y, C[2] + R[2] * z)
        if p[1] < 1.5 or (p[2] > 0.05 and p[1] < 2.12 and abs(p[0]) < 0.52):
            continue  # the face stays clear; the hairline row below closes it
        # front layer down to well behind the ears, so no back curl shows through the mass as a seam
        sphere(HF if p[2] > -0.3 else HB, p, 0.15 + 0.04 * ((i * 7) % 5) / 4)
    for k in range(-5, 6):  # hairline: a row of small curls on the forehead, arched, higher in the middle
        x = 0.085 * k
        y = 2.04 - 0.008 * k * k
        zz = max(1 - ((y - 1.68) / 0.4465) ** 2 - (x / 0.4935) ** 2, 0.02)
        front((x, y, 0.47 * math.sqrt(zz) + 0.02), 0.11 + 0.02 * (k % 2))
    for sx in (-1, 1):  # temples: curls closing the hairline into the side mass
        front((0.47 * sx, 1.95, 0.12), 0.13)
        front((0.53 * sx, 1.82, 0.33), 0.13)  # fills the crevice between temple and side curls
        front((0.46 * sx, 1.87, 0.28), 0.1)
        front((0.42 * sx, 1.78, 0.25), 0.07)  # sideburn curls: the face edge runs straight down
        front((0.43 * sx, 1.66, 0.24), 0.07)


HF = ("hair_front", "head", "R")
HB = ("hair_back", "head", "R")


def buzz():
    """Buzz: one thin layer hugging the skull, hairline traced on the forehead and above the ears; no fringe, no lip."""
    sphere(HB, (0, 1.66, -0.1), 0.48, (1.0, 0.92, 0.98))  # nape
    # the whole visible crown is one front piece ~0.07 over the skull, so no edge runs across the top
    sphere(HF, (0, 1.77, -0.06), 0.505, (1.02, 0.9, 1.0))


def side_part():
    """Short side part: a clean part line at x 0.2, the long side swept smooth across the top and down to the far temple."""
    _short_sides()
    for z in (0.27, 0.14, 0.0, -0.14, -0.28):  # overlapping strands fuse into one smooth sweep from the part
        e = -0.36 if z > 0.2 else -0.42
        chain(HF, _top(0.2, z, 0.02 if z > 0.2 else 0.04), _top(-0.08, z, 0.05), 0.1, 6)
        chain(HF, _top(-0.08, z, 0.05), _top(e, z, 0.02), 0.1, 6)


def quiff():
    """Quiff: short sides, the front brushed up off the forehead, flaring forward into a rounded crest, tapering back."""
    _short_sides()
    front((0.02, 2.06, 0.25), 1.0, (0.28, 0.2, 0.15))  # brushed up from the hairline
    for x in (-0.09, 0.09):  # two soft grooves on the upswept face
        chain(HF, (x, 1.98, 0.32), (x * 1.3 + 0.03, 2.22, 0.36), 0.1, 6)
    front((0.04, 2.25, 0.3), 1.0, (0.3, 0.12, 0.16))  # the crest, wider than the base, rolled forward
    chain(HF, (0.03, 2.25, 0.24), (0.0, 2.14, -0.22), 0.13, 6)  # tapers back over the crown


def pompadour():
    """Pompadour: one tall smooth roll rising off a high hairline, swept back; short slick sides."""
    _short_sides()
    front((0, 1.98, -0.14), 1.0, (0.47, 0.4, 0.5))  # the raised top, continuous with the sides at y 1.85
    front((0.05, 2.2, 0.16), 1.0, (0.34, 0.2, 0.28))  # the roll's crest, forward over the forehead


def slick_back():
    """Slicked back: smooth and flat, combed straight back off a high hairline; tight sides, no fringe."""
    _short_sides(1.8, 0.41, 0.5, -0.1)
    for x in (-0.26, -0.13, 0.0, 0.13, 0.26):  # comb ridges: fade in at the hairline, run straight back
        z0 = 0.3 - abs(x) * 0.35
        for i in range(14):
            t = i / 13
            front(_top(x, z0 + (-0.32 - z0) * t, 0.035), 0.015 + 0.04 * min(t * 2.5, 1))


def mohawk():
    """Mohawk: a tall fin from the forehead to the nape; the sides are shaved, a narrow crown strip covers the top."""
    import math

    cap(0.44, 1.8, 0.6)  # hidden behind the head from the front: no rim beside the shaved sides
    hug(rx=0.42, ry=0.3, rz=0.43, y=1.86)  # a high crown strip, not a helmet: it ends above the temples
    for i in range(17):
        a = math.radians(40 - 150 * i / 16)  # from over the forehead, over the top, down to the nape
        for k, r in ((0.44, 0.09), (0.54, 0.095), (0.64, 0.09), (0.72, 0.07)):
            p = (0, 1.7 + k * math.cos(a), k * math.sin(a))
            sphere(HF if p[2] > -0.05 else HB, p, r, (1.25, 1, 1))


def undercut():
    """Undercut: sides clipped close to the skull, a long top lifted at the front and swept over to one side."""
    cap(0.46, 1.84, 0.66)  # top 2.14, under the hug layer; the sides end above the ears
    hug()
    front((0.03, 2.12, 0.0), 0.3, (0.95, 0.42, 1.25))  # the long top, no wider than the skull
    chain(HF, (-0.22, 2.18, 0.2), (0.26, 2.1, 0.27), 0.13, 6)  # lifted front, swept from the part across
    front((0.32, 2.03, 0.22), 0.1, (1.0, 1.3, 0.8))  # the swept tip, above the temple
    back((0.0, 2.06, -0.3), 0.28, (1.0, 0.5, 0.8))


def curly_top():
    """Curly top fade: sides clipped close, tight curls over the whole top down to the hairline."""
    import math

    cap(0.46, 1.84, 0.66)
    hug(rx=0.44, ry=0.34)
    curls = [(0, 90)] + [(t, 64) for t in range(0, 360, 60)] + [(t + 20, 40) for t in range(0, 360, 40)]
    curls += [(t, 18) for t in range(-60, 61, 24)]  # the front hairline is curls too, so the edge has no lip
    for t, e in curls:
        t, e = math.radians(t), math.radians(e)
        x, y, z = 0.42 * math.cos(e) * math.sin(t), 1.86 + 0.32 * math.sin(e), 0.42 * math.cos(e) * math.cos(t)
        sphere(HF if z > -0.1 else HB, (x, y, z), 0.105)


def man_bun():
    """Man bun: sides and top pulled back flat, a big bun high on the back of the crown, showing over the top."""
    cap(0.47, 1.8, 0.72)  # top 2.14, under the hug layer
    hug()
    back((0, 2.3, -0.3), 0.2)
    back((0, 2.14, -0.36), 0.14)  # the neck of the bun, joining it to the cap


def top_knot():
    """Top knot: hair pulled up, a bun sitting high on top of the head."""
    cap(0.5, 1.84, 0.9)
    shell()
    temples()
    front((0, 2.36, -0.08), 0.18, (1.0, 0.85, 1.0))


def low_ponytail():
    """Low ponytail: pulled back, tied low behind the left ear; the smooth tail falls forward over the shoulder."""
    _pulled()
    back((0.3, 1.58, -0.26), 0.13)  # the gathered hair behind the ear
    _behind_ear(1)
    _tube(HF, ((0.36, 1.52, -0.12), (0.26, 1.4, -0.02), (0.15, 1.34, 0.16), (0.1, 1.2, 0.22), (0.08, 1.06, 0.2)),
          0.09, 0.05)


def pigtails():
    """Pigtails: middle part, two bunches tied high behind the ears that flare out and taper above the shoulders."""
    _pulled()
    for s in (-1, 1):
        back((0.44 * s, 1.76, -0.14), 0.09)  # the tie
        _tube(HB, ((0.48 * s, 1.74, -0.14), (0.57 * s, 1.66, -0.14), (0.59 * s, 1.52, -0.13), (0.55 * s, 1.4, -0.12)),
              0.12, 0.05)


def two_braids():
    """Two braids, middle part: the left plait comes forward over the shoulder and down the front, the right one
    (the waving arm's side, which crosses the chest) falls back behind the shoulder, seen from ear to shoulder."""
    _pulled()
    for s in (-1, 1):
        back((0.36 * s, 1.62, -0.2), 0.11)
        _behind_ear(s)
    _plait(HF, ((0.36, 1.52, -0.12), (0.26, 1.4, -0.02), (0.16, 1.34, 0.16), (0.1, 1.18, 0.22), (0.07, 1.0, 0.2)),
           0.08, 0.055)
    front((0.07, 0.97, 0.2), 0.045)
    _plait(HB, ((-0.4, 1.58, -0.1), (-0.45, 1.42, -0.12), (-0.42, 1.2, -0.16)), 0.1, 0.08)


def single_braid():
    """Single braid: pulled back to one side, one plait forward over the left shoulder and down the front
    (the right arm waves across the chest, so the plait stays clear of it)."""
    _pulled()
    back((0.3, 1.58, -0.26), 0.13)
    _behind_ear(1)
    _plait(HF, ((0.36, 1.52, -0.12), (0.26, 1.4, -0.02), (0.16, 1.34, 0.16), (0.1, 1.18, 0.22), (0.07, 1.0, 0.2)),
           0.085, 0.055)
    front((0.07, 0.97, 0.2), 0.045)


def space_buns():
    """Space buns: all the hair pulled up tight off the face and sides into two coiled buns high on the crown."""
    import math

    cap(0.49, 1.85, 0.84)
    _crown()
    for s in (-1, 1):
        c = (0.27 * s, 2.32, 0.04)
        front((0.22 * s, 2.2, 0.03), 0.14, (1.0, 0.7, 1.0))  # gathered base, deep in the crown
        front(c, 0.17, (1.0, 0.85, 1.0))
        # a rope of hair wound round the bun, base to top: reads as a twisted bun, not a smooth round ear
        for i in range(140):
            t = i / 139
            th, ph = s * 2 * math.pi * 2.75 * t, math.radians(-25 + 100 * t)
            p = (c[0] + 0.17 * math.cos(ph) * math.sin(th), c[1] + 0.145 * math.sin(ph), c[2] + 0.17 * math.cos(ph) * math.cos(th))
            front(p, 0.065 - 0.025 * t)


def curly_bob():
    """Curly bob: a round chin-length mass of tight curls all over, curly fringe; the ends tuck under at the jaw."""
    cap(0.53, 1.78, 0.95)
    back((0, 1.62, -0.12), 0.44, (1.12, 0.7, 0.85))
    _crown(1.8, -0.06, 0.51, 0.9)
    _curls((0, 1.72, -0.04), (0.53, 0.5, 0.53), 0.1, (2.2, 2.09, 1.98, 1.86, 1.74, 1.62, 1.51), 24, 1.97)


def long_wavy():
    """Long wavy: middle part, curtains framing the face, one sheet down the back whose edges ripple in S waves."""
    cap()
    _crown()
    temples()
    for s in (-1, 1):
        chain(HF, (0.04 * s, 2.1, 0.2), (0.3 * s, 1.86, 0.18), 0.13, 5)
        chain(HF, (0.34 * s, 1.84, -0.03), (0.37 * s, 1.62, -0.02), 0.16, 4)
        pts = [(0.37, 1.72, -0.1), (0.47, 1.54, -0.12), (0.33, 1.36, -0.14), (0.48, 1.18, -0.15), (0.35, 1.0, -0.16)]
        for a, b in zip(pts, pts[1:]):
            chain(HB, (a[0] * s, a[1], a[2]), (b[0] * s, b[1], b[2]), 0.15)
    back((0, 1.42, -0.24), 0.4, (1.02, 1.2, 0.55))


def long_curly():
    """Long curly: a big curly mane, curls over the crown and fringe, one mass to mid back with a curly outline."""
    cap(0.55, 1.8, 0.95)
    _crown(1.8, -0.06, 0.52, 0.9)
    back((0, 1.72, -0.16), 0.52, (1.12, 0.62, 0.85))
    back((0, 1.36, -0.24), 0.44, (1.2, 1.05, 0.55))
    _curls((0, 1.74, -0.05), (0.54, 0.5, 0.54), 0.11, (2.2, 2.09, 1.98, 1.86, 1.74), 24, 1.97)
    for s in (-1, 1):
        for i, y in enumerate((1.62, 1.5, 1.38, 1.26, 1.14, 1.02)):
            back(((0.52 + 0.03 * (i % 2)) * s, y, -0.16), 0.12)
            back(((0.4 + 0.02 * (i % 2)) * s, y - 0.06, -0.06), 0.11)
    for x in (-0.42, -0.21, 0, 0.21, 0.42):
        back((x, 0.96 - 0.03 * (abs(x) > 0.3), -0.24), 0.13)


def dreadlocks():
    """Dreadlocks: thick ropes from the crown over the skull; the front ones frame the face to the jaw, the rest hang
    behind the neck and shoulders (no loose ends beside them)."""
    cap(0.5, 1.84, 0.9)
    shell(0.46, 2.0, 0.42)
    r = 0.065
    for s in (-1, 1):
        # swept off the forehead to the sides along the skull, then down beside the face
        for a, b, c, d in (
            ((0.06, 2.19, 0.18), (0.26, 2.05, 0.31), (0.42, 1.8, 0.2), (0.44, 1.44, 0.14)),
            ((0.16, 2.21, 0.02), (0.38, 2.04, 0.16), (0.5, 1.78, 0.06), (0.5, 1.42, 0.04)),
        ):
            for p, q in ((a, b), (b, c), (c, d)):
                chain(HF, (p[0] * s, p[1], p[2]), (q[0] * s, q[1], q[2]), r)
        chain(HF, (0.3 * s, 2.16, -0.12), (0.5 * s, 1.9, -0.1), r)
        # over the crown from the front hairline to the back, where they carry on down behind
        chain(HF, (0.1 * s, 2.14, 0.3), (0.12 * s, 2.25, 0.04), r)
        chain(HF, (0.12 * s, 2.25, 0.04), (0.14 * s, 2.12, -0.3), r)
        # behind: ropes down the back of the head to the upper back, inside the neck and shoulder line
        for x in (0.14, 0.3, 0.42):
            chain(HB, (x * s, 2.02, -0.34), (x * 0.9 * s, 1.08, -0.3), r)
    chain(HB, (0, 2.05, -0.4), (0, 1.08, -0.36), r)


def cornrows():
    """Cornrows: seven slim rows running straight back from the hairline, standing proud of a thin skull-close base
    that starts at the hairline (the grooves between the rows show the scalp-tight base)."""
    import math

    cap(0.47, 1.8, 0.86)  # behind: kept under the rows so they make the top outline
    shell(0.42, 1.8, 0.88, 1.12)  # thin skin over the skull, crossing the head surface at the hairline
    for x in (-0.36, -0.24, -0.12, 0.0, 0.12, 0.24, 0.36):
        k = math.sqrt(1 - (x / 0.5) ** 2)  # the row's arc over the skull narrows towards the sides
        pts = [(x, 1.8 + 0.4 * k * math.sin(t), 0.02 + 0.45 * k * math.cos(t))
               for t in (math.radians(10 + i * 20) for i in range(9))]  # hairline over the top to the crown back
        for p, q in zip(pts, pts[1:]):
            chain(HF, p, q, 0.045)


def mullet():
    """Mullet: short textured top and short sides above the ears; the long back stays hidden behind the head down to
    the jaw and only shows below it, on both sides of the neck down to the shoulders (behind the body)."""
    cap(0.49, 1.86, 0.84)
    front((0, 1.95, -0.02), 0.5, (1.0, 0.66, 1.0))  # short all over; the head occluder trims it above ears and brow
    for x, z in ((-0.2, 0.18), (0.0, 0.24), (0.2, 0.18), (-0.12, -0.08), (0.12, -0.08)):
        front((x, 2.2, z), 0.1, (1.0, 0.6, 1.0))  # textured top, sunk into the cap (no lip)
    for s in (-1, 1):
        chain(HB, (0.24 * s, 1.42, -0.24), (0.34 * s, 1.2, -0.16), 0.09)  # inside the head outline above the jaw
        back((0.35 * s, 1.16, -0.14), 0.09, (1.2, 0.8, 1.0))  # the flick below the jaw
    chain(HB, (0, 1.74, -0.36), (0, 1.22, -0.3), 0.24)


def shag():
    """Shag: choppy layers, a messy fringe and flicked-out sides at jaw length."""
    cap(0.52, 1.83, 0.92)
    shell(0.45, 2.04, 0.48)
    temples()
    # choppy top: overlapping clumps of mixed size over the crown, each row lower and further forward
    for x, y, z, r in ((-0.2, 2.24, -0.05, 0.13), (0.05, 2.27, -0.02, 0.14), (0.26, 2.2, -0.06, 0.12),
                       (-0.32, 2.14, 0.1, 0.12), (-0.1, 2.2, 0.14, 0.12), (0.14, 2.19, 0.15, 0.13),
                       (0.35, 2.1, 0.1, 0.11)):
        front((x, y, z), r, (1.0, 0.8, 1.0))
    # messy fringe: uneven points falling over the brow, one row, tips at different lengths
    for x, y, d in ((-0.3, 2.04, 0.16), (-0.14, 2.08, 0.24), (0.02, 2.08, 0.17), (0.17, 2.07, 0.25), (0.32, 2.03, 0.14)):
        spike(HF, (x, y, 0.24), (x * 1.1, y - d, 0.36), 0.09, 0.035, 5)
    for s in (-1, 1):
        # layered sides down to the jaw, the ends flicked out but still joined to the head
        spike(HF, (0.42 * s, 1.92, 0.04), (0.5 * s, 1.7, 0.08), 0.13, 0.08, 5)
        spike(HF, (0.44 * s, 1.78, -0.02), (0.54 * s, 1.56, 0.0), 0.12, 0.08, 5)
        spike(HB, (0.4 * s, 1.66, -0.12), (0.54 * s, 1.46, -0.1), 0.12, 0.08, 5)


def bowl_cut():
    """Bowl cut: a rounded helmet of hair combed straight down from the crown, cut in one level blunt line round the
    head just above the brows and the ears (no pads, no ridge, no hanging sides)."""
    import math

    cap(0.5, 1.94, 0.66)  # back edge level with the sides, nothing hangs down behind
    c, rx, ry = (0, 1.92, 0.0), 0.51, 0.337
    front(c, rx, (1.0, ry / rx, 1.0))  # the helmet; the head occluder trims it at the bowl line
    for f in range(-120, 121, 15):  # combed strands down the visible front half, their tips make the blunt line
        p = math.radians(f)
        pts = [(c[0] + rx * math.sin(t) * math.sin(p), c[1] + ry * math.cos(t), c[2] + rx * math.sin(t) * math.cos(p))
               for t in (math.radians(a) for a in (35, 60, 85, 108))]
        for a, b in zip(pts, pts[1:]):
            chain(HF, a, b, 0.055)


def spiky():
    """Spiky: short sides, upright spikes across the top."""
    import math

    cap(0.47, 1.94, 0.66)  # short at the back: the lower edge sits at the ear tops, not the jaw
    shell(0.42, 2.02, 0.4, 1.05)  # thin over the brow: no rim for the spikes to stand on; no side flaps
    # spikes of mixed length, rooted inside the crown and standing mostly up (a little out, the front
    # ones forward over the brow): pointing straight out from the head centre made a crown ring
    for x, z, ln, r in ((-0.25, 0.18, 0.15, 0.065), (-0.08, 0.24, 0.19, 0.07), (0.12, 0.23, 0.16, 0.065),
                        (0.29, 0.12, 0.14, 0.06), (-0.2, 0.04, 0.24, 0.09), (0.03, 0.1, 0.28, 0.1),
                        (0.22, 0.0, 0.22, 0.09), (-0.1, -0.16, 0.24, 0.085), (0.13, -0.2, 0.2, 0.085),
                        (0.0, -0.32, 0.17, 0.08), (-0.3, -0.12, 0.17, 0.075), (0.32, -0.14, 0.16, 0.075)):
        y = 1.68 + 0.46 * math.sqrt(max(1 - (x / 0.5) ** 2 - (z / 0.48) ** 2, 0.04))  # on the crown
        base = Vector((x, y, z))
        out = (base - Vector((0, 1.68, 0))).normalized()
        d = (out * 0.45 + Vector((0, 1, 0)) + Vector((0, 0, 0.12 if z > 0.15 else 0))).normalized()
        spike(HF, base - d * 0.08, base + d * ln, r, 0.022, 7)


def curtains():
    """Curtains: 90s middle part, short; two fringe wings frame the forehead, ears covered."""
    cap(0.5, 1.84, 0.88)
    shell(0.45, 2.1, 0.5)  # set high, so the middle of the forehead shows between the wings
    temples()
    for s in (-1, 1):
        # each wing: from the middle part high on the forehead, falling down and out to the temple, so a
        # V of forehead shows between them; thin at the part, fullest over the brow, melting into the crown
        pts = ((0.05, 2.16, 0.2, 0.06), (0.1, 2.06, 0.32, 0.08), (0.18, 1.95, 0.36, 0.095),
               (0.28, 1.86, 0.32, 0.1), (0.37, 1.8, 0.22, 0.09), (0.44, 1.76, 0.1, 0.08))
        for i in range(len(pts) - 1):
            (x0, y0, z0, r0), (x1, y1, z1, r1) = pts[i], pts[i + 1]
            spike(HF, (x0 * s, y0, z0), (x1 * s, y1, z1), r0, r1, 4)
        # the wing's root blends back into the crown (no step between wing and shell)
        spike(HF, (0.12 * s, 2.2, 0.06), (0.26 * s, 2.0, 0.26), 0.12, 0.1, 4)
        front((0.42 * s, 1.92, 0.12), 0.11, (0.85, 1.2, 1.0))  # closes the gap between the wing's end and the side hair


def half_up():
    """Half up: top section tied back in a small knot, the rest hangs long behind (long_straight sides)."""
    cap()
    shell(0.46, 2.02, 0.6, 0.97)  # the tied top: sleek and close to the skull
    temples()
    for s in (-1, 1):
        # the top section combed back from the hairline to the knot: smooth bands over the crown
        chain(HF, (0.3 * s, 2.02, 0.2), (0.1 * s, 2.24, -0.22), 0.09, 6)
        # the loose length below the tied section, close over the ears (no lobe), falling behind the shoulders
        chain(HF, (0.37 * s, 1.88, -0.02), (0.4 * s, 1.62, -0.04), 0.13, 4)
        chain(HB, (0.42 * s, 1.74, -0.1), (0.38 * s, 0.98, -0.16), 0.17, 10)
    chain(HB, (0, 1.6, -0.3), (0, 0.98, -0.3), 0.3, 8)
    # the knot: a round bun high on the back of the crown, standing clear of the head outline from the front
    front((0, 2.3, -0.22), 0.11)
    front((0, 2.4, -0.26), 0.17, (1.1, 0.95, 1.0))


def _crown(y=1.8, z=-0.07, r=0.5, sy=0.88):
    """Crown that grazes the skull: thins to nothing at the hairline (above the brow, the ear tops), so no lip."""
    front((0, y, z), r, (1.0, sy, 1.0))


def _curls(c, rad, r, ys, n0, face_y, hf_y=1.86):
    """Curls packed round an ellipsoid at heights ys; none over the face below face_y. Low or wide ones go behind."""
    import math

    for k, y in enumerate(ys):
        f = max(1 - ((y - c[1]) / rad[1]) ** 2, 0) ** 0.5
        n = max(int(n0 * f), 3)
        for i in range(n):
            t = 2 * math.pi * (i + 0.5 * (k % 2)) / n
            p = (c[0] + rad[0] * f * math.sin(t), y, c[2] + rad[2] * f * math.cos(t))
            if y < face_y and p[2] > 0.1:
                continue
            sphere(HF if y >= hf_y and abs(p[0]) < 0.42 else HB, p, r)

# Notes: helpers sit just before space_buns in body.py. The worktree started at main 54f086d, so it was detached to 67b4632 first (there is no local m5/hair-list branch). git lfs pull was needed for the child and adult_m body PNGs. The Godot import changes to docs/art-test were reverted. Nothing is committed. Last stills: scratchpad/w6/r3 (space_buns, long_curly), r2 (long_wavy) and r4 (curly_bob). The shared scratchpad loop.sh belongs to another agent; mine is scratchpad/w6/loop6.sh.


def _top(x, z, d=0.0):
    """Point on the child head's top surface (body(): centre y 1.68, radii 0.4935 / 0.4465 / 0.47) grown by d."""
    u = max(1 - (x / (0.4935 + d)) ** 2 - (z / (0.47 + d)) ** 2, 0.0)
    return (x, 1.68 + (0.4465 + d) * u**0.5, z)


def _short_sides(y=1.8, ry=0.4, rz=0.5, z=-0.08, rx=0.51):
    """Short-cut base: a skull-tight layer that surfaces above the temples (y 1.7), never below the ears,
    and from y 1.9 on the forehead; the head occluder trims the rest. No side flaps."""
    cap(0.48, 1.88, 0.78)
    front((0, y, z), 1.0, (rx, ry, rz))
    for s in (-1, 1):  # short sideburn in front of the ear
        front((0.455 * s, 1.72, 0.12), 0.07, (0.7, 1.5, 0.8))

# Caveats: body.py in worktree wf_4bf621e0-3e6-3 holds this code (latin-1, LF); nothing committed. Godot --import changed many unrelated .import files (assets/clay, house, clay2d, docs/art-test), which still need `git checkout` of the non-hair .import files. The quiff cap5 capture (bg bccfmkv89) may still be running; cap.sh deletes override.cfg when it ends.


def skin_z(x, y):
    """Front surface of the modelled head ((0, 1.68, 0) r 0.47 x(1.05, 0.95, 1)) at x, y: hairlines sit on it."""
    q = 1 - (x / 0.4935) ** 2 - ((y - 1.68) / 0.4465) ** 2
    return 0.47 * max(q, 0) ** 0.5


def hug(rx=0.46, ry=0.36, rz=0.46, y=1.8, z=-0.03):
    """Skull-tight crown layer for short and pulled-back cuts: it follows the forehead's curve (0.02 off at
    y 2.0), so its front edge meets the skin at a grazing angle with no lip, and it stays inside the head's
    outline below y 1.85, so the sides read short. Use it in place of shell() where a rim would show."""
    front((0, y, z), rx, (1.0, ry / rx, rz / rx))


def _path(pts, step):
    """Points every `step` along the polyline pts, with their 0-1 position along it."""
    pts = [Vector(p) for p in pts]
    segs = [(a, b, (b - a).length) for a, b in zip(pts, pts[1:])]
    total = sum(s[2] for s in segs)
    out, d = [], 0.0
    for a, b, n in segs:
        k = max(int(n / step), 1)
        for i in range(k):
            out.append((a.lerp(b, i / k), (d + n * i / k) / total))
        d += n
    out.append((pts[-1], 1.0))
    return out


def _tube(key, pts, r0, r1):
    """Smooth tail tapering r0 -> r1 along pts; beads 0.3 r apart so the remesh fuses one tube."""
    for p, t in _path(pts, 0.3 * min(r0, r1)):
        sphere(key, p, r0 + (r1 - r0) * t, segs=16)


def _plait(key, pts, r0, r1):
    """Braid: a thin core with flattened lobes alternating left and right, so it reads as plaited, not a tube."""
    _tube(key, pts, 0.55 * r0, 0.55 * r1)
    for i, (p, t) in enumerate(_path(pts, 0.7 * (r0 + r1) / 2)):
        r = r0 + (r1 - r0) * t
        sphere(key, p + Vector((0.16 * r * (1 if i % 2 else -1), 0, 0)), r, (1.0, 0.55, 0.8), segs=16)


def _pulled():
    """Hair pulled back tight, one smooth skin over the skull (head r 0.47 at y 1.68), about 0.05 thick: the back
    layer rims the outline down to the ears, the front crown dips under the forehead at a rounded hairline
    (y 1.9 in the middle, lower at the temples), so there is no ridge, no helmet and no side flap."""
    back((0, 1.76, -0.04), 0.47, (1.1, 0.95, 1.05))
    front((0, 1.84, -0.02), 0.5, (1.0, 0.72, 0.87))


def _behind_ear(s, y=1.5):
    """Hair combed back behind the ear down to the tie: shows only as a thin edge past the cheek, so the tail is attached."""
    chain(HB, (0.43 * s, 1.82, -0.1), (0.38 * s, y, -0.08), 0.08, 6)


def spike(key, base, tip, r0, r1, n=6):
    """A tapered spike: beads shrinking from r0 at the base to r1 at the tip (cut-local; chain() keeps one radius)."""
    a, b = Vector(base), Vector(tip)
    n = max(n, int((b - a).length / (0.3 * min(r0, r1))) + 2)  # dense enough to fuse, like chain()
    for i in range(n):
        t = i / (n - 1)
        sphere(key, a.lerp(b, t), r0 + (r1 - r0) * t, segs=16)


def sheet(key, a, b, r, scale):
    """Cut-local: a straight run of flattened beads 0.15 r apart, so the remesh fuses it into a flat panel, no bulges."""
    a, b = Vector(a), Vector(b)
    n = int((b - a).length / (0.15 * r)) + 2
    for i in range(n):
        sphere(key, a.lerp(b, i / (n - 1)), r, scale)


HAIRS = {
    f.__name__: f
    for f in (
        wisp,
        bob,
        crop,
        crew_cut,
        pixie,
        long_straight,
        high_ponytail,
        afro,
        buzz,
        side_part,
        quiff,
        pompadour,
        slick_back,
        mohawk,
        undercut,
        curly_top,
        man_bun,
        top_knot,
        low_ponytail,
        pigtails,
        two_braids,
        single_braid,
        space_buns,
        curly_bob,
        long_wavy,
        long_curly,
        dreadlocks,
        cornrows,
        mullet,
        shag,
        bowl_cut,
        spiky,
        curtains,
        half_up,
    )
}


# Seamless joints (director 2026-11-03): two pieces meeting at a joint are also remeshed together into a
# proxy "proxy|<layer>|<a>|<b>". render.py colours both pieces near the joint from the proxy's front render,
# so the overlap shows the fused surface (no rim at rest); silhouettes stay the pieces' own.
JOINTS = [("pelvis", "chest", "waist", 1), ("chest", "head", "neck", 1)] + [
    pair for s, d in ((1, "_l"), (-1, "_r")) for pair in (
        ("chest", "upper_arm" + d, "shoulder", s), ("upper_arm" + d, "forearm" + d, "elbow", s),
        ("forearm" + d, "hand" + d, "wrist", s), ("pelvis", "thigh" + d, "hip", s),
        ("thigh" + d, "shin" + d, "knee", s), ("shin" + d, "foot" + d, "ankle", s))]


GROW = {"tee": 0.03, "sweater": 0.025, "trousers": 0.03, "onesie": 0.04}  # garment sockets past the bare joint


def clay(ob):
    r = ob.modifiers.new("fuse", "REMESH")
    r.mode = "VOXEL"
    r.voxel_size = 0.012
    ob.modifiers.new("decimate", "DECIMATE").ratio = 0.25
    r = ob.modifiers.new("smooth", "CORRECTIVE_SMOOTH")
    r.iterations = 8
    r.use_only_smooth = True


def proxies():
    layers = {k[0] for k in PARTS}
    for layer in layers:
        for a, b, joint, s in JOINTS:
            src = PARTS.get((layer, a, "R"), []) + PARTS.get((layer, b, "R"), [])
            if not (PARTS.get((layer, a, "R")) and PARTS.get((layer, b, "R"))):
                continue
            copies = []
            for o in src:
                c = o.copy()
                c.data = o.data.copy()
                bpy.context.collection.objects.link(c)
                copies.append(c)
            bpy.ops.object.select_all(action="DESELECT")
            for c in copies:
                c.select_set(True)
            bpy.context.view_layer.objects.active = copies[0]
            bpy.ops.object.join()
            ob = bpy.context.object
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            ob.name = f"proxy|{layer}|{a}|{b}"
            ob["clay_color"] = NEUTRAL
            clay(ob)
            at, f, _ = T(j(joint, s))
            ob["joint"] = list(at)  # render.py takes the colour near this joint from the proxy's front render
            ob["r"] = (JR[joint] + GROW.get(layer, 0)) * f  # garments are wider: blend over their whole overlap


def fuse():
    for (layer, piece, mask), obs in PARTS.items():
        bpy.ops.object.select_all(action="DESELECT")
        for ob in obs:
            ob.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        bpy.ops.object.join()
        ob = bpy.context.object
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        ob.name = f"{layer}|{piece}|{mask}"
        ob["clay_color"] = FACE.get(mask, NEUTRAL) if layer == "face" else NEUTRAL
        kind = piece[:-2] if piece[-2] == "_" else piece
        flip = -1 if piece.endswith("_r") else 1
        ob["pivot"] = list(T(j(PIVOT[kind], flip))[0])
        ob["end"] = list(T(j(END[kind], flip))[0])
        if layer not in ("face", "wrinkles"):
            clay(ob)


HEM_Y = 0.8  # modelled height of a loose top's hem (director: straight hem, no point)
BAND_Y = 0.92  # modelled height of a tucked waistband


def hem(ob, y, keep_above):
    """Cut a piece flat at height y (modelled), leaving a straight edge."""
    import bmesh

    bm = bmesh.new()
    bm.from_mesh(ob.data)
    y = T((0, y, 0))[0][1]
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, y),
                           plane_no=(0, 0, 1 if keep_above else -1), clear_inner=True)
    bm.to_mesh(ob.data)
    bm.free()


def bake_ao():
    """AO per layer on its own (pieces turn, so contact shading between pieces would lie)."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    scene.cycles.device = "CPU"
    obs = [o for o in scene.objects if o.type == "MESH"]
    for ob in obs:
        bpy.context.view_layer.objects.active = ob
        for mod in list(ob.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        layer, piece = ob.name.split("|")[:2]
        if piece == "chest" and layer in ("body", "tee", "sweater"):  # skin cut too: no belly under the hem
            hem(ob, HEM_Y if WAIST == "loose" else BAND_Y, keep_above=True)
        ob.data.shade_smooth()
        ob.data.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        ob.data.attributes.active_color = ob.data.color_attributes["Col"]
        ob.data.materials.append(bpy.data.materials.new(ob.name))
    for ob in obs:
        others = [o for o in obs if o is not ob]
        for o in others:
            o.hide_render = True
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        scene.render.bake.target = "VERTEX_COLORS"
        bpy.ops.object.bake(type="AO")
        for o in others:
            o.hide_render = False
        base = hexc(ob["clay_color"])
        for d in ob.data.color_attributes["Col"].data:
            ao = 0.4 + 0.6 * d.color[0]
            d.color = (base[0] * ao, base[1] * ao, base[2] * ao, 1.0)
        ob.data.materials.clear()


bpy.ops.wm.read_factory_settings(use_empty=True)
body()
if HAIR_ONLY:
    for key in [k for k in PARTS if not (k[0] == "body" and k[1] in ("head", "chest"))]:
        for ob in PARTS.pop(key):
            bpy.data.objects.remove(ob)
elif AGE == "baby":
    onesie()
else:
    tee()
    sweater()
    trousers()
if HAIR:
    HAIRS[HAIR]()
if not HAIR_ONLY:
    proxies()
fuse()
bake_ao()
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_vertex_color="ACTIVE", export_materials="NONE",
                          export_texcoords=False, export_extras=True)
print("EXPORTED", OUT, len([o for o in bpy.context.scene.objects]))
