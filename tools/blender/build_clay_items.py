"""Build the shop items (GDD §6.1, §10.2) as clay props and export them for the Godot room stage.

Run headless:
  blender -b --factory-startup --python tools/blender/build_clay_items.py -- <out.glb>

One mesh per item in data/property/items.json, named by its id. Each stands on the floor with its
origin at the middle of its base and its front toward +z (Godot), like the house props. Colour and
baked AO ride in the vertex colours, the same as build_clay_house.py. Godot axes (x, y up, z).
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_clay_room as R  # noqa: E402

box, ball, tube, cloth, pillow = R.box, R.ball, R.tube, R.cloth, R.pillow
WOOD, DARKWOOD, CREAM = "d9935a", "b8743f", "f3ead8"
SPACING = 3.5
ITEMS = {}  # id -> origin x
_current = {"id": None, "x": 0.0}


def at(item):
    """Start an item; returns a helper that offsets props by the item's slot on the work row."""
    x = len(ITEMS) * SPACING
    ITEMS[item] = x
    _current.update(id=item, x=x)


def n(part):
    return f"{_current['id']}__{part}"


def p(x, y, z):
    return (_current["x"] + x, y, z)


def plant():
    at("plant")
    tube(n("pot"), p(0, 0.2, 0), 0.22, 0.4, "c8693f")
    for i, (dx, dy, dz) in enumerate(((0, 0.38, 0), (0.15, 0.25, 0.05), (-0.14, 0.28, -0.04), (0.04, 0.55, 0.08), (-0.08, 0.5, 0.12), (0.1, 0.4, -0.12))):
        ball(n(f"leaf{i}"), p(0.0 + dx, 0.4 + dy, dz), 0.2, "6f9e57" if i % 2 else "7fae6a", scale=(1, 0.65, 1), seed=i)


def bookshelf():
    at("bookshelf")
    box(n("left"), p(-0.5, 0.85, 0), (0.06, 1.7, 0.34), WOOD, bevel=0.02)
    box(n("right"), p(0.5, 0.85, 0), (0.06, 1.7, 0.34), WOOD, bevel=0.02)
    box(n("back"), p(0, 0.85, -0.14), (1.0, 1.7, 0.05), DARKWOOD, bevel=0.01)
    cols = ("c45c4a", "e0b45a", "4e6a8a", "7fae6a", "8a5a7a", "e58f5a")
    for s, y in enumerate((0.03, 0.46, 0.89, 1.32, 1.7)):
        box(n(f"shelf{s}"), p(0, y, 0), (1.0, 0.05, 0.34), WOOD, bevel=0.015)
        if s < 4:
            for i in range(6):
                h = 0.26 + 0.05 * ((i * 5 + s) % 3)
                box(n(f"b{s}_{i}"), p(-0.36 + i * 0.13, y + 0.03 + h / 2, 0.0), (0.1, h, 0.24), cols[(i + s) % 6], bevel=0.015, seed=i + s)


def rug():
    at("rug")
    cloth(n("outer"), p(0, 0.03, 0), (1.9, 0.05, 1.3), "d9a3a0", folds=0.006)
    cloth(n("inner"), p(0, 0.06, 0), (1.5, 0.03, 0.95), "e6c0b4", folds=0.006)


def sofa():
    at("sofa")
    c, d = "5f8f8a", "4e7a76"
    box(n("base"), p(0, 0.24, 0), (1.9, 0.3, 0.85), d, bevel=0.08)
    box(n("back"), p(0, 0.62, -0.34), (1.9, 0.55, 0.22), c, bevel=0.1)
    box(n("arm_l"), p(-0.88, 0.48, 0.02), (0.22, 0.52, 0.85), c, bevel=0.1)
    box(n("arm_r"), p(0.88, 0.48, 0.02), (0.22, 0.52, 0.85), c, bevel=0.1)
    box(n("seat_l"), p(-0.4, 0.46, 0.08), (0.78, 0.18, 0.62), "6fa09a", bevel=0.07)
    box(n("seat_r"), p(0.4, 0.46, 0.08), (0.78, 0.18, 0.62), "6fa09a", bevel=0.07)
    pillow(n("cushion"), p(0.55, 0.72, -0.12), (0.42, 0.4, 0.16), "e0b45a")


def tv():
    at("tv")
    # open media unit: frame, a cubby with a docked Switch, a cubby of DVD cases
    t = dict(bevel=0.012, subd=1, lump=0.002)
    box(n("back"), p(0, 0.25, -0.195), (1.2, 0.5, 0.03), DARKWOOD, **t)
    box(n("top"), p(0, 0.475, 0), (1.2, 0.05, 0.42), WOOD, bevel=0.025, subd=1, lump=0.004)
    box(n("base"), p(0, 0.025, 0), (1.2, 0.05, 0.42), WOOD, bevel=0.025, subd=1, lump=0.004)
    for i, dx in enumerate((-0.575, 0.575)):
        box(n(f"side{i}"), p(dx, 0.25, 0), (0.05, 0.5, 0.42), WOOD, bevel=0.02, subd=1, lump=0.004)
    box(n("divider"), p(0.15, 0.25, 0), (0.04, 0.4, 0.4), WOOD, **t)
    box(n("dock_back"), p(-0.2, 0.15, -0.1), (0.32, 0.2, 0.04), "e8e8ea", **t)
    box(n("dock_base"), p(-0.2, 0.08, -0.02), (0.34, 0.06, 0.16), "e8e8ea", **t)
    box(n("switch"), p(-0.2, 0.185, -0.06), (0.24, 0.14, 0.03), "2b2f36", **t)
    box(n("joycon_l"), p(-0.34, 0.185, -0.06), (0.04, 0.14, 0.03), "e8474c", **t)
    box(n("joycon_r"), p(-0.06, 0.185, -0.06), (0.04, 0.14, 0.03), "3aa6e8", **t)
    box(n("switch_screen"), p(-0.2, 0.19, -0.04), (0.2, 0.11, 0.005), "55606a", bevel=0.003, subd=0, lump=0)
    cases = ("e8474c", "f3ead8", "3aa6e8", "f0c24a", "3c3f46", "6fb36f", "e8e8ea", "9b6fd0")
    for i, c in enumerate(cases):
        box(n(f"dvd{i}"), p(0.2 + i * 0.044, 0.155, 0.02), (0.036, 0.19, 0.14), c, **t)
    box(n("remote"), p(-0.4, 0.51, 0.1), (0.05, 0.025, 0.16), "3a3d42", **t)
    box(n("neck"), p(0, 0.55, 0), (0.18, 0.1, 0.1), "3a3d42", bevel=0.02)
    box(n("screen"), p(0, 0.95, 0), (1.05, 0.62, 0.07), "3a3d42", bevel=0.03)
    box(n("glass"), p(0, 0.95, 0.04), (0.94, 0.52, 0.02), "55606a", bevel=0.01, subd=0, lump=0)


def piano():
    at("piano")
    box(n("body"), p(0, 0.55, -0.1), (1.5, 1.1, 0.5), "3b2f35", bevel=0.06)
    box(n("shelf"), p(0, 0.72, 0.18), (1.5, 0.08, 0.22), "3b2f35", bevel=0.03)
    box(n("keys"), p(0, 0.78, 0.2), (1.3, 0.04, 0.2), "f6f0e4", bevel=0.01, subd=0, lump=0)
    for i in range(9):
        box(n(f"black{i}"), p(-0.55 + i * 0.14 + (0.07 if i > 2 else 0), 0.81, 0.15), (0.05, 0.03, 0.11), "26222a", bevel=0.005, subd=0, lump=0)
    box(n("leg_l"), p(-0.65, 0.34, 0.18), (0.1, 0.68, 0.1), "3b2f35", bevel=0.02)
    box(n("leg_r"), p(0.65, 0.34, 0.18), (0.1, 0.68, 0.1), "3b2f35", bevel=0.02)
    box(n("stool"), p(0, 0.28, 0.65), (0.55, 0.1, 0.3), "7a4a35", bevel=0.04)
    for i, dx in enumerate((-0.2, 0.2)):
        tube(n(f"stool_leg{i}"), p(dx, 0.14, 0.65), 0.035, 0.28, "7a4a35")


def mattress():
    at("mattress")
    box(n("frame"), p(0, 0.12, 0), (1.5, 0.22, 2.0), DARKWOOD, bevel=0.06)
    box(n("mat"), p(0, 0.34, 0), (1.4, 0.26, 1.9), CREAM, bevel=0.1)
    cloth(n("duvet"), p(0, 0.57, 0.28), (1.62, 0.1, 1.5), "9fb6d2", folds=0.025, droop=0.32)
    for i, dx in enumerate((-0.32, 0.32)):
        pillow(n(f"pillow{i}"), p(dx, 0.55, -0.7), (0.6, 0.2, 0.42), "fbf6ec", seed=i)


def desk():
    at("desk")
    box(n("top"), p(0, 0.95, 0), (1.3, 0.06, 0.65), WOOD, bevel=0.02)
    for i, dx in enumerate((-0.6, 0.6)):
        box(n(f"leg{i}"), p(dx, 0.47, 0), (0.08, 0.94, 0.5), "6b6f75", bevel=0.02)
    box(n("laptop_base"), p(0.1, 1.0, 0.05), (0.42, 0.03, 0.3), "b8bdc4", bevel=0.01)
    box(n("laptop_screen"), p(0.1, 1.15, -0.1), (0.42, 0.28, 0.02), "55606a", bevel=0.01)
    tube(n("mug"), p(-0.4, 1.05, 0.1), 0.05, 0.1, "c45c4a")


def wardrobe():
    at("wardrobe")
    box(n("body"), p(0, 0.95, 0), (1.1, 1.9, 0.55), WOOD, bevel=0.05)
    box(n("door_l"), p(-0.27, 0.95, 0.28), (0.52, 1.75, 0.03), DARKWOOD, bevel=0.015)
    box(n("door_r"), p(0.27, 0.95, 0.28), (0.52, 1.75, 0.03), DARKWOOD, bevel=0.015)
    ball(n("knob_l"), p(-0.06, 0.95, 0.32), 0.035, "e0b45a")
    ball(n("knob_r"), p(0.06, 0.95, 0.32), 0.035, "e0b45a")
    box(n("sleeve"), p(0.45, 0.6, 0.31), (0.12, 0.35, 0.02), "c45c4a", bevel=0.01)


def espresso():
    at("espresso")
    box(n("table"), p(0, 0.4, 0), (0.6, 0.06, 0.45), WOOD, bevel=0.02)
    for i, (dx, dz) in enumerate(((-0.25, -0.18), (0.25, -0.18), (-0.25, 0.18), (0.25, 0.18))):
        tube(n(f"leg{i}"), p(dx, 0.19, dz), 0.025, 0.38, DARKWOOD)
    box(n("machine"), p(0, 0.62, -0.05), (0.34, 0.38, 0.32), "b8bdc4", bevel=0.04)
    box(n("tray"), p(0, 0.46, 0.12), (0.3, 0.03, 0.1), "6b6f75", bevel=0.01)
    tube(n("cup"), p(0, 0.51, 0.12), 0.035, 0.07, "f6f0e4")


def cooker():
    at("cooker")
    box(n("body"), p(0, 0.45, 0), (0.9, 0.9, 0.7), "c9ced3", bevel=0.05)
    box(n("hob"), p(0, 0.92, 0), (0.88, 0.04, 0.68), "3a3d42", bevel=0.02)
    for i, (dx, dz) in enumerate(((-0.22, -0.16), (0.22, -0.16), (-0.22, 0.16), (0.22, 0.16))):
        tube(n(f"ring{i}"), p(dx, 0.95, dz), 0.1, 0.02, "55606a")
    box(n("door"), p(0, 0.42, 0.36), (0.72, 0.5, 0.03), "a9aeb4", bevel=0.015)
    box(n("window"), p(0, 0.45, 0.385), (0.5, 0.26, 0.01), "26222a", bevel=0.005, subd=0, lump=0)
    box(n("handle"), p(0, 0.7, 0.4), (0.6, 0.04, 0.05), "6b6f75", bevel=0.015)
    for i, dx in enumerate((-0.28, -0.1, 0.1, 0.28)):
        ball(n(f"knob{i}"), p(dx, 0.84, 0.36), 0.035, "3a3d42")


def spa_bath():
    at("spa_bath")
    # open tub: floor and four walls, so the water sits visibly inside the rim
    box(n("tub_floor"), p(0, 0.08, 0), (1.7, 0.16, 0.85), "f6f0e4", bevel=0.05)
    for i, dz in enumerate((-0.365, 0.365)):
        box(n(f"tub_side{i}"), p(0, 0.3, dz), (1.7, 0.6, 0.12), "f6f0e4", bevel=0.05)
    for i, dx in enumerate((-0.79, 0.79)):
        box(n(f"tub_end{i}"), p(dx, 0.3, 0), (0.12, 0.6, 0.85), "f6f0e4", bevel=0.05)
    box(n("water"), p(0, 0.44, 0), (1.5, 0.05, 0.66), "7fc4e0", bevel=0.015, lump=0.004)
    for i, (dx, dz) in enumerate(((-0.45, 0.1), (0.05, -0.12), (0.4, 0.12))):
        ball(n(f"bubble{i}"), p(dx, 0.5, dz), 0.09, "ffffff", scale=(1, 0.7, 1), lump=0.01, seed=i)
    tube(n("tap"), p(0.7, 0.75, -0.3), 0.025, 0.3, "b8bdc4")
    box(n("spout"), p(0.62, 0.9, -0.3), (0.2, 0.04, 0.04), "b8bdc4", bevel=0.01)


def sofa_leather():
    at("sofa_leather")
    c, d = "7a4630", "5e3524"
    box(n("base"), p(0, 0.24, 0), (2.1, 0.3, 0.9), d, bevel=0.08)
    box(n("back"), p(0, 0.66, -0.36), (2.1, 0.62, 0.22), c, bevel=0.1)
    for i, dx in enumerate((-0.98, 0.98)):
        box(n(f"arm{i}"), p(dx, 0.52, 0.02), (0.26, 0.6, 0.9), c, bevel=0.12)
        ball(n(f"roll{i}"), p(dx, 0.82, 0.02), 0.15, c, scale=(1, 1, 3.0), seed=i)
    for i, dx in enumerate((-0.6, 0.0, 0.6)):
        box(n(f"seat{i}"), p(dx, 0.47, 0.08), (0.58, 0.18, 0.66), "8c5238", bevel=0.07, seed=i)
        for j, dy in enumerate((0.55, 0.78)):
            ball(n(f"button{i}_{j}"), p(dx, dy, -0.245), 0.025, d)


def bed_king():
    at("bed_king")
    box(n("frame"), p(0, 0.14, 0), (2.0, 0.26, 2.2), DARKWOOD, bevel=0.07)
    box(n("head"), p(0, 0.75, -1.08), (2.1, 1.1, 0.14), "8c6a9a", bevel=0.1)
    box(n("mat"), p(0, 0.4, 0), (1.9, 0.28, 2.1), CREAM, bevel=0.1)
    cloth(n("duvet"), p(0, 0.64, 0.3), (2.1, 0.1, 1.6), "c8b6dc", folds=0.025, droop=0.34)
    cloth(n("throw"), p(0, 0.72, 0.8), (2.15, 0.06, 0.45), "8c6a9a", folds=0.02, droop=0.36)
    for i, dx in enumerate((-0.6, 0.0, 0.6)):
        pillow(n(f"pillow{i}"), p(dx, 0.62, -0.78), (0.6, 0.22, 0.42), "fbf6ec", seed=i)


def tv_cinema():
    at("tv_cinema")
    box(n("unit"), p(0, 0.25, 0), (1.9, 0.5, 0.45), "3a3d42", bevel=0.04)
    for i, dx in enumerate((-0.45, 0.45)):
        box(n(f"door{i}"), p(dx, 0.25, 0.23), (0.85, 0.4, 0.02), "4a4e55", bevel=0.01)
    box(n("screen"), p(0, 1.15, -0.05), (1.8, 0.95, 0.07), "26282d", bevel=0.03)
    box(n("glass"), p(0, 1.15, -0.01), (1.68, 0.84, 0.02), "4a5868", bevel=0.01, subd=0, lump=0)
    for i, dx in enumerate((-1.2, 1.2)):
        box(n(f"speaker{i}"), p(dx, 0.6, 0), (0.32, 1.2, 0.32), "2f3136", bevel=0.05)
        tube(n(f"cone{i}a"), p(dx, 0.9, 0.17), 0.1, 0.03, "55595f", rot=(math.pi / 2, 0, 0))
        tube(n(f"cone{i}b"), p(dx, 0.45, 0.17), 0.12, 0.03, "55595f", rot=(math.pi / 2, 0, 0))
    box(n("soundbar"), p(0, 0.55, 0.1), (1.1, 0.1, 0.14), "2f3136", bevel=0.03)


def goldfish():
    at("goldfish")
    box(n("stand"), p(0, 0.35, 0), (0.5, 0.7, 0.4), WOOD, bevel=0.04)
    ball(n("water"), p(0, 0.92, 0), 0.24, "a9d6e8", scale=(1, 0.85, 1))
    tube(n("rim"), p(0, 1.1, 0), 0.17, 0.04, "d8eef5")
    ball(n("fish"), p(0.04, 0.93, 0.2), 0.07, "f08a2c", scale=(1.4, 0.9, 0.7))
    ball(n("fin"), p(-0.07, 0.93, 0.2), 0.045, "f5a24c", scale=(0.6, 1.2, 0.5))
    ball(n("gravel"), p(0, 0.72, 0), 0.17, "c9b48a", scale=(1, 0.3, 1))


def cat():
    at("cat")
    g, w = "e09a4c", "f6e2c8"
    ball(n("body"), p(0, 0.24, 0), 0.2, g, scale=(0.9, 1.2, 1.0))
    ball(n("chest"), p(0, 0.27, 0.12), 0.12, w, scale=(0.9, 1.3, 0.6))
    ball(n("head"), p(0, 0.56, 0.06), 0.15, g, scale=(1.1, 0.95, 1.0))
    ball(n("muzzle"), p(0, 0.52, 0.18), 0.06, w, scale=(1.3, 0.8, 0.7))
    ball(n("nose"), p(0, 0.55, 0.22), 0.018, "d86a6a")
    for i, dx in enumerate((-0.07, 0.07)):
        ball(n(f"ear{i}"), p(dx * 1.3, 0.7, 0.04), 0.06, g, scale=(0.7, 1.3, 0.35), seed=i)
        ball(n(f"eye{i}"), p(dx * 0.75, 0.59, 0.19), 0.022, "2b2f36")
        ball(n(f"paw{i}"), p(dx, 0.05, 0.16), 0.055, w, scale=(1, 0.7, 1.4))
    for i in range(14):
        a = i / 13.0
        ball(n(f"tail{i}"), p(0.17 + 0.07 * math.sin(a * 2.5), 0.05 + 0.1 * a, 0.05 - 0.2 * a + 0.3 * a * a), 0.042, g)


def dog():
    at("dog")
    b, d = "b07848", "7a4e2e"
    ball(n("body"), p(0, 0.42, -0.05), 0.2, b, scale=(1.0, 0.95, 1.8))
    ball(n("chest"), p(0, 0.44, 0.22), 0.16, "e8d2b0", scale=(1.0, 1.1, 0.7))
    ball(n("head"), p(0, 0.72, 0.36), 0.15, b)
    ball(n("snout"), p(0, 0.67, 0.5), 0.08, "e8d2b0", scale=(0.9, 0.8, 1.2))
    ball(n("nose"), p(0, 0.7, 0.59), 0.03, "2b2f36")
    for i, dx in enumerate((-0.13, 0.13)):
        ball(n(f"ear{i}"), p(dx, 0.68, 0.33), 0.07, d, scale=(0.5, 1.5, 0.9), seed=i)
        ball(n(f"eye{i}"), p(dx * 0.45, 0.76, 0.48), 0.022, "2b2f36")
    for i, (dx, dz) in enumerate(((-0.11, 0.2), (0.11, 0.2), (-0.11, -0.3), (0.11, -0.3))):
        tube(n(f"leg{i}"), p(dx, 0.17, dz), 0.055, 0.34, b)
        ball(n(f"foot{i}"), p(dx, 0.03, dz + 0.03), 0.065, "e8d2b0", scale=(1, 0.6, 1.3))
    for i in range(9):
        ball(n(f"tail{i}"), p(0, 0.5 + 0.027 * i, -0.4 - 0.018 * i), 0.045 - 0.002 * i, b)


def bake():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    scene.render.bake.target = "VERTEX_COLORS"
    box("temp_floor", (len(ITEMS) * SPACING / 2, -0.05, 0), (len(ITEMS) * SPACING + 4, 0.1, 6), "ffffff", bevel=0, subd=0, lump=0)
    obs = [o for o in scene.objects if o.type == "MESH"]
    for ob in obs:
        bpy.context.view_layer.objects.active = ob
        for m in list(ob.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
        if len(ob.data.vertices) > 1200:
            d = ob.modifiers.new("budget", "DECIMATE")
            d.ratio = 1200 / len(ob.data.vertices)
            bpy.ops.object.modifier_apply(modifier="budget")
        ob.data.shade_smooth()
        ob.data.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        ob.data.attributes.active_color = ob.data.color_attributes["Col"]
        ob.data.materials.append(bpy.data.materials.new(ob.name))
    props = [o for o in obs if o.name != "temp_floor"]
    bpy.ops.object.select_all(action="DESELECT")
    for ob in props:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = props[0]
    bpy.ops.object.bake(type="AO")
    for ob in props:
        c = R.hexc(ob["clay_color"])
        for d in ob.data.color_attributes["Col"].data:
            ao = 0.35 + 0.65 * d.color[0]
            d.color = (c[0] * ao, c[1] * ao, c[2] * ao, 1.0)
        ob.data.materials.clear()
    bpy.data.objects["temp_floor"].select_set(False)
    bpy.data.objects.remove(bpy.data.objects["temp_floor"], do_unlink=True)
    names = [o.name for o in props]
    for item, x in ITEMS.items():
        bpy.ops.object.select_all(action="DESELECT")
        parts = [bpy.data.objects[nm] for nm in names if nm.startswith(item + "__")]
        for o in parts:
            o.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]
        bpy.ops.object.join()
        joined = bpy.context.object
        joined.name = item
        bpy.context.scene.cursor.location = R.g2b(x, 0, 0)
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        joined.location = (0, 0, 0)


if __name__ == "__main__":
    OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for build in (plant, bookshelf, rug, sofa, tv, piano, mattress, desk, wardrobe, espresso, cooker, spa_bath,
                  sofa_leather, bed_king, tv_cinema, goldfish, cat, dog):
        build()
    bake()
    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_vertex_color="ACTIVE",
                              export_materials="NONE", export_texcoords=False)
    print("ITEMS", list(ITEMS))
