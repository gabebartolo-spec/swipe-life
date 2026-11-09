"""Lighten body.py's pieces into a mesh the game draws live in 3D.

Run headless:
  blender -b --factory-startup --python tools/blender/people/fig3d.py -- <pieces.glb> <out.glb> [ratio]

Objects become <layer>__<piece>__<mask>, vertices stay in body space. A body also writes <out>.json
with each piece's pivot and end joint and the ground height. Hair-only input keeps just the hair.
"""

import json
import sys

import bpy

ARGS = sys.argv[sys.argv.index("--") + 1 :]
SRC, OUT = ARGS[:2]
RATIO = float(ARGS[2]) if len(ARGS) > 2 else 0.12
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
scene = bpy.context.scene
obs = [o for o in scene.objects if o.type == "MESH"]
hair_only = any(o.name.startswith("hair_") for o in obs) and not any(o.name.startswith("tee|") for o in obs)
meta, ground = {}, 9.0
for o in obs:
    layer = o.name.split("|")[0]
    if layer in ("proxy", "wrinkles") or (hair_only and not layer.startswith("hair_")):
        bpy.data.objects.remove(o)
        continue
    parts = o.name.split("|")
    if "pivot" in o:
        meta[parts[1]] = {"pivot": list(o["pivot"]), "end": list(o["end"]) if "end" in o else None}
    ground = min([ground] + [(o.matrix_world @ v.co).z for v in o.data.vertices])
    if len(o.data.polygons) > 150:
        d = o.modifiers.new("d", "DECIMATE")
        d.ratio = RATIO
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier="d")
    o.name = "__".join(parts)
print("FACES", sum(len(o.data.polygons) for o in scene.objects if o.type == "MESH"))
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_vertex_color="ACTIVE", export_materials="NONE",
                          export_texcoords=False)
if not hair_only:
    with open(OUT[: -len(".glb")] + ".json", "w") as fh:
        json.dump({"ground": round(ground, 4), "pieces": meta}, fh, separators=(",", ":"))
