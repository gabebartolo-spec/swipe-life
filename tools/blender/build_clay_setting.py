"""Build one home's setting (GDD 10.9): the place a room scene sits in, fading into a soft sky.

Run headless:
  blender -b --factory-startup --python tools/blender/build_clay_setting.py -- <kind> <out.glb>

Coordinates are Godot's, relative to the room's centre: the room's slab covers x, z -2.15..2.15 and its back walls
stand at x = -2.15 and z = -2.15. render_house.gd places one copy under each room it renders. The street runs along
+x (screen bottom right), where the driveway meets it. The ground ends on the line x + z = -HORIZON, which the
isometric camera sees as a level horizon near the top of the frame; past it is the sky card. Everything fades
toward the horizon colour with distance behind the room, baked into the vertex colours with the AO.
Render-only: the GLB is rebuilt for filming and never committed.
"""

import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_clay_room as R  # noqa: E402

box, ball, tube = R.box, R.ball, R.tube
HORIZON = 7.2  # ground ends at x + z = -HORIZON
HAZE = (-3.4, -HORIZON)  # x + z where the fade starts and where it is complete
SKY = {  # horizon, zenith
    "default": ("eef0ea", "a8c8e0"),
    "beach": ("eef3ef", "93c3e2"),
}
CAM_Z = Vector((0.57735, 0.57735, 0.57735))  # Godot camera back axis (render_house.gd)
CAM_Y = Vector((-0.408248, 0.816497, -0.408248))
CAM_X = Vector((0.707107, 0, -0.707107))
rng = random.Random(7)


def g(x, y, z):
    return R.g2b(x, y, z)


def ground(col, y=-0.12, back=HORIZON):
    """A clay board whose far edge is x + z = -back, dense enough to carry baked contact shadows."""
    n = 140
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=n, y_subdivisions=n, size=1)
    ob = bpy.context.object
    ob.name = "ground"
    for v in ob.data.vertices:
        a, b = v.co.x * 26, v.co.y * 26  # a across the view, b along it (toward the camera)
        b += 13 - back / math.sqrt(2) * 1.0
        gx = (b - a) / math.sqrt(2)
        gz = (b + a) / math.sqrt(2)
        v.co = g(gx, y, gz)
    m = ob.modifiers.new("solid", "SOLIDIFY")
    m.thickness = 0.3
    return R.finish(ob, col, bevel=0, subd=0, lump=0.01)


def patch(name, verts_xz, col, y=-0.1, h=0.06):
    """A flat clay piece (road, path, sand) over the ground, from Godot (x, z) corners."""
    bpy.ops.mesh.primitive_plane_add(size=1)
    ob = bpy.context.object
    ob.name = name
    bm_verts = ob.data.vertices
    for v, (x, z) in zip(bm_verts, verts_xz):
        v.co = g(x, y + h, z)
    m = ob.modifiers.new("solid", "SOLIDIFY")
    m.thickness = h
    sub = ob.modifiers.new("subd", "SUBSURF")
    sub.levels = sub.render_levels = 3
    sub.subdivision_type = "SIMPLE"
    return R.finish(ob, col, bevel=0, subd=0, lump=0.006)


def strip_x(name, x0, x1, col, y=-0.1, h=0.06, z0=-HORIZON - 9, z1=12):
    """A strip running along z (parallel to the street) between x0 and x1."""
    return patch(name, [(x0, z1), (x1, z1), (x1, z0), (x0, z0)], col, y, h)


def strip_z(name, z0, z1, col, y=-0.1, h=0.06, x0=-HORIZON - 9, x1=12):
    return patch(name, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], col, y, h)


def prism(name, center, size, col, along_x=True, **kw):
    """A gable roof: a box whose ridge runs along x (or z)."""
    ob = box(name, center, size, col, **kw)
    mid = g(*center)
    for v in ob.data.vertices:
        if v.co.z > mid.z:  # Blender z is up; pull the top to the ridge (the mesh holds world coordinates)
            if along_x:
                v.co.y = mid.y
            else:
                v.co.x = mid.x
    return ob


def turn(ob, axis, angle):
    """Rotates a piece about its own middle (the clay helpers bake the position into the mesh)."""
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    ob.rotation_euler[axis] = angle
    return ob


def tree(n, x, z, h=3.2, r=1.1, trunk="7a5a3e", leaf="6f9e52", kind="round"):
    tube(f"{n}_trunk", (x, h * 0.3 - 0.1, z), 0.11 + r * 0.04, h * 0.6, trunk)
    if kind == "poplar":
        ball(f"{n}_crown", (x, h * 0.62, z), r, leaf, scale=(0.55, 1.6, 0.55), lump=0.04)
        return
    if kind == "young":
        ball(f"{n}_crown", (x, h * 0.72, z), r, leaf, scale=(0.8, 1.05, 0.8), lump=0.03)
        return
    ball(f"{n}_crown", (x, h * 0.66, z), r, leaf, scale=(1, 0.9, 1), lump=0.05)
    for i in range(3):
        a = i * 2.1 + rng.random()
        ball(f"{n}_puff{i}", (x + math.cos(a) * r * 0.55, h * 0.6 + rng.random() * 0.3, z + math.sin(a) * r * 0.55),
             r * 0.62, leaf, lump=0.04)


def palm(n, x, z, h=3.6):
    for i in range(6):
        t = i / 6
        tube(f"{n}_seg{i}", (x + t * t * 0.5, 0.3 + t * h * 0.9, z), 0.12 - t * 0.03, h * 0.17, "a88a62")
    top = (x + 0.5, h, z)
    for i in range(7):
        a = i * math.tau / 7
        ball(f"{n}_frond{i}", (top[0] + math.cos(a) * 0.7, top[1] - 0.15, top[2] + math.sin(a) * 0.7), 0.45,
             "5f9a4a", scale=(1.6 if abs(math.cos(a)) > 0.5 else 0.5, 0.18, 0.5 if abs(math.cos(a)) > 0.5 else 1.6),
             lump=0.02)


def bush(n, x, z, r=0.45, col="5f8f4a"):
    ball(n, (x, r * 0.7 - 0.1, z), r, col, scale=(1, 0.85, 1), lump=0.04)


def picket_x(n, x, z0, z1, col="f4f0e6", h=0.75, lean=0.0):
    """Picket fence along z at x."""
    k = int(abs(z1 - z0) / 0.28)
    for i in range(k + 1):
        z = z0 + (z1 - z0) * i / k
        tilt = lean * (0.5 + rng.random()) if lean else 0
        p = box(f"{n}_p{i}", (x, h / 2 - 0.1, z), (0.06, h, 0.14), col, bevel=0.02, subd=1, lump=0.004)
        if tilt:
            turn(p, 1, tilt)  # Blender y = Godot -z: lean across the line
    for j, y in enumerate((h * 0.3, h * 0.72)):
        box(f"{n}_rail{j}", (x - 0.05, y - 0.1, (z0 + z1) / 2), (0.04, 0.07, abs(z1 - z0)), col, bevel=0.015)


def picket_z(n, z, x0, x1, col="f4f0e6", h=0.75, lean=0.0):
    k = int(abs(x1 - x0) / 0.28)
    for i in range(k + 1):
        x = x0 + (x1 - x0) * i / k
        p = box(f"{n}_p{i}", (x, h / 2 - 0.1, z), (0.14, h, 0.06), col, bevel=0.02, subd=1, lump=0.004)
        if lean:
            turn(p, 0, lean * (0.5 + rng.random()))
    for j, y in enumerate((h * 0.3, h * 0.72)):
        box(f"{n}_rail{j}", ((x0 + x1) / 2, y - 0.1, z - 0.05), (abs(x1 - x0), 0.07, 0.04), col, bevel=0.015)


def board_fence_x(n, x, z0, z1, col="b08a62", h=1.5):
    box(n, (x, h / 2 - 0.1, (z0 + z1) / 2), (0.08, h, abs(z1 - z0)), col, bevel=0.03, lump=0.006)
    for i in range(int(abs(z1 - z0) / 1.6) + 1):
        box(f"{n}_post{i}", (x + 0.06, h / 2 - 0.1, min(z0, z1) + i * 1.6), (0.12, h + 0.08, 0.12), "8f6c48",
            bevel=0.03)


def board_fence_z(n, z, x0, x1, col="b08a62", h=1.5):
    box(n, ((x0 + x1) / 2, h / 2 - 0.1, z), (abs(x1 - x0), h, 0.08), col, bevel=0.03, lump=0.006)
    for i in range(int(abs(x1 - x0) / 1.6) + 1):
        box(f"{n}_post{i}", (min(x0, x1) + i * 1.6, h / 2 - 0.1, z + 0.06), (0.12, h + 0.08, 0.12), "8f6c48",
            bevel=0.03)


def railing_z(n, z, x0, x1, col="2f3136", h=0.9):
    """Black iron railings along x at z."""
    k = int(abs(x1 - x0) / 0.18)
    for i in range(k + 1):
        x = x0 + (x1 - x0) * i / k
        tube(f"{n}_bar{i}", (x, h / 2 - 0.1, z), 0.022, h, col, lump=0)
        ball(f"{n}_tip{i}", (x, h - 0.08, z), 0.04, col, scale=(1, 1.6, 1), lump=0)
    for j, y in enumerate((0.1, h - 0.25)):
        box(f"{n}_rail{j}", ((x0 + x1) / 2, y, z), (abs(x1 - x0), 0.05, 0.05), col, bevel=0.015, lump=0)


def railing_x(n, x, z0, z1, col="2f3136", h=0.9):
    k = int(abs(z1 - z0) / 0.18)
    for i in range(k + 1):
        z = z0 + (z1 - z0) * i / k
        tube(f"{n}_bar{i}", (x, h / 2 - 0.1, z), 0.022, h, col, lump=0)
        ball(f"{n}_tip{i}", (x, h - 0.08, z), 0.04, col, scale=(1, 1.6, 1), lump=0)
    for j, y in enumerate((0.1, h - 0.25)):
        box(f"{n}_rail{j}", (x, y, (z0 + z1) / 2), (0.05, 0.05, abs(z1 - z0)), col, bevel=0.015, lump=0)


def chainlink_x(n, x, z0, z1, h=1.6):
    for i in range(int(abs(z1 - z0) / 2.0) + 1):
        tube(f"{n}_post{i}", (x, h / 2 - 0.1, min(z0, z1) + i * 2.0), 0.04, h, "9a9ea3", lump=0)
    box(f"{n}_mesh", (x, h / 2 - 0.1, (z0 + z1) / 2), (0.02, h * 0.95, abs(z1 - z0)), "b9bec2", bevel=0.005,
        subd=1, lump=0)
    tube(f"{n}_top", (x, h - 0.12, (z0 + z1) / 2), 0.03, abs(z1 - z0), "9a9ea3", rot=(math.radians(90), 0, 0), lump=0)


def chainlink_z(n, z, x0, x1, h=1.6):
    for i in range(int(abs(x1 - x0) / 2.0) + 1):
        tube(f"{n}_post{i}", (min(x0, x1) + i * 2.0, h / 2 - 0.1, z), 0.04, h, "9a9ea3", lump=0)
    box(f"{n}_mesh", ((x0 + x1) / 2, h / 2 - 0.1, z), (abs(x1 - x0), h * 0.95, 0.02), "b9bec2", bevel=0.005,
        subd=1, lump=0)
    tube(f"{n}_top", ((x0 + x1) / 2, h - 0.12, z), 0.03, abs(x1 - x0), "9a9ea3", rot=(0, math.radians(90), 0), lump=0)


def windows_on(n, face, c, w, d, h, floors, per, col="2f4858", frame="f4efe4", y0=0.0, fh=1.0):
    """Window grid on the camera-facing side of a building: face "x" (the +x side) or "z" (the +z side)."""
    x, z = c
    for f in range(floors):
        y = y0 + (f + 0.55) * fh
        for i in range(per):
            t = (i + 0.5) / per - 0.5
            if face == "x":
                p = (x + w / 2 + 0.02, y, z + t * d)
                box(f"{n}_win{f}_{i}", p, (0.05, fh * 0.48, d / per * 0.45), col, bevel=0.015, subd=1, lump=0)
                box(f"{n}_sill{f}_{i}", (p[0] + 0.03, y - fh * 0.27, p[2]), (0.07, 0.05, d / per * 0.55), frame,
                    bevel=0.015, lump=0)
            else:
                p = (x + t * w, y, z + d / 2 + 0.02)
                box(f"{n}_win{f}_{i}", p, (w / per * 0.45, fh * 0.48, 0.05), col, bevel=0.015, subd=1, lump=0)
                box(f"{n}_sill{f}_{i}", (p[0], y - fh * 0.27, p[2] + 0.03), (w / per * 0.55, 0.05, 0.07), frame,
                    bevel=0.015, lump=0)


def house(n, x, z, w, d, col, roof, ridge_x=True, floors=2, door="c0392b", peel=False):
    """A detached house: two floors, gable roof, windows and a door on both camera-facing sides."""
    h = floors * 1.15 + 0.2
    box(f"{n}_body", (x, h / 2 - 0.1, z), (w, h, d), col, bevel=0.08, lump=0.008)
    prism(f"{n}_roof", (x, h - 0.1 + 0.55, z), (w + 0.4, 1.1, d + 0.4), roof, along_x=ridge_x, bevel=0.05,
          lump=0.008)
    windows_on(n + "x", "x", (x, z), w, d, h, floors, 2, y0=0.05, fh=1.15)
    windows_on(n + "z", "z", (x, z), w, d, h, floors, 2, y0=0.05, fh=1.15)
    box(f"{n}_door", (x + w / 2 + 0.02, 0.45, z + d * 0.05), (0.06, 1.0, 0.5), door, bevel=0.02, lump=0)
    if peel:
        for i in range(4):
            ball(f"{n}_peel{i}", (x + w / 2 + 0.01, 0.4 + rng.random() * (h - 0.8), z + (rng.random() - 0.5) * d * 0.8),
                 0.22, "c9bba0", scale=(0.05, 0.7, 1.1))


def block(n, x, z, w, d, floors, col, win="2f4858", trim="e6dfd2", balcony=False):
    """An apartment block with a flat roof parapet."""
    fh = 0.95
    h = floors * fh + 0.25
    box(f"{n}_body", (x, h / 2 - 0.1, z), (w, h, d), col, bevel=0.08, lump=0.008)
    box(f"{n}_parapet", (x, h - 0.05, z), (w + 0.12, 0.16, d + 0.12), trim, bevel=0.04)
    per_x, per_z = max(2, int(d / 1.1)), max(2, int(w / 1.1))
    windows_on(n + "x", "x", (x, z), w, d, h, floors, per_x, col=win, frame=trim, y0=0.15, fh=fh)
    windows_on(n + "z", "z", (x, z), w, d, h, floors, per_z, col=win, frame=trim, y0=0.15, fh=fh)
    if balcony:
        for f in range(1, floors):
            box(f"{n}_bal{f}", (x + w / 2 + 0.25, 0.15 + f * fh - 0.05, z), (0.5, 0.08, d * 0.5), trim, bevel=0.03)


def lamp(n, x, z, h=2.6):
    tube(f"{n}_pole", (x, h / 2 - 0.1, z), 0.05, h, "3a3d42", lump=0)
    box(f"{n}_head", (x, h - 0.05, z), (0.36, 0.14, 0.2), "3a3d42", bevel=0.04, lump=0)
    ball(f"{n}_bulb", (x, h - 0.16, z), 0.1, "fff3c4", scale=(1.3, 0.5, 0.9), lump=0)


def road_x(x0, x1, kerb_col="cfcac0", walk="d8d2c6", tar="74767c", line=True, crack=False):
    """Pavement from the plot edge to x0, kerb, then the road out to x1 (along z)."""
    strip_x("pavement", 2.3, x0, walk)
    strip_x("kerb", x0, x0 + 0.18, kerb_col, h=0.1)
    strip_x("road", x0 + 0.18, x1, tar, h=0.02)
    if line:
        mid = (x0 + 0.18 + x1) / 2
        for i in range(-8, 6):
            box(f"dash{i}", (mid, -0.03, i * 1.6), (0.12, 0.02, 0.8), "f2efe6", bevel=0.01, subd=1, lump=0)
    if crack:
        for i in range(5):
            c = box(f"crack{i}", (x0 + 0.3 + rng.random() * 0.8, -0.035, -3 + i * 1.5),
                    (0.03, 0.01, 0.5 + rng.random()), "55575c", bevel=0.005, subd=0, lump=0)
            turn(c, 2, rng.random() - 0.5)


def tufts(n, area, count, col="7f9a48", tall=0.35):
    (xa, xb), (za, zb) = area
    for i in range(count):
        x, z = xa + rng.random() * (xb - xa), za + rng.random() * (zb - za)
        if abs(x) < 2.4 and abs(z) < 2.4:
            continue
        ball(f"{n}{i}", (x, -0.05 + tall * 0.3, z), 0.12, col, scale=(0.8, tall * 5, 0.8), lump=0.02)


# ---- settings -----------------------------------------------------------------------------------------------------
# What the camera sees of a setting: the ground in front of the slab (about 2.3 m on each front side: the street at
# +x, the garden at +z) and, over the two back walls, the tops of whatever stands behind them (x < -2.3 and z < -2.3),
# then the hazy ground running to the horizon and the sky. Positions below were checked by projecting them to the
# screen: sx = 0.707 (x - z), sy = -0.408 (x + z) + 0.816 (y - 1), frame |sx| < 3.36, |sy| < 2.8.


def chimney(n, x, y, z, col="9b5a46"):
    box(n, (x, y, z), (0.45, 1.0, 0.45), col, bevel=0.05, lump=0.006)
    box(f"{n}_cap", (x, y + 0.52, z), (0.55, 0.1, 0.55), "d8d0c0", bevel=0.03, lump=0)


def neighbour(n, col, roof, peel=False, x_front=-3.0):
    """The house next door on the left, its roof and chimney rising over the left wall."""
    house(n, x_front - 2.0, 1.6, 4.0, 4.4, col, roof, ridge_x=False, peel=peel)
    chimney(f"{n}_chim", x_front - 1.2, 3.0, 2.6)


def suburb(young=False):
    """Family house and childhood home: a suburban street with fences, lawns and big trees. Starter house (young):
    the same street newer, with small trees and low fences."""
    ground("86b05e" if young else "7aa85a")
    road_x(3.0, 12)
    if young:
        picket_z("front", 3.3, -7.0, 2.3, h=0.5, col="f4f0e6")
        neighbour("nl", "efe3c8", "b5654a")
        tree("tr", -0.4, -3.4, h=3.0, r=0.7, kind="young")
        tree("tr2", 1.8, -4.6, h=2.6, r=0.55, kind="young")
        picket_x("back", -2.6, -2.6, -9, h=0.55, col="efe9dc")
        bush("b0", -4.2, 2.9, 0.3)
        tree("st0", 2.7, 3.6, h=2.0, r=0.4, kind="young")
    else:
        picket_z("front", 3.3, -7.0, 2.3)
        neighbour("nl", "e9d7bb", "8f4f3a")
        tree("tr", -0.3, -3.4, h=4.0, r=1.15, leaf="5f9447")
        board_fence_z("back", -4.4, -2.6, 9)
        tree("tr2", 3.6, -6.4, h=4.2, r=1.2)
        bush("b0", -4.4, 2.8, 0.36)
        bush("b1", -3.6, 2.85, 0.3, "6a9a4e")


def flats():
    """Small flat: brick apartment blocks in town, a pavement and a street tree."""
    ground("b9b2a6")  # paved courtyard
    road_x(3.0, 12)
    block("bl", -5.2, 2.0, 4.4, 7.0, 6, "b5654a", trim="e6dccb", balcony=True)
    block("br", 1.6, -5.0, 7.0, 3.6, 3, "c27a56", trim="ece4d6")
    box("grate", (2.65, -0.04, 3.4), (0.7, 0.04, 0.7), "4a4c52", bevel=0.02, lump=0)
    tree("st0", 2.65, 3.4, h=2.6, r=0.6, kind="young")
    lamp("lamp0", 2.7, -3.0, h=3.0)
    box("planter", (-3.6, 0.15, 3.0), (1.6, 0.5, 0.6), "8a8378", bevel=0.05)
    bush("pb0", -3.9, 3.0, 0.3, "6a9a4a")
    bush("pb1", -3.3, 3.0, 0.28, "5f8f4a")


def lowrise():
    """Rental: plain two-storey flats round a car park, behind a chain-link fence."""
    ground("82a05e")
    strip_x("carpark", 2.3, 12, "6e7075", h=0.03)
    for i in range(-5, 4):
        box(f"bay{i}", (3.9, -0.03, i * 2.4 + 1.2), (3.0, 0.02, 0.09), "f2efe6", bevel=0.01, subd=1, lump=0)
    chainlink_z("fence", 3.3, -7.0, 2.3)
    block("bl", -5.2, 1.6, 3.8, 7.0, 2, "e2d6bc", win="4a5c68", trim="cfc4ac")
    chainlink_z("fence_b", -3.0, -2.4, 9)
    block("br", 2.0, -7.2, 7.0, 3.2, 2, "d8ccb2", win="4a5c68", trim="c7bca4")
    bush("b0", -0.8, -3.6, 0.5, "6f8f4a")
    tufts("weed", ((-6, 2.3), (2.3, 3.2)), 10)


def tired_street():
    """Fixer-upper: a tired older street, overgrown lawn, a leaning fence and peeling neighbours."""
    ground("8f9e58")
    road_x(3.0, 12, kerb_col="bcb5a6", walk="c6bfb0", tar="7c7a76", line=False, crack=True)
    picket_z("front", 3.3, -7.0, 2.3, col="d8d0bc", lean=0.2)
    neighbour("nl", "c7b48e", "6d5a4a", peel=True)
    tube("pole", (-0.6, 2.4, -3.2), 0.09, 5.0, "6b5440")
    box("pole_arm", (-0.6, 4.4, -3.2), (1.2, 0.1, 0.12), "6b5440", bevel=0.02)
    tree("tr", 1.8, -4.4, h=3.8, r=1.0, leaf="7a964e")
    picket_x("back", -2.6, -2.6, -9, col="cfc6ae", lean=0.16)
    tufts("weed", ((-6.5, 2.3), (2.3, 3.2)), 16, col="9aa850", tall=0.45)
    tufts("weed_b", ((-2.5, 6), (-6.5, -2.5)), 30, col="9aa850", tall=0.5)


def terrace():
    """Town house: a terraced row in the city, black railings and a street lamp."""
    ground("b7b0a4")
    road_x(3.0, 12, walk="c9c2b5", tar="65676c")
    railing_z("rail", 3.2, -7.0, 2.3)
    lamp("lamp0", 2.7, -3.0, h=3.2)
    for i, (z, col) in enumerate(((-0.4, "8a5a48"), (3.4, "9b6a52"))):
        block(f"tl{i}", -5.0, z, 4.0, 3.8, 3, col, trim="efe8dc")
        chimney(f"tl{i}_chim", -4.0, 3.3, z + 1.2, col)
    block("tr0", 1.8, -5.6, 3.8, 4.0, 3, "86584a", trim="efe8dc")
    chimney("tr0_chim", 2.8, 3.3, -4.6, "86584a")
    tree("st0", 2.65, 3.6, h=2.6, r=0.6, kind="young")


def band(name, s0, s1, col, y=-0.1, h=0.06, across=24):
    """A piece covering x + z from s0 to s1 (lines the camera sees level), `across` wide."""
    pts = []
    for a, s in ((-across, s0), (across, s0), (across, s1), (-across, s1)):
        b = s / math.sqrt(2)
        pts.append(((a + b) / math.sqrt(2), (b - a) / math.sqrt(2)))
    return patch(name, pts, col, y, h)


def beach():
    """Seaside villa: sand and dune grass running down to the sea, out to the horizon."""
    shore = -4.8
    ground("e8d7ae")
    band("wet_sand", shore + 0.6, shore, "d6c094", y=-0.12, h=0.03)
    band("sea", shore, -HORIZON - 0.01, "5f9ec4", y=-0.12, h=0.05)
    for i in range(16):  # waves breaking along the shore
        a = -10 + i * 1.3 + rng.random() * 0.4
        b = (shore - 0.15) / math.sqrt(2)
        f = ball(f"foam{i}", ((a + b) / math.sqrt(2), -0.07, (b - a) / math.sqrt(2)), 0.5, "f4f6f2",
                 scale=(1.3, 0.06, 0.32), lump=0.01)
        turn(f, 2, math.radians(45))
    for i, (x, z, r) in enumerate(((-4.4, 3.4, 0.9), (3.4, -2.8, 0.8))):
        ball(f"dune{i}", (x, -0.12, z), r, "e2cf9f", scale=(1.6, 0.35, 1.6), lump=0.03)
        tufts(f"grass{i}_", ((x - r, x + r), (z - r, z + r)), 7, col="9aaa58", tall=0.5)
    palm("palm0", -3.2, 0.9, h=3.0)
    tube("umb_pole", (3.1, 0.55, 1.2), 0.03, 1.3, "f4f0e6", lump=0)
    ball("umb", (3.1, 1.2, 1.2), 0.7, "e8805a", scale=(1, 0.32, 1), lump=0.01)
    box("towel", (3.5, -0.05, 0.3), (0.55, 0.02, 1.1), "5b93b8", bevel=0.01, subd=1, lump=0)


def grounds():
    """Mansion: big grounds, a mown lawn, a gravel drive, clipped hedges and tall trees."""
    ground("6f9c50")
    strip_x("gravel", 2.3, 12, "d9cfb8", h=0.04)
    for i in range(-8, 4):  # mown stripes
        strip_z(f"stripe{i}", i * 1.6 + 2.6, i * 1.6 + 3.4, "7aa85a", h=0.01, x0=-HORIZON - 9, x1=2.25)
    box("hedge_f", (-2.6, 0.22, 3.0), (8.0, 0.65, 0.5), "4f7f3e", bevel=0.18, lump=0.02)
    for i, (x, z) in enumerate(((2.75, 3.1), (-3.2, -3.2))):
        tube(f"cone_pot{i}", (x, 0.1, z), 0.3, 0.4, "d8cfb8")
        ball(f"cone{i}", (x, 0.95, z), 0.35, "4a7a3a", scale=(1, 2.4, 1), lump=0.02)
    for i, z in enumerate((-1.0, 1.4, 3.8)):
        tree(f"pl{i}", -3.4, z, h=4.6, r=0.7, kind="poplar", leaf="567f42")
    tree("oak", -0.4, -3.6, h=4.2, r=1.3, leaf="5f8f45")
    for i, x in enumerate((2.2, 4.2)):
        tree(f"pr{i}", x, -3.6, h=4.6, r=0.7, kind="poplar", leaf="5a8545")


SETTINGS = {
    "suburb": suburb,
    "new_suburb": lambda: suburb(young=True),
    "flats": flats,
    "lowrise": lowrise,
    "tired_street": tired_street,
    "terrace": terrace,
    "beach": beach,
    "grounds": grounds,
}


# ---- sky, bake, haze -----------------------------------------------------------------------------------------------


def sky_card(horizon, zenith):
    """A card square to the camera, far behind the room, coloured from the horizon line up."""
    n = 24
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=n, y_subdivisions=n, size=1)
    ob = bpy.context.object
    ob.name = "sky"
    centre = CAM_Z * -18.0 + Vector((0, 1.0, 0))
    ob.data.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    hz, zn = R.hexc(horizon), R.hexc(zenith)
    horizon_sy = HORIZON * 0.408248 - 0.816497  # screen height of the ground's far edge (camera at y 1)
    cols = ob.data.color_attributes["Col"].data
    for i, v in enumerate(ob.data.vertices):
        sy = v.co.y * 14
        t = min(max((sy - horizon_sy) / 1.6, 0.0), 1.0) ** 0.8
        cols[i].color = tuple(hz[k] + (zn[k] - hz[k]) * t for k in range(3)) + (1.0,)
        p = centre + CAM_X * (v.co.x * 16) + CAM_Y * sy
        v.co = g(p.x, p.y, p.z)
    ob["no_bake"] = True
    return ob


def bake_and_haze(horizon):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.render.bake.target = "VERTEX_COLORS"
    # The room itself casts the contact shadows on the ground around it; removed after the bake.
    slab = box("occ_slab", (0, -0.2, 0), (4.3, 0.4, 4.3), "ffffff", bevel=0, subd=0, lump=0)
    wx = box("occ_wx", (-2.3, 1.4, 0), (0.3, 2.8, 4.3), "ffffff", bevel=0, subd=0, lump=0)
    wz = box("occ_wz", (0, 1.4, -2.3), (4.3, 2.8, 0.3), "ffffff", bevel=0, subd=0, lump=0)
    occ = [slab, wx, wz]
    obs = [o for o in scene.objects if o.type == "MESH" and o not in occ and "no_bake" not in o]
    for ob in obs + occ:
        bpy.context.view_layer.objects.active = ob
        for m in list(ob.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects["sky"].hide_render = True
    for ob in obs:
        ob.data.shade_smooth()
        ob.data.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        ob.data.attributes.active_color = ob.data.color_attributes["Col"]
        ob.data.materials.append(bpy.data.materials.new(ob.name))
    bpy.ops.object.select_all(action="DESELECT")
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.bake(type="AO")
    hz = R.hexc(horizon)
    for ob in obs:
        c = R.hexc(ob["clay_color"]) if "clay_color" in ob else (0.8, 0.8, 0.8)
        mw = ob.matrix_world
        for i, d in enumerate(ob.data.color_attributes["Col"].data):
            p = mw @ ob.data.vertices[i].co
            s = p.x + (-p.y)  # Godot x + z
            t = min(max((s - HAZE[0]) / (HAZE[1] - HAZE[0]), 0.0), 1.0)
            t = t * t * (3 - 2 * t)
            ao = 0.35 + 0.65 * d.color[0]
            d.color = tuple(c[k] * ao * (1 - t) + hz[k] * t for k in range(3)) + (1.0,)
        ob.data.materials.clear()
    bpy.data.objects["sky"].hide_render = False
    for o in occ:
        bpy.data.objects.remove(o, do_unlink=True)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:]
    kind, out = args[0], os.path.abspath(args[1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    SETTINGS[kind]()
    for ob in bpy.context.scene.objects:
        ob.name = "set__" + ob.name
    horizon, zenith = SKY.get(kind, SKY["default"])
    sky_card(horizon, zenith)
    bake_and_haze(horizon)
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_vertex_color="ACTIVE",
                              export_materials="NONE", export_texcoords=False)
    print("SETTING", kind, len(bpy.context.scene.objects))
