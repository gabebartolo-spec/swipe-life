"""Build the childhood home (GDD §10.6) as a clay dollhouse and export it for the Godot layer render.

Run headless:
  blender -b --factory-startup --python tools/blender/build_clay_house.py -- <out.glb>

Four rooms on one level in a 2x2 plan, seen in true isometric like the approved clay bedroom test:
bedroom at the back, bathroom right, living room left, kitchen at the front. Back walls are full
height; interior walls are cut low so every room shows. Props carry baked AO in their vertex colours.

Every object is named "<layer>__<prop>":
  shell      floors, walls, windows (always shown)
  base       living room, kitchen, bathroom furniture (always shown)
  bed_<band> bedroom for one age band: baby, child, teen (§10.8)
  act_<id>   props left by an activity, keyed by the action id in data/actions (§10.8)
Coordinates are Godot's (x, y up, z); the helpers convert to Blender.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_clay_room as R  # noqa: E402

S, M = 8.0, 4.0
WALL_H, LOW_H = 2.8, 0.7
WALL, CREAM, WOOD, DARKWOOD = "efe3cf", "f3ead8", "d9935a", "b8743f"
LAYERS = {}


box, ball, tube, cloth = R.box, R.ball, R.tube, R.cloth  # all take Godot (x, y up, z) coordinates


def layer(name):
    LAYERS[name] = set()
    layer.current = name


def tag():
    for ob in list(bpy.context.scene.objects):
        if ob.type == "MESH" and "__" not in ob.name:
            ob.name = f"{layer.current}__{ob.name}"
            LAYERS[layer.current].add(ob.name)


def shell():
    layer("shell")
    box("slab", (S / 2, -0.2, S / 2), (S + 0.3, 0.4, S + 0.3), "f6eddd", bevel=0.14)
    for i in range(8):
        box(f"bplank{i}", (2, 0.02, 0.25 + i * 0.5), (M, 0.06, 0.46), ["d9935a", "cf8650", "e09f66"][i % 3],
            bevel=0.025, seed=i)
        box(f"lplank{i}", (0.25 + i * 0.5, 0.02, 6), (0.46, 0.06, M), ["c98a55", "bf7f4a", "d29560"][i % 3],
            bevel=0.025, seed=i)
    for i in range(8):
        for j in range(8):
            box(f"btile{i}_{j}", (M + 0.25 + i * 0.5, 0.02, 0.25 + j * 0.5), (0.46, 0.05, 0.46),
                ["f6f1e8", "cfe3e6"][(i + j) % 2], bevel=0.02, subd=1, lump=0.004, seed=i * 9 + j)
            box(f"ktile{i}_{j}", (M + 0.25 + i * 0.5, 0.02, M + 0.25 + j * 0.5), (0.46, 0.05, 0.46),
                ["f3ead8", "e8c9a0"][(i + j) % 2], bevel=0.02, subd=1, lump=0.004, seed=i * 7 + j)
    box("wall_x", (-0.15, WALL_H / 2, S / 2), (0.3, WALL_H, S + 0.3), WALL, bevel=0.14)
    box("wall_z", (S / 2, WALL_H / 2, -0.15), (S + 0.3, WALL_H, 0.3), WALL, bevel=0.14)
    box("paper_bx", (0.01, 1.5, 2), (0.02, 2.5, 3.9), "e4ead7", bevel=0.01, subd=1, lump=0.004)
    box("paper_bz", (2, 1.5, 0.01), (3.9, 2.5, 0.02), "e4ead7", bevel=0.01, subd=1, lump=0.004)
    box("paper_tz", (6, 1.5, 0.01), (3.9, 2.5, 0.02), "dbeaf0", bevel=0.01, subd=1, lump=0.004)
    box("paper_lx", (0.01, 1.5, 6), (0.02, 2.5, 3.9), "f4e2c8", bevel=0.01, subd=1, lump=0.004)
    box("iwall_a", (M, LOW_H / 2, 1.2), (0.2, LOW_H, 2.4), WALL, bevel=0.08)
    box("iwall_b", (M, LOW_H / 2, 6.6), (0.2, LOW_H, 2.8), WALL, bevel=0.08)
    box("iwall_c", (1.2, LOW_H / 2, M), (2.4, LOW_H, 0.2), WALL, bevel=0.08)
    box("iwall_d", (6.6, LOW_H / 2, M), (2.8, LOW_H, 0.2), WALL, bevel=0.08)
    for n, z in (("wb", 1.6), ("wl", 6.2)):
        box(f"{n}_frame", (0.03, 1.6, z), (0.12, 1.26, 1.46), "fbf8f2", bevel=0.05)
        box(f"{n}_win_pane", (0.07, 1.6, z), (0.05, 1.1, 1.3), "fff3d6", bevel=0.01, subd=0, lump=0)
        box(f"{n}_sill", (0.15, 1.0, z), (0.3, 0.08, 1.6), "fbf8f2", bevel=0.03)
        for k, dz in (("a", -0.8), ("b", 0.8)):
            box(f"{n}_curtain_{k}", (0.12, 1.55, z + dz), (0.08, 1.6, 0.32), "f1e4cf", bevel=0.04, lump=0.02)
    box("wt_frame", (6.6, 1.9, 0.03), (1.06, 0.86, 0.12), "fbf8f2", bevel=0.05)
    box("wt_win_pane", (6.6, 1.9, 0.07), (0.9, 0.7, 0.05), "fff3d6", bevel=0.01, subd=0, lump=0)
    tag()


def base():
    layer("base")
    # living room
    box("rug_l", (2.2, 0.08, 6), (2.6, 0.04, 2.0), "d9a3a0", bevel=0.02, lump=0.004)
    box("sofa_base", (0.55, 0.3, 6), (0.85, 0.45, 2.0), "7f9fb8", bevel=0.14)
    box("sofa_back", (0.22, 0.75, 6), (0.25, 0.65, 2.0), "7f9fb8", bevel=0.12)
    for i, z in enumerate((4.95, 7.05)):
        box(f"sofa_arm{i}", (0.55, 0.52, z), (0.85, 0.5, 0.26), "6f8fa8", bevel=0.1)
    ball("cushion_a", (0.45, 0.74, 5.45), 0.22, "e0b45a", scale=(0.4, 0.9, 1))
    ball("cushion_b", (0.45, 0.74, 6.55), 0.22, "e8dccb", scale=(0.4, 0.9, 1), seed=2)
    box("coffee_top", (2.1, 0.45, 6), (0.9, 0.08, 1.3), WOOD, bevel=0.04)
    for i, (dx, dz) in enumerate(((-0.35, -0.55), (0.35, -0.55), (-0.35, 0.55), (0.35, 0.55))):
        tube(f"coffee_leg{i}", (2.1 + dx, 0.22, 6 + dz), 0.04, 0.42, DARKWOOD)
    tube("mug", (2.0, 0.56, 5.8), 0.07, 0.14, "f4efe6")
    box("tv_unit", (3.55, 0.25, 6), (0.5, 0.5, 1.6), DARKWOOD, bevel=0.05)
    box("tv", (3.55, 0.95, 6), (0.08, 0.7, 1.15), "4a4d55", bevel=0.04)
    tube("pot_l", (0.4, 0.25, 7.6), 0.22, 0.5, "c8693f")
    for i, o in enumerate([(0, 0.75, 0), (0.15, 0.62, 0.08), (-0.14, 0.65, -0.06), (0.04, 0.95, 0.1)]):
        ball(f"leaf_l{i}", (0.4 + o[0], o[1], 7.6 + o[2]), 0.2, "6f9e57", scale=(1, 0.6, 1), seed=i)
    # kitchen
    box("counter", (5.9, 0.45, 4.45), (2.6, 0.9, 0.6), CREAM, bevel=0.05)
    box("counter_top", (5.9, 0.93, 4.45), (2.7, 0.08, 0.66), "a9b0a2", bevel=0.03)
    box("stove", (6.4, 0.98, 4.45), (0.6, 0.03, 0.5), "4a4d55", bevel=0.01)
    tube("pan", (6.3, 1.1, 4.45), 0.15, 0.22, "c45c4a")
    tube("kettle", (5.1, 1.08, 4.4), 0.11, 0.22, "e0b45a")
    box("fridge", (7.55, 0.9, 4.5), (0.7, 1.8, 0.7), "fbf8f2", bevel=0.08)
    tube("table_top", (6, 0.72, 6.3), 0.62, 0.07, WOOD)
    tube("table_leg", (6, 0.36, 6.3), 0.07, 0.7, DARKWOOD)
    for i, (dx, dz) in enumerate(((-0.85, 0), (0.85, 0), (0, 0.85))):
        box(f"chair{i}", (6 + dx, 0.45, 6.3 + dz), (0.42, 0.08, 0.42), CREAM, bevel=0.04)
        tube(f"chair_leg{i}", (6 + dx, 0.22, 6.3 + dz), 0.04, 0.44, DARKWOOD)
    for i, col in enumerate(("e0a24a", "c45c4a", "7fae6a")):
        ball(f"fruit{i}", (5.9 + i * 0.1, 0.84, 6.3), 0.075, col, lump=0, seed=i)
    # bathroom
    box("tub", (7.2, 0.32, 1.1), (1.3, 0.6, 2.0), "fbf8f2", bevel=0.18)
    box("tub_water", (7.2, 0.64, 1.1), (1.05, 0.06, 1.75), "a9d0e0", bevel=0.05, subd=1, lump=0)
    ball("duck", (7.0, 0.74, 1.4), 0.08, "f3d36b", lump=0)
    box("sink", (5.2, 0.85, 0.3), (0.7, 0.2, 0.5), "fbf8f2", bevel=0.08)
    tube("sink_ped", (5.2, 0.4, 0.25), 0.11, 0.75, "fbf8f2")
    box("mirror", (5.2, 1.65, 0.05), (0.6, 0.75, 0.05), "cfe3ea", bevel=0.03)
    box("toilet", (6.1, 0.22, 0.42), (0.42, 0.44, 0.52), "fbf8f2", bevel=0.12)
    box("toilet_tank", (6.1, 0.7, 0.15), (0.5, 0.5, 0.2), "fbf8f2", bevel=0.08)
    box("bath_mat", (6.3, 0.07, 1.8), (0.9, 0.04, 0.6), "a9c2a2", bevel=0.02)
    box("towel", (4.6, 1.0, 0.08), (0.5, 0.45, 0.05), "e58f5a", bevel=0.03, lump=0.02)
    tag()


def fairy(band):
    for i in range(12):
        y = 2.45 - 0.18 * math.sin(math.pi * (i % 6) / 6)
        ball(f"fairy_{band}{i}", (0.6 + i * 0.28, y, 0.08), 0.05, "ffc860", lump=0, seed=i)


def bedrooms():
    layer("bed_baby")
    fairy("baby")
    box("crib_base", (1.2, 0.45, 0.7), (1.4, 0.12, 0.85), CREAM, bevel=0.04)
    box("crib_mattress", (1.2, 0.56, 0.7), (1.28, 0.12, 0.72), "cfe0ea", bevel=0.06)
    for i in range(9):
        for z in (0.32, 1.08):
            tube(f"slat{i}_{z}", (0.56 + i * 0.16, 0.72, z), 0.025, 0.65, CREAM)
    for z in (0.32, 1.08):
        box(f"rail{z}", (1.2, 1.06, z), (1.42, 0.06, 0.06), CREAM, bevel=0.025)
    ball("teddy_body", (2.9, 0.3, 2.0), 0.21, "c98a55", scale=(1, 1.1, 0.9))
    ball("teddy_head", (2.9, 0.62, 2.02), 0.15, "c98a55")
    for i, dx in enumerate((-0.11, 0.11)):
        ball(f"teddy_ear{i}", (2.9 + dx, 0.75, 2.0), 0.055, "a8703f", lump=0)
    ball("teddy_snout", (2.9, 0.59, 2.16), 0.06, "e6c49a", lump=0)
    for i, col in enumerate(("c45c4a", "e0b45a", "5c7a5a", "4e6a8a")):
        box(f"block{i}", (2.1 + (i % 2) * 0.24, 0.2 + (i // 2) * 0.2, 2.5), (0.2, 0.2, 0.2), col, bevel=0.03)
    box("changer", (0.35, 0.45, 3.1), (0.6, 0.9, 1.0), "fbf6ec", bevel=0.06)
    tag()
    layer("bed_child")
    fairy("child")
    box("kid_bed", (0.85, 0.25, 1.1), (1.3, 0.38, 1.9), "e58f5a", bevel=0.09)
    box("kid_duvet", (0.88, 0.48, 1.35), (1.36, 0.1, 1.3), "f3d36b", bevel=0.05, lump=0.02)
    ball("kid_pillow", (0.85, 0.52, 0.5), 0.26, "fbf6ec", scale=(1.2, 0.4, 0.7))
    box("toy_box", (2.9, 0.28, 0.4), (0.9, 0.55, 0.55), "5c7a5a", bevel=0.07)
    ball("toy_ball", (2.65, 0.75, 0.4), 0.14, "c45c4a", lump=0)
    box("shelf_c", (2.0, 1.55, 0.18), (1.2, 0.07, 0.34), WOOD, bevel=0.03)
    for i, col in enumerate(("c45c4a", "e0b45a", "4e6a8a", "7fae6a")):
        box(f"picbook{i}", (1.6 + i * 0.22, 1.75, 0.18), (0.18, 0.34, 0.28), col, bevel=0.025)
    tag()
    layer("bed_teen")
    fairy("teen")
    box("teen_bed", (1.0, 0.3, 1.3), (1.7, 0.42, 2.3), DARKWOOD, bevel=0.09)
    box("teen_mattress", (1.0, 0.58, 1.32), (1.58, 0.26, 2.15), CREAM, bevel=0.1)
    box("teen_duvet", (1.05, 0.76, 1.65), (1.72, 0.12, 1.5), "9fb6d2", bevel=0.06, lump=0.02)
    box("desk_top", (3.0, 1.0, 0.45), (1.5, 0.08, 0.75), WOOD, bevel=0.04)
    box("desk_drawers", (3.5, 0.5, 0.45), (0.5, 0.95, 0.7), "c98a55", bevel=0.05)
    box("laptop", (2.9, 1.07, 0.5), (0.6, 0.04, 0.4), "c4c7cc", bevel=0.02)
    box("laptop_lid", (2.9, 1.28, 0.3), (0.6, 0.4, 0.04), "9fa4ab", bevel=0.02)
    ball("lamp_glow_t", (3.5, 1.52, 0.35), 0.12, "fff0cc", scale=(1, 0.75, 1))
    box("poster_t", (0.03, 1.75, 3.1), (0.04, 0.85, 0.65), "4e6a8a", bevel=0.02)
    box("backpack", (1.9, 0.33, 2.9), (0.48, 0.62, 0.32), "b88a5a", bevel=0.15)
    tag()


def activities():
    layer("act_club")
    ball("club_ball", (3.0, 0.2, 7.3), 0.2, "f3ead8", lump=0.01)
    tag()
    layer("act_study")
    for i, col in enumerate(("4e6a8a", "c45c4a", "e0b45a")):
        box(f"study_book{i}", (5.7, 0.8 + i * 0.07, 6.6), (0.42 - i * 0.03, 0.06, 0.32), col, bevel=0.02)
    tag()
    layer("act_play_toys")
    for i, col in enumerate(("c45c4a", "4e6a8a", "e0b45a")):
        box(f"train{i}", (2.6, 0.2, 5.3 + i * 0.36), (0.22, 0.22, 0.32), col, bevel=0.05)
    tag()


def bake_groups():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    scene.render.bake.target = "VERTEX_COLORS"
    obs = {o.name: o for o in scene.objects if o.type == "MESH"}
    for ob in obs.values():
        bpy.context.view_layer.objects.active = ob
        for m in list(ob.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
        if len(ob.data.vertices) > 1500:  # mobile budget: room GLB under ~7 MB
            d = ob.modifiers.new("budget", "DECIMATE")
            d.ratio = 1500 / len(ob.data.vertices)
            bpy.ops.object.modifier_apply(modifier="budget")
        ob.data.shade_smooth()
        ob.data.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        ob.data.attributes.active_color = ob.data.color_attributes["Col"]
        ob.data.materials.append(bpy.data.materials.new(ob.name))
    fixed = LAYERS["shell"] | LAYERS["base"]
    for name, members in [("fixed", fixed)] + [(n, m) for n, m in LAYERS.items() if n not in ("shell", "base")]:
        bpy.ops.object.select_all(action="DESELECT")
        for n, ob in obs.items():
            ob.hide_render = n not in members and n not in fixed
            ob.select_set(n in members)
        bpy.context.view_layer.objects.active = obs[next(iter(members))]
        bpy.ops.object.bake(type="AO")
    for ob in obs.values():
        ob.hide_render = False
        c = R.hexc(ob["clay_color"]) if "clay_color" in ob else (0.8, 0.8, 0.8)
        for d in ob.data.color_attributes["Col"].data:
            ao = 0.35 + 0.65 * d.color[0]
            d.color = (c[0] * ao, c[1] * ao, c[2] * ao, 1.0)
        ob.data.materials.clear()


if __name__ == "__main__":
    OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    shell()
    base()
    bedrooms()
    activities()
    bake_groups()
    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_vertex_color="ACTIVE",
                              export_materials="NONE", export_texcoords=False)
    print("HOUSE", {k: len(v) for k, v in LAYERS.items()})
