"""Render the clay girl's cut-out pieces flat and copy the Mixamo wave onto them as 2D joint angles.

Run headless:
  blender -b --factory-startup --python tools/blender/render_cutouts.py -- <cutout.glb> <rig.glb> <out_dir>

<cutout.glb> comes from build_clay_girl.py --cutout: arm pieces are separate objects with a "pivot"
extra (Godot axes). Writes <out_dir>/<piece>.png, all on one shared front-ortho canvas so they line up
untouched, and <out_dir>/cutout.json: pivot pixel per piece and, 12 times a second, each piece's
rotation (radians, Godot sign, relative to its parent piece) so its segment points the way the
matching Mixamo bone points in the clip, seen from the front.
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1 :]
CUT, RIG, OUT = argv[0], argv[1], os.path.abspath(argv[2])
RES = 768
SCALE = 2.9  # metres across the canvas
CENTRE = (0.0, 1.3)  # (x, height) at the canvas centre
SIDES = ("Left", "Right")
BONES = ("Arm", "ForeArm", "Hand")
PIECES = [s + b for s in SIDES for b in BONES]


def px(x, h):
    return [round((x - CENTRE[0]) / SCALE * RES + RES / 2, 2), round(RES / 2 - (h - CENTRE[1]) / SCALE * RES, 2)]


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=CUT)
scene = bpy.context.scene
obs = [o for o in scene.objects if o.type == "MESH"]
groups = {p: [o for o in obs if o.name == p] for p in PIECES}
groups["body"] = [o for o in obs if o.name not in PIECES]
pivot = {p: tuple(groups[p][0]["pivot"]) for p in PIECES}  # Godot axes: x right, y up

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.view_settings.exposure = 0.9  # studio light alone muddies the baked clay colours; flat light loses the lumps
scene.display.shading.color_type = "VERTEX"
scene.render.film_transparent = True
scene.render.resolution_x = scene.render.resolution_y = RES
scene.view_settings.view_transform = "Standard"
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
scene.collection.objects.link(cam)
cam.data.type = "ORTHO"
cam.data.ortho_scale = SCALE
cam.location = (CENTRE[0], -10, CENTRE[1])
cam.rotation_euler = (math.pi / 2, 0, 0)
scene.camera = cam
os.makedirs(OUT, exist_ok=True)
for name, members in groups.items():
    for o in obs:
        o.hide_render = o not in members
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)

# each piece's own rest direction in the cut-out: from its pivot to the next joint down the arm
nxt = {s + "Arm": s + "ForeArm" for s in SIDES} | {s + "ForeArm": s + "Hand" for s in SIDES}


def rest_angle(p):
    a = pivot[p]
    if p in nxt:
        b = pivot[nxt[p]]
    else:  # hand: from the wrist to the hand blob's centre
        c = sum((Vector(v.co) for v in groups[p][0].data.vertices), Vector()) / len(groups[p][0].data.vertices)
        c = groups[p][0].matrix_world @ c
        b = (c.x, c.z)
    return math.atan2(b[1] - a[1], b[0] - a[0])


cut_rest = {p: rest_angle(p) for p in PIECES}

# the clip: evaluate fcurves directly (headless frame_set reads stale poses)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=RIG)
rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
action = bpy.data.actions[0]
curves = list(action.fcurves) if getattr(action, "fcurves", None) else [
    fc for ly in action.layers for st in ly.strips for bag in st.channelbags for fc in bag.fcurves]
if rig.animation_data:
    rig.animation_data.action = None
    for tr in list(rig.animation_data.nla_tracks):
        rig.animation_data.nla_tracks.remove(tr)
start, end = action.frame_range
poses = []
for i in range(int((end - start) * 12 / 30) + 1):
    f = start + i * 30 / 12
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    for fc in curves:
        path = fc.data_path
        if 'pose.bones["' in path and path.endswith(("rotation_quaternion", "location")):
            getattr(rig.pose.bones[path.split('"')[1]], path.rsplit(".", 1)[1])[fc.array_index] = fc.evaluate(f)
    bpy.context.view_layer.update()
    pose = {}
    for s in SIDES:
        parent = 0.0
        for b in BONES:
            pb = rig.pose.bones["mixamorig:" + s + b]
            d = rig.matrix_world @ pb.tail - rig.matrix_world @ pb.head
            turn = math.atan2(d.z, d.x) - cut_rest[s + b]
            turn = (turn + math.pi) % (2 * math.pi) - math.pi
            local = (turn - parent + math.pi) % (2 * math.pi) - math.pi
            pose[s + b] = round(-local, 4)  # Godot's y points down: angles flip
            parent = turn
    poses.append(pose)
pivots = {"body": px(0, 0)} | {p: px(pivot[p][0], pivot[p][1]) for p in PIECES}
json.dump({"res": RES, "pivots": pivots, "fps": 12, "poses": poses}, open(os.path.join(OUT, "cutout.json"), "w"), indent=1)
print("CUTOUT", len(poses), "poses", pivots)
