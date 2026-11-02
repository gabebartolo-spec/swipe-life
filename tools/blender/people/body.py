"""Modular people, vertical slice (docs/PEOPLE.md §10 step 1): child_f_skinny as 15 rigid clay pieces,
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
# approved age bands (build_clay_girl.py --age, clay_sets_front.png): the child is modelled, other ages
# rescale the body below the neck (sx width, sy height) and the head (h) about the neck
SX, SY, H = {"baby": (1.12, 0.55, 0.95), "child": (1, 1, 1), "teen": (0.95, 1.35, 0.9), "adult": (1, 1.5, 0.86)}[AGE]
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


def torso(layer, grow, mask="R"):
    sphere((layer, "chest", mask), (0, 1.02, 0), 0.35 + grow, (0.95, 0.95, 0.72))
    sphere((layer, "chest", mask), (0, 1.27, 0), 0.22 + grow, (1.05, 0.42, 0.75))


def body():
    torso("body", 0)
    sphere(("body", "pelvis", "R"), (0, 0.78, 0), 0.28, (1.1, 0.6, 0.85))
    for s in (-1, 1):
        sphere(("body", "pelvis", "R"), (0.15 * s, 0.72, 0), 0.12)
    sphere(("body", "head", "R"), J["head_c"], 0.47, (1.05, 0.95, 1.0))
    chain(("body", "head", "R"), (0, 1.3, 0), (0, 1.46, 0), 0.09, 3)
    for s, side in ((1, "l"), (-1, "r")):
        chain(("body", "upper_arm_" + side, "R"), j("shoulder", s), j("elbow", s), 0.095)
        chain(("body", "forearm_" + side, "R"), j("elbow", s), j("wrist", s), 0.09)
        sphere(("body", "hand_" + side, "R"), j("hand_c", s), 0.1)
        sphere(("body", "hand_" + side, "R"), j("wrist", s), 0.075)
        chain(("body", "thigh_" + side, "R"), j("hip", s), j("knee", s), 0.11)
        chain(("body", "shin_" + side, "R"), j("knee", s), j("ankle", s), 0.1)
        sphere(("body", "foot_" + side, "R"), j("toe", s), 0.13, (0.85, 0.6, 1.25))
        sphere(("body", "foot_" + side, "R"), j("ankle", s), 0.085)
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


def sweater():
    torso("sweater", 0.035)
    ring(("sweater", "chest", "G"), (0, 1.36, 0.0), 0.13, 0.11, 0.04)
    for s, side in ((1, "l"), (-1, "r")):
        chain(("sweater", "upper_arm_" + side, "R"), j("shoulder", s), j("elbow", s), 0.13)
        chain(("sweater", "forearm_" + side, "R"), j("elbow", s), j("wrist", s), 0.125)


def trousers():
    sphere(("trousers", "pelvis", "R"), (0, 0.78, 0), 0.31, (1.1, 0.6, 0.85))
    for s, side in ((1, "l"), (-1, "r")):
        sphere(("trousers", "pelvis", "R"), (0.15 * s, 0.72, 0), 0.145)
        chain(("trousers", "thigh_" + side, "R"), j("hip", s), j("knee", s), 0.14)
        chain(("trousers", "shin_" + side, "R"), j("knee", s), (0.17 * s, 0.2, 0), 0.13)


def hair():
    # bob: cap over the back and top (drawn behind the head), fringe and side curtains in front
    sphere(("hair_back", "head", "R"), (0, 1.82, -0.1), 0.5, (1.03, 0.92, 0.95))
    sphere(("hair_back", "head", "R"), (0, 1.55, -0.3), 0.3, (1.1, 1.0, 0.7))
    sphere(("hair_front", "head", "R"), (-0.12, 2.0, 0.2), 0.24, (1.3, 0.55, 1.0))
    sphere(("hair_front", "head", "R"), (0.16, 1.96, 0.26), 0.2, (1.1, 0.5, 0.8))
    for s in (-1, 1):
        chain(("hair_front", "head", "R"), (0.33 * s, 1.78, -0.05), (0.37 * s, 1.36, -0.02), 0.17, 8)
        sphere(("hair_front", "head", "R"), (0.42 * s, 1.3, -0.02), 0.11)


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
        if layer == "face":
            continue
        r = ob.modifiers.new("fuse", "REMESH")
        r.mode = "VOXEL"
        r.voxel_size = 0.012
        ob.modifiers.new("decimate", "DECIMATE").ratio = 0.25
        r = ob.modifiers.new("smooth", "CORRECTIVE_SMOOTH")
        r.iterations = 8
        r.use_only_smooth = True


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
tee()
sweater()
trousers()
hair()
fuse()
bake_ao()
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_vertex_color="ACTIVE", export_materials="NONE",
                          export_texcoords=False, export_extras=True)
print("EXPORTED", OUT, len([o for o in bpy.context.scene.objects]))
