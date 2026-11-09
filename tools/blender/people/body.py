"""Modular people, vertical slice (docs/PEOPLE.md ยง10 step 1): child_f_skinny as 15 rigid clay pieces,
plus garment and hair recipes, all in neutral clay for tinting in game.

Run headless:
  blender -b --factory-startup --python tools/blender/people/body.py -- <out.glb>

Every object is named "<layer>|<piece>|<mask>":
  layer  body, face (fixed colours, not tinted), tee, sweater, trousers, onesie, pacifier, hair_back, hair_front
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
    # dense enough to fuse after T() stretches the neck (director: sparse beads pinched under the head)
    chain(("body", "head", "R"), (0, 1.3, 0), (0, 1.46, 0), 0.09, 5 + int(NECK_UP * 40))
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
    sphere((layer, "upper_arm_" + side, "R"), tuple(a), r, (1, 0.96, 1))  # top ~ 0.1 above the joint


def tee():
    torso("tee", 0.025)
    ring(("tee", "chest", "G"), (0, 1.36, 0.0), 0.12, 0.1, 0.035)
    for s, side in ((1, "l"), (-1, "r")):
        mid = Vector(j("shoulder", s)).lerp(Vector(j("elbow", s)), 0.65)
        if GROWN:
            sleeve_top("tee", side, s, mid, 0.105)  # arm 0.095 + 0.01: close fit, no puff
        else:
            chain(("tee", "upper_arm_" + side, "R"), j("shoulder", s), tuple(mid), 0.115, 4)
            socket("tee", "upper_arm_" + side, "shoulder", s, 0.015)


def sweater():
    torso("sweater", 0.035)
    ring(("sweater", "chest", "G"), (0, 1.36, 0.0), 0.13, 0.11, 0.04)
    if GROWN:
        for s, side in ((1, "l"), (-1, "r")):
            sleeve_top("sweater", side, s, j("elbow", s), 0.105)
            socket("sweater", "upper_arm_" + side, "elbow", s, 0.012)
            chain(("sweater", "forearm_" + side, "R"), j("elbow", s), j("wrist", s), 0.098)  # forearm 0.085 + 0.013, tapering from the upper sleeve
            socket("sweater", "forearm_" + side, "elbow", s, 0.012)
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


def bob_az(g):
    """Azimuth of a skin normal from straight ahead: 0 front, 1.57 side, 3.14 back."""
    from math import atan2

    return atan2(abs(g.x), g.z)


def bob_edge(tab, x):
    """Height and slope of the polyline tab [(x, y), ...] at x (flat beyond its ends)."""
    if x <= tab[0][0]:
        return tab[0][1], 0.0
    for (x0, y0), (x1, y1) in zip(tab, tab[1:]):
        if x <= x1:
            m = (y1 - y0) / (x1 - x0)
            return y0 + m * (x - x0), m
    return tab[-1][1], 0.0


def bob_field(inside, thick, w=0.05, ymin=1.45, R=0.075, back=True):
    """Hair laid on the skin: inside(p, g) is how far (m) the skin point p sits inside the hair's outline (<= 0
    outside); the hair stands thick(p, g) off the skull and eases in over the first w of that, so the hairline or
    hem is a round edge, never a lip. Low hair behind the ears goes on hair_back (it draws behind the body)."""

    def depth(p, g):
        s = inside(p, g)
        if s <= 0:
            return None
        return thick(p, g) * _step(0.0, w, s)

    _beads_on_skin(HF, lambda p, g: None if bob_az(g) > 2.2 and p.y < 1.85 else depth(p, g), ymin=ymin, R=R)
    if back:
        _beads_on_skin(HB, lambda p, g: depth(p, g) if bob_az(g) > 1.7 else None, ymin=ymin, R=R)


def crop_tab(tab, t):
    """Value at t of the piecewise-linear table [(t, v), ...] (sorted by t), held flat beyond its ends."""
    if t <= tab[0][0]:
        return tab[0][1]
    for (t0, v0), (t1, v1) in zip(tab, tab[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return tab[-1][1]


def crop_cover(thick, hairline, w=0.045, lumps=(), ymin=1.5, R=0.075):
    """A short cut as one layer of hair on the skin (no cap, no rim): thick(ny, p) is its thickness by the height of
    the skin normal, lumps [((x, y, z), sigma, height)] add soft chunks, and the layer eases to nothing over `w`
    above hairline(p, th), th being the azimuth from straight ahead (0 face, 1.57 ear, 3.14 back)."""
    from math import atan2, exp

    def depth(p, g):
        th = atan2(abs(p.x), p.z)
        d = thick(max(g.y, 0.0), p)
        for c, s, h in lumps:
            d += h * exp(-(((p - Vector(c)).length / s) ** 2))
        return d * _step(0.0, w, p.y - hairline(p, th))

    _beads_on_skin(HF, depth, ymin=ymin, R=R)


def crop_tips(x, pitch, amp, x0=0.0):
    """0 at the middle of each point of a scalloped edge (period `pitch`), `amp` between two points."""
    f = abs(((x - x0) / pitch + 0.5) % 1.0 - 0.5) * 2  # 0 at a tip, 1 between
    return amp * f


def quiff_yh(th, line):
    """Hairline height at azimuth th (degrees from straight ahead, 0-180): eased between the (degrees, y) nodes."""
    for (a0, y0), (a1, y1) in zip(line, line[1:]):
        if th <= a1:
            return y0 + (y1 - y0) * _step(a0, a1, th)
    return line[-1][1]


def quiff_ridge(p, spine, hs, ws, k=1.5):
    """Height of a swept ridge over the skin point p: a bell across the polyline `spine` (skin points), height hs and
    half-width ws interpolated along it; k > 1 steepens the walls (a loaf, not a dome)."""
    best = None
    for i in range(len(spine) - 1):
        a, b = Vector(spine[i]), Vector(spine[i + 1])
        ab = b - a
        t = min(max((p - a).dot(ab) / ab.length_squared, 0.0), 1.0)
        s = (p - (a + ab * t)).length / (ws[i] + (ws[i + 1] - ws[i]) * t)
        if best is None or s < best[0]:
            best = (s, hs[i] + (hs[i + 1] - hs[i]) * t)
    return best[1] * _step(0.0, 1.0, min(max(1.0 - best[0] ** 2, 0.0) * k, 1.0))


def quiff_hair(line, base, ridges=(), skew=0.0, ease=0.06, side=0.55, low=None, groove=None, R=0.06, up=0.0):
    """Hair as ONE layer on the skin (no ellipsoid crossing the head, so no lip): thickness `base` (thinner at the
    sides, so it never flares past the head) plus swept ridges [(spine, heights, widths, k)], all easing from nothing
    at the hairline `line` (tilted by skew along x). Where a ridge lifts the hair the beads grow with the lift, so the
    taller mass stays solid. low = (line, thickness): a thin layer under it (shaved sides). groove(p) adds combed
    lines."""
    from math import atan2, degrees

    lo = low[0] if low else line
    beads = []
    for p, g in _on_skin(min(y for _, y in lo) - 0.01, 0.5 * R):
        th = degrees(atan2(abs(p.x), p.z))
        yh = quiff_yh(th, line) - skew * p.x * (1.0 - _step(30.0, 80.0, th))
        cov = _step(yh, yh + ease, p.y)
        thin = 0.0
        if low:
            thin = low[1] * _step(quiff_yh(th, low[0]), quiff_yh(th, low[0]) + ease, p.y)
        elif cov <= 0:
            continue
        lift = sum(quiff_ridge(p, *r) for r in ridges) if cov > 0 else 0.0
        b = base * (side + (1 - side) * min(max(g.y, 0.0), 1.0))
        d = b + lift
        if groove:
            d += groove(p) * cov**3
        d = thin + cov * max(d - thin, 0.0)
        lift *= cov
        if d > 0.003:
            r = R * (1.0 + 4.0 * lift)
            u = (g + Vector((0.0, up, 0.0))).normalized()
            beads.append((tuple(p + g * (d - lift - r) + u * lift), r))
    cloud(HF, beads)


def mohawk_stubble(half=0.3, fade=0.12, th=0.026):
    """The shaved part: a thin stubble layer on the skin that hugs the crest (|x| < half, fading out over `fade`),
    rising from a hairline on the forehead over the crown and down to the nape; bare skin beyond it."""

    def depth(p, g):
        side = 1.0 - _step(half, half + fade, abs(p.x))
        yh = 1.7 + 0.2 * g.z
        d = th * side * _step(yh, yh + 0.08, p.y)
        return d if d > 0.004 else None

    _beads_on_skin(HF, depth, ymin=1.45, R=0.05)


def mohawk_dir(a):
    """Point on the head's midline profile at angle a (degrees from straight up, positive towards the face) and
    its outward unit normal, both in the (y, z) plane."""
    from math import cos, radians, sin

    a = radians(a)
    y, z = HEAD_C[1] + HEAD_R[1] * cos(a), HEAD_R[2] * sin(a)
    ny, nz = cos(a) / HEAD_R[1], sin(a) / HEAD_R[2]
    n = (ny * ny + nz * nz) ** 0.5
    return y, z, ny / n, nz / n


def mohawk_ridge(top=0.3, w=0.125, a0=68, a1=-124, tufts=True):
    """The crest: one continuous fin from the forehead over the crown to the nape, standing `top` off the skull at
    the crown, rounded on top, tapering to a thin strip at both ends. Beads in columns along the midline, ~0.04
    apart, so the remesh fuses it into one smooth fin; a row of short tufts along its top breaks the silhouette.
    Stations from the crown forward go on hair_front, the rest on hair_back (both cover the crown so the two
    halves meet inside the fin)."""
    from math import sin

    hf, hb = [], []

    def height(a):
        rise = _step(a0, a0 - 36, a) * (1 - 0.82 * _step(-18, a1 + 4, a))
        return 0.045 + (top - 0.045) * rise

    def put(a, bead):
        if a > -22:
            hf.append(bead)
        if a < 14:
            hb.append(bead)

    n = int((a0 - a1) / 3.5)
    for i in range(n + 1):
        a = a0 - (a0 - a1) * i / n
        y, z, ny, nz = mohawk_dir(a)
        h = height(a)
        ww = w * (0.6 + 0.4 * _step(a0, a0 - 14, a)) * (0.7 + 0.3 * _step(a1, a1 + 22, a))
        ks = [-0.03 + 0.035 * q for q in range(int((h + 0.03) / 0.035))]
        rt = min(0.1, 0.5 * (h + 0.03))
        ks = [k for k in ks if k < h - rt] + [h - rt]
        for k in ks:
            r = ww * (1 - 0.3 * max(k, 0) / max(h, 0.05)) if k < h - rt else min(ww, rt + 0.015)
            put(a, ((0, y + ny * k, z + nz * k), r))
    if tufts:  # short tapered tufts standing up from the crest line, leaning back a little
        for q, a in enumerate(range(54, -80, -12)):
            y, z, ny, nz = mohawk_dir(a)
            h = height(a) - 0.04
            ln = 0.1 + 0.05 * sin(q * 2.1) ** 2
            base = Vector((0, y + ny * h, z + nz * h))
            tip = base + Vector((0.0, ny + 0.5, nz - 0.25)).normalized() * ln
            tb = []
            mohawk_spike(tb, tuple(base), tuple(tip), 0.075, 0.025)
            for bead in tb:
                put(a, bead)
    cloud(HF, hf)
    cloud(HB, hb)


def mohawk_spike(beads, base, tip, r0, r1):
    """A tapered spike as beads [(at, r)] for cloud(): r0 at the base to r1 at the tip, each bead 0.3 r from the last."""
    a, b = Vector(base), Vector(tip)
    n = (b - a).length
    t = 0.0
    while True:
        r = r0 + (r1 - r0) * t
        beads.append((tuple(a.lerp(b, t)), r))
        if t >= 1.0:
            break
        t = min(t + 0.3 * r / n, 1.0)


def man_bun_cap(fy=1.9, ty=1.76, sy=1.62, by=1.5, top=0.1, side=0.035, w=0.09):
    """Pulled-back hair as one layer on the skin: thin at the sides, chunkier on top, eased in to nothing over `w`
    at a rounded hairline (fy in the middle of the forehead, ty at the temple, sy above the ear, by round the
    back), so there is no rim, no lip and no lobe wider than the head."""
    from math import atan2, pi

    pts = ((0.0, fy), (0.6, fy - 0.015), (1.0, ty), (1.5, sy), (2.3, by), (pi, by))

    def hairline(th):
        for (a0, y0), (a1, y1) in zip(pts, pts[1:]):
            if th <= a1:
                return y0 + (y1 - y0) * _step(a0, a1, th)
        return by

    def depth(p, g):
        e = _step(0.0, w, p.y - hairline(abs(atan2(g.x, g.z))))
        if e <= 0:
            return None
        return (side + (top - side) * max(g.y, 0.0) ** 1.5) * e

    _beads_on_skin(HF, depth, ymin=by)


def man_bun_coil(c, rad, s=1, n=140, r0=0.065, r1=0.04, turns=2.75, ph0=-25, ph1=75):
    """A rope of hair wound round an ellipsoid (centre c, radii rad), base to top, so a bun reads as twisted."""
    from math import cos, pi, radians, sin

    for i in range(n):
        t = i / (n - 1)
        th, ph = s * 2 * pi * turns * t, radians(ph0 + (ph1 - ph0) * t)
        front(
            (c[0] + rad[0] * cos(ph) * sin(th), c[1] + rad[1] * sin(ph), c[2] + rad[2] * cos(ph) * cos(th)),
            r0 + (r1 - r0) * t,
        )


def man_bun_bun(c, rad, root, r_root, r_neck, s=1, turns=2.75):
    """A bun: a wide root grown out of the crown (root = a point inside the head, so there is no seam), a tapering
    neck up to the ball, and the coil round it. All one front piece, so it fuses with the cap."""
    spike(HF, root, (c[0], c[1] - 0.6 * rad[1], c[2]), r_root, r_neck, 6)
    front(c, 1.0, rad)
    man_bun_coil(c, (rad[0] * 0.95, rad[1] * 0.95, rad[2] * 0.95), s, turns=turns)


def man_bun_curtain(y0=1.7, y1=1.3, z=-0.2):
    """The long hair behind: one wide flat sheet (the long_straight back sheet, 0.42 half-width: narrower than the
    head), dense beads so it fuses smooth, with a rounded end at the shoulders."""
    sheet(HB, (0, y0, z), (0, y1, z - 0.02), 0.3, (1.4, 1.0, 0.6))
# --- m1 end ---


def low_ponytail_raw(key, beads, segs=12):
    """Round beads [(point, radius)] given in the finished figure's own space (no age transform), as ONE object."""
    from math import cos, pi, sin

    rings = segs // 2
    unit = [(0.0, 0.0, 1.0)]
    for i in range(1, rings):
        ph = pi * i / rings
        unit += [(sin(ph) * cos(2 * pi * k / segs), sin(ph) * sin(2 * pi * k / segs), cos(ph)) for k in range(segs)]
    unit.append((0.0, 0.0, -1.0))
    last = len(unit) - 1
    tris = [(0, 1 + k, 1 + (k + 1) % segs) for k in range(segs)]
    for i in range(rings - 2):
        for k in range(segs):
            a0, a1 = 1 + i * segs + k, 1 + i * segs + (k + 1) % segs
            tris.append((a0, a0 + segs, a1 + segs))
            tris.append((a0, a1 + segs, a1))
    tris += [(last, last - segs + (k + 1) % segs, last - segs + k) for k in range(segs)]
    verts, faces = [], []
    for at, r in beads:
        c = g2b(*at)
        o = len(verts)
        verts += [(c.x + r * u[0], c.y + r * u[1], c.z + r * u[2]) for u in unit]
        faces += [(o + a, o + b, o + d) for a, b, d in tris]
    me = bpy.data.meshes.new("raw")
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new("raw", me)
    bpy.context.collection.objects.link(ob)
    PARTS.setdefault(key, []).append(ob)


def low_ponytail_cap(c=(0.0, 1.8, -0.02), rad=(0.5, 0.4, 0.44), w=0.16, part=None, wave=0.008, tilt=0.0):
    """Pulled-back hair as one skin on the skull: the old front crown, but its hairline is eased in over w, scalloped
    (wave) so it is not a ruled edge, and carries a parting groove at x = part (None: no parting) over the top."""
    from math import atan2, exp, sin

    def depth(p, g):
        x = _ell_depth(p, g, c, rad)
        if x is None:
            return None
        x -= wave * (0.5 + 0.5 * sin(24 * atan2(p.x, p.z))) * (1 - _step(0.1, 0.4, abs(p.x)) * 0.5)
        if x <= 0:
            return None
        d = x * _step(0.0, w, x)
        k = skin_lim(g.y)
        d = (d**-3 + k**-3) ** (-1 / 3)
        if part is not None:
            d -= 0.034 * exp(-(((p.x - part) + tilt * p.z) / 0.032) ** 2) * _step(-0.12, 0.08, p.z) * _step(1.9, 2.0, p.y)
        return d if d > 0 else None

    _beads_on_skin(HF, depth)


def low_ponytail_tail(key, pts, r0, r1, plait=False, tie=None, end=1.0, ti=1.0):
    """A tail or braid along pts (cut-local), tapering r0 -> r1. The path is laid in the figure's space first (scaled
    about the head centre, not stretched with the body), and the beads are spaced and sized there, so the tail is as
    fat, as long (in heads) and as smooth in teens and adults as in the child. tie: distance from the start where a
    gathered tie bulges and pinches; ti: strength of the tie's bulge and pinch; end: size of the last bead (a knot or tie at the tip) against r1."""
    from math import exp

    hc = Vector(T(HEAD_C)[0])  # the whole tail rides on the head bone: it keeps the head's scale and lies where the head puts it
    w = [hc + (Vector(p) - Vector(HEAD_C)) * H for p in pts]
    seg = [(a, b, (b - a).length) for a, b in zip(w, w[1:]) if (b - a).length > 1e-6]
    total = sum(s[2] for s in seg)

    def at(d):
        for a, b, n in seg:
            if d <= n:
                return a.lerp(b, d / n)
            d -= n
        return seg[-1][1]

    def rad(d):
        r = (r0 + (r1 - r0) * d / total) * H
        if tie is not None:
            u = d / H
            r *= 1 + 0.42 * ti * exp(-(((u - tie) / 0.04) ** 2)) - 0.4 * ti * exp(-(((u - tie - 0.085) / 0.035) ** 2))
        return r

    beads = []
    core = 0.72 if plait else 1.0
    step = 0.3 * min(r0, r1) * H * core
    for i in range(int(total / step) + 1):
        beads.append((at(i * step), rad(i * step) * core))
    beads.append((w[-1], r1 * H * core * end))
    if plait:  # lobes alternating left and right of the core: a plait, not a rope
        d, i = 0.0, 0
        while d < total:
            r = rad(d)
            beads.append((at(d) + Vector((0.32 * r * (1 if i % 2 else -1), 0, 0)), 0.78 * r))
            d += 0.7 * r
            i += 1
    low_ponytail_raw(key, beads)
# --- end low_ponytail helpers ---


def long_straight_lock(key, a, b, r0, r1, sc):
    """Cut-local: a flat hanging panel from a to b, tapering r0 -> r1, beads 0.2 r apart so the remesh fuses it."""
    a, b = Vector(a), Vector(b)
    n = int((b - a).length / (0.2 * min(r0, r1))) + 2
    for i in range(n):
        t = i / (n - 1)
        sphere(key, a.lerp(b, t), r0 + (r1 - r0) * t, sc)


def long_straight_curls(r=0.08, y_front=1.93, y_side=1.5, out=0.05, gap=1.5, flare=0.0):
    """Curls on the skin: beads r wide, gap*r apart, centred on the skull's surface (out lifts them on top, flare swells the sides around y 1.6, the bob's ends). The
    front edge is a curly fringe at y_front, sinking to y_side at the temples and sides, so no smooth band shows
    under them. Beads above y 1.84 go on hair_front (over the temples), the rest behind the head."""
    from math import atan2, sin

    hf, hb = [], []
    for p, g in _on_skin(y_side, gap * r):
        yth = y_front - (y_front - y_side) * _step(0.85, 1.25, atan2(abs(g.x), g.z))
        yth -= 0.06 * (1 + sin(p.x * 36)) * 0.5 * (1 - _step(0.85, 1.25, atan2(abs(g.x), g.z)))  # scalloped fringe
        if p.y < yth:
            continue
        c = p + g * (out * max(g.y, 0.0) - 0.01 + flare * max(0.0, 1 - ((p.y - 1.6) / 0.14) ** 2))
        (hf if p.y >= 1.84 else hb).append((tuple(c), r))
    cloud(HF, hf)
    cloud(HB, hb)


HEAD_C = (0.0, 1.68, 0.0)


HEAD_R = (0.4935, 0.4465, 0.47)  # the head ball in body(): (0, 1.68, 0) r 0.47 x (1.05, 0.95, 1)


def _step(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def skin_lim(ny):
    """Cap on hair thickness by the height of the skin normal (ny): thin at the sides, so side lobes hug the head's
    width, chunky on top."""
    return 0.045 + 0.26 * max(ny, 0.0) ** 1.5


def _on_skin(ymin, step=0.035):
    """(point, unit normal) over the head ball above ymin, about `step` apart."""
    from math import cos, pi, sin

    nr = int(pi * 0.47 / step)
    for i in range(nr + 1):
        ph = -pi / 2 + pi * i / nr
        c = cos(ph)
        n = max(int(2 * pi * c * 0.47 / step), 1)
        for k in range(n):
            th = 2 * pi * (k + 0.5 * (i % 2)) / n
            u = (c * sin(th), sin(ph), c * cos(th))
            p = Vector(tuple(HEAD_C[a] + HEAD_R[a] * u[a] for a in range(3)))
            if p.y >= ymin:
                yield p, Vector(tuple(u[a] / HEAD_R[a] for a in range(3))).normalized()


def cloud(key, beads, segs=12):
    """Many round beads [(at, r)] as ONE object (a bpy.ops sphere add, or a bmesh op per bead, gets slower with
    every object or vertex already there)."""
    from math import cos, pi, sin

    rings = segs // 2
    unit = [(0.0, 0.0, 1.0)]
    for i in range(1, rings):
        ph = pi * i / rings
        unit += [(sin(ph) * cos(2 * pi * k / segs), sin(ph) * sin(2 * pi * k / segs), cos(ph)) for k in range(segs)]
    unit.append((0.0, 0.0, -1.0))
    last = len(unit) - 1
    tris = [(0, 1 + k, 1 + (k + 1) % segs) for k in range(segs)]
    for i in range(rings - 2):
        for k in range(segs):
            a0, a1 = 1 + i * segs + k, 1 + i * segs + (k + 1) % segs
            tris.append((a0, a0 + segs, a1 + segs))
            tris.append((a0, a1 + segs, a1))
    tris += [(last, last - segs + (k + 1) % segs, last - segs + k) for k in range(segs)]
    verts, faces = [], []
    for at, r in beads:
        at, f, _ = T(tuple(at))
        c = g2b(*at)
        o = len(verts)
        verts += [(c.x + r * f * u[0], c.y + r * f * u[1], c.z + r * f * u[2]) for u in unit]
        faces += [(o + a, o + b, o + d) for a, b, d in tris]
    me = bpy.data.meshes.new("cloud")
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new("cloud", me)
    bpy.context.collection.objects.link(ob)
    PARTS.setdefault(key, []).append(ob)


def _beads_on_skin(key, depth, ymin=1.5, R=0.075):
    """A layer of hair on the skin: where depth(p, g) > 0 a bead whose top sits that far off the skin (centre
    R - depth below it, so the layer is inside the head wherever it thins out). Beads ~0.5 R apart: the remesh
    fuses them into one smooth skin of hair."""
    beads = []
    for p, g in _on_skin(ymin, 0.5 * R):
        d = depth(p, g)
        if d is not None and d > 0.003:
            beads.append((tuple(p + g * (d - R)), R))
    cloud(key, beads)


def _ell_depth(p, g, c, rad):
    """How far from skin point p along its normal g the outer surface of the ellipsoid (c, rad) lies; None when p
    is outside it."""
    q, a2, b2 = -1.0, 0.0, 0.0
    for a in range(3):
        o = (p[a] - c[a]) / rad[a]
        q += o * o
        b2 += 2 * o * g[a] / rad[a]
        a2 += (g[a] / rad[a]) ** 2
    if q > 0:
        return None
    return (-b2 + (b2 * b2 - 4 * a2 * q) ** 0.5) / (2 * a2)


def _skull_like(at, rad):
    return abs(at[0]) < 0.1 and 1.6 < at[1] < 2.2 and rad[0] >= 0.38 and rad[2] >= 0.33 and rad[1] <= 0.55


def skull(c, rad, w=0.07, lim=skin_lim):
    """The old way to cover the crown was an ellipsoid crossing the head, which left a lip along the crossing (a
    beret). This lays the same ellipsoid on the skin instead: hair as thick as the ellipsoid stands above the
    skull, along the skull's own normals, eased in over the first `w` (zero slope at the hairline, so it meets the
    skin at a graze) and soft-capped by lim(normal height), so the sides stay at the head's width. Where the
    ellipsoid is inside the head there is nothing."""

    def depth(p, g):
        x = _ell_depth(p, g, c, rad)
        if x is None or x <= 0:
            return None
        d = x * _step(0.0, w, x)
        if d <= 0:
            return None
        if lim:
            k = lim(g.y)
            d = (d**-3 + k**-3) ** (-1 / 3)
        return d

    _beads_on_skin(HF, depth)


def side_patch(D=0.034, y_lo=1.66, y_hi=1.98, th0=0.85, th1=1.2, w=0.11):
    """A thin patch of hair on the skin at each side of the head (the temple down to the ear top): D thick, fading
    out below y_lo, above y_hi and towards the face (azimuth th0 to th1 from straight ahead)."""
    from math import atan2

    def depth(p, g):
        th = atan2(abs(g.x), g.z)
        return D * _step(y_lo, y_lo + w, p.y) * (1 - _step(y_hi, y_hi + w, p.y)) * _step(th0, th1, th)

    _beads_on_skin(HF, depth, ymin=y_lo)


def shell(r=0.47, y=2.02, sy=0.6, sx=1.0):  # top 2.3 covers the cap dome; lower edge 1.74
    """Crown shell (PEOPLE.md: no scalp between fringe lumps): the old ellipsoid's top and thickness, but laid on
    the skull as a layer that thins to nothing at the hairline (see skull()), so no lip and no brim. It also
    closes the temples (side_patch())."""
    skull((0, y, 0.02), (r * sx, r * sy, r))
    side_patch()


def front(at, r, scale=(1, 1, 1)):
    rad = (r * scale[0], r * scale[1], r * scale[2])
    if _skull_like(at, rad):  # a skull-sized ellipsoid (crown, hug, short sides, helmet): lay it on the skin
        skull(at, rad)
    else:
        sphere(("hair_front", "head", "R"), at, r, scale)


def back(at, r, scale=(1, 1, 1)):
    sphere(("hair_back", "head", "R"), at, r, scale)


def temples():
    """Closes the sliver of scalp at the head's edge between the crown shell and the side hair (hair_check): a thin
    patch on the skin that fades at its lower and front edges, never wider than the head."""
    side_patch()


# Cuts (director 2026-11-03: 34, any cut on anyone). Rules that keep them clean in motion:
# - every piece hangs off the head bone, so whatever covers the scalp at rest covers it in every frame;
# - hair_front stays above the shoulder tops (y 1.36) outside |x| 0.2, so it never covers an arm;
#   anything longer goes on hair_back, which draws behind the body.
def wisp():
    """Baby hair: a wisp on top (build_clay_girl.py --age baby)."""
    front((0.05, 2.1, 0.12), 0.14, (1.3, 0.5, 1.0))


def bob():
    """Chin-length bob: one smooth skin of hair on the skull, straight fringe, sides falling to a level line under
    the ears, no layers; a round hem, no lip and no wings."""

    def inside(p, g):  # the fringe line across the brow, or the sides below the face-framing edge
        return max(p.y - 1.91, min(p.y - 1.52, (bob_az(g) - 1.1) * 0.45))

    bob_field(inside, lambda p, g: 0.068 + 0.082 * max(g.y, 0.0) ** 1.3)


def crop():
    """Crop: short and textured, the top in a few soft chunks, a short fringe of soft points brushed forward onto
    the forehead, the sides kept short but closing the temple down to the ear top."""
    top = [_top(x, z) for x, z in ((0.0, 0.05), (-0.2, 0.0), (0.2, 0.0), (0.0, -0.22), (-0.24, -0.2), (0.24, -0.2))]
    lumps = [(c, 0.1, 0.035) for c in top]

    def thick(ny, p):
        return 0.045 + 0.05 * ny**1.2

    def hairline(p, th):
        side = [(0.0, 1.93), (0.6, 1.95), (0.95, 1.84), (1.25, 1.72), (1.5, 1.68), (2.0, 1.62), (3.2, 1.55)]
        fringe = 1.0 - _step(0.5, 0.95, th)
        return crop_tab(side, th) - fringe * crop_tips(p.x, 0.12, 0.05, 0.06)

    crop_cover(thick, hairline, 0.05, lumps)


def crew_cut():
    """Crew cut: short and even, standing up flat across the top, a straight high hairline, the sides faded thin
    into the skin down to the ear top; no fringe."""

    def thick(ny, p):
        return 0.03 + 0.05 * ny**0.7

    def hairline(p, th):
        return crop_tab([(0.0, 1.99), (0.5, 1.98), (0.9, 1.9), (1.2, 1.76), (1.5, 1.7), (2.0, 1.62), (3.2, 1.55)], th)

    crop_cover(thick, hairline, 0.04)


def pixie():
    """Pixie: short and soft all over, longer on top and swept in one thick lock across the forehead from a side
    part to the far temple, short wisps in front of the ears."""

    def thick(ny, p):
        return 0.05 + 0.07 * ny**1.1

    lumps = [(_top(x, z), s, h) for x, z, s, h in ((-0.1, 0.1, 0.13, 0.06), (0.1, 0.0, 0.12, 0.04), (-0.2, -0.1, 0.12, 0.04))]

    def hairline(p, th):
        sweep = 2.0 - 0.45 * max(0.22 - p.x, 0.0)  # the lock's lower edge: high on the part side, down to the far temple
        side = crop_tab([(0.0, 1.99), (0.9, 1.88), (1.2, 1.74), (1.45, 1.64), (1.7, 1.6), (3.2, 1.55)], th)
        return min(side, sweep) if th < 1.0 else side

    crop_cover(thick, hairline, 0.05, lumps)
    for s in (-1, 1):  # a short wisp in front of each ear
        _tube(HF, [(0.44 * s, 1.74, 0.14), (0.44 * s, 1.6, 0.2)], 0.05, 0.022)


def long_straight():
    """Long straight, middle part: one thin layer on the skin (no rim at the forehead), the hairline falling from a
    centre part to the temples; thin panels framing the face carry on behind the shoulders, one flat sheet down the
    back; the ends taper and stop at different lengths."""
    cap(0.45, 1.76, 0.8)
    quiff_hair([(0, 2.02), (18, 1.95), (40, 1.8), (62, 1.66), (90, 1.56), (180, 1.5)], 0.05, side=0.85, ease=0.05)
    for s in (-1, 1):
        long_straight_lock(HF, (0.42 * s, 1.86, 0.0), (0.42 * s, 1.56, 0.0), 0.1, 0.11, (0.55, 1.0, 1.2))
        long_straight_lock(HB, (0.39 * s, 1.68, -0.04), (0.36 * s, 0.96, -0.1), 0.15, 0.1, (0.55, 1.0, 1.2))
    long_straight_lock(HB, (0, 1.72, -0.2), (0, 0.98, -0.22), 0.3, 0.24, (1.4, 1.0, 0.6))




def high_ponytail():
    """High ponytail: hair pulled up smooth off the forehead and the temples, gathered and tied on the crown; the tail
    arcs up over the tie and falls back, hugging the side of the head."""
    back((0, 1.78, -0.05), 0.47, (1.1, 0.97, 1.05))
    low_ponytail_cap(c=(0, 1.86, -0.02), rad=(0.5, 0.4, 0.44), part=None)
    side_patch(D=0.04, y_lo=1.58, y_hi=2.02)
    front((0, 2.16, -0.1), 0.15, (1.0, 0.8, 1.0))  # the hair drawn up into the tie
    pts = [(0.0, 2.2, -0.12), (0.0, 2.3, -0.2), (0.1, 2.35, -0.3), (0.24, 2.28, -0.42), (0.34, 2.08, -0.47),
           (0.41, 1.84, -0.46), (0.45, 1.6, -0.42), (0.46, 1.4, -0.38)]
    low_ponytail_tail(HB, pts, 0.14, 0.07, tie=0.1)


def afro():
    """Afro: a big round mass of small tight curls, wider and taller than the head; it rises from a high, arched
    hairline and wraps the sides down to the ears and round the back. A smooth core under a scatter of curls, so
    the outline is bumpy, not a smooth dome."""
    C, R = (0, 1.95, -0.04), (0.565, 0.5, 0.52)
    back(C, 0.5, (1.0, 0.9, 0.93))  # a smooth core behind the head, so no gap shows between the curls
    beads_f, beads_b = [], []
    for i, (p, g) in enumerate(_on_skin(1.45, 0.07)):  # the dense layer: fills the core's surface
        d = _ell_depth(p, g, C, R)
        if d is None or d < 0.02:
            continue
        yh = 1.72 + 0.32 * max(g.z, 0.0) ** 1.2  # arched hairline: high on the forehead, down to the ears at the sides
        m = _step(yh, yh + 0.2, p.y) if g.z > -0.15 else 1.0
        d *= m * _step(0.0, 0.07, d)
        if d < 0.012:
            continue
        j = (i * 2654435761 % 1000) / 1000.0
        rb = 0.085 + 0.02 * j
        c = p + g * (d - rb)
        (beads_f if c.z > -0.3 else beads_b).append((tuple(c), rb))
    for i, (p, g) in enumerate(_on_skin(1.5, 0.082)):  # the curls: round bumps standing out of that surface
        d = _ell_depth(p, g, C, R)
        if d is None or d < 0.05:
            continue
        yh = 1.72 + 0.32 * max(g.z, 0.0) ** 1.2
        m = _step(yh + 0.06, yh + 0.26, p.y) if g.z > -0.15 else 1.0
        if m < 0.1:
            continue
        j = (i * 40503 % 1000) / 1000.0
        rc = (0.052 + 0.026 * j) * m
        c = p + g * (d - 0.015 * (1 - m))
        (beads_f if c.z > -0.3 else beads_b).append((tuple(c), rc))
    cloud(HF, beads_f)
    cloud(HB, beads_b)


HF = ("hair_front", "head", "R")
HB = ("hair_back", "head", "R")


# --- crop/crew_cut/pixie/buzz begin
def buzz():
    """Buzz: the thinnest even layer on the skull, a clean high hairline, the sides faded back to the skin above the
    ears; no fringe, no lip."""

    def thick(ny, p):
        return 0.02 + 0.022 * ny

    def hairline(p, th):
        return crop_tab([(0.0, 1.99), (0.5, 1.98), (0.9, 1.9), (1.2, 1.82), (1.5, 1.8), (2.0, 1.66), (3.2, 1.55)], th)

    crop_cover(thick, hairline, 0.04)
# --- crop/crew_cut/pixie/buzz end


def side_part():
    """Short side part: a clear furrow from the hairline over the crown at x 0.14; the long side combed across and
    down to the far temple (hairline sloping from the part), the short side thinner; sides tight to the ear tops."""
    xp = 0.14
    tab = ((-0.5, 1.62), (-0.4, 1.72), (-0.28, 1.80), (-0.14, 1.90), (0.0, 1.96), (xp, 2.0), (0.28, 1.93), (0.4, 1.78), (0.5, 1.64))

    def inside(p, g):
        e, m = bob_edge(tab, p.x)
        return (p.y - e) / (1 + m * m) ** 0.5

    def thick(p, g):
        ny = max(g.y, 0.0) ** 1.2
        if p.x < xp:  # combed across: fullest at the part, thinning to the temple
            t = (0.055 + 0.085 * ny) * (1.0 + 0.15 * _step(-0.3, xp, p.x))
        else:
            t = 0.045 + 0.06 * ny
        return t * _step(0.025, 0.07, abs(p.x - xp))

    bob_field(inside, lambda p, g: 0.06, w=0.03)
    bob_field(inside, thick)


def quiff():
    """Quiff: short tight sides, the front lifted off the forehead into one wave that leans forward and sweeps to the
    side, its height falling away quickly towards the crown."""
    cap(0.46, 1.8, 0.68)
    quiff_hair(
        [(0, 1.96), (30, 1.94), (55, 1.86), (80, 1.76), (110, 1.68), (180, 1.6)],
        0.035,
        [([(-0.3, 1.97, 0.38), (-0.04, 2.02, 0.42), (0.24, 2.04, 0.3), (0.3, 2.06, 0.08)], [0.14, 0.3, 0.26, 0.08], [0.15, 0.17, 0.16, 0.12], 1.6)],
        side=0.35,
        up=0.15,
    )




def pompadour():
    """Pompadour: one tall roll the width of the forehead, leaning forward over the hairline and combed straight back
    from it in a falling ridge; sides short and slick."""
    cap(0.46, 1.8, 0.68)
    quiff_hair(
        [(0, 1.98), (25, 1.97), (45, 1.9), (65, 1.82), (85, 1.74), (110, 1.68), (180, 1.6)],
        0.03,
        [
            ([(-0.36, 1.96, 0.32), (-0.16, 2.02, 0.4), (0.16, 2.02, 0.4), (0.36, 1.96, 0.32)], [0.09, 0.2, 0.2, 0.09], [0.17, 0.2, 0.2, 0.17], 1.6),
            ([(0, 2.1, 0.22), (0, 2.13, -0.08), (0, 2.03, -0.32)], [0.09, 0.06, 0.02], [0.36, 0.38, 0.34], 1.1),
        ],
        side=0.3,
        up=0.2,
    )




def slick_back():
    """Slicked back: smooth and flat, combed straight back off a high hairline; tight sides, no fringe."""
    import math

    cap(0.46, 1.8, 0.68)
    quiff_hair(
        [(0, 1.99), (28, 1.99), (45, 1.9), (65, 1.8), (90, 1.72), (180, 1.6)],
        0.04,
        [([(0, 2.0, 0.3), (0, 2.12, 0.0), (0, 1.98, -0.3)], [0.03, 0.06, 0.04], [0.35, 0.4, 0.35], 1.5)],
        groove=lambda p: 0.012 * math.cos(math.atan2(p.x, p.z + 0.7) * 14),
        R=0.045,
    )


def mohawk():
    """Mohawk: a tall fin of hair from the forehead to the nape, tufted along the top; the sides are shaved, a thin
    stubble hugging the fin, so the crest stands alone and reads from the front as a bold strip down the middle."""
    cap(0.47, 1.8, 0.66)  # nape stubble: hidden behind the head from the front
    mohawk_stubble()
    mohawk_ridge(top=0.3, w=0.13)


def undercut():
    """Undercut: bare skin at the sides and back up to a high line, a long top swept over to one side that overhangs
    that line, so a step and a strip of skin show all round."""
    cap(0.3, 1.98, 0.5)
    quiff_hair(
        [(0, 1.95), (30, 1.98), (55, 2.0), (85, 2.0), (110, 1.97), (180, 1.84)],
        0.06,
        [([(-0.3, 1.97, 0.3), (-0.02, 2.08, 0.22), (0.3, 2.0, 0.0)], [0.07, 0.12, 0.07], [0.2, 0.26, 0.2], 1.1)],
        side=0.9,
        skew=0.35,
        ease=0.015,
        up=0.25,
        low=([(0, 1.93), (50, 1.87), (85, 1.72), (180, 1.56)], 0.008),
    )


# --- quiff block end ---


def curly_top():
    """Curly top fade: sides and nape clipped to a soft stubble, a mop of tight round curls over the whole top that
    grow out of the skin along a wavy hairline (each curl starts buried and rises to full size), so there is no lip."""
    from math import sin

    cap(0.46, 1.84, 0.66)

    def wave(p):
        return 0.03 * sin(p.x * 29 + p.z * 11) + 0.015 * sin(p.x * 61 - p.z * 17)

    def stubble(p, g):  # the faded sides: a thin soft layer from the ears up, easing into the skin
        yh = 1.62 + 0.2 * max(g.z, 0.0) + 0.5 * wave(p)
        return (0.028 + 0.03 * max(g.y, 0.0)) * _step(yh, yh + 0.12, p.y)

    _beads_on_skin(HF, stubble, ymin=1.5, R=0.05)
    beads_f, beads_b = [], []
    for i, (p, g) in enumerate(_on_skin(1.6, 0.098)):
        yh = 1.78 + 0.2 * g.z + wave(p)  # wavy hairline, not a straight edge
        s = _step(0.0, 1.0, (p.y - yh) / 0.12)  # 0 at the hairline, 1 from 0.12 above it
        if s < 0.03:
            continue
        j = (i * 2654435761 % 1000) / 1000.0
        up = _step(0.1, 0.75, g.y)  # curls shrink down the sides, so they never flare past the head's width
        rb = (0.03 + 0.075 * s * up) * (0.85 + 0.3 * j)
        c = p + g * (rb * (1.5 * s**0.8 - 1.0))  # buried at the hairline, standing half out from 0.2 above it
        (beads_f if c.z > -0.1 else beads_b).append((tuple(c), rb))
        if s > 0.6 and up > 0.7 and j < 0.35:  # a curl stacked on the top ones: a lumpy outline instead of a smooth dome
            c2 = p + g * (1.4 * rb)
            (beads_f if c2.z > -0.1 else beads_b).append((tuple(c2), 0.8 * rb))
    cloud(HF, beads_f)
    cloud(HB, beads_b)


def man_bun():
    """Man bun: hair pulled back flat with short tapered sides, one big round bun high on the back of the crown,
    standing clear above the head from the front."""
    cap(0.47, 1.8, 0.72)  # top 2.14, behind the head
    man_bun_cap(fy=1.84, ty=1.75, sy=1.62, side=0.038)
    man_bun_bun((0, 2.22, -0.32), (0.22, 0.19, 0.22), (0, 2.0, -0.2), 0.17, 0.16)


def top_knot():
    """Top knot: all the hair gathered up to a tie on the very top of the head; a tall knot with a pinched base
    stands up from it."""
    cap(0.5, 1.84, 0.9)
    man_bun_cap(fy=1.85, ty=1.73, sy=1.62)
    spike(HF, (0, 2.0, 0.0), (0, 2.26, 0.0), 0.15, 0.11, 6)  # narrows to the tie
    c = (0, 2.43, 0.0)
    front(c, 1.0, (0.17, 0.16, 0.17))
    man_bun_coil(c, (0.16, 0.15, 0.16), 1, turns=2.25)


def low_ponytail():
    """Low ponytail: smooth centre-parted hair swept back over the ears into a tie low at the side of the nape; the
    tail hangs from the tie over the front of the shoulder."""
    back((0, 1.76, -0.04), 0.47, (1.1, 0.95, 1.05))
    low_ponytail_cap(part=0.0)
    side_patch(D=0.04, y_lo=1.58, y_hi=2.0)
    chain(HB, (0.4, 1.86, -0.06), (0.44, 1.6, -0.1), 0.08, 5)  # the swept lock behind the ear, down to the tie
    pts = [(0.4, 1.7, -0.1), (0.46, 1.54, -0.05), (0.42, 1.36, 0.05), (0.35, 1.22, 0.13), (0.3, 1.08, 0.17),
           (0.28, 0.98, 0.18)]
    low_ponytail_tail(HF, pts, 0.1, 0.07, tie=0.17, end=1.2, ti=1.5)


def pigtails():
    """Pigtails: smooth centre-parted hair, two tails each gathered and tied at the ear and tucked in against the head."""
    back((0, 1.76, -0.04), 0.47, (1.1, 0.95, 1.05))
    low_ponytail_cap(part=0.0)
    side_patch(D=0.04, y_lo=1.6, y_hi=2.0)
    for s in (-1, 1):
        pts = [(0.4 * s, 1.84, -0.04), (0.47 * s, 1.72, -0.05), (0.47 * s, 1.58, -0.06), (0.43 * s, 1.42, -0.06),
               (0.39 * s, 1.28, -0.05)]
        low_ponytail_tail(HB, pts, 0.1, 0.075, tie=0.14, end=1.25, ti=1.5)


def two_braids():
    """Two braids: smooth centre-parted hair swept back behind the ears; each braid grows out of the hair over the ear
    and hangs down, one over the shoulder, one behind it (the other arm waves)."""
    back((0, 1.76, -0.04), 0.47, (1.1, 0.95, 1.05))
    low_ponytail_cap(part=0.0)
    side_patch(D=0.04, y_lo=1.58, y_hi=2.0)
    pts = [(0.38, 1.8, -0.08), (0.44, 1.66, -0.06), (0.47, 1.5, -0.02), (0.42, 1.36, 0.05), (0.35, 1.22, 0.13),
           (0.3, 1.08, 0.17), (0.28, 0.98, 0.18)]
    low_ponytail_tail(HF, pts, 0.105, 0.07, plait=True, end=1.3)
    pts = [(-0.38, 1.8, -0.08), (-0.44, 1.66, -0.08), (-0.48, 1.5, -0.08), (-0.47, 1.34, -0.08), (-0.45, 1.2, -0.1)]
    low_ponytail_tail(HB, pts, 0.105, 0.08, plait=True, end=1.2)


def single_braid():
    """Single braid: smooth side-parted hair swept back behind the ear; the braid grows out of the hair there and hangs
    over the shoulder to the chest, tied at the end."""
    back((0, 1.76, -0.04), 0.47, (1.1, 0.95, 1.05))
    low_ponytail_cap(part=-0.14, tilt=-0.15)
    side_patch(D=0.04, y_lo=1.58, y_hi=2.0)
    chain(HB, (0.4, 1.86, -0.06), (0.44, 1.6, -0.1), 0.08, 5)
    pts = [(0.4, 1.72, -0.1), (0.46, 1.58, -0.06), (0.47, 1.46, -0.02), (0.42, 1.34, 0.05), (0.35, 1.2, 0.13),
           (0.3, 1.06, 0.17), (0.28, 0.96, 0.18)]
    low_ponytail_tail(HF, pts, 0.115, 0.075, plait=True, end=1.3)


def space_buns():
    """Space buns: all the hair pulled up tight off the face and sides into two coiled buns high on the crown."""
    cap(0.49, 1.85, 0.84)
    man_bun_cap(fy=1.84, ty=1.73, sy=1.62, top=0.12)
    for s in (-1, 1):
        man_bun_bun((0.28 * s, 2.3, 0.02), (0.18, 0.16, 0.18), (0.18 * s, 2.0, 0.0), 0.15, 0.15, s)


def curly_bob():
    """Curly bob: a round chin-length mass of tight curls that hug the head, curly fringe above the brows; the ends
    tuck under at the jaw."""
    cap(0.48, 1.72, 0.9)
    back((0, 1.52, -0.12), 0.4, (1.12, 0.78, 0.9))
    skull((0, 2.12, 0.0), (0.5, 0.32, 0.5), lim=lambda ny: 0.04)
    side_patch()
    long_straight_curls(0.085, 1.98, 1.42, 0.05, 1.5, 0.06)


def long_wavy():
    """Long wavy: middle part, side-swept curtains framing the face, one sheet down the back whose edges ripple in S waves."""
    cap()
    shell(0.47, 2.06, 0.56)
    for s in (-1, 1):
        skull((0.3 * s, 2.04, 0.02), (0.34, 0.34, 0.5), lim=lambda ny: 0.06)
        pts = [(0.37, 1.86, 0.1), (0.41, 1.76, 0.06), (0.37, 1.64, 0.03), (0.41, 1.52, 0.0)]
        for a, b in zip(pts, pts[1:]):
            chain(HF, (a[0] * s, a[1], a[2]), (b[0] * s, b[1], b[2]), 0.11)
        pts = [(0.41, 1.52, -0.04), (0.37, 1.4, -0.1), (0.43, 1.28, -0.12), (0.35, 1.16, -0.14), (0.4, 1.04, -0.15), (0.34, 0.96, -0.16)]
        for a, b in zip(pts, pts[1:]):
            chain(HB, (a[0] * s, a[1], a[2]), (b[0] * s, b[1], b[2]), 0.13)
    back((0, 1.4, -0.22), 0.36, (1.0, 1.2, 0.55))


def long_curly():
    """Long curly: a big mane of curls of mixed size scattered at random (no rows), fringe above the brows, one uneven
    mass to mid back, wider than the shoulders."""
    from random import Random

    rnd = Random(11)
    cap(0.5, 1.8, 0.95)
    skull((0, 2.12, 0.0), (0.5, 0.32, 0.5), lim=lambda ny: 0.04)
    side_patch()
    long_straight_curls(0.095, 1.99, 1.5, 0.05, 1.15)
    back((0, 1.66, -0.16), 0.48, (1.08, 0.62, 0.85))
    back((0, 1.32, -0.24), 0.44, (1.2, 1.05, 0.55))
    curls = []
    for _ in range(170):
        y = rnd.uniform(0.98, 1.66)
        w = 0.5 + 0.12 * min((1.66 - y) / 0.4, 1.0)
        if y < 0.98 + 0.14 * rnd.random():
            continue
        curls.append(((rnd.uniform(-w, w), y, rnd.uniform(-0.3, -0.08)), rnd.uniform(0.07, 0.14)))
    cloud(HB, curls)




def dreadlocks():
    """Dreadlocks: knobbly ropes with gaps between them: a few swept off the crown to frame the face, the rest hang
    behind the neck and shoulders, each ending at its own length with a blunt tip."""
    import math

    cap(0.47, 1.8, 0.9)
    skull((0, 2.1, 0.0), (0.5, 0.3, 0.5), lim=lambda ny: 0.04 + 0.1 * max(ny, 0.0) ** 1.5)
    side_patch()
    kid = AGE == "child"

    def lock(key, pts, r0, r1, ph=0.0):
        beads = []
        L = sum((Vector(a) - Vector(b)).length for a, b in zip(pts, pts[1:]))
        for p, t in _path(pts, 0.3 * r1):
            beads.append((tuple(p), (r0 + (r1 - r0) * t) * (1 + 0.07 * math.sin(ph + t * L / 0.09))))
        cloud(key, beads)

    for s in (-1, 1):
        # off the forehead to the sides along the skull, then down beside the face
        lock(HF, [(0.06 * s, 2.19, 0.18), (0.26 * s, 2.05, 0.31), (0.43 * s, 1.8, 0.2), (0.45 * s, 1.56, 0.14), (0.45 * s, 1.4 if kid else 1.3, 0.12)], 0.07, 0.06)
        lock(HF, [(0.16 * s, 2.21, 0.02), (0.38 * s, 2.04, 0.16), (0.52 * s, 1.78, 0.04), (0.53 * s, 1.52, 0.0), (0.52 * s, 1.44 if kid else 1.34, -0.02)], 0.07, 0.06, 1.0)
        lock(HF, [(0.3 * s, 2.16, -0.12), (0.5 * s, 1.9, -0.1), (0.5 * s, 1.6, -0.08)], 0.07, 0.06, 2.0)
        # over the crown from the front hairline to the back
        lock(HF, [(0.12 * s, 2.0, 0.36), (0.13 * s, 2.2, 0.12), (0.16 * s, 2.2, -0.2), (0.22 * s, 2.0, -0.4)], 0.07, 0.065, 3.0)
    for i, x in enumerate((-0.44, -0.29, -0.15, 0.0, 0.15, 0.29, 0.44)):
        end = (1.36 if kid else 1.04) + (0.0, 0.06, -0.04, 0.03, -0.05, 0.05, -0.02)[i]
        lock(HB, [(0.8 * x, 2.1, -0.2), (x, 1.84, -0.4 + 0.5 * x * x), (0.97 * x, 1.5, -0.33), (0.95 * x, end, -0.3)], 0.07, 0.058, i)


def cornrows():
    """Cornrows: seven slim plaited rows lying tight on the skull from the hairline over the crown to the nape, each
    following the head's own surface, with a skin-thin base between them so the grooves show."""
    from math import cos, radians, sin, sqrt

    cap(0.44, 1.76, 0.86)
    crop_cover(lambda ny, p: 0.012, lambda p, th: 1.9 - 0.2 * min(th, 1.57), w=0.02)
    hf, hb = [], []
    for x in (-0.36, -0.24, -0.12, 0.0, 0.12, 0.24, 0.36):
        k = sqrt(1 - (x / HEAD_R[0]) ** 2)
        for i in range(int((215 - 26 - 40 * abs(x)) / 3.2)):
            t = 26 + 40 * abs(x) + 3.2 * i  # the rows start at a hairline that follows the forehead to the temples
            a = radians(t)
            y, z = HEAD_C[1] + HEAD_R[1] * k * sin(a), HEAD_R[2] * k * cos(a)
            r = 0.05 if (i // 3) % 2 else 0.038  # the plait: fat and thin stretches in turn
            (hf if t < 120 else hb).append(((x, y + 0.012, z), r))
    cloud(HF, hf)
    cloud(HB, hb)




def mullet():
    """Mullet: short textured top with a broken fringe, tight sides; the long back flares out past the neck on both
    sides and reaches the shoulders, wide enough that it shows from the front."""
    cap(0.45, 1.78, 0.75)
    crop_cover(
        lambda ny, p: 0.035 + 0.05 * ny,
        lambda p, th: 1.95 + crop_tips(p.x, 0.17, 0.05) * (1.0 - _step(0.7, 1.1, th)) - 0.08 * _step(0.7, 1.57, th),
        lumps=(((-0.22, 2.1, 0.2), 0.14, 0.05), ((0.05, 2.14, 0.2), 0.14, 0.06), ((0.24, 2.08, 0.12), 0.14, 0.05), ((0.0, 2.1, -0.15), 0.16, 0.05)),
    )
    for s in (-1, 1):
        chain(HB, (0.2 * s, 1.36, -0.22), (0.34 * s, 1.12, -0.18), 0.11)
        chain(HB, (0.34 * s, 1.12, -0.18), (0.38 * s, 1.02, -0.16), 0.07)
        chain(HB, (0.12 * s, 1.4, -0.28), (0.2 * s, 1.0, -0.24), 0.12)
    chain(HB, (0, 1.74, -0.36), (0, 1.02, -0.3), 0.24)




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
    """Bowl cut: a round helmet of hair fitted to the skull, cut in one level line round the head just above the
    brows and ears; the fringe length varies a little, the edge is rounded, nothing hangs or flares."""
    from math import sin

    def inside(p, g):
        az = bob_az(g)
        wob = 0.011 * sin(29 * p.x + 0.7) + 0.009 * sin(67 * p.x + 2.1)  # uneven fringe length
        hem = 1.84 - 0.07 * _step(0.9, 1.5, az) + wob * (1 - _step(0.7, 1.3, az))
        return p.y - hem

    bob_field(inside, lambda p, g: 0.065 + 0.085 * max(g.y, 0.0) ** 1.2, w=0.04, ymin=1.55)


def spiky():
    """Spiky: a full head of hair on a natural hairline with a mop of chunky spikes of mixed length, standing up
    and out, the front ones forward over the brow; the spikes are fat enough to merge into one mass, so no smooth
    dome or rim shows between them."""
    from math import cos, radians, sin

    sf, sb = [], []
    cap(0.47, 1.9, 0.7)  # short at the back: the lower edge sits at the ear tops, not the jaw

    def depth(p, g):  # a thin layer on the skin: hairline at the brow, down to the ears at the sides, thicker on top
        yh = 1.64 + 0.26 * max(g.z, 0.0)
        return (0.035 + 0.06 * max(g.y, 0.0)) * _step(yh, yh + 0.12, p.y)

    _beads_on_skin(HF, depth, ymin=1.6, R=0.06)
    # (azimuth from the front, elevation above the horizon, length, base radius, forward lean); bases sit on the crown
    locks = [(0, 88, 0.34, 0.13, 0.0)]
    for k, th in enumerate((-150, -90, -30, 30, 90, 150)):  # upper ring
        locks.append((th, 66, 0.26 + 0.05 * (k % 3) / 2, 0.125, 0.1 if th == 30 else 0.0))
    for k in range(10):  # middle ring
        th = -170 + 36 * k
        locks.append((th, 42, 0.2 + 0.05 * ((k * 3) % 4) / 3, 0.115, 0.25 if abs(th) < 40 else 0.0))
    for th in (-75, -45, -15, 15, 45, 75):  # fringe over the brow
        locks.append((th, 23, 0.14 + 0.03 * ((th // 15) % 2), 0.09, 0.55))
    for th, el, ln, r, fwd in locks:
        t, e = radians(th), radians(el)
        out = Vector((sin(t) * cos(e), sin(e) * 0.9, cos(t) * cos(e)))
        base = Vector((0, 1.72, 0)) + Vector((out.x * 0.5, out.y * 0.5, out.z * 0.49))
        d = (Vector((out.x, 0, out.z)) * (0.5 if el < 80 else 0.0) + Vector((0, 1.0 if el > 30 else 0.55, 0))
             + Vector((0, 0, fwd))).normalized()
        mohawk_spike(sf if base.z > -0.2 else sb, base - d * 0.08, base + d * ln, r, 0.03)
    cloud(HF, sf)
    cloud(HB, sb)


def curtains():
    """Curtains: 90s centre part, a thin furrow from the hairline over the crown; the two halves sweep down and out
    to the temples (a V of forehead between them) and fall over the ears; tight to the head."""
    tab = ((0.0, 2.09), (0.12, 2.04), (0.25, 1.88), (0.36, 1.73), (0.46, 1.62))

    def inside(p, g):
        e, m = bob_edge(tab, abs(p.x))
        return (p.y - e) / (1 + m * m) ** 0.5

    bob_field(inside, lambda p, g: 0.06, w=0.03)  # the floor of the part
    bob_field(
        inside,
        lambda p, g: (0.045 + 0.075 * max(g.y, 0.0) ** 1.2) * _step(0.025, 0.07, abs(p.x)),
    )


def half_up():
    """Half up: the top section combed back and tied in a small knot on the crown, the rest hangs long behind
    the shoulders at the head's width."""
    man_bun_cap(fy=1.85, ty=1.69, sy=1.6, by=1.52, top=0.09, side=0.04)
    man_bun_bun((0, 2.27, -0.12), (0.15, 0.14, 0.15), (0, 2.0, -0.08), 0.14, 0.13)
    cap(0.47, 1.8, 0.75)
    man_bun_curtain()


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
    side_patch(D=0.036, y_lo=1.64)  # short sideburn: covers the temple down to the ear top, fading into the skin

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


# --- low_ponytail helpers ---
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


def pacifier():
    """Baby's dummy, over the mouth: shield and teat in c1 (mask R), a ring handle in c2 (mask G)."""
    import math

    sphere(("pacifier", "head", "R"), (0, 1.52, 0.47), 0.1, (1.2, 0.85, 0.3))
    sphere(("pacifier", "head", "R"), (0, 1.52, 0.51), 0.04)
    for i in range(16):
        t = 2 * math.pi * i / 16
        sphere(("pacifier", "head", "G"), (0.05 * math.cos(t), 1.5 + 0.05 * math.sin(t), 0.54), 0.016, segs=12)


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
    pacifier()
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
