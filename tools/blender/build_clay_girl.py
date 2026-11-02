"""Build the chibi clay girl (director's reference image 5) and export her for Godot.

Run headless:
  blender --background --factory-startup --python tools/blender/build_clay_girl.py -- <out.glb>

One fused piece per material colour (skin, sweater, jeans, socks, hair), so each colour
is voxel-remeshed into a single soft blob like pressed plasticine. Converted to mesh, AO baked into vertex
colours like the room. Godot axes: feet at origin, facing +Z, y up. Neutral standing pose;
the wave waits for a Mixamo clip.
"""

import math
import sys

import bpy
from mathutils import Vector

sys.path.append(__import__("os").path.dirname(__file__))
from build_clay_room import g2b, hexc  # noqa: E402  (shared colour/axis helpers)

OUT = sys.argv[sys.argv.index("--") + 1]
# --apose: arms out at ~45 degrees for Mixamo's auto-rigger; exports FBX instead of GLB.
APOSE = "--apose" in sys.argv
WRIST, HAND = ((0.78, 0.92, 0.02), (0.86, 0.84, 0.03)) if APOSE else ((0.45, 0.8, 0.02), (0.47, 0.68, 0.03))

PARTS = {
    "skin": "f2c9a5",
    "sweater": "e8d6bd",
    "jeans": "6f8fb5",
    "socks": "faf7f2",
    "hair": "6b4430",
    "eyes": "2b2024",
    "blush": "f0a0a0",
    "mouth": "8a3a3a",
}


# Face details are too small for metaballs (they fall under the threshold): plain beads.
BLOBS = ("skin", "sweater", "jeans", "socks", "hair")


def bead(name, at, radius, scale):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=g2b(*at), segments=16, ring_count=8)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (scale[0], scale[2], scale[1])
    ob["clay_color"] = PARTS[name]


def blob(parts, at, radius, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=g2b(*at), segments=32, ring_count=16)
    ob = bpy.context.object
    ob.scale = (scale[0], scale[2], scale[1])
    parts.append(ob)


def line(parts, a, b, radius, n):
    a, b = Vector(a), Vector(b)
    for i in range(n):
        blob(parts, a.lerp(b, i / (n - 1)), radius)


def build():
    m = {k: [] for k in BLOBS}
    for s in (-1, 1):
        # socks/feet, jeans legs, sweater sleeves, hands
        blob(m["socks"], (0.15 * s, 0.08, 0.05), 0.13, (0.85, 0.6, 1.25))
        line(m["jeans"], (0.15 * s, 0.2, 0), (0.14 * s, 0.7, 0), 0.14, 9)
        line(m["sweater"], (0.33 * s, 1.22, 0), (WRIST[0] * s, *WRIST[1:]), 0.12, 9)
        blob(m["skin"], (HAND[0] * s, *HAND[1:]), 0.1)
        # face details: eyes, blush
        bead("eyes", (0.14 * s, 1.64, 0.43), 0.05, (0.8, 1.15, 0.5))
        bead("blush", (0.25 * s, 1.55, 0.38), 0.06, (1, 0.55, 0.35))
        # hair: shoulder-length side curtains, slightly flicked out at the ends
        line(m["hair"], (0.33 * s, 1.78, -0.05), (0.37 * s, 1.36, -0.02), 0.17, 8)
        blob(m["hair"], (0.42 * s, 1.3, -0.02), 0.11)
    blob(m["jeans"], (0, 0.78, 0), 0.3, (1.15, 0.6, 0.85))
    blob(m["sweater"], (0, 1.02, 0), 0.38, (1.0, 0.95, 0.75))
    blob(m["sweater"], (0, 1.3, 0), 0.24, (1.1, 0.4, 0.8))
    blob(m["skin"], (0, 1.68, 0), 0.47, (1.05, 0.95, 1.0))
    blob(m["skin"], (0, 1.38, 0), 0.1)
    # hair cap over the back and top, side-swept fringe
    blob(m["hair"], (0, 1.82, -0.1), 0.5, (1.03, 0.92, 0.95))
    blob(m["hair"], (-0.12, 2.0, 0.2), 0.24, (1.3, 0.55, 1.0))
    blob(m["hair"], (0.16, 1.96, 0.26), 0.2, (1.1, 0.5, 0.8))
    blob(m["hair"], (0, 1.55, -0.3), 0.3, (1.1, 1.0, 0.7))
    bead("mouth", (0, 1.52, 0.44), 0.04, (1.2, 0.5, 0.4))
    return m


def to_meshes(m):
    """Fuse each colour's spheres into one clay piece: join, voxel remesh, smooth."""
    for name, parts in m.items():
        bpy.ops.object.select_all(action="DESELECT")
        for ob in parts:
            ob.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]
        bpy.ops.object.join()
        ob = bpy.context.object
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        ob.name = name
        ob["clay_color"] = PARTS[name]
        r = ob.modifiers.new("fuse", "REMESH")
        r.mode = "VOXEL"
        r.voxel_size = 0.012
        r = ob.modifiers.new("smooth", "CORRECTIVE_SMOOTH")
        r.iterations = 8
        r.use_only_smooth = True
        d = ob.modifiers.new("decimate", "DECIMATE")
        d.ratio = 0.25


def bake_ao():
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
    # floor so the feet get contact shading
    bpy.ops.mesh.primitive_plane_add(size=4)
    floor = bpy.context.object
    bpy.ops.object.select_all(action="DESELECT")
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    scene.render.bake.target = "VERTEX_COLORS"
    bpy.ops.object.bake(type="AO")
    bpy.data.objects.remove(floor)
    for ob in obs:
        base = hexc(ob["clay_color"])
        for d in ob.data.color_attributes["Col"].data:
            ao = 0.4 + 0.6 * d.color[0]
            d.color = (base[0] * ao, base[1] * ao, base[2] * ao, 1.0)
        ob.data.materials.clear()


bpy.ops.wm.read_factory_settings(use_empty=True)
to_meshes(build())
bake_ao()
if APOSE:
    bpy.ops.export_scene.fbx(filepath=OUT, colors_type="LINEAR")
else:
    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_vertex_color="ACTIVE", export_materials="NONE", export_texcoords=False
    )
print("EXPORTED", OUT, [(o.name, len(o.data.vertices)) for o in bpy.context.scene.objects])
