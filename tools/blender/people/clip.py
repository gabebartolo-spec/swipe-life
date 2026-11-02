"""Copy a Mixamo clip as front-view world angles, so one clip drives every body (docs/PEOPLE.md §6).

Run headless:
  blender -b --factory-startup --python tools/blender/people/clip.py -- <rig.glb> <out.json>

Writes {fps: 12, frames: n, bones: {piece: [deg, ...]}}: each piece's direction seen from the front,
degrees counter-clockwise from screen right, 12 times a second. Godot turns a piece by
(clip - rest_deg) and composes it down the chain. Pelvis and feet keep their rest direction (the hips
bone and the forward-pointing foot have no stable front-view angle). "front" holds, per side and frame,
how far (m) the hand is in front of the head; above 0 the arm draws over the head and hair.
"""

import json
import math
import sys

import bpy

RIG, OUT = sys.argv[sys.argv.index("--") + 1 :][:2]
# piece -> (bone whose head..tail gives the direction) or (from bone head, to bone head)
SRC = {"chest": ("Spine", "Neck"), "head": ("Head",)}
for side, m in (("l", "Left"), ("r", "Right")):
    SRC |= {f"upper_arm_{side}": (m + "Arm",), f"forearm_{side}": (m + "ForeArm",), f"hand_{side}": (m + "Hand",),
            f"thigh_{side}": (m + "UpLeg",), f"shin_{side}": (m + "Leg",)}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=RIG)
rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
action = bpy.data.actions[0]
curves = list(action.fcurves) if getattr(action, "fcurves", None) else [
    fc for ly in action.layers for st in ly.strips for bag in st.channelbags for fc in bag.fcurves]
if rig.animation_data:  # evaluate fcurves directly: headless frame_set reads stale poses
    rig.animation_data.action = None
    for tr in list(rig.animation_data.nla_tracks):
        rig.animation_data.nla_tracks.remove(tr)
start, end = action.frame_range
bones = {p: [] for p in SRC}
front = {"l": [], "r": []}  # hand nearer the camera than the head: the arm draws over head and hair
n = int((end - start) * 12 / 30) + 1
for i in range(n):
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
    for piece, src in SRC.items():
        b = rig.pose.bones["mixamorig:" + src[0]]
        a, z = (b.head, b.tail) if len(src) == 1 else (b.head, rig.pose.bones["mixamorig:" + src[1]].head)
        d = rig.matrix_world @ z - rig.matrix_world @ a
        bones[piece].append(round(math.degrees(math.atan2(d.z, d.x)), 2))
    head_y = (rig.matrix_world @ rig.pose.bones["mixamorig:Head"].head).y
    for side, m in (("l", "Left"), ("r", "Right")):
        hand_y = (rig.matrix_world @ rig.pose.bones[f"mixamorig:{m}Hand"].head).y
        front[side].append(round(head_y - hand_y, 3))  # Blender -y points at the camera
json.dump({"fps": 12, "frames": n, "bones": bones, "front": front}, open(OUT, "w"))
print("CLIP", n, "frames", {p: v[0] for p, v in bones.items()})
