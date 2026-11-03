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


def T(p):
    """Age transform of a modelled point -> (point, radius factor, per-axis stretch); copied from build_clay_girl."""
    x, y, z = p
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


def torso(layer, grow, mask="R"):
    # slim: widest at the ribs, narrowing to the waist (director: the one-ball belly read as fat)
    sphere((layer, "chest", mask), (0, 1.1, 0), 0.29 + grow, (1.0, 0.8, 0.62))
    sphere((layer, "chest", mask), (0, 1.27, 0), 0.22 + grow, (1.05, 0.42, 0.7))
    socket(layer, "chest", "waist", grow=grow, mask=mask)
    if SEX == "f" and AGE in ("teen", "adult"):  # chest beads (PEOPLE.md ง2, director: women need breasts)
        # undo the age stretch (tall bodies stretched round beads into vertical footballs): k/SY, k/SX
        k = (SX + SY) / 2
        for s in (-1, 1):
            if AGE == "adult":  # teardrop: a soft upper slope into a fuller, slightly lower round
                sphere((layer, "chest", mask), (0.11 * s, 1.18, 0.06), 0.07 + grow, (k / SX, 0.8 * k / SY, 0.8 * k / SX))
                sphere((layer, "chest", mask), (0.12 * s, 1.12, 0.1), 0.095 + grow, (1.05 * k / SX, 0.92 * k / SY, k / SX))
            else:  # teen: small and round
                sphere((layer, "chest", mask), (0.12 * s, 1.13, 0.1), 0.095 + grow, (k / SX, 0.95 * k / SY, 0.85 * k / SX))
    if layer != "body":  # tops hang straight past the hips, wider than the trousers (director)
        for y in (1.05, 1.02, 0.99, 0.96, 0.93, 0.9, 0.87, 0.84):  # straight sides from the ribs to the hem: no round belly
            sphere((layer, "chest", mask), (0, y, 0), 0.3 + grow, (1.0, 0.35, 0.62))
        sphere((layer, "chest", mask), (0, 0.8, 0), 0.24 + grow, (1.3, 0.28, 0.74))
    socket(layer, "chest", "neck", grow=grow, mask=mask)


def pelvis(layer, grow):
    socket(layer, "pelvis", "waist", grow=grow)
    sphere((layer, "pelvis", "R"), (0, 0.78, 0), 0.24 + grow, (1.05, 0.55, 0.75))
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
    chain(("body", "head", "R"), (0, 1.3, 0), (0, 1.46, 0), 0.09, 3)
    socket("body", "head", "neck")
    for s, side in ((1, "l"), (-1, "r")):
        bone("body", "upper_arm_" + side, "shoulder", "elbow", s, 0.095)
        bone("body", "forearm_" + side, "elbow", "wrist", s, 0.085)
        sphere(("body", "hand_" + side, "R"), j("hand_c", s), 0.1)
        socket("body", "hand_" + side, "wrist", s)
        sphere(("body", "foot_" + side, "R"), j("toe", s), 0.13, (0.85, 0.6, 1.25))
        socket("body", "foot_" + side, "ankle", s)
        # face beads ride on the head piece
        sphere(("face", "head", "eyes"), (0.14 * s, 1.64, 0.43), 0.05, (0.8, 1.15, 0.5), 16)
        sphere(("face", "head", "blush"), (0.25 * s, 1.55, 0.38), 0.06, (1, 0.55, 0.35), 16)
    sphere(("face", "head", "mouth"), (0, 1.52, 0.44), 0.04, (1.2, 0.5, 0.4), 16)


def tee():
    torso("tee", 0.025)
    ring(("tee", "chest", "G"), (0, 1.36, 0.0), 0.12, 0.1, 0.035)
    for s, side in ((1, "l"), (-1, "r")):
        mid = Vector(j("shoulder", s)).lerp(Vector(j("elbow", s)), 0.65)
        chain(("tee", "upper_arm_" + side, "R"), j("shoulder", s), tuple(mid), 0.125, 4)
        socket("tee", "upper_arm_" + side, "shoulder", s, 0.03)


def sweater():
    torso("sweater", 0.035)
    ring(("sweater", "chest", "G"), (0, 1.36, 0.0), 0.13, 0.11, 0.04)
    arms("sweater", 0.04)


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


def shell(r=0.47, y=2.0, sy=0.42):
    """Crown shell (PEOPLE.md: no scalp between fringe lumps); the head occluder trims it to the top."""
    sphere(("hair_front", "head", "R"), (0, y, 0.02), r, (1.08, sy, 1.0))


def front(at, r, scale=(1, 1, 1)):
    sphere(("hair_front", "head", "R"), at, r, scale)


def back(at, r, scale=(1, 1, 1)):
    sphere(("hair_back", "head", "R"), at, r, scale)


# Cuts (director 2026-11-03: 34, any cut on anyone). Rules that keep them clean in motion:
# - every piece hangs off the head bone, so whatever covers the scalp at rest covers it in every frame;
# - hair_front stays above the shoulder tops (y 1.36) outside |x| 0.2, so it never covers an arm;
#   anything longer goes on hair_back, which draws behind the body.
def wisp():
    """Baby hair: a wisp on top (build_clay_girl.py --age baby)."""
    front((0.05, 2.1, 0.12), 0.14, (1.3, 0.5, 1.0))


def bob():
    # cap over the back and top (drawn behind the head), fringe and side curtains in front
    cap()
    back((0, 1.55, -0.3), 0.3, (1.1, 1.0, 0.7))
    shell()
    front((-0.12, 2.0, 0.2), 0.24, (1.3, 0.55, 1.0))
    front((0.16, 1.96, 0.26), 0.2, (1.1, 0.5, 0.8))
    for s in (-1, 1):
        # in front down to just above the shoulder; the tips fall behind it, clear of a raised arm
        chain(("hair_front", "head", "R"), (0.33 * s, 1.78, -0.05), (0.35 * s, 1.62, -0.04), 0.17, 4)
        chain(("hair_back", "head", "R"), (0.35 * s, 1.6, -0.04), (0.37 * s, 1.36, -0.02), 0.17, 6)
        back((0.42 * s, 1.3, -0.02), 0.11)


def crop():
    """Short crop (build_clay_girl.py --sex boy): cap close to the skull, small fringe."""
    cap(0.49, 1.86, 0.82)
    shell(0.45, 2.0, 0.36)
    front((0.05, 2.02, 0.22), 0.22, (1.35, 0.45, 0.9))


def crew_cut():
    """Crew cut: shorter than the crop, a low flat ridge at the front, no fringe."""
    cap(0.49, 1.87, 0.8)
    shell(0.46, 2.01, 0.36)
    front((0, 2.05, 0.2), 0.2, (1.6, 0.35, 0.8))


def pixie():
    """Pixie: short all over, a side-swept fringe, small wisps in front of the ears."""
    cap(0.5, 1.84, 0.86)
    shell()
    chain(("hair_front", "head", "R"), (0.22, 2.01, 0.24), (-0.22, 1.88, 0.31), 0.14, 6)
    for s in (-1, 1):
        front((0.44 * s, 1.62, 0.02), 0.1, (0.8, 1.4, 0.8))


def long_straight():
    """Long straight, middle part: side curtains stop above the shoulders in front; the length falls behind."""
    cap()
    shell()
    for s in (-1, 1):
        front((0.15 * s, 1.98, 0.24), 0.2, (1.2, 0.5, 0.8))
        chain(("hair_front", "head", "R"), (0.34 * s, 1.84, -0.03), (0.36 * s, 1.62, -0.02), 0.16, 4)
        chain(("hair_back", "head", "R"), (0.38 * s, 1.7, -0.12), (0.34 * s, 0.98, -0.16), 0.16, 10)
    chain(("hair_back", "head", "R"), (0, 1.6, -0.3), (0, 0.98, -0.3), 0.3, 8)


def high_ponytail():
    """High ponytail: hair pulled back off the forehead, tail swung out to one side behind the head."""
    cap(0.5, 1.84, 0.9)
    shell(0.47, 1.98, 0.48)
    back((0.04, 2.05, -0.38), 0.1)
    chain(("hair_back", "head", "R"), (0.1, 2.02, -0.45), (0.44, 1.46, -0.5), 0.12, 8)
    back((0.46, 1.4, -0.5), 0.09)


def afro():
    """Afro: a big round mass, wider than the head; its lower edge sits behind the shoulders."""
    back((0, 1.86, -0.05), 0.64, (1.08, 0.95, 0.9))
    shell(0.58, 2.05, 0.45)
    front((0, 2.0, 0.25), 0.3, (1.5, 0.45, 0.8))


HAIRS = {f.__name__: f for f in (wisp, bob, crop, crew_cut, pixie, long_straight, high_ponytail, afro)}


# Seamless joints (director 2026-11-03): two pieces meeting at a joint are also remeshed together into a
# proxy "proxy|<layer>|<a>|<b>". render.py colours both pieces near the joint from the proxy's front render,
# so the overlap shows the fused surface (no rim at rest); silhouettes stay the pieces' own.
JOINTS = [("pelvis", "chest", "waist", 1), ("chest", "head", "neck", 1)] + [
    pair for s, d in ((1, "_l"), (-1, "_r")) for pair in (
        ("chest", "upper_arm" + d, "shoulder", s), ("upper_arm" + d, "forearm" + d, "elbow", s),
        ("forearm" + d, "hand" + d, "wrist", s), ("pelvis", "thigh" + d, "hip", s),
        ("thigh" + d, "shin" + d, "knee", s), ("shin" + d, "foot" + d, "ankle", s))]


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
            ob["r"] = JR[joint] * f


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
        if layer != "face":
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
