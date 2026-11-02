"""Render the people pieces from body.py into tintable sprites (docs/PEOPLE.md §4).

Run headless:
  blender -b --factory-startup --python tools/blender/people/render.py -- <pieces.glb> <out_dir>

All pieces share one front-ortho canvas, then each sprite is cropped to its pixels. Per sprite
<layer>__<piece>.png: R = clay luminance (a lit face of the chest = 0.5), G and B = trim/detail masks,
A = alpha. Face pieces keep their own colours (raw). <out_dir>/manifest.json holds the canvas pivots,
each sprite's rect and each piece's rest direction (degrees, counter-clockwise, front view).
"""

import json
import math
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1 :]
GLB, OUT = argv[0], os.path.abspath(argv[1])
RES = 768
SCALE = 2.9  # metres across the canvas
CENTRE = (0.0, 1.2)
PAD = 2


def px(x, h):
    return [round((x - CENTRE[0]) / SCALE * RES + RES / 2, 2), round(RES / 2 - (h - CENTRE[1]) / SCALE * RES, 2)]


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
scene = bpy.context.scene
obs = [o for o in scene.objects if o.type == "MESH"]
groups = {}
for o in obs:
    layer, piece, mask = o.name.split("|")
    groups.setdefault((layer, piece), []).append((mask, o))

scene.render.engine = "BLENDER_WORKBENCH"
scene.render.film_transparent = True
scene.render.resolution_x = scene.render.resolution_y = RES
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "Standard"
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
scene.collection.objects.link(cam)
cam.data.type = "ORTHO"
cam.data.ortho_scale = SCALE
cam.location = (CENTRE[0], -10, CENTRE[1])
cam.rotation_euler = (math.pi / 2, 0, 0)
scene.camera = cam
tmp = os.path.join(OUT, "_tmp.png")
os.makedirs(OUT, exist_ok=True)


def shot(members, mask_pass):
    sh = scene.display.shading
    if mask_pass:  # flat object colours: R/G/B = which mask
        sh.light, sh.color_type = "FLAT", "OBJECT"
        scene.view_settings.exposure = 0
    else:  # studio light keeps the clay lumps; exposure 0.9 as approved for the cut-outs
        sh.light, sh.color_type = "STUDIO", "VERTEX"
        scene.view_settings.exposure = 0.9
    for o in obs:
        o.hide_render = o not in members
    scene.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(tmp)
    a = np.array(img.pixels[:], dtype=np.float32).reshape(RES, RES, 4)[::-1]  # top row first
    bpy.data.images.remove(img)
    return a


COL = {"R": (1, 0, 0, 1), "G": (0, 1, 0, 1), "B": (0, 0, 1, 1)}
shots = {}
for key, members in groups.items():
    for mask, o in members:
        o.color = COL.get(mask, (1, 0, 0, 1))
    mob = [o for _, o in members]
    # garments and hair: the body piece under them is an occluder (black in the mask pass), so whatever
    # the body hides in 3D (e.g. side hair behind the cheeks) is cut out of the sprite
    occ = [o for _, o in groups.get(("body", key[1]), [])] if key[0] not in ("body", "face", "hair_back") else []
    for o in occ:
        o.color = (0, 0, 0, 1)
    shots[key] = (shot(mob + occ, False), shot(mob + occ, True), bool(occ))

lit = shots[("body", "chest")][0]
lum = lit[..., :3] @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
k = 0.5 / float(np.median(lum[lit[..., 3] > 0.99]))  # the chest's median lit clay = 0.5

manifest = {"res": RES, "px_per_m": RES / SCALE, "pivots": {}, "rest_deg": {}, "sprites": {}}
for (layer, piece), (rgb, msk, occluded) in shots.items():
    raw = layer == "face"
    out = np.zeros((RES, RES, 4), dtype=np.float32)
    alpha = rgb[..., 3]
    if occluded:
        alpha = alpha * np.clip(msk[..., :3].sum(-1) * 2, 0, 1)
    if raw:
        out[..., :3] = rgb[..., :3]
    else:
        out[..., 0] = np.clip((rgb[..., :3] @ np.array([0.299, 0.587, 0.114], dtype=np.float32)) * k, 0, 1)
        s = msk[..., :3].sum(-1) + 1e-6
        out[..., 1] = msk[..., 1] / s
        out[..., 2] = msk[..., 2] / s
    out[..., 3] = alpha
    ys, xs = np.nonzero(alpha > 0.002)
    x0, y0 = max(xs.min() - PAD, 0), max(ys.min() - PAD, 0)
    x1, y1 = min(xs.max() + PAD + 1, RES), min(ys.max() + PAD + 1, RES)
    crop = out[y0:y1, x0:x1]
    name = f"{layer}__{piece}"
    img = bpy.data.images.new(name, x1 - x0, y1 - y0, alpha=True)
    img.colorspace_settings.name = "Non-Color"  # data, not colour: store values as they are
    img.pixels = crop[::-1].ravel()
    img.filepath_raw = os.path.join(OUT, name + ".png")
    img.file_format = "PNG"
    img.save()
    manifest["sprites"][name] = {"layer": layer, "piece": piece, "rect": [int(x0), int(y0), int(x1 - x0), int(y1 - y0)],
                                 "raw": raw}
    if layer == "body":
        pv = groups[(layer, piece)][0][1]["pivot"]
        en = groups[(layer, piece)][0][1]["end"]
        manifest["pivots"][piece] = px(pv[0], pv[1])
        manifest["rest_deg"][piece] = round(math.degrees(math.atan2(en[1] - pv[1], en[0] - pv[0])), 2)
os.remove(tmp)
json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
print("RENDERED", len(manifest["sprites"]), "sprites, k", round(k, 3))
