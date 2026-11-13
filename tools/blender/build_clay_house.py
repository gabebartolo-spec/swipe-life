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


box, ball, tube, cloth, pillow = R.box, R.ball, R.tube, R.cloth, R.pillow  # all take Godot (x, y up, z) coordinates


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
        tube(f"{n}_rod", (0.16, 2.38, z), 0.03, 2.0, "8a6a55", rot=(math.radians(90), 0, 0))
        box(f"{n}_bar_v", (0.1, 1.6, z), (0.04, 1.1, 0.05), "fbf8f2", bevel=0.015)
        box(f"{n}_bar_h", (0.1, 1.6, z), (0.04, 0.05, 1.3), "fbf8f2", bevel=0.015)
        tube(f"{n}_sillpot", (0.18, 1.1, z + 0.35), 0.07, 0.13, "c8693f")
        ball(f"{n}_sillleaf", (0.18, 1.24, z + 0.35), 0.1, "7fae6a", scale=(1, 0.8, 1))
    box("wt_frame", (6.6, 1.9, 0.03), (1.06, 0.86, 0.12), "fbf8f2", bevel=0.05)
    box("wt_win_pane", (6.6, 1.9, 0.07), (0.9, 0.7, 0.05), "fff3d6", bevel=0.01, subd=0, lump=0)
    tag()


def chair(n, x, z, face, col=CREAM):
    """Kitchen chair; face = direction the sitter looks, as (dx, dz)."""
    box(f"{n}_seat", (x, 0.46, z), (0.44, 0.07, 0.44), col, bevel=0.04)
    box(f"{n}_back", (x - face[0] * 0.2, 0.75, z - face[1] * 0.2),
        (0.44 if face[0] == 0 else 0.07, 0.5, 0.07 if face[0] == 0 else 0.44), col, bevel=0.04)
    for i, (dx, dz) in enumerate(((-0.17, -0.17), (0.17, -0.17), (-0.17, 0.17), (0.17, 0.17))):
        tube(f"{n}_leg{i}", (x + dx, 0.22, z + dz), 0.03, 0.44, DARKWOOD)


def media_unit(cx, cz, w, h, wood, dark, tv, d=0.46):
    """Open TV unit on the +x wall, facing the sofa: a docked Switch in one cubby, DVD cases in the other.
    No back panel: the game camera looks in from behind. `dark` is unused, kept for the callers.
    Same build as the shop TV (build_clay_items.tv). tv = (x, y, thick, height, width, colour)."""
    t = dict(bevel=0.012, subd=1, lump=0.002)
    f = dict(bevel=0.025, subd=1, lump=0.004)
    k = w / 1.2
    box("tv_unit_top", (cx, h - 0.025, cz), (d, 0.05, w), wood, **f)
    box("tv_unit_base", (cx, 0.025, cz), (d, 0.05, w), wood, **f)
    for i, dz in enumerate((-w / 2 + 0.025, w / 2 - 0.025)):
        box(f"tv_unit_side{i}", (cx, h / 2, cz + dz), (d, h, 0.05), wood, **f)
    box("tv_unit_divider", (cx, h / 2, cz + 0.15 * k), (d - 0.02, h - 0.1, 0.04), wood, **t)
    sz = cz - 0.2 * k
    box("tv_dock_back", (cx + 0.1, 0.11, sz), (0.04, 0.12, 0.32), "e8e8ea", **t)
    box("tv_dock_base", (cx + 0.02, 0.08, sz), (0.16, 0.06, 0.34), "e8e8ea", **t)
    box("tv_switch", (cx + 0.06, 0.185, sz), (0.03, 0.14, 0.24), "2b2f36", **t)
    box("tv_joycon_l", (cx + 0.06, 0.185, sz - 0.14), (0.03, 0.14, 0.04), "e8474c", **t)
    box("tv_joycon_r", (cx + 0.06, 0.185, sz + 0.14), (0.03, 0.14, 0.04), "3aa6e8", **t)
    box("tv_switch_screen", (cx + 0.04, 0.19, sz), (0.005, 0.11, 0.2), "55606a", bevel=0.003, subd=0, lump=0)
    cases = ("e8474c", "f3ead8", "3aa6e8", "f0c24a", "3c3f46", "6fb36f", "e8e8ea", "9b6fd0")
    z0 = cz + 0.15 * k + 0.06
    for i in range(int((cz + w / 2 - 0.07 - z0) / 0.044)):
        box(f"tv_dvd{i}", (cx - 0.02, 0.155, z0 + i * 0.044), (0.14, 0.19, 0.036), cases[i % len(cases)], **t)
    x, y, thick, th, tw, col = tv
    box("tv_neck", (x, (h + y - th / 2) / 2, cz), (0.1, y - th / 2 - h + 0.04, 0.18), "3a3d42", bevel=0.02)
    box("tv", (x, y, cz), (thick, th, tw), col, bevel=0.03)
    box("tv_glass", (x - thick / 2 - 0.004, y, cz), (0.02, th - 0.1, tw - 0.11), "55606a", bevel=0.01, subd=0, lump=0)


def books(n, x, y, z, count, along_x=True, seed=0):
    cols = ("c45c4a", "e0b45a", "4e6a8a", "7fae6a", "8a5a7a", "e58f5a", "5c7a5a")
    for i in range(count):
        h = 0.26 + 0.06 * ((i * 7 + seed) % 3)
        c = (x + i * 0.11, y + h / 2, z) if along_x else (x, y + h / 2, z + i * 0.11)
        s = (0.09, h, 0.24) if along_x else (0.24, h, 0.09)
        box(f"{n}{i}", c, s, cols[(i + seed) % len(cols)], bevel=0.02, seed=i)


def plant(n, x, z, r=0.2, pot="c8693f", h=0.42):
    tube(f"{n}_pot", (x, h / 2, z), r, h, pot)
    for i, (dx, dy, dz) in enumerate(((0, 0.3, 0), (0.16, 0.18, 0.06), (-0.15, 0.2, -0.05), (0.05, 0.42, 0.1),
                                      (-0.08, 0.36, 0.14), (0.1, 0.3, -0.14))):
        ball(f"{n}_leaf{i}", (x + dx, h + dy * r / 0.2, z + dz * r / 0.2), r * 0.95,
             "6f9e57" if i % 2 else "7fae6a", scale=(1, 0.6, 1), seed=i)


def base():
    layer("base")
    # ---- living room (x 0..4, z 4..8)
    cloth("rug_l", (2.0, 0.07, 6.1), (2.6, 0.04, 2.3), "d9a3a0", folds=0.004)
    cloth("rug_l_in", (2.0, 0.09, 6.1), (2.1, 0.03, 1.8), "ecc6b8", folds=0.004)
    box("sofa_base", (0.55, 0.28, 6.1), (0.9, 0.42, 2.1), "7f9fb8", bevel=0.14)
    for i, z in enumerate((5.6, 6.6)):
        box(f"sofa_seat{i}", (0.62, 0.55, z), (0.78, 0.18, 0.98), "8fb0c8", bevel=0.09)
    box("sofa_back", (0.22, 0.8, 6.1), (0.28, 0.75, 2.1), "7f9fb8", bevel=0.13)
    for i, z in enumerate((4.98, 7.22)):
        box(f"sofa_arm{i}", (0.55, 0.55, z), (0.9, 0.55, 0.26), "6f8fa8", bevel=0.11)
    pillow("cushion_a", (0.42, 0.85, 5.5), (0.18, 0.42, 0.46), "e0b45a")
    pillow("cushion_b", (0.42, 0.85, 6.7), (0.18, 0.42, 0.46), "e8dccb", seed=2)
    cloth("throw", (0.75, 0.66, 6.85), (0.6, 0.05, 0.7), "c45c4a", folds=0.03, droop=0.1)
    box("coffee_top", (2.0, 0.42, 6.1), (0.85, 0.08, 1.3), WOOD, bevel=0.04)
    box("coffee_shelf", (2.0, 0.14, 6.1), (0.75, 0.05, 1.2), DARKWOOD, bevel=0.02)
    for i, (dx, dz) in enumerate(((-0.35, -0.55), (0.35, -0.55), (-0.35, 0.55), (0.35, 0.55))):
        tube(f"coffee_leg{i}", (2.0 + dx, 0.21, 6.1 + dz), 0.04, 0.42, DARKWOOD)
    tube("mug", (1.9, 0.53, 5.75), 0.07, 0.14, "f4efe6")
    box("magazine", (2.1, 0.47, 6.35), (0.38, 0.02, 0.3), "4e6a8a", bevel=0.01)
    media_unit(3.55, 6.1, 1.7, 0.54, WOOD, DARKWOOD, (3.6, 0.92, 0.1, 0.64, 1.05, "3a3d42"))
    books("tv_books", 3.5, 0.54, 6.75, 3, along_x=False)
    tube("speaker", (3.55, 0.7, 5.45), 0.08, 0.32, "4a4d55")
    box("low_shelf", (1.3, 0.3, 4.35), (2.0, 0.6, 0.38), WOOD, bevel=0.05)
    books("shelf_books", 0.5, 0.6, 4.35, 7)
    plant("plant_shelf", 1.85, 4.35, r=0.12, h=0.25)
    tube("lamp_pole", (0.35, 0.8, 7.6), 0.025, 1.6, "8a6a55")
    tube("lamp_base", (0.35, 0.03, 7.6), 0.18, 0.05, "8a6a55")
    tube("lamp_glow_shade", (0.35, 1.62, 7.6), 0.22, 0.3, "fff0cc")
    plant("plant_l", 3.5, 7.5, r=0.22, h=0.45)
    box("frame_l", (0.03, 1.85, 5.2), (0.05, 0.55, 0.45), "f6efe2", bevel=0.02)
    box("frame_l_art", (0.06, 1.85, 5.2), (0.03, 0.42, 0.33), "7fae6a", bevel=0.015)
    box("frame_l2", (0.03, 1.75, 7.2), (0.05, 0.42, 0.55), "f6efe2", bevel=0.02)
    box("frame_l2_art", (0.06, 1.75, 7.2), (0.03, 0.3, 0.43), "e0a24a", bevel=0.015)
    # ---- kitchen (x 4..8, z 4..8)
    box("counter", (5.85, 0.45, 4.45), (2.5, 0.9, 0.6), CREAM, bevel=0.05)
    box("counter_top", (5.85, 0.93, 4.45), (2.6, 0.08, 0.66), "a9b0a2", bevel=0.03)
    for i in range(4):
        box(f"cab_door{i}", (4.95 + i * 0.6, 0.45, 4.76), (0.54, 0.72, 0.03), "ead9bd", bevel=0.02)
        box(f"cab_knob{i}", (5.15 + i * 0.6, 0.65, 4.79), (0.06, 0.06, 0.04), "8a6a55", bevel=0.02)
    box("stove", (6.4, 0.98, 4.45), (0.62, 0.03, 0.52), "4a4d55", bevel=0.01)
    tube("pan", (6.3, 1.1, 4.45), 0.16, 0.22, "c45c4a")
    tube("pan_lid", (6.3, 1.23, 4.45), 0.17, 0.04, "a9b0a2")
    tube("kettle", (5.05, 1.08, 4.4), 0.11, 0.22, "e0b45a")
    tube("jar_a", (5.45, 1.05, 4.3), 0.07, 0.18, "f4efe6")
    tube("jar_b", (5.62, 1.03, 4.3), 0.06, 0.14, "e8c9a0")
    box("board", (5.9, 0.98, 4.5), (0.42, 0.03, 0.3), WOOD, bevel=0.01)
    box("fridge", (7.55, 0.95, 4.5), (0.72, 1.9, 0.72), "fbf8f2", bevel=0.1)
    box("fridge_split", (7.55, 1.3, 4.87), (0.68, 0.02, 0.02), "d8dde0", bevel=0.01)
    box("fridge_handle", (7.3, 1.55, 4.88), (0.05, 0.38, 0.05), "a9b0a2", bevel=0.02)
    ball("magnet_a", (7.65, 1.7, 4.87), 0.05, "c45c4a", scale=(1, 1, 0.4), lump=0)
    box("note", (7.75, 1.5, 4.87), (0.16, 0.2, 0.01), "f3d36b", bevel=0.005)
    box("dresser", (7.65, 0.45, 6.4), (0.55, 0.9, 1.5), "9fb6a2", bevel=0.06)
    box("dresser_top", (7.65, 0.93, 6.4), (0.62, 0.06, 1.58), WOOD, bevel=0.03)
    for i in range(3):
        ball(f"plate{i}", (7.6, 1.15, 5.95 + i * 0.35), 0.15, ("f4efe6", "cfe3e6", "f3d36b")[i],
             scale=(0.25, 1, 1), lump=0)
    plant("plant_k", 7.6, 7.55, r=0.2, h=0.4)
    cloth("rug_k", (5.6, 0.07, 6.3), (2.0, 0.03, 2.0), "e0b45a", folds=0.004)
    tube("table_top", (5.6, 0.74, 6.3), 0.7, 0.07, WOOD)
    tube("table_leg", (5.6, 0.37, 6.3), 0.08, 0.7, DARKWOOD)
    tube("table_foot", (5.6, 0.04, 6.3), 0.32, 0.06, DARKWOOD)
    chair("chair_w", 4.75, 6.3, (1, 0))
    chair("chair_n", 5.6, 5.45, (0, 1))
    chair("chair_e", 6.45, 6.3, (-1, 0))
    ball("fruit_bowl", (5.45, 0.82, 6.15), 0.2, "f4efe6", scale=(1, 0.4, 1))
    for i, col in enumerate(("e0a24a", "c45c4a", "7fae6a")):
        ball(f"fruit{i}", (5.35 + i * 0.1, 0.9, 6.15 + (i - 1) * 0.05), 0.075, col, lump=0, seed=i)
    # ---- bathroom (x 4..8, z 0..4)
    box("tub", (7.2, 0.33, 1.15), (1.3, 0.62, 2.0), "fbf8f2", bevel=0.18)
    box("tub_water", (7.2, 0.66, 1.15), (1.02, 0.05, 1.7), "a9d0e0", bevel=0.05, subd=1, lump=0)
    ball("duck", (7.0, 0.75, 1.45), 0.09, "f3d36b", scale=(1.2, 0.9, 1), lump=0)
    ball("foam_a", (7.4, 0.72, 0.8), 0.14, "fbf8f2", scale=(1, 0.4, 1))
    ball("foam_b", (7.25, 0.72, 0.6), 0.11, "fbf8f2", scale=(1, 0.4, 1), seed=2)
    tube("tub_tap", (7.2, 0.85, 0.15), 0.04, 0.25, "a9b0a2")
    box("sink", (5.0, 0.86, 0.32), (0.72, 0.18, 0.52), "fbf8f2", bevel=0.08)
    tube("sink_ped", (5.0, 0.4, 0.25), 0.11, 0.78, "fbf8f2")
    tube("tap", (5.0, 1.03, 0.12), 0.03, 0.16, "a9b0a2")
    tube("soap", (5.25, 1.0, 0.2), 0.04, 0.1, "e58f5a")
    box("mirror_frame", (5.0, 1.68, 0.04), (0.66, 0.82, 0.05), WOOD, bevel=0.03)
    box("mirror", (5.0, 1.68, 0.07), (0.52, 0.68, 0.03), "cfe3ea", bevel=0.015, subd=1, lump=0)
    tube("toilet_bowl", (6.0, 0.22, 0.5), 0.22, 0.42, "fbf8f2")
    tube("toilet_seat", (6.0, 0.45, 0.5), 0.24, 0.05, "e6eef0")
    box("toilet_tank", (6.0, 0.72, 0.17), (0.5, 0.5, 0.22), "fbf8f2", bevel=0.08)
    box("bath_shelf", (6.0, 1.45, 0.12), (0.7, 0.05, 0.22), WOOD, bevel=0.02)
    for i, col in enumerate(("e58f5a", "9fb6d2", "7fae6a")):
        tube(f"bottle{i}", (5.8 + i * 0.2, 1.56, 0.12), 0.045, 0.18, col)
    cloth("bath_mat", (6.1, 0.06, 1.7), (1.0, 0.04, 0.65), "a9c2a2", folds=0.006)
    tube("towel_rail", (4.2, 1.15, 1.6), 0.02, 0.8, "a9b0a2", rot=(math.radians(90), 0, 0))
    box("towel", (4.22, 0.95, 1.6), (0.05, 0.42, 0.6), "e58f5a", bevel=0.03, lump=0.02)
    tube("basket", (4.5, 0.25, 3.45), 0.22, 0.5, "d9b98a")
    cloth("basket_clothes", (4.5, 0.53, 3.45), (0.38, 0.06, 0.38), "9fb6d2", folds=0.03)
    plant("plant_b", 7.55, 3.5, r=0.16, h=0.34)
    tag()


def fairy(band):
    for i in range(12):
        y = 2.45 - 0.18 * math.sin(math.pi * (i % 6) / 6)
        ball(f"fairy_{band}{i}", (0.6 + i * 0.28, y, 0.08), 0.05, "ffc860", lump=0, seed=i)
    cloth(f"rug_{band}", (2.2, 0.07, 2.3), (2.0, 0.04, 1.6), "e6c0b4", folds=0.004)
    cloth(f"rug_{band}_in", (2.2, 0.09, 2.3), (1.6, 0.03, 1.2), "f1d8cc", folds=0.004)


def bedrooms():
    layer("bed_baby")
    fairy("baby")
    box("crib_base", (1.2, 0.42, 0.75), (1.45, 0.12, 0.88), CREAM, bevel=0.04)
    box("crib_mattress", (1.2, 0.54, 0.75), (1.32, 0.12, 0.76), "cfe0ea", bevel=0.06)
    cloth("crib_blanket", (1.4, 0.63, 0.8), (0.75, 0.05, 0.66), "f3d36b", folds=0.02)
    pillow("crib_pillow", (0.75, 0.65, 0.75), (0.26, 0.13, 0.38), "fbf6ec")
    for i in range(9):
        for z in (0.33, 1.17):
            tube(f"slat{i}_{z}", (0.58 + i * 0.155, 0.75, z), 0.025, 0.62, CREAM)
    for z in (0.33, 1.17):
        box(f"rail{z}", (1.2, 1.07, z), (1.45, 0.06, 0.06), CREAM, bevel=0.025)
    for i, x in enumerate((0.47, 1.93)):
        box(f"crib_end{i}", (x, 0.62, 0.75), (0.08, 1.1, 0.9), CREAM, bevel=0.035)
    tube("mobile_arm", (1.93, 1.45, 0.75), 0.02, 0.6, CREAM)
    tube("mobile_rod", (1.6, 1.75, 0.75), 0.015, 0.7, "8a6a55", rot=(0, math.radians(90), 0))
    for i, col in enumerate(("f3d36b", "e58f5a", "9fb6d2")):
        ball(f"mobile_{i}", (1.35 + i * 0.2, 1.58, 0.75), 0.08, col, lump=0)
    ball("teddy_body", (2.9, 0.3, 2.0), 0.21, "c98a55", scale=(1, 1.1, 0.9))
    ball("teddy_head", (2.9, 0.62, 2.02), 0.15, "c98a55")
    for i, dx in enumerate((-0.11, 0.11)):
        ball(f"teddy_ear{i}", (2.9 + dx, 0.75, 2.0), 0.055, "a8703f", lump=0)
    ball("teddy_snout", (2.9, 0.59, 2.16), 0.06, "e6c49a", lump=0)
    for i, col in enumerate(("c45c4a", "e0b45a", "5c7a5a", "4e6a8a")):
        box(f"block{i}", (2.0 + (i % 2) * 0.24, 0.2 + (i // 2) * 0.2, 2.5), (0.2, 0.2, 0.2), col, bevel=0.03)
    box("changer", (0.35, 0.45, 3.1), (0.6, 0.9, 1.0), "fbf6ec", bevel=0.06)
    box("changer_pad", (0.35, 0.95, 3.1), (0.52, 0.08, 0.85), "cfe0ea", bevel=0.04)
    box("nappies", (0.35, 1.06, 3.45), (0.3, 0.14, 0.2), "fbf8f2", bevel=0.04)
    tube("bottle", (0.32, 1.09, 2.8), 0.04, 0.2, "f6f1e8")
    box("chair_rock", (3.0, 0.35, 0.7), (0.7, 0.2, 0.7), "e8dccb", bevel=0.08)
    box("chair_rock_back", (3.0, 0.75, 0.38), (0.7, 0.7, 0.14), "e8dccb", bevel=0.08)
    ball("chair_rock_cush", (3.0, 0.5, 0.7), 0.26, "e0b45a", scale=(1, 0.3, 1))
    tag()
    layer("bed_child")
    fairy("child")
    box("kid_bed", (0.85, 0.24, 1.15), (1.3, 0.36, 2.0), "e58f5a", bevel=0.09)
    box("kid_head", (0.85, 0.62, 0.2), (1.3, 0.75, 0.14), "e58f5a", bevel=0.07)
    box("kid_mattress", (0.85, 0.47, 1.17), (1.2, 0.18, 1.85), CREAM, bevel=0.07)
    cloth("kid_duvet", (0.88, 0.6, 1.45), (1.32, 0.09, 1.25), "f3d36b", folds=0.03, droop=0.18)
    pillow("kid_pillow", (0.85, 0.645, 0.5), (0.62, 0.21, 0.36), "fbf6ec")
    ball("plush", (1.15, 0.75, 0.62), 0.13, "9fb6d2")
    box("toy_box", (2.9, 0.28, 0.4), (0.9, 0.55, 0.55), "5c7a5a", bevel=0.07)
    box("toy_box_lid", (2.9, 0.58, 0.35), (0.95, 0.06, 0.6), "6f8f6a", bevel=0.03)
    ball("toy_ball", (2.65, 0.75, 0.4), 0.14, "c45c4a", lump=0)
    box("toy_car", (2.3, 0.15, 2.7), (0.4, 0.18, 0.22), "4e6a8a", bevel=0.06)
    box("shelf_c", (2.0, 1.55, 0.18), (1.2, 0.07, 0.34), WOOD, bevel=0.03)
    books("picbook", 1.55, 1.59, 0.18, 7)
    box("drawing", (3.25, 1.55, 0.03), (0.5, 0.4, 0.03), "fbf8f2", bevel=0.01)
    ball("drawing_sun", (3.15, 1.6, 0.06), 0.08, "f3d36b", scale=(1, 1, 0.3), lump=0)
    box("kid_desk", (0.35, 0.3, 3.1), (0.55, 0.6, 0.9), "9fb6d2", bevel=0.05)
    box("crayons", (0.38, 0.63, 3.0), (0.25, 0.05, 0.15), "e0b45a", bevel=0.02)
    tag()
    layer("bed_teen")
    fairy("teen")
    box("teen_bed", (1.0, 0.28, 1.3), (1.7, 0.4, 2.3), DARKWOOD, bevel=0.09)
    box("teen_head", (1.0, 0.82, 0.2), (1.7, 1.15, 0.14), DARKWOOD, bevel=0.08)
    box("teen_mattress", (1.0, 0.56, 1.32), (1.58, 0.24, 2.15), CREAM, bevel=0.1)
    cloth("teen_duvet", (1.05, 0.73, 1.7), (1.72, 0.11, 1.45), "9fb6d2", folds=0.035, droop=0.25)
    pillow("teen_pillow_a", (0.65, 0.77, 0.55), (0.6, 0.22, 0.42), "fbf6ec")
    pillow("teen_pillow_b", (1.35, 0.77, 0.58), (0.6, 0.22, 0.42), "a9c2a2", seed=1)
    box("desk_top", (3.0, 1.0, 0.45), (1.5, 0.08, 0.75), WOOD, bevel=0.04)
    box("desk_drawers", (3.5, 0.5, 0.45), (0.5, 0.95, 0.7), "c98a55", bevel=0.05)
    for i, z in enumerate((0.2, 0.7)):
        tube(f"desk_leg{i}", (2.35, 0.5, z), 0.04, 0.95, DARKWOOD)
    box("laptop", (2.9, 1.06, 0.5), (0.6, 0.04, 0.4), "c4c7cc", bevel=0.02)
    box("laptop_lid", (2.9, 1.27, 0.3), (0.6, 0.4, 0.04), "9fa4ab", bevel=0.02)
    box("laptop_glow_screen", (2.9, 1.27, 0.33), (0.52, 0.32, 0.02), "dfe8f0", bevel=0.01, subd=1, lump=0)
    tube("lamp_stem_t", (3.55, 1.3, 0.3), 0.02, 0.45, CREAM)
    ball("lamp_glow_t", (3.5, 1.52, 0.35), 0.12, "fff0cc", scale=(1, 0.75, 1))
    tube("desk_mug", (3.3, 1.1, 0.65), 0.06, 0.12, "f4efe6")
    box("chair_t_seat", (2.9, 0.52, 1.2), (0.55, 0.1, 0.55), CREAM, bevel=0.06)
    box("chair_t_back", (2.9, 0.88, 1.45), (0.55, 0.6, 0.1), CREAM, bevel=0.06)
    tube("chair_t_stem", (2.9, 0.26, 1.2), 0.04, 0.45, "5a5a62")
    tube("chair_t_foot", (2.9, 0.03, 1.2), 0.3, 0.05, "5a5a62")
    box("shelf_t", (2.9, 1.95, 0.18), (1.4, 0.07, 0.34), WOOD, bevel=0.03)
    books("teen_book", 2.3, 1.99, 0.18, 9, seed=2)
    box("poster_t", (0.03, 1.8, 3.1), (0.04, 0.85, 0.65), "e58f5a", bevel=0.02)
    ball("poster_t_sun", (0.06, 1.85, 3.1), 0.18, "f3d36b", scale=(0.25, 1, 1))
    box("backpack", (1.9, 0.3, 2.9), (0.45, 0.58, 0.3), "c45c4a", bevel=0.14)
    box("backpack_pocket", (1.9, 0.22, 3.07), (0.32, 0.25, 0.06), "a8483a", bevel=0.05)
    cloth("hoodie", (2.6, 0.1, 3.3), (0.6, 0.07, 0.45), "5a7aa0", folds=0.05)
    tag()


def activities():
    layer("act_club")
    ball("club_ball", (3.0, 0.2, 7.0), 0.2, "f3ead8", lump=0.01)
    for i, (dx, dz) in enumerate(((0, 0.18), (0.13, 0.08), (-0.13, 0.08))):
        ball(f"club_patch{i}", (3.0 + dx, 0.33, 7.0 + dz), 0.06, "4a4d55", scale=(1, 0.5, 1), lump=0)
    tag()
    layer("act_study")
    for i, col in enumerate(("4e6a8a", "c45c4a", "e0b45a")):
        box(f"study_book{i}", (5.3, 0.82 + i * 0.07, 6.6), (0.42 - i * 0.03, 0.06, 0.32), col, bevel=0.02)
    box("notebook", (5.95, 0.79, 6.15), (0.32, 0.02, 0.42), "fbf8f2", bevel=0.01)
    tag()
    layer("act_play_toys")
    for i, col in enumerate(("c45c4a", "4e6a8a", "e0b45a")):
        box(f"train{i}", (2.7, 0.2, 5.3 + i * 0.36), (0.22, 0.22, 0.32), col, bevel=0.05)
        for dz in (-0.09, 0.09):
            tube(f"wheel{i}{dz}", (2.82, 0.1, 5.3 + i * 0.36 + dz), 0.06, 0.03, "4a4d55",
                 rot=(0, math.radians(90), 0))
    tag()



def rooms():
    """One room at a time (GDD 10.6): each room's own slab and full-height back walls."""
    papers = {"bedroom": (None, None), "bathroom": ("dbeaf0", None), "living": (None, "f4e2c8"),
              "kitchen": ("f6efdc", "f6efdc")}
    for room, (x0, z0) in {"bedroom": (0, 0), "bathroom": (M, 0), "living": (0, M), "kitchen": (M, M)}.items():
        layer(f"room_{room}")
        box("slab", (x0 + M / 2, -0.2, z0 + M / 2), (M + 0.3, 0.4, M + 0.3), "f6eddd", bevel=0.14)
        box("wall_x", (x0 - 0.15, WALL_H / 2, z0 + M / 2 - 0.15), (0.3, WALL_H, M + 0.3), WALL, bevel=0.14)
        box("wall_z", (x0 + M / 2 - 0.15, WALL_H / 2, z0 - 0.15), (M + 0.3, WALL_H, 0.3), WALL, bevel=0.14)
        px, pz = papers[room]
        if px:
            box("paper_x", (x0 + 0.01, 1.5, z0 + M / 2), (0.02, 2.5, 3.9), px, bevel=0.01, subd=1, lump=0.004)
        if pz:
            box("paper_z", (x0 + M / 2, 1.5, z0 + 0.01), (3.9, 2.5, 0.02), pz, bevel=0.01, subd=1, lump=0.004)
        tag()


def bake_groups():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    R.use_gpu(scene)
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
            if name.startswith("room_") and n.startswith("shell__") and ("slab" in n or "wall_" in n):
                ob.hide_render = True  # the room's own slab/walls replace these; coincident faces bake black
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
    rooms()
    bake_groups()
    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_vertex_color="ACTIVE",
                              export_materials="NONE", export_texcoords=False)
    print("HOUSE", {k: len(v) for k, v in LAYERS.items()})
