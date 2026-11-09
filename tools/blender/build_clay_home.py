"""Build one adult home (GDD 10.2) in the childhood home's clay look and 2x2 plan.

Run headless:
  blender -b --factory-startup --python tools/blender/build_clay_home.py -- <home_id> <out.glb>

Rooms sit where build_clay_house.py puts them: bedroom (x 0..4, z 0..4), bathroom (x 4..8, z 0..4),
living (x 0..4, z 4..8), kitchen (x 4..8, z 4..8). Coordinates are Godot's.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_clay_house as H  # noqa: E402

box, ball, tube, cloth = H.box, H.ball, H.tube, H.cloth
ORIGINS = {"bedroom": (0, 0), "bathroom": (4, 0), "living": (0, 4), "kitchen": (4, 4)}


def walls(colours):
    """Each room's slab and two back walls; colours = {room: wall colour}."""
    for room, (x0, z0) in ORIGINS.items():
        H.layer(f"room_{room}")
        c = colours[room]
        box("slab", (x0 + 2, -0.2, z0 + 2), (4.3, 0.4, 4.3), "e8dfd0", bevel=0.14)
        box("wall_x", (x0 - 0.15, H.WALL_H / 2, z0 + 1.85), (0.3, H.WALL_H, 4.3), c, bevel=0.14)
        box("wall_z", (x0 + 1.85, H.WALL_H / 2, z0 - 0.15), (4.3, H.WALL_H, 0.3), c, bevel=0.14)
        H.tag()


def window(n, x0, z, w=1.4, h=1.15, y=1.6, view="tree", frame="f0ece2"):
    """An open window on a room's x wall, one leaf swung into the room. The leaf hides the high-z side, so views sit low-z."""
    px = x0 + 0.075
    sky = "f6fcff" if view == "frosted" else "bfe0f0"
    box(f"{n}_sky_pane", (x0 + 0.05, y, z), (0.03, h, w), sky, bevel=0.01, subd=1, lump=0)
    base = view.split("_")[0]
    tall = {"b": 0.12, "c": -0.1}.get(view.split("_")[-1], 0)  # the _b and _c variants shift the skyline
    if view == "tree":
        box(f"{n}_trunk", (px - 0.005, y - h * 0.32, z - w * 0.2), (0.01, h * 0.36, 0.09), "7a5c45", bevel=0.003, subd=1, lump=0)
        for i, (dy, dz, r, col) in enumerate(((0.14, -0.2, 0.17, "7fae6a"), (0.0, -0.32, 0.12, "6f9e57"), (0.0, -0.08, 0.12, "8fbc78"))):
            ball(f"{n}_leaves{i}", (px + 0.004, y + h * dy, z + w * dz), w * r, col, scale=(0.05, 1, 1), lump=0)
    elif view == "street":
        for i, (dz, top, col, roof) in enumerate(((-0.34, 0.15, "c98f6f", "6f5a55"), (-0.06, -0.08, "e0cfa8", "8a5a4a"))):
            bh = h * (0.5 + top)
            bc = y - h / 2 + bh / 2
            box(f"{n}_house{i}", (px, bc, z + w * dz), (0.01, bh, w * 0.28), col, bevel=0.003, subd=1, lump=0)
            box(f"{n}_roof{i}", (px + 0.004, y - h / 2 + bh + 0.03, z + w * dz), (0.01, 0.07, w * 0.31), roof, bevel=0.003, subd=1, lump=0)
            box(f"{n}_pane{i}", (px + 0.008, bc + bh * 0.15, z + w * dz), (0.008, 0.11, 0.11), "fbf0c8", bevel=0.002, subd=1, lump=0)
    elif view == "hills":
        ball(f"{n}_sun", (px, y + h * 0.24, z - w * 0.3), w * 0.09, "f3d36b", scale=(0.05, 1, 1), lump=0)
        box(f"{n}_hill", (px, y - h * 0.32, z), (0.01, h * 0.36, w), "9dbb78", bevel=0.003, subd=1, lump=0)
        for i in range(5):  # a fence along the bottom of the garden
            box(f"{n}_fence{i}", (px + 0.006, y - h * 0.38, z - w * 0.42 + i * w * 0.16), (0.008, h * 0.2, 0.06), "e8dccb", bevel=0.002, subd=1, lump=0)
    if base == "roofs":
        for i, (dz, top, col) in enumerate(((-0.36, 0.22 + tall, "8f9aa8"), (-0.14, -0.02 - tall, "b0a090"), (0.06, 0.1, "7f8c9a"))):
            bh = h * (0.45 + top)
            bc = y - h / 2 + bh / 2
            box(f"{n}_block{i}", (px, bc, z + w * dz), (0.01, bh, w * 0.2), col, bevel=0.003, subd=1, lump=0)
            for j in range(2):
                box(f"{n}_lit{i}_{j}", (px + 0.008, bc + bh * (0.25 - j * 0.3), z + w * dz), (0.008, 0.07, 0.07), "fbf0c8", bevel=0.002, subd=1, lump=0)
    elif base in ("garden", "park", "swing"):
        lawn = {"garden": "9cc06f", "park": "7fa85c", "swing": "a8c878"}[base]
        box(f"{n}_lawn", (px, y - h * 0.32, z), (0.01, h * 0.36, w), lawn, bevel=0.003, subd=1, lump=0)
        if base == "garden":
            for i, col in enumerate(("e0694a", "f3d36b", "d88ac0", "fbf8f2")):
                ball(f"{n}_flower{i}", (px + 0.005, y - h * (0.28 + i % 2 * 0.1), z - w * (0.42 - i * 0.14 - tall)), 0.04, col, scale=(0.1, 1, 1), lump=0)
            box(f"{n}_hedge", (px + 0.002, y - h * 0.08, z), (0.01, h * 0.16, w), "6f9e57", bevel=0.003, subd=1, lump=0)
        elif base == "park":
            for i, d in enumerate((-0.38, -0.12)):
                ball(f"{n}_oak{i}", (px + 0.004, y + h * (0.08 + tall), z + w * d), w * 0.13, "5f8f4f", scale=(0.05, 1.3, 1), lump=0)
                box(f"{n}_oak_t{i}", (px + 0.002, y - h * 0.1, z + w * d), (0.008, h * 0.2, 0.05), "7a5c45", bevel=0.002, subd=1, lump=0)
        else:
            box(f"{n}_swing_top", (px + 0.004, y + h * 0.18, z - w * 0.22), (0.008, 0.04, w * 0.42), "8a6a55", bevel=0.002, subd=1, lump=0)
            for i, d in enumerate((-0.42, -0.02)):
                box(f"{n}_swing_leg{i}", (px + 0.004, y - h * 0.15, z + w * d), (0.008, h * 0.66, 0.04), "8a6a55", bevel=0.002, subd=1, lump=0)
            box(f"{n}_swing_seat", (px + 0.006, y - h * 0.2, z - w * 0.22), (0.008, 0.03, w * 0.12), "e0694a", bevel=0.002, subd=1, lump=0)
    elif base == "sea":
        box(f"{n}_water", (px, y - h * 0.2, z), (0.01, h * 0.34, w), "4f9cc4", bevel=0.003, subd=1, lump=0)
        box(f"{n}_sand", (px + 0.003, y - h * 0.42, z), (0.01, h * 0.16, w), "ecd9a8", bevel=0.003, subd=1, lump=0)
        if view == "sea":
            box(f"{n}_hull", (px + 0.005, y - h * 0.08, z - w * 0.28), (0.008, 0.05, 0.2), "fbf8f2", bevel=0.002, subd=1, lump=0)
            box(f"{n}_sail", (px + 0.005, y + h * 0.03, z - w * 0.28), (0.008, 0.2, 0.09), "e8805a", bevel=0.002, subd=1, lump=0)
        elif view == "sea_b":
            ball(f"{n}_sun", (px, y + h * 0.26, z - w * 0.3), w * 0.09, "f3d36b", scale=(0.05, 1, 1), lump=0)
        else:
            ball(f"{n}_isle", (px + 0.005, y - h * 0.02, z - w * 0.2), w * 0.2, "6f9e57", scale=(0.05, 0.35, 1), lump=0)
    t = 0.08
    for k, c, sz in (("top", (y + h / 2, z), (t, w + t)), ("bot", (y - h / 2, z), (t, w + t)),
                     ("l", (y, z - w / 2), (h, t)), ("r", (y, z + w / 2), (h, t))):
        box(f"{n}_frame_{k}", (x0 + 0.07, c[0], c[1]), (0.1, sz[0], sz[1]), frame, bevel=0.03)
    box(f"{n}_sill", (x0 + 0.15, y - h / 2 - 0.05, z), (0.3, 0.07, w + 0.25), frame, bevel=0.03)
    # the open leaf stands out from the hinge, square to the wall
    box(f"{n}_leaf", (x0 + 0.42, y, z + w / 2), (0.7, h - 0.05, 0.05), frame, bevel=0.02)
    box(f"{n}_leaf_pane", (x0 + 0.42, y, z + w / 2 + 0.03), (0.52, h - 0.25, 0.015), "dcecf2", bevel=0.005, subd=1, lump=0)


def poster(n, x, y, z, w, h, col, on_x=True, art=None):
    """A sheet stuck on a wall, with a blob of colour on it."""
    sz = (0.02, h, w) if on_x else (w, h, 0.02)
    box(n, (x, y, z), sz, col, bevel=0.006, subd=1, lump=0.002)
    if art:
        o = (0.015, 0, 0) if on_x else (0, 0, 0.015)
        ball(f"{n}_art", (x + o[0], y, z + o[2]), min(w, h) * 0.28, art,
             scale=(0.08, 1, 1) if on_x else (1, 1, 0.08), lump=0)


def skirting(room_x, room_z, col="efe8d8"):
    box(f"skirt_x{room_x}{room_z}", (room_x + 0.02, 0.1, room_z + 2), (0.05, 0.18, 4), col, bevel=0.015, subd=1, lump=0)
    box(f"skirt_z{room_x}{room_z}", (room_x + 2, 0.1, room_z + 0.02), (4, 0.18, 0.05), col, bevel=0.015, subd=1, lump=0)


def carton(n, x, y, z, s=0.6, seed=0):
    box(n, (x, y + s * 0.4, z), (s, s * 0.8, s * 0.8), "c9a273", bevel=0.03, seed=seed)
    box(f"{n}_tape", (x, y + s * 0.8, z), (s * 0.18, 0.015, s * 0.82), "e0cda6", bevel=0.005, subd=1, lump=0)


def radiator(n, x, z, along_x=True):
    for i in range(6):
        d = i * 0.14
        c = (x + d, 0.4, z) if along_x else (x, 0.4, z + d)
        box(f"{n}{i}", c, (0.1, 0.6, 0.1), "e8e4da", bevel=0.03, seed=i)


def rental():
    H.layer("shell")
    for i in range(8):  # worn carpet in the bedroom, cheap laminate in the living room
        for j in range(8):
            box(f"ctile{i}_{j}", (0.25 + i * 0.5, 0.02, 0.25 + j * 0.5), (0.5, 0.05, 0.5),
                ["a89a88", "a2937f", "ad9f8c"][(i * 3 + j) % 3], bevel=0.02, subd=1, lump=0.008, seed=i * 5 + j)
            box(f"vtile{i}_{j}", (4.25 + i * 0.5, 0.02, 0.25 + j * 0.5), (0.46, 0.05, 0.46),
                ["d5d7cf", "c4c8c0"][(i + j) % 2], bevel=0.02, subd=1, lump=0.004, seed=i * 9 + j)
            box(f"ltile{i}_{j}", (4.25 + i * 0.5, 0.02, 4.25 + j * 0.5), (0.46, 0.05, 0.46),
                ["cfc5ae", "b8ae97"][(i + j) % 2], bevel=0.02, subd=1, lump=0.004, seed=i * 7 + j)
        box(f"lplank{i}", (0.25 + i * 0.5, 0.02, 6), (0.46, 0.06, 4), ["b9a07f", "ae9576", "c2a988"][i % 3],
            bevel=0.025, seed=i)
    window("wb", 0, 1.5, view="tree")
    window("wl", 0, 6.0, view="street")
    window("wk", 4, 5.2, w=1.2, h=1.0, y=1.65, view="hills")
    window("wt", 4, 1.7, w=0.7, h=0.6, y=2.05, view="frosted")
    for x, z in ORIGINS.values():
        skirting(x, z)
    # damp patch in the bedroom corner, and the mark the old tenant's picture left
    box("picture_mark", (2.9, 1.8, 0.01), (0.55, 0.45, 0.012), "ded2ba", bevel=0.004, subd=1, lump=0)
    H.tag()

    H.layer("base")
    # ---- bedroom: a mattress on a low frame, a clothes rail, boxes never unpacked
    box("bed_frame", (1.05, 0.12, 1.25), (1.6, 0.2, 2.2), "b39a78", bevel=0.05)
    box("mattress", (1.05, 0.32, 1.25), (1.5, 0.24, 2.1), "e9e2d2", bevel=0.1)
    cloth("duvet", (1.1, 0.47, 1.65), (1.62, 0.1, 1.35), "6f8294", folds=0.04, droop=0.2)
    ball("pillow", (0.75, 0.52, 0.5), 0.3, "f2ede0", scale=(1.0, 0.36, 0.7))
    tube("rail_l", (2.45, 0.9, 0.3), 0.025, 1.75, "8d9094")
    tube("rail_r", (3.75, 0.9, 0.3), 0.025, 1.75, "8d9094")
    tube("rail_top", (3.1, 1.75, 0.3), 0.025, 1.34, "8d9094", rot=(0, math.radians(90), 0))
    for i, col in enumerate(("c45c4a", "4e6a8a", "e8dccb", "5c7a5a", "39404a")):
        box(f"hung{i}", (2.65 + i * 0.22, 1.2, 0.3), (0.16, 0.95 - (i % 2) * 0.15, 0.46), col, bevel=0.05, seed=i)
    carton("box_a", 3.2, 0.05, 2.0, s=0.72)
    carton("box_b", 3.2, 0.63, 2.0, s=0.52, seed=1)
    box("bedside", (0.45, 0.2, 2.75), (0.5, 0.36, 0.4), "e0b45a", bevel=0.05)  # a milk crate
    tube("bedside_lamp", (0.45, 0.47, 2.75), 0.02, 0.2, "8a6a55")
    ball("lamp_glow_bed", (0.45, 0.62, 2.75), 0.13, "fff0cc", scale=(1, 0.8, 1))
    cloth("floor_clothes", (2.0, 0.08, 3.1), (0.75, 0.08, 0.6), "9fb6d2", folds=0.05)
    radiator("rad_b", 0.1, 3.1, along_x=False)
    # ---- living room: a sagging two-seater, a TV on a crate
    box("sofa_base", (0.55, 0.26, 5.9), (0.9, 0.36, 1.55), "8c7f6e", bevel=0.13)
    for i, z in enumerate((5.55, 6.25)):
        box(f"sofa_seat{i}", (0.62, 0.46 - 0.03 * i, z), (0.78, 0.16, 0.7), "9b8e7c", bevel=0.09, lump=0.03, seed=i)
    box("sofa_back", (0.22, 0.74, 5.9), (0.28, 0.72, 1.55), "8c7f6e", bevel=0.12)
    for i, z in enumerate((5.04, 6.76)):
        box(f"sofa_arm{i}", (0.55, 0.5, z), (0.9, 0.5, 0.24), "7e7262", bevel=0.1)
    cloth("sofa_throw", (0.68, 0.6, 5.65), (0.75, 0.04, 0.7), "c45c4a", folds=0.03, droop=0.1)
    box("tv_crate", (3.5, 0.24, 6.0), (0.55, 0.46, 1.1), "c9a273", bevel=0.04)
    box("tv", (3.55, 0.75, 6.0), (0.1, 0.55, 0.9), "55595f", bevel=0.05)
    carton("box_l", 1.1, 0.05, 4.5, s=0.66, seed=2)
    H.plant("plant_dying", 0.5, 7.5, r=0.14, h=0.3)
    # ---- kitchen: one short worktop, an old fridge, a folding table with odd chairs
    box("counter", (5.45, 0.45, 4.45), (1.7, 0.9, 0.6), "e6dfcd", bevel=0.05)
    box("counter_top", (5.45, 0.93, 4.45), (1.8, 0.07, 0.66), "b8a98f", bevel=0.03)
    for i in range(3):
        box(f"cab_door{i}", (4.85 + i * 0.6, 0.45, 4.76), (0.54, 0.72, 0.03), "dad2bc", bevel=0.02)
    box("hob", (5.85, 0.98, 4.45), (0.55, 0.03, 0.5), "4a4d55", bevel=0.01)
    tube("pan", (5.8, 1.07, 4.45), 0.15, 0.13, "8d9094")
    tube("kettle", (4.85, 1.07, 4.4), 0.1, 0.2, "c8cbd0")
    box("sink_steel", (5.25, 0.97, 4.45), (0.5, 0.03, 0.42), "bcc0c4", bevel=0.01, subd=1, lump=0)
    for i in range(3):
        ball(f"dirty_plate{i}", (5.25, 1.0 + i * 0.03, 4.45), 0.14, "f0ece2", scale=(1, 0.15, 1), lump=0)
    for i in range(2):
        box(f"wall_cab{i}", (4.85 + i * 0.75, 1.85, 4.2), (0.68, 0.7, 0.34), "dad2bc", bevel=0.04, seed=i)
    box("k_shelf", (4.12, 1.6, 7.2), (0.26, 0.05, 1.1), "b39a78", bevel=0.02)
    for i, col in enumerate(("f4efe6", "e8a24a", "9fb6c6")):
        tube(f"k_jar{i}", (4.14, 1.71, 6.85 + i * 0.32), 0.07, 0.17, col)
    box("fridge", (6.85, 0.75, 4.5), (0.68, 1.5, 0.68), "e4e0d4", bevel=0.1)
    box("fridge_split", (6.85, 1.05, 4.85), (0.64, 0.02, 0.02), "c8c4b8", bevel=0.01)
    box("fridge_note", (6.95, 1.25, 4.85), (0.18, 0.22, 0.01), "f3d36b", bevel=0.005)
    box("table_top", (5.6, 0.72, 6.3), (1.2, 0.05, 0.8), "e8e2d4", bevel=0.02)
    for i, (dx, dz) in enumerate(((-0.5, -0.33), (0.5, -0.33), (-0.5, 0.33), (0.5, 0.33))):
        tube(f"table_leg{i}", (5.6 + dx, 0.36, 6.3 + dz), 0.025, 0.72, "8d9094")
    H.chair("chair_a", 4.72, 6.3, (1, 0), col="c98a55")
    H.chair("chair_b", 6.45, 6.3, (-1, 0), col="7f9fb8")
    tube("noodle_cup", (5.5, 0.82, 6.2), 0.09, 0.15, "e8a24a")
    box("bills", (5.85, 0.76, 6.4), (0.3, 0.02, 0.22), "fbf8f2", bevel=0.005)
    tube("bin", (7.5, 0.3, 7.5), 0.22, 0.6, "6e7278")
    # ---- bathroom: a shower cubicle, a small basin, the cheapest toilet going
    box("shower_tray", (4.75, 0.08, 0.75), (1.3, 0.14, 1.3), "ece9e0", bevel=0.05)
    # one fixed glass panel from the back wall; walk in from the open side
    box("shower_glass_x", (5.4, 1.1, 0.72), (0.02, 1.9, 1.4), "dcecf2", bevel=0.005, subd=1, lump=0)
    box("shower_trim_x", (5.4, 2.06, 0.72), (0.04, 0.04, 1.4), "bcc0c4", bevel=0.01, subd=1, lump=0)
    tube("shower_drain", (4.75, 0.16, 0.75), 0.07, 0.02, "9a9ea2")
    tube("shower_pipe", (4.12, 1.35, 0.5), 0.02, 1.5, "bcc0c4")
    tube("shower_arm", (4.25, 2.1, 0.5), 0.018, 0.3, "bcc0c4", rot=(0, 0, math.radians(90)))
    ball("shower_head", (4.42, 2.05, 0.5), 0.12, "bcc0c4", scale=(1, 0.4, 1), lump=0)
    tube("toilet_bowl", (6.1, 0.22, 0.5), 0.22, 0.42, "f4f1e8")
    tube("toilet_seat", (6.1, 0.45, 0.5), 0.24, 0.05, "e0ddd2")
    box("toilet_tank", (6.1, 0.7, 0.17), (0.48, 0.46, 0.22), "f4f1e8", bevel=0.08)
    tube("loo_roll", (6.55, 0.08, 0.3), 0.07, 0.12, "fbf8f2")
    tube("loo_roll_b", (6.55, 0.2, 0.3), 0.07, 0.12, "fbf8f2")
    box("sink", (7.2, 0.84, 0.3), (0.6, 0.16, 0.44), "f4f1e8", bevel=0.07)
    tube("sink_ped", (7.2, 0.4, 0.25), 0.09, 0.78, "f4f1e8")
    tube("tap", (7.2, 1.0, 0.12), 0.025, 0.14, "bcc0c4")
    tube("toothbrush_cup", (7.42, 0.98, 0.25), 0.04, 0.1, "e8a24a")
    box("mirror", (7.2, 1.66, 0.05), (0.5, 0.62, 0.03), "cfe3ea", bevel=0.015, subd=1, lump=0)
    cloth("bath_mat", (5.0, 0.06, 1.95), (0.9, 0.04, 0.6), "b8a98f", folds=0.006)
    tube("towel_rail", (4.1, 1.5, 2.6), 0.02, 0.7, "8d9094", rot=(math.radians(90), 0, 0))
    box("towel", (4.12, 1.12, 2.6), (0.05, 0.72, 0.5), "c45c4a", bevel=0.03, lump=0.02)
    tube("basket", (4.5, 0.25, 3.45), 0.22, 0.5, "b8a98f")
    cloth("basket_clothes", (4.5, 0.53, 3.45), (0.38, 0.06, 0.38), "6f8294", folds=0.03)
    # ---- walls
    poster("b_poster", 2.0, 1.75, 0.02, 0.6, 0.85, "2f3b52", on_x=False, art="e0a24a")
    poster("b_postcard_a", 0.02, 1.75, 2.95, 0.3, 0.22, "9fc6d8", art="fbf8f2")
    poster("b_postcard_b", 0.02, 1.45, 3.2, 0.22, 0.3, "f3d36b", art="4e6a8a")
    box("b_shelf", (3.4, 2.15, 0.14), (0.9, 0.05, 0.26), "b39a78", bevel=0.02)
    H.books("b_shelf_book", 3.05, 2.18, 0.14, 5, seed=4)
    poster("l_poster", 2.0, 1.65, 4.02, 0.95, 0.7, "4e7a8a", on_x=False, art="f3d36b")
    box("l_shelf", (3.4, 1.7, 4.14), (0.8, 0.05, 0.26), "b39a78", bevel=0.02)
    tube("l_candle", (3.65, 1.8, 4.14), 0.05, 0.16, "e0b45a")
    for i, (col, art, y) in enumerate((("8a6a55", "e0a24a", 1.85), ("39404a", "9fb6d2", 1.5), ("b39a78", "7fae6a", 1.9))):
        poster(f"l_frame{i}", 0.02, y, 7.05 + i * 0.36, 0.28, 0.32, col, art=art)
    H.books("l_shelf_book", 3.1, 1.73, 4.14, 3, seed=7)
    tube("k_clock", (6.9, 2.2, 4.03), 0.2, 0.03, "fbf8f2", rot=(math.radians(90), 0, 0))
    box("k_clock_hand", (6.9, 2.26, 4.06), (0.025, 0.14, 0.01), "39404a", bevel=0.004, subd=1, lump=0)
    box("k_clock_hand_b", (6.95, 2.2, 4.06), (0.1, 0.022, 0.01), "39404a", bevel=0.004, subd=1, lump=0)
    poster("k_calendar", 7.6, 1.75, 4.02, 0.42, 0.58, "fbf8f2", on_x=False)
    box("k_calendar_head", (7.6, 1.97, 4.035), (0.42, 0.13, 0.015), "c45c4a", bevel=0.004, subd=1, lump=0)
    for i in range(4):
        for j in range(4):
            box(f"k_day{i}_{j}", (7.48 + i * 0.08, 1.84 - j * 0.09, 4.035), (0.05, 0.05, 0.01), "b8b2a4",
                bevel=0.002, subd=1, lump=0)
    for i in range(6):  # splashback tiles behind the worktop
        for j in range(2):
            box(f"k_tile{i}_{j}", (4.8 + i * 0.3, 1.14 + j * 0.27, 4.03), (0.28, 0.25, 0.02),
                ["f0ece2", "cfe0e0"][(i + j) % 2], bevel=0.01, subd=1, lump=0.002)
    for i in range(10):  # half-tiled bathroom walls
        for j in range(3):
            box(f"t_tz{i}_{j}", (4.2 + i * 0.38, 0.32 + j * 0.38, 0.02), (0.36, 0.36, 0.02),
                ["f4f1e8", "dcebe6"][(i + j) % 2], bevel=0.01, subd=1, lump=0.002)
            box(f"t_tx{i}_{j}", (4.02, 0.32 + j * 0.38, 0.2 + i * 0.38), (0.02, 0.36, 0.36),
                ["f4f1e8", "dcebe6"][(i + j) % 2], bevel=0.01, subd=1, lump=0.002)
    box("t_shelf", (6.1, 1.5, 0.14), (0.7, 0.05, 0.24), "b39a78", bevel=0.02)
    for i, col in enumerate(("e58f5a", "9fb6d2", "7fae6a")):
        tube(f"t_bottle{i}", (5.9 + i * 0.2, 1.61, 0.14), 0.045, 0.18, col)
    H.tag()
    walls({"bedroom": "d8d0bc", "bathroom": "cdd6d0", "living": "dcd3bd", "kitchen": "dfd9c2"})


def floor(p, room, kind, cols):
    x0, z0 = ORIGINS[room]
    if kind == "plank":
        for i in range(8):
            box(f"{p}{i}", (x0 + 0.25 + i * 0.5, 0.02, z0 + 2), (0.46, 0.06, 4), cols[i % len(cols)], bevel=0.025, seed=i)
    elif kind == "plank_x":
        for i in range(8):
            box(f"{p}{i}", (x0 + 2, 0.02, z0 + 0.25 + i * 0.5), (4, 0.06, 0.46), cols[i % len(cols)], bevel=0.025, seed=i)
    elif kind == "carpet":
        box(p, (x0 + 2, 0.02, z0 + 2), (4, 0.06, 4), cols[0], bevel=0.02, lump=0.006)
    elif kind == "parquet":
        for i in range(4):
            for j in range(4):
                for k in range(3):
                    along = (i + j) % 2 == 0
                    d = -0.33 + k * 0.33
                    c = (x0 + 0.5 + i, 0.02, z0 + 0.5 + j + d) if along else (x0 + 0.5 + i + d, 0.02, z0 + 0.5 + j)
                    size = (0.96, 0.05, 0.3) if along else (0.3, 0.05, 0.96)
                    box(f"{p}{i}_{j}_{k}", c, size, cols[(i + j + k) % len(cols)], bevel=0.012, subd=1, lump=0.002)
    else:  # tile
        n = 8 if kind == "tile" else 4
        s = 4 / n
        for i in range(n):
            for j in range(n):
                box(f"{p}{i}_{j}", (x0 + s / 2 + i * s, 0.02, z0 + s / 2 + j * s), (s - 0.04, 0.05, s - 0.04),
                    cols[(i + j) % len(cols)], bevel=0.02, subd=1, lump=0.003)


def deco(p, room, kind, col):
    """Dress a room's two back walls. Never name a shell piece with a wall word: the render hides those."""
    x0, z0 = ORIGINS[room]
    if kind == "stripes":
        for i in range(10):
            box(f"{p}_sx{i}", (x0 + 0.012, H.WALL_H / 2, z0 + 0.2 + i * 0.4), (0.012, H.WALL_H, 0.17), col, bevel=0.003, subd=1, lump=0)
            box(f"{p}_sz{i}", (x0 + 0.2 + i * 0.4, H.WALL_H / 2, z0 + 0.012), (0.17, H.WALL_H, 0.012), col, bevel=0.003, subd=1, lump=0)
    elif kind == "panels":
        for i in range(5):
            box(f"{p}_px{i}", (x0 + 0.025, 0.62, z0 + 0.42 + i * 0.8), (0.03, 0.8, 0.66), col, bevel=0.012, subd=1, lump=0)
            box(f"{p}_pz{i}", (x0 + 0.42 + i * 0.8, 0.62, z0 + 0.025), (0.66, 0.8, 0.03), col, bevel=0.012, subd=1, lump=0)
        box(f"{p}_railx", (x0 + 0.025, 1.1, z0 + 2), (0.04, 0.06, 4), col, bevel=0.012, subd=1, lump=0)
        box(f"{p}_railz", (x0 + 2, 1.1, z0 + 0.025), (4, 0.06, 0.04), col, bevel=0.012, subd=1, lump=0)
    elif kind == "dado":  # a painted lower half
        box(f"{p}_dx", (x0 + 0.012, 0.55, z0 + 2), (0.012, 1.1, 4), col, bevel=0.003, subd=1, lump=0)
        box(f"{p}_dz", (x0 + 2, 0.55, z0 + 0.012), (4, 1.1, 0.012), col, bevel=0.003, subd=1, lump=0)


def wall_tiles(p, rows, a, b):
    for i in range(10):
        for j in range(rows):
            col = [a, b][(i + j) % 2]
            box(f"{p}z{i}_{j}", (4.2 + i * 0.38, 0.32 + j * 0.38, 0.02), (0.36, 0.36, 0.02), col, bevel=0.01, subd=1, lump=0.002)
            box(f"{p}x{i}_{j}", (4.02, 0.32 + j * 0.38, 0.2 + i * 0.38), (0.02, 0.36, 0.36), col, bevel=0.01, subd=1, lump=0.002)


def bed_room(s):
    w = s["bed_w"]
    wide = w >= 1.8
    cx = (0.2 if wide else 0.35) + w / 2
    side = cx + w / 2 + (0.25 if wide else 0.3)
    wx, ww = (3.5, 0.9) if wide else (3.4, 1.1)
    wood = s["wood"]
    box("bed_frame", (cx, 0.16, 1.2), (w, 0.26, 2.15), wood, bevel=0.05)
    box("mattress", (cx, 0.4, 1.2), (w - 0.1, 0.24, 2.05), "ece6d6", bevel=0.09)
    cloth("duvet", (cx + 0.03, 0.56, 1.62), (w + 0.04, 0.1, 1.35), s["duvet"], folds=0.03, droop=0.2)
    for i in range(2 if w > 1.5 else 1):
        ball(f"pillow{i}", (cx + (i - 0.5) * w * 0.48 if w > 1.5 else cx, 0.6, 0.48), w * 0.2 if w > 1.5 else 0.3, "f4efe4", scale=(1, 0.38, 0.7))
    box("headboard", (cx, 0.6, 0.1), (w + 0.08, 1.15, 0.1), s.get("head", wood), bevel=0.05)
    if s.get("posts"):
        for i, (dx, z) in enumerate(((-w / 2, 0.12), (w / 2, 0.12), (-w / 2, 2.28), (w / 2, 2.28))):
            tube(f"bed_post{i}", (cx + dx, 1.05, z), 0.05, 2.1, wood)
        tube("bed_rail_a", (cx, 2.1, 2.28), 0.03, w, wood, rot=(0, math.radians(90), 0))
        tube("bed_rail_b", (cx, 2.1, 0.12), 0.03, w, wood, rot=(0, math.radians(90), 0))
        tube("bed_rail_c", (cx - w / 2, 2.1, 1.2), 0.03, 2.16, wood, rot=(math.radians(90), 0, 0))
        tube("bed_rail_d", (cx + w / 2, 2.1, 1.2), 0.03, 2.16, wood, rot=(math.radians(90), 0, 0))
    box("bedside", (side, 0.25, 0.4), (0.44, 0.5, 0.44), wood, bevel=0.04)
    tube("bedside_lamp", (side, 0.6, 0.4), 0.025, 0.22, "8a6a55")
    ball("lamp_glow_bed", (side, 0.78, 0.4), 0.13, "fff0cc", scale=(1, 0.85, 1))
    box("wardrobe", (wx, 1.0, 0.38), (ww, 2.0, 0.62), wood, bevel=0.04)
    box("wardrobe_split", (wx, 1.0, 0.7), (0.02, 1.9, 0.02), "6e5a48", bevel=0.005, subd=1, lump=0)
    for i in (-1, 1):
        ball(f"wardrobe_knob{i}", (wx + i * 0.07, 1.0, 0.72), 0.03, "d6b75e", lump=0)
    if s.get("bed_rug"):
        cloth("bed_rug", (cx + 0.3, 0.07, 3.0), (1.9, 0.03, 1.2), s["bed_rug"], folds=0.004)
    poster("b_poster", cx + 0.1, 1.85, 0.02, 0.7, 0.55, s["art"][0], on_x=False, art=s["art"][1])
    if s.get("dresser"):
        box("dresser", (0.33, 0.42, 3.15), (0.5, 0.84, 1.15), wood, bevel=0.04)
        box("dresser_glass", (0.05, 1.4, 3.15), (0.03, 0.8, 0.7), "cfe3ea", bevel=0.012, subd=1, lump=0)
        tube("dresser_jar", (0.33, 0.9, 2.85), 0.05, 0.12, "e0a24a")
    else:
        poster("b_card_a", 0.02, 1.7, 3.0, 0.32, 0.25, s["art"][1], art=s["art"][0])
        poster("b_card_b", 0.02, 1.3, 3.3, 0.25, 0.32, s["art"][2], art="fbf8f2")


def sofa(col, arm, seats=2):
    pitch = 0.72 if seats > 2 else 0.8
    cz = 5.85 if seats > 2 else 5.9
    length = pitch * seats
    box("sofa_base", (0.6, 0.26, cz), (0.95, 0.36, length), arm, bevel=0.1)
    for i in range(seats):
        box(f"sofa_seat{i}", (0.68, 0.48, cz + (i - (seats - 1) / 2) * pitch), (0.8, 0.16, pitch - 0.04), col, bevel=0.08, lump=0.02, seed=i)
    box("sofa_back", (0.25, 0.75, cz), (0.28, 0.75, length), arm, bevel=0.11)
    for i, d in enumerate((-1, 1)):
        box(f"sofa_arm{i}", (0.6, 0.5, cz + d * (length / 2 + 0.1)), (0.95, 0.52, 0.24), arm, bevel=0.09)


def live_room(s):
    wood = s["wood"]
    shift = 0.45 if s.get("seats", 2) > 2 else 0  # bookcase moves along the wall, clear of a long sofa
    sofa(s["sofa"], s["sofa_arm"], s.get("seats", 2))
    box("cushion", (0.5, 0.7, 5.55), (0.14, 0.34, 0.34), s["art"][1], bevel=0.07, seed=2)
    if s.get("rug"):
        cloth("rug", (2.2, 0.07, 5.95), (1.9, 0.03, 2.2), s["rug"], folds=0.004)
    box("coffee_top", (2.15, 0.42, 5.95), (0.7, 0.05, 1.05), wood, bevel=0.02)
    for i, (dx, dz) in enumerate(((-0.28, -0.44), (0.28, -0.44), (-0.28, 0.44), (0.28, 0.44))):
        tube(f"coffee_leg{i}", (2.15 + dx, 0.2, 5.95 + dz), 0.025, 0.4, wood)
    box("tv_unit", (3.6, 0.27, 6.0), (0.5, 0.5, 1.5), wood, bevel=0.04)
    box("tv", (3.68, 0.92, 6.0), (0.08, 0.72, 1.15), "4a4e55", bevel=0.03)
    box("bookcase", (1.1 + shift, 1.0, 4.2), (1.25, 2.0, 0.34), wood, bevel=0.03)
    for j, y in enumerate((0.38, 0.95, 1.5)):
        box(f"bookcase_back{j}", (1.1 + shift, y + 0.18, 4.38), (1.1, 0.4, 0.02), "5d4a3a", bevel=0.005, subd=1, lump=0)
        H.books(f"book_{j}", 0.72 + shift, y, 4.42, 6 - j, seed=j + 2)
    if s.get("fire"):
        box("fire_surround", (3.0, 0.65, 4.14), (1.2, 1.3, 0.26), s["fire"], bevel=0.04)
        box("fire_hole", (3.0, 0.42, 4.28), (0.68, 0.72, 0.02), "2b2622", bevel=0.005, subd=1, lump=0)
        ball("lamp_glow_fire", (3.0, 0.25, 4.3), 0.17, "ee8a3a", scale=(1.3, 0.8, 0.2), lump=0)
        box("fire_mantel", (3.0, 1.33, 4.17), (1.42, 0.07, 0.34), s["fire"], bevel=0.02)
        box("fire_glass", (3.0, 1.95, 4.03), (0.85, 0.95, 0.03), "cfe3ea", bevel=0.015, subd=1, lump=0)
    elif not s.get("bare_back"):
        poster("l_poster", 3.0, 1.65, 4.045, 1.05, 0.75, s["art"][0], on_x=False, art=s["art"][1])
    for i, (art, y) in enumerate(((s["art"][1], 1.85), (s["art"][2], 1.5), ("fbf8f2", 1.9))):
        poster(f"l_frame{i}", 0.02, y, 7.05 + i * 0.36, 0.28, 0.32, s["art"][0], art=art)
    if s.get("chair"):
        box("arm_seat", (2.4, 0.35, 7.45), (0.8, 0.42, 0.72), s["chair"], bevel=0.1)
        box("arm_back", (2.4, 0.72, 7.76), (0.8, 0.7, 0.2), s["chair"], bevel=0.08)
    H.plant("plant", 0.5, 7.5, r=min(s.get("plant_r", 0.22), 0.26), h=0.42)


def kit_room(s):
    cab, top, n = s["cab"], s["top"], s.get("cabs", 4)
    cx = 4.35 + n * 0.3
    box("counter", (cx, 0.45, 4.42), (n * 0.6, 0.9, 0.62), cab, bevel=0.04)
    box("counter_top", (cx, 0.93, 4.45), (n * 0.6 + 0.08, 0.07, 0.68), top, bevel=0.025)
    for i in range(n):
        box(f"cab_door{i}", (4.65 + i * 0.6, 0.45, 4.74), (0.54, 0.72, 0.03), s.get("door", cab), bevel=0.018)
        if i < n - 1:
            box(f"wall_cab{i}", (4.65 + i * 0.6, 1.9, 4.2), (0.56, 0.72, 0.34), cab, bevel=0.035, seed=i)
    box("hob", (4.65 + (n - 2) * 0.6, 0.98, 4.45), (0.54, 0.03, 0.5), "4a4d55", bevel=0.01)
    tube("pan", (4.65 + (n - 2) * 0.6, 1.07, 4.45), 0.15, 0.13, s.get("pan", "8d9094"))
    box("sink_steel", (5.25 if n > 3 else 4.65, 0.97, 4.45), (0.5, 0.03, 0.42), "bcc0c4", bevel=0.01, subd=1, lump=0)
    if n > 3:
        tube("kettle", (4.62, 1.07, 4.4), 0.1, 0.2, "c8cbd0")
    box("fridge", (4.5 + n * 0.6 + 0.2, 0.85, 4.5), (0.72, 1.7, 0.7), s.get("fridge", "e4e0d4"), bevel=0.08)
    box("fridge_split", (4.5 + n * 0.6 + 0.2, 1.18, 4.86), (0.66, 0.02, 0.02), "b8b4a8", bevel=0.008)
    for i in range(6):
        for j in range(2):
            box(f"k_tile{i}_{j}", (4.7 + i * 0.3, 1.14 + j * 0.27, 4.03), (0.28, 0.25, 0.02),
                s["splash"][(i + j) % 2], bevel=0.01, subd=1, lump=0.002)
    if s.get("island"):
        box("island", (6.05, 0.47, 6.3), (1.9, 0.94, 0.85), cab, bevel=0.05)
        box("island_top", (6.05, 0.97, 6.3), (2.05, 0.07, 1.0), top, bevel=0.025)
        for i in range(3):
            tube(f"stool{i}", (5.4 + i * 0.65, 0.34, 7.05), 0.03, 0.66, "8a6a55")
            tube(f"stool_seat{i}", (5.4 + i * 0.65, 0.69, 7.05), 0.17, 0.06, s["art"][1])
        ball("fruit_bowl", (6.05, 1.06, 6.3), 0.2, "e8dccb", scale=(1, 0.4, 1))
        for i, col in enumerate(("d8843a", "b83f33", "7fae6a")):
            ball(f"fruit{i}", (5.96 + i * 0.09, 1.13, 6.3), 0.07, col, lump=0)
    else:
        L = s.get("table", 1.2)
        box("table_top", (5.75, 0.72, 6.4), (L, 0.06, 0.85), s["wood"], bevel=0.02)
        for i, (dx, dz) in enumerate(((-L / 2 + 0.08, -0.35), (L / 2 - 0.08, -0.35), (-L / 2 + 0.08, 0.35), (L / 2 - 0.08, 0.35))):
            tube(f"table_leg{i}", (5.75 + dx, 0.36, 6.4 + dz), 0.03, 0.72, s["wood"])
        H.chair("chair_a", 5.75 - L / 2 - 0.25, 6.4, (1, 0), col=s["chairs"])
        H.chair("chair_b", 5.75 + L / 2 + 0.25, 6.4, (-1, 0), col=s["chairs"])
        if L > 1.3:
            H.chair("chair_c", 5.45, 5.65, (0, 1), col=s["chairs"])
            H.chair("chair_d", 6.05, 5.65, (0, 1), col=s["chairs"])
        tube("table_jug", (5.75, 0.84, 6.4), 0.07, 0.18, s["art"][1])
    tube("k_clock", (7.3, 2.1, 4.03), 0.2, 0.03, "fbf8f2", rot=(math.radians(90), 0, 0))
    box("k_clock_hand", (7.3, 2.16, 4.06), (0.025, 0.14, 0.01), "39404a", bevel=0.004, subd=1, lump=0)
    box("k_clock_hand_b", (7.35, 2.1, 4.06), (0.1, 0.022, 0.01), "39404a", bevel=0.004, subd=1, lump=0)
    box("k_shelf", (4.12, 1.6, 7.0), (0.26, 0.05, 1.1), s["wood"], bevel=0.02)
    for i, col in enumerate(("f4efe6", "e8a24a", "9fb6c6")):
        tube(f"k_jar{i}", (4.14, 1.71, 6.65 + i * 0.32), 0.07, 0.17, col)


def bath_room(s):
    suite = s.get("suite", "f4f1e8")
    metal = s.get("metal", "bcc0c4")
    kind = s["wash"]
    if kind == "tub":
        box("bath", (4.48, 0.3, 1.0), (0.85, 0.56, 1.75), suite, bevel=0.08)
        box("bath_water", (4.48, 0.59, 1.0), (0.66, 0.02, 1.52), "a9d3e0", bevel=0.01, subd=1, lump=0)
        tube("bath_tap", (4.48, 0.68, 0.22), 0.03, 0.16, metal)
    elif kind == "roll":
        ball("bath", (4.85, 0.4, 1.25), 0.5, suite, scale=(0.85, 0.64, 1.7), lump=0.004)
        ball("bath_rim", (4.85, 0.7, 1.25), 0.5, suite, scale=(0.85, 0.06, 1.7), lump=0)
        ball("bath_water", (4.85, 0.73, 1.25), 0.42, "a9d3e0", scale=(0.82, 0.03, 1.66), lump=0)
        for i, (dx, dz) in enumerate(((-0.25, -0.55), (0.25, -0.55), (-0.25, 0.55), (0.25, 0.55))):
            ball(f"bath_foot{i}", (4.85 + dx, 0.07, 1.25 + dz), 0.075, metal, lump=0)
        tube("bath_tap", (4.85, 0.47, 0.22), 0.025, 0.94, metal)
        tube("bath_spout", (4.85, 0.93, 0.34), 0.02, 0.26, metal, rot=(math.radians(90), 0, 0))
    else:
        box("shower_tray", (4.75, 0.08, 0.75), (1.3, 0.14, 1.3), "ece9e0", bevel=0.05)
        box("shower_glass_x", (5.4, 1.1, 0.72), (0.02, 1.9, 1.4), "dcecf2", bevel=0.005, subd=1, lump=0)
        box("shower_trim_x", (5.4, 2.06, 0.72), (0.04, 0.04, 1.4), metal, bevel=0.01, subd=1, lump=0)
        tube("shower_drain", (4.75, 0.16, 0.75), 0.07, 0.02, "9a9ea2")
        tube("shower_pipe", (4.12, 1.35, 0.5), 0.02, 1.5, metal)
        tube("shower_arm", (4.25, 2.1, 0.5), 0.018, 0.3, metal, rot=(0, 0, math.radians(90)))
        ball("shower_head", (4.42, 2.05, 0.5), 0.12, metal, scale=(1, 0.4, 1), lump=0)
    tube("toilet_bowl", (6.1, 0.22, 0.5), 0.22, 0.42, suite)
    tube("toilet_seat", (6.1, 0.45, 0.5), 0.24, 0.05, s.get("seat", "e0ddd2"))
    box("toilet_tank", (6.1, 0.7, 0.17), (0.48, 0.46, 0.22), suite, bevel=0.08)
    sinks = (6.95, 7.55) if s.get("double") else (7.2,)
    for i, x in enumerate(sinks):
        box(f"sink{i}", (x, 0.84, 0.3), (0.56, 0.16, 0.44), suite, bevel=0.07)
        tube(f"sink_ped{i}", (x, 0.4, 0.25), 0.09, 0.78, suite)
        tube(f"tap{i}", (x, 1.0, 0.12), 0.025, 0.14, metal)
        box(f"mirror{i}", (x, 1.75, 0.05), (0.5, 0.7, 0.03), "cfe3ea", bevel=0.015, subd=1, lump=0)
    cloth("bath_mat", (5.3, 0.06, 2.45), (1.0, 0.04, 0.65), s["mat"], folds=0.006)
    tube("towel_rail", (4.1, 1.5, 3.05), 0.02, 0.7, metal, rot=(math.radians(90), 0, 0))
    box("towel", (4.12, 1.12, 3.05), (0.05, 0.72, 0.5), s["art"][1], bevel=0.03, lump=0.02)
    if s.get("t_plant"):
        H.plant("t_plant", 7.5, 3.5, r=0.2, h=0.4)
    box("t_shelf", (6.1, 1.65, 0.14), (0.7, 0.05, 0.24), s["wood"], bevel=0.02)
    for i, col in enumerate(("e58f5a", "9fb6d2", "7fae6a")):
        tube(f"t_bottle{i}", (5.9 + i * 0.2, 1.76, 0.14), 0.045, 0.18, col)


def ladder(x, z):
    for i, d in enumerate((-0.22, 0.22)):
        tube(f"ladder_side{i}", (x, 1.05, z + d), 0.022, 2.1, "b39a78", rot=(0, 0, math.radians(-8)))
    for i in range(6):
        tube(f"ladder_step{i}", (x + 0.13 - i * 0.05, 0.25 + i * 0.32, z), 0.018, 0.44, "b39a78", rot=(math.radians(90), 0, 0))


def home(s):
    H.layer("shell")
    for room, (kind, cols) in s["floors"].items():
        floor(f"fl_{room}", room, kind, cols)
    window("wb", 0, 1.5, view=s["views"][0], frame=s.get("frame", "f0ece2"))
    window("wl", 0, 6.0, view=s["views"][1], frame=s.get("frame", "f0ece2"))
    window("wk", 4, 5.45, w=1.2, h=1.0, y=1.65, view=s["views"][2], frame=s.get("frame", "f0ece2"))
    window("wt", 4, 1.9, w=0.7, h=0.6, y=2.1, view="frosted", frame=s.get("frame", "f0ece2"))
    for room, (x, z) in ORIGINS.items():
        skirting(x, z, s.get("frame", "efe8d8"))
        if room in s.get("deco", {}):
            deco(f"dc_{room}", room, *s["deco"][room])
    wall_tiles("t_t", s["tile_rows"], *s["tiles"])
    H.tag()
    H.layer("base")
    bed_room(s)
    live_room(s)
    kit_room(s)
    bath_room(s)
    if s.get("extra"):
        s["extra"]()
    H.tag()
    walls(s["walls"])


def fixer_extra():
    """Half a renovation: fresh paint started on one wall, a ladder and the tins that go with it."""
    box("new_paint", (2.3, 1.2, 4.015), (2.4, 2.1, 0.012), "e9dfbd", bevel=0.004, subd=1, lump=0.006)
    ladder(3.65, 4.5)
    for i, col in enumerate(("e9dfbd", "c9b48a")):
        tube(f"paint_tin{i}", (3.1 + i * 0.3, 0.14, 4.35), 0.11, 0.24, col)
    for i, (y, z) in enumerate(((2.35, 3.45), (0.72, 3.65))):  # bare plaster where the old paper came off
        ball(f"plaster{i}", (0.015, y, z), 0.28, "c8b49a", scale=(0.03, 0.8, 1.2))
    ball("plaster_k", (4.015, 2.1, 6.9), 0.3, "c8b49a", scale=(0.03, 0.75, 1.3))


W = "f4efe4"
SPECS = {
    "small_flat": {
        "floors": {"bedroom": ("carpet", ["9aa7ad"]), "living": ("plank", ["c8b89c", "bfae90"]),
                   "kitchen": ("tile", ["e8e4d8", "d8d4c8"]), "bathroom": ("tile", ["dfe6e8", "ccd6d8"])},
        "walls": {"bedroom": "cdd8dc", "living": "dfe2dc", "kitchen": "e6e2d4", "bathroom": "d3e0e2"},
        "views": ("roofs", "roofs_b", "street"), "bed_w": 1.5, "wood": "c6a982", "duvet": "567a8c",
        "art": ("2f4858", "e8a24a", "9fc6d8"), "sofa": "7e97a6", "sofa_arm": "6b8493", "rug": "d9cdb4",
        "cab": W, "top": "a8927a", "splash": ("f0ece2", "c6dbe2"), "chairs": "6f94a8", "cabs": 3,
        "wash": "shower", "tile_rows": 3, "tiles": (W, "c9dde2"), "mat": "7e97a6",
    },
    "fixer_upper": {
        "floors": {"bedroom": ("plank", ["a58a6a", "977c5c", "ad9272"]), "living": ("plank", ["9c8263", "8e7556", "a78d6d"]),
                   "kitchen": ("tile_big", ["b9a88c", "a4937a"]), "bathroom": ("tile", ["c5b8a0", "b0a38c"])},
        "walls": {"bedroom": "c9b98f", "living": "bfae88", "kitchen": "c6bb94", "bathroom": "b7c0a6"},
        "bare_back": True, "views": ("hills", "tree", "street"), "bed_w": 1.5, "wood": "8d7358", "duvet": "8c7a5e",
        "art": ("6e5a48", "c9a273", "a58a6a"), "sofa": "a8956c", "sofa_arm": "8f7c58",
        "cab": "b9b18f", "door": "9fb08a", "top": "8a7458", "splash": ("c9c0a0", "a9b596"), "chairs": "8d7358",
        "cabs": 3, "fridge": "cfc9a8", "wash": "tub", "suite": "9fb58a", "seat": "8a9c78", "tile_rows": 2,
        "tiles": ("c9c0a0", "a9b596"), "mat": "8c7a5e", "extra": fixer_extra, "frame": "cfc6ab",
    },
    "starter_house": {
        "floors": {"bedroom": ("carpet", ["c9bba2"]), "living": ("plank", ["c7a77c", "bb9b70", "cfae84"]),
                   "kitchen": ("tile", ["ede3cd", "d9c9ab"]), "bathroom": ("tile", ["f0ece0", "c8dcc8"])},
        "walls": {"bedroom": "d9e0c9", "living": "efe2c6", "kitchen": "f0e6c0", "bathroom": "d7e8d8"},
        "views": ("garden", "garden_b", "hills"), "bed_w": 1.8, "wood": "b98f5e", "duvet": "8fa66f",
        "art": ("5c7a5a", "e8b85a", "c97a5a"), "sofa": "c2895a", "sofa_arm": "a97347", "rug": "e6d6b4",
        "bed_rug": "e6d6b4", "cab": "9fb58f", "top": "e6dcc4", "splash": ("f4efe0", "cfe0c4"), "chairs": "b98f5e",
        "wash": "tub", "tile_rows": 3, "tiles": ("f4efe0", "c8dcc8"), "mat": "8fa66f", "t_plant": True,
        "deco": {"bedroom": ("dado", "c5d0b0")},
    },
    "family_house": {
        "floors": {"bedroom": ("carpet", ["b7c0cc"]), "living": ("plank", ["b98f62", "ab8155", "c49a6c"]),
                   "kitchen": ("plank_x", ["c9a878", "bb9a6a"]), "bathroom": ("tile", ["f2efe6", "bcd4e0"])},
        "walls": {"bedroom": "dbe4ee", "living": "f2dcc0", "kitchen": "f6efd6", "bathroom": "cfe4ee"},
        "views": ("garden", "garden_b", "swing"), "bed_w": 2.0, "wood": "a8784c", "duvet": "4f7396",
        "art": ("8a6a55", "e8703f", "6fa0c0"), "sofa": "6f8fa8", "sofa_arm": "5a7a93", "seats": 3, "rug": "e0694a",
        "bed_rug": "f0e6d0", "chair": "d39b4a", "cab": "f0ece2", "top": "9a6a42", "splash": ("f4efe6", "f0c98a"),
        "chairs": "e0694a", "table": 1.9, "cabs": 5, "wash": "tub", "tile_rows": 4, "tiles": ("f8f5ec", "bcd4e0"),
        "mat": "e0694a", "t_plant": True, "deco": {"living": ("stripes", "f8e8d2")},
    },
    "town_house": {
        "floors": {"bedroom": ("parquet", ["8a5f3e", "7a5234", "96694a"]), "living": ("parquet", ["8a5f3e", "7a5234", "96694a"]),
                   "kitchen": ("tile_big", ["e6e2d8", "4a5058"]), "bathroom": ("tile", ["3f4a55", "dfe2e4"])},
        "walls": {"bedroom": "4c5f73", "living": "3f5166", "kitchen": "dfe2dc", "bathroom": "5b7380"},
        "views": ("street", "roofs", "roofs_b"), "bed_w": 2.0, "wood": "5c3d28", "head": "c9a24a", "duvet": "e6dcc4",
        "art": ("e6dcc4", "b8863a", "7a2f35"), "sofa": "7a2f35", "sofa_arm": "642630", "rug": "b8a98a", "bed_rug": "b8a98a",
        "chair": "c9a24a", "fire": "ece6d6", "dresser": True, "cab": "2f3e4e", "top": "ece6d6",
        "splash": ("f4efe6", "dfe2dc"), "chairs": "5c3d28", "island": True, "cabs": 5, "wash": "roll", "metal": "c9a24a",
        "tile_rows": 3, "tiles": ("f4efe6", "dfe2dc"), "mat": "e6dcc4", "frame": "f4efe6",
        "deco": {"bedroom": ("panels", "5d7288"), "living": ("panels", "506478")},
    },
    "seaside_villa": {
        "floors": {"bedroom": ("tile_big", ["e8d8bc", "dcc8a8"]), "living": ("tile_big", ["d9825a", "cc7550"]),
                   "kitchen": ("tile", ["f4f1e8", "5b93b8"]), "bathroom": ("tile", ["f4f1e8", "8cc0d8"])},
        "walls": {"bedroom": "f5f2e8", "living": "f8f5ec", "kitchen": "f5f2e8", "bathroom": "e4f1f4"},
        "views": ("sea", "sea_b", "sea_c"), "bed_w": 2.1, "wood": "d6b98a", "duvet": "f6f3ea", "head": "5b93b8",
        "art": ("2f6f92", "f3d36b", "e8805a"), "sofa": "f0e8d6", "sofa_arm": "5b93b8", "seats": 3, "rug": "cfe3ea",
        "bed_rug": "cfe3ea", "chair": "d6b98a", "plant_r": 0.34, "cab": "5b93b8", "top": "f6f3ea",
        "splash": ("f4f1e8", "8cc0d8"), "chairs": "d6b98a", "island": True, "cabs": 5, "wash": "shower",
        "tile_rows": 5, "tiles": ("f8f6ee", "8cc0d8"), "mat": "e8805a", "t_plant": True, "frame": "ffffff",
    },
    "mansion": {
        "floors": {"bedroom": ("carpet", ["6d2f3a"]), "living": ("parquet", ["6d4326", "5c3820", "7a4c2c"]),
                   "kitchen": ("tile_big", ["f2eee2", "2f3136"]), "bathroom": ("tile_big", ["f4f1ea", "cfc8b8"])},
        "walls": {"bedroom": "a68a5a", "living": "3e5a4c", "kitchen": "dcd6c0", "bathroom": "b7ad94"},
        "views": ("park", "park_b", "park"), "bed_w": 2.15, "wood": "4a2c18", "head": "6d2f3a", "duvet": "8a2f3c", "posts": True,
        "art": ("c9a24a", "3e5a4c", "8a2f3c"), "sofa": "2f4a3d", "sofa_arm": "263c32", "seats": 3, "rug": "8a2f3c",
        "bed_rug": "d9c27e", "chair": "8a2f3c", "fire": "ece6d6", "dresser": True, "plant_r": 0.3, "cab": "e6dfc8", "door": "f2ecd8",
        "top": "2f3136", "pan": "c47a44", "splash": ("f4f1ea", "cfc8b8"), "chairs": "4a2c18", "island": True, "cabs": 5,
        "wash": "roll", "suite": "fbf8f0", "metal": "d4af37", "double": True, "tile_rows": 5, "tiles": ("f4f1ea", "cfc8b8"),
        "mat": "8a2f3c", "t_plant": True, "frame": "e8dcb4",
        "deco": {"bedroom": ("panels", "b89a68"), "living": ("panels", "4a6a5a"), "kitchen": ("panels", "cfc8ae")},
    },
}

HOMES = {"rental": rental}
for _id, _spec in SPECS.items():
    HOMES[_id] = lambda s=_spec: home(s)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:]
    OUT = os.path.abspath(args[1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    HOMES[args[0]]()
    H.bake_groups()
    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_vertex_color="ACTIVE",
                              export_materials="NONE", export_texcoords=False)
    print("HOME", args[0], {k: len(v) for k, v in H.LAYERS.items()})
