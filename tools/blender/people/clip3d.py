"""Copy Mixamo clips as 3D rotations, so one clip drives every body from any angle.

Run headless:
  blender -b --factory-startup --python tools/blender/people/clip3d.py -- <out_dir> <clip.fbx> ... [fps]

Writes <out_dir>/<clip>.json: {fps, frames, hips: [x,y,z per frame, in hip heights],
rot: {piece: [w,x,y,z per frame]}}. Rotations are world-space, Godot axes, relative to the T-pose.
"""

import json
import os
import sys

import bpy

ARGS = sys.argv[sys.argv.index("--") + 1 :]
OUT, FILES = ARGS[0], ARGS[1:]
FPS = 24
MAX_SECONDS = 12
SRC = {"pelvis": "Hips", "chest": "Spine1", "head": "Head"}
for side, m in (("l", "Left"), ("r", "Right")):
    SRC |= {f"upper_arm_{side}": m + "Arm", f"forearm_{side}": m + "ForeArm", f"hand_{side}": m + "Hand",
            f"thigh_{side}": m + "UpLeg", f"shin_{side}": m + "Leg", f"foot_{side}": m + "Foot"}

os.makedirs(OUT, exist_ok=True)
for path in FILES:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    scene = bpy.context.scene
    rig = next(o for o in scene.objects if o.type == "ARMATURE")
    start, end = bpy.data.actions[0].frame_range
    n = min(int((end - start) * FPS / 30) + 1, FPS * MAX_SECONDS)
    pre = "mixamorig:"
    hip_rest = rig.matrix_world @ rig.data.bones[pre + "Hips"].head_local
    rest = {p: (rig.matrix_world @ rig.data.bones[pre + b].matrix_local).to_quaternion().inverted() for p, b in SRC.items()}
    hips, rot = [], {p: [] for p in SRC}
    for i in range(n):
        f = start + i * 30 / FPS
        scene.frame_set(int(f), subframe=f - int(f))
        h = rig.matrix_world @ rig.pose.bones[pre + "Hips"].head
        hips += [round(v / hip_rest.z, 3) for v in (h.x, h.z, -h.y)]
        for p, b in SRC.items():
            q = (rig.matrix_world @ rig.pose.bones[pre + b].matrix).to_quaternion() @ rest[p]
            rot[p] += [round(v, 3) for v in (q.w, q.x, q.z, -q.y)]
    name = os.path.splitext(os.path.basename(path))[0]
    with open(os.path.join(OUT, name + ".json"), "w") as fh:
        json.dump({"fps": FPS, "frames": n, "hips": hips, "rot": rot}, fh, separators=(",", ":"))
    print("CLIP", name, n)
