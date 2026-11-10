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

box, ball, tube, cloth = R.box, R.ball, R.tube, R.cloth
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
    ball(n("cushion"), p(0.55, 0.68, 0.0), 0.22, "e0b45a", scale=(1, 1, 0.45), lump=0.02)


def tv():
    at("tv")
    box(n("stand"), p(0, 0.25, 0), (1.2, 0.5, 0.42), WOOD, bevel=0.05)
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
    cloth(n("duvet"), p(0, 0.5, 0.25), (1.45, 0.1, 1.2), "9fb6d2", folds=0.03, droop=0.2)
    ball(n("pillow"), p(0, 0.55, -0.7), 0.3, "fbf6ec", scale=(1.4, 0.4, 0.8), lump=0.02)


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
    box(n("tub"), p(0, 0.3, 0), (1.7, 0.6, 0.85), "f6f0e4", bevel=0.18)
    box(n("water"), p(0, 0.56, 0), (1.4, 0.04, 0.6), "9fc7d8", bevel=0.02, lump=0.004)
    for i, dx in enumerate((-0.5, 0.0, 0.5)):
        ball(n(f"bubble{i}"), p(dx, 0.6, 0.05 * (i - 1)), 0.1, "ffffff", scale=(1, 0.7, 1), lump=0.01, seed=i)
    tube(n("tap"), p(0.7, 0.75, -0.3), 0.025, 0.3, "b8bdc4")
    box(n("spout"), p(0.62, 0.9, -0.3), (0.2, 0.04, 0.04), "b8bdc4", bevel=0.01)


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
    for build in (plant, bookshelf, rug, sofa, tv, piano, mattress, desk, wardrobe, espresso, cooker, spa_bath):
        build()
    bake()
    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_vertex_color="ACTIVE",
                              export_materials="NONE", export_texcoords=False)
    print("ITEMS", list(ITEMS))
