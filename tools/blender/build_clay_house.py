"""Build the childhood home (GDD §10.6) as a clay dollhouse and prerender it to layered PNGs (§10.4).

Run headless:
  blender -b --factory-startup --python tools/blender/build_clay_house.py -- <out_dir>

Four rooms in a 2x2 front cutaway: bedroom and bathroom upstairs, living room and kitchen downstairs.
Every prop is clay-modelled with build_clay_room.py's helpers and gets baked AO in its vertex colours.
Each layer renders alone on the same isometric camera with a transparent background, so Godot can
stack them without re-aligning anything:
  shell      walls, floors, windows (always shown)
  base       living room, kitchen, bathroom furniture (always shown)
  bed_<band> bedroom furniture for one age band: baby, child, teen (§10.8)
  act_<id>   props left by an activity, keyed by the action id in data/actions (§10.8)
Writes <out_dir>/<layer>.png and <out_dir>/house.json (canvas size, layer list).
Axes are Godot's: x right (0..6), y up, z toward the camera (0..3).
"""

import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from build_clay_room import ball, box, cloth, hexc, tube  # noqa: E402

RES = (1080, 900)  # dollhouse strip: ~45% of a 1080x1920 portrait screen (§10.5)
W, D, H = 6.0, 3.0, 2.6  # house width, depth, storey height
UP = H + 0.2  # upstairs floor level
WALL, CREAM, WOOD = "e6d9c6", "f3ead8", "c98a55"

LAYERS = {}  # layer name -> object names


def layer(name):
    """Everything built after this call, until the next call, belongs to the named layer."""
    LAYERS[name] = set()
    layer.current = name


def tag():
    for ob in bpy.context.scene.objects:
        if ob.type == "MESH" and not any(ob.name in s for s in LAYERS.values()):
            LAYERS[layer.current].add(ob.name)


def window(x, y, z_wall=0.03, w=1.0, h=0.9):
    """Window on the back wall, centre (x, y)."""
    box(f"win_frame{x}{y}", (x, y, z_wall), (w + 0.2, h + 0.2, 0.12), "fbf8f2", bevel=0.05)
    box(f"win_pane{x}{y}", (x, y, z_wall + 0.05), (w, h, 0.04), "fff3d6", bevel=0.01, subd=0, lump=0)
    box(f"win_bar{x}{y}", (x, y, z_wall + 0.08), (0.06, h, 0.04), "fbf8f2", bevel=0.02)
    box(f"win_sill{x}{y}", (x, y - h / 2 - 0.08, z_wall + 0.12), (w + 0.3, 0.08, 0.26), "fbf8f2", bevel=0.03)


def shell():
    layer("shell")
    for i, (y, floor) in enumerate(((0.0, "c98a55"), (UP, "d9b48a"))):
        box(f"slab{i}", (W / 2, y - 0.12, D / 2), (W + 0.4, 0.24, D + 0.2), WALL, bevel=0.1)
        tints = [floor, "bf7f4a", "d29560"] if i == 0 else [floor, "cfa87c", "e0c095"]
        for p in range(12):
            box(f"plank{i}_{p}", (0.25 + p * 0.5, y + 0.02, D / 2), (0.46, 0.06, D - 0.05), tints[p % 3],
                bevel=0.025, seed=p + i * 12)
    box("roof_slab", (W / 2, 2 * UP - 0.08, D / 2), (W + 0.4, 0.2, D + 0.2), "c45c4a", bevel=0.1)
    box("wall_back", (W / 2, UP, -0.15), (W + 0.4, 2 * UP, 0.3), WALL, bevel=0.15)
    box("wall_left", (-0.15, UP, D / 2), (0.3, 2 * UP, D + 0.2), WALL, bevel=0.15)
    box("wall_right", (W + 0.15, UP, D / 2), (0.3, 2 * UP, D + 0.2), WALL, bevel=0.15)
    for y in (0.0, UP):  # room divider with a door gap at the front
        box(f"divider{y}", (W / 2, y + H / 2, 0.85), (0.16, H, 1.7), WALL, bevel=0.06)
    # wallpaper tints per room, set into the back wall
    for (x, y, col) in ((1.5, UP, "dfe6d2"), (4.5, UP, "d6e4ea"), (1.5, 0, "f0dcc4"), (4.5, 0, "f2e8c8")):
        box(f"paper{x}{y}", (x, y + H / 2, 0.01), (2.8, H - 0.1, 0.02), col, bevel=0.01, subd=1, lump=0.004)
    window(1.2, UP + 1.5, w=0.9)
    window(4.4, UP + 1.6, w=0.6, h=0.6)
    window(1.0, 1.5)
    window(4.6, 1.55, w=0.8, h=0.7)
    tag()


def base():
    layer("base")
    # living room (downstairs left): sofa, rug, TV, lamp
    cloth("living_rug", (1.5, 0.08, 1.9), (2.2, 0.04, 1.4), "d9a3a0", folds=0.005)
    box("sofa_base", (1.4, 0.3, 0.55), (1.9, 0.45, 0.8), "7f9fb8", bevel=0.14)
    box("sofa_back", (1.4, 0.75, 0.25), (1.9, 0.6, 0.25), "7f9fb8", bevel=0.12)
    for i, x in enumerate((0.45, 2.35)):
        box(f"sofa_arm{i}", (x, 0.52, 0.55), (0.25, 0.5, 0.8), "6f8fa8", bevel=0.1)
    ball("cushion", (0.85, 0.7, 0.5), 0.22, "e0b45a", scale=(1, 0.9, 0.38), lump=0.015)
    # TV on a low stand against the left wall, facing into the room (never between camera and sofa)
    box("tv_stand", (0.25, 0.22, 1.75), (0.4, 0.4, 1.2), WOOD, bevel=0.05)
    box("tv", (0.22, 0.75, 1.75), (0.08, 0.62, 0.95), "4a4d55", bevel=0.04)
    box("tv_screen", (0.27, 0.75, 1.75), (0.02, 0.52, 0.84), "6a7a8a", bevel=0.01, subd=1, lump=0)
    # kitchen (downstairs right): counter, fridge, table
    # the right wall's outside hides anything tall against it, so the fridge stands by the divider
    box("fridge", (3.5, 0.85, 0.4), (0.7, 1.7, 0.7), "fbf8f2", bevel=0.08)
    box("fridge_handle", (3.78, 1.1, 0.76), (0.04, 0.4, 0.04), "a9b0a2", bevel=0.015)
    box("counter", (4.85, 0.45, 0.35), (1.9, 0.9, 0.6), "f3ead8", bevel=0.05)
    box("counter_top", (4.85, 0.93, 0.35), (2.0, 0.08, 0.66), "a9b0a2", bevel=0.03)
    tube("pot", (4.4, 1.07, 0.35), 0.14, 0.2, "c45c4a")
    tube("herb_pot", (5.3, 1.05, 0.3), 0.09, 0.16, "c8693f")
    ball("herb", (5.3, 1.2, 0.3), 0.12, "6f9e57", scale=(1, 0.7, 1), seed=3)
    tube("table_top", (4.4, 0.72, 2.0), 0.55, 0.07, WOOD)
    tube("table_leg", (4.4, 0.36, 2.0), 0.06, 0.7, "bf7f4a")
    for i, (dx, dz) in enumerate(((-0.75, 0.0), (0.75, 0.0))):
        box(f"stool{i}", (4.4 + dx, 0.45, 2.0 + dz), (0.4, 0.08, 0.4), CREAM, bevel=0.04)
        tube(f"stool_leg{i}", (4.4 + dx, 0.22, 2.0 + dz), 0.04, 0.44, "bf7f4a")
    ball("fruit_bowl", (4.4, 0.8, 2.0), 0.18, "f4efe6", scale=(1, 0.4, 1))
    for i, col in enumerate(("e0a24a", "c45c4a", "7fae6a")):
        ball(f"fruit{i}", (4.3 + i * 0.1, 0.88, 2.0 + (i - 1) * 0.06), 0.07, col, lump=0, seed=i)
    # bathroom (upstairs right): tub, toilet, sink, mirror
    # sink and mirror on the back wall, tub beside it, toilet against the right wall facing in
    box("sink", (3.65, UP + 0.85, 0.3), (0.6, 0.2, 0.45), "fbf8f2", bevel=0.08)
    tube("sink_pedestal", (3.65, UP + 0.4, 0.25), 0.1, 0.75, "fbf8f2")
    tube("tap", (3.65, UP + 1.0, 0.12), 0.03, 0.14, "a9b0a2")
    box("mirror_frame", (3.65, UP + 1.6, 0.04), (0.6, 0.75, 0.05), "c98a55", bevel=0.03)
    box("mirror", (3.65, UP + 1.6, 0.07), (0.48, 0.62, 0.03), "cfe3ea", bevel=0.015, subd=1, lump=0)
    box("tub", (4.85, UP + 0.32, 0.5), (1.5, 0.6, 0.8), "fbf8f2", bevel=0.18)
    box("tub_water", (4.85, UP + 0.58, 0.5), (1.25, 0.06, 0.58), "a9d0e0", bevel=0.05, lump=0.004)
    ball("duck", (4.6, UP + 0.68, 0.55), 0.08, "f3d36b", scale=(1.2, 0.9, 1), lump=0)
    box("toilet_base", (3.5, UP + 0.22, 1.95), (0.5, 0.44, 0.42), "fbf8f2", bevel=0.12)
    box("toilet_seat", (3.55, UP + 0.47, 1.95), (0.52, 0.06, 0.44), "e6eef0", bevel=0.03)
    box("toilet_tank", (3.25, UP + 0.7, 1.95), (0.2, 0.5, 0.5), "fbf8f2", bevel=0.08)
    cloth("bath_mat", (4.7, UP + 0.07, 1.4), (1.0, 0.04, 0.5), "a9c2a2", folds=0.006)
    tag()


def bedroom_common(band):
    cloth(f"bed_rug_{band}", (1.5, UP + 0.08, 1.9), (1.8, 0.04, 1.3), "e6c0b4", folds=0.005)


def bed_baby():
    layer("bed_baby")
    bedroom_common("baby")
    # crib: slatted box with a soft mattress, a mobile above, blocks on the rug
    box("crib_base", (1.0, UP + 0.45, 0.7), (1.3, 0.12, 0.8), "f3ead8", bevel=0.04)
    box("crib_mattress", (1.0, UP + 0.56, 0.7), (1.18, 0.12, 0.68), "cfe0ea", bevel=0.06)
    for i in range(9):
        x = 0.4 + i * 0.15
        for z in (0.36, 1.04):
            tube(f"crib_slat{i}_{z}", (x, UP + 0.65, z), 0.025, 0.7, "f3ead8")
    for z in (0.36, 1.04):
        box(f"crib_rail{z}", (1.0, UP + 1.0, z), (1.32, 0.06, 0.06), "f3ead8", bevel=0.025)
    tube("mobile_rod", (1.0, UP + 1.85, 0.7), 0.015, 0.7, "8a6a55")
    for i, col in enumerate(("f3d36b", "e58f5a", "9fb6d2")):
        a = i * 2 * math.pi / 3
        ball(f"mobile_{i}", (1.0 + 0.25 * math.cos(a), UP + 1.45, 0.7 + 0.25 * math.sin(a)), 0.08, col, lump=0)
    for i, col in enumerate(("c45c4a", "e0b45a", "5c7a5a", "4e6a8a")):
        box(f"block{i}", (1.6 + (i % 2) * 0.24, UP + 0.18 + (i // 2) * 0.2, 2.0 + (i % 2) * 0.05),
            (0.2, 0.2, 0.2), col, bevel=0.03, seed=i)
    ball("teddy_body", (2.35, UP + 0.28, 1.4), 0.2, "c98a55", scale=(1, 1.1, 0.9))
    ball("teddy_head", (2.35, UP + 0.58, 1.42), 0.14, "c98a55")
    for i, dx in enumerate((-0.1, 0.1)):
        ball(f"teddy_ear{i}", (2.35 + dx, UP + 0.7, 1.4), 0.055, "a8703f", lump=0)
    ball("teddy_snout", (2.35, UP + 0.55, 1.55), 0.06, "e6c49a", lump=0)
    tag()


def bed_child():
    layer("bed_child")
    bedroom_common("child")
    box("kid_bed", (0.85, UP + 0.25, 0.9), (1.4, 0.35, 1.6), "e58f5a", bevel=0.08)
    cloth("kid_duvet", (0.85, UP + 0.47, 1.05), (1.45, 0.1, 1.2), "f3d36b", folds=0.03, droop=0.2)
    ball("kid_pillow", (0.85, UP + 0.52, 0.35), 0.25, "fbf6ec", scale=(1.2, 0.4, 0.7))
    box("toy_box", (2.3, UP + 0.25, 0.4), (0.8, 0.5, 0.5), "5c7a5a", bevel=0.07)
    ball("toy_ball", (2.1, UP + 0.6, 0.4), 0.13, "c45c4a", lump=0)
    tag()


def bed_teen():
    layer("bed_teen")
    bedroom_common("teen")
    box("teen_bed", (0.95, UP + 0.28, 0.95), (1.6, 0.4, 1.8), "b8743f", bevel=0.08)
    cloth("teen_duvet", (0.95, UP + 0.53, 1.15), (1.65, 0.1, 1.35), "9fb6d2", folds=0.03, droop=0.22)
    ball("teen_pillow", (0.95, UP + 0.58, 0.35), 0.28, "fbf6ec", scale=(1.2, 0.36, 0.7))
    box("desk_top", (2.3, UP + 0.75, 0.35), (1.0, 0.08, 0.6), WOOD, bevel=0.03)
    for x in (1.88, 2.72):
        box(f"desk_leg{x}", (x, UP + 0.37, 0.35), (0.08, 0.74, 0.5), "bf7f4a", bevel=0.03)
    box("poster_t", (2.25, UP + 1.45, 0.04), (0.5, 0.7, 0.04), "4e6a8a", bevel=0.02)
    ball("poster_t_star", (2.25, UP + 1.5, 0.08), 0.13, "f3d36b", scale=(1, 1, 0.25))
    tag()


def activities():
    layer("act_club")  # sports club: a ball by the sofa
    ball("club_ball", (2.5, 0.2, 1.3), 0.18, "f3ead8", lump=0.01)
    ball("club_ball_patch", (2.5, 0.3, 1.42), 0.07, "4a4d55", scale=(1, 1, 0.5), lump=0)
    tag()
    layer("act_study")  # study: a stack of books on the kitchen table
    for i, col in enumerate(("4e6a8a", "c45c4a", "e0b45a")):
        box(f"study_book{i}", (4.15, 0.8 + i * 0.07, 2.15), (0.4 - i * 0.03, 0.06, 0.3), col, bevel=0.02, seed=i)
    tag()
    layer("act_play_toys")  # toys: a toy train on the living room rug
    for i, col in enumerate(("c45c4a", "4e6a8a", "e0b45a")):
        box(f"train{i}", (1.1 + i * 0.32, 0.2, 1.85), (0.28, 0.2, 0.2), col, bevel=0.05, seed=i)
        for dx in (-0.08, 0.08):
            tube(f"wheel{i}{dx}", (1.1 + i * 0.32 + dx, 0.1, 1.97), 0.05, 0.03, "4a4d55", rot=(math.pi / 2, 0, 0))
    tag()


def camera():
    scene = bpy.context.scene
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 8.0
    # isometric-ish from the front right, looking down 30 degrees; Blender: -Y is Godot +z (toward camera)
    yaw, pitch = math.radians(18), math.radians(14)
    centre = (W / 2 + 0.05, -D / 2, UP - 0.25)  # Blender coordinates
    dist = 30
    cam.location = (centre[0] + dist * math.sin(yaw) * math.cos(pitch),
                    centre[1] - dist * math.cos(yaw) * math.cos(pitch),
                    centre[2] + dist * math.sin(pitch))
    cam.rotation_euler = (math.pi / 2 - pitch, 0, yaw)
    scene.camera = cam


def _prep(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    if len(ob.data.vertices) > 1500:  # mobile-era budget kept from the room; these become PNGs anyway
        d = ob.modifiers.new("budget", "DECIMATE")
        d.ratio = 1500 / len(ob.data.vertices)
        bpy.ops.object.modifier_apply(modifier="budget")
    ob.data.shade_smooth()
    ob.data.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    ob.data.attributes.active_color = ob.data.color_attributes["Col"]
    ob.data.materials.append(bpy.data.materials.new(ob.name))


def bake_groups():
    """AO per layer: the shell and base bake together; each other layer bakes with only the shell and
    base around it, so the crib never leaves a ghost shadow under the teen bed."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    scene.cycles.device = "CPU"
    scene.render.bake.target = "VERTEX_COLORS"
    obs = {o.name: o for o in scene.objects if o.type == "MESH"}
    for ob in obs.values():
        _prep(ob)
    fixed = LAYERS["shell"] | LAYERS["base"]
    groups = [fixed] + [m for n, m in LAYERS.items() if n not in ("shell", "base")]
    for members in groups:
        for n, ob in obs.items():
            ob.hide_render = n not in members and n not in fixed
            ob.select_set(n in members)
        bpy.context.view_layer.objects.active = obs[next(iter(members))]
        bpy.ops.object.bake(type="AO")
    for ob in obs.values():
        ob.hide_render = False
        base = hexc(ob["clay_color"])
        for d in ob.data.color_attributes["Col"].data:
            ao = 0.35 + 0.65 * d.color[0]
            d.color = (base[0] * ao, base[1] * ao, base[2] * ao, 1.0)
        ob.data.materials.clear()


def _pixels(path):
    img = bpy.data.images.load(path)
    a = np.empty(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(-1, 4)


def render(out):
    """Workbench ignores holdouts, so each prop layer renders together with the shell (walls hide what
    they should) and then loses every pixel that matches the shell-only render. Workbench is noise-free,
    so hidden pixels match exactly; edge pixels keep a partial alpha."""
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "VERTEX"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0.9
    scene.render.film_transparent = True
    scene.render.resolution_x, scene.render.resolution_y = RES
    scene.render.image_settings.color_mode = "RGBA"
    os.makedirs(out, exist_ok=True)
    meshes = [o for o in scene.objects if o.type == "MESH"]
    shell_png = os.path.join(out, "shell.png")
    for name, members in LAYERS.items():
        for o in meshes:
            o.hide_render = o.name not in members and o.name not in LAYERS["shell"]
        scene.render.filepath = os.path.join(out, name + ".png")
        bpy.ops.render.render(write_still=True)
        if name == "shell":
            continue
        px, sh = _pixels(scene.render.filepath), _pixels(shell_png)
        diff = np.abs(px - sh).max(axis=1)
        px[:, 3] *= np.clip(diff * 12.0, 0.0, 1.0)
        img = bpy.data.images.new(name, RES[0], RES[1], alpha=True)
        img.pixels.foreach_set(px.ravel())
        img.filepath_raw = scene.render.filepath
        img.file_format = "PNG"
        img.save()
        bpy.data.images.remove(img)
    json.dump({"res": list(RES), "layers": list(LAYERS)}, open(os.path.join(out, "house.json"), "w"), indent=1)


if __name__ == "__main__":
    OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    shell()
    base()
    bed_baby()
    bed_child()
    bed_teen()
    activities()
    bake_groups()
    camera()
    render(OUT)
    print("HOUSE", {k: len(v) for k, v in LAYERS.items()})
