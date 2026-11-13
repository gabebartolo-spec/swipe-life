"""Build one home's setting (GDD 10.9): the place a room scene sits in, fading into a soft sky.

Run headless:
  blender -b --factory-startup --python tools/blender/build_clay_setting.py -- <kind> <out.glb>
Hand edits (moved, turned, resized or removed pieces) come from tools/blender/setting_edits/<kind>.json;
tools/edit_setting.sh opens a setting in Blender to make them (docs/SETTING_EDITS.md).

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
import setting_edit as E  # noqa: E402

box, ball, tube = R.box, R.ball, R.tube
# ground ends at x + z = -HORIZON; a setting with a house or trees standing far back runs its grass on past them
_KIND = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else ""
HORIZON = 11.0 if _KIND in ("suburb", "new_suburb", "tired_street", "grounds") else 7.2
HAZE = (-4.0, -HORIZON)  # x + z where the fade starts and where it is strongest
HAZE_MAX = 0.18
EDGE = 1.2  # x + z depth over which the ground dissolves into the horizon colour
STOREY = 2.9  # a real storey at the room's scale (its wall is 2.8 high)  # a light tint toward the horizon colour, never a fog
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


# The drive's surface spans x, z within +-DRIVE and tops out at y -0.05 here (render_house.gd lifts the setting
# 0.1 to the room's 0.05); level pieces round it top out at -0.055 so they meet it without a step.
DRIVE = 2.05
LEVEL_H = 0.045  # top -0.055: flush with the drive; built round it (level_round), never under it, so no clay pokes
LAWN_TOP = -0.055  # a raised ground's top: level with the drive (-0.05), so the drive lies in the lawn, not on a step
LO, HI = -1.4, 1.6  # a house drive's sides (z): the garage door (-1.2..1.4) plus 0.2 either side



def ground(col, y=-0.12, back=HORIZON, lawn=None):
    """A clay board whose far edge is x + z = -back, dense enough to carry baked contact shadows. Where
    `lawn(x, z)` holds its top is LAWN_TOP (level with the drive) instead of y; it slopes down within one cell
    (0.2 m), which callers keep under a pavement or down a bank."""
    # cells of 0.2 m on the x and z lines, so the drive's edges (z -1.4 and 1.6) lie on grid lines: a grid at 45
    # degrees to them bakes their contact shadow as a staircase of dark teeth
    c = 0.2
    lo = -round((back / 2 + 9.4) / c)
    hi = round(13 / c)
    n = hi - lo + 1
    verts = []
    for i in range(n):
        for k in range(n):
            gx, gz = (lo + i) * c, (lo + k) * c
            d = -back - (gx + gz)
            if d > 0:  # beyond the far edge: pulled on to it
                gx, gz = gx + d / 2, gz + d / 2
            verts.append(g(gx, LAWN_TOP if lawn and lawn(gx, gz) else y, gz))
    faces = []
    for i in range(n - 1):
        for k in range(n - 1):
            if (lo + i + 1) + (lo + k + 1) > -back / c:  # a cell wholly beyond the edge would only collapse
                faces.append((i * n + k, (i + 1) * n + k, (i + 1) * n + k + 1, i * n + k + 1))
    me = bpy.data.meshes.new("ground")
    me.from_pydata(verts, [], faces)
    if me.polygons[0].normal.z < 0:
        me.flip_normals()
    ob = bpy.data.objects.new("ground", me)
    bpy.context.collection.objects.link(ob)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    m = ob.modifiers.new("solid", "SOLIDIFY")
    m.thickness = 0.3
    # exactly flat: a lumpy lawn rises through the drive's edge and bakes a sawtooth of dark teeth along it
    return R.finish(ob, col, bevel=0, subd=0, lump=0)


def clip_to_horizon(pts):
    """Clips a polygon of Godot (x, z) points to the ground, x + z >= -HORIZON (nothing hangs in the sky)."""
    out = []
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        da, db = a[0] + a[1] + HORIZON, b[0] + b[1] + HORIZON
        if da >= 0:
            out.append(a)
        if (da >= 0) != (db >= 0):
            t = da / (da - db)
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def patch(name, verts_xz, col, y=-0.1, h=0.06):
    """A flat clay piece (road, path, sand) over the ground, from Godot (x, z) corners in order round the edge."""
    pts = clip_to_horizon(verts_xz)
    verts = [g(x, y + h, z) for x, z in pts]
    face = list(range(len(verts)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [face])
    if me.polygons[0].normal.z < 0:  # face up, so the solidify grows down into the ground
        me.clear_geometry()
        me.from_pydata(verts, [], [face[::-1]])
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    m = ob.modifiers.new("solid", "SOLIDIFY")
    m.thickness = h
    # cells of ~0.12 m, so a contact shadow baked into the vertex colours stays where it falls, not smeared
    # over a whole coarse cell
    span = max(max(x for x, _ in pts) - min(x for x, _ in pts), max(z for _, z in pts) - min(z for _, z in pts))
    sub = ob.modifiers.new("subd", "SUBSURF")
    sub.levels = sub.render_levels = min(max(math.ceil(math.log2(span / 0.12)), 3), 6)
    sub.subdivision_type = "SIMPLE"
    # exactly flat: a displaced top dips millimetres under its neighbour and bakes a dark sawtooth at the seam
    return R.finish(ob, col, bevel=0, subd=0, lump=0)


def strip_x(name, x0, x1, col, y=-0.1, h=0.06, z0=-HORIZON - 9, z1=12):
    """A strip running along z (parallel to the street) between x0 and x1."""
    return patch(name, [(x0, z1), (x1, z1), (x1, z0), (x0, z0)], col, y, h)


def strip_z(name, z0, z1, col, y=-0.1, h=0.06, x0=-HORIZON - 9, x1=12):
    return patch(name, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], col, y, h)


def level_round(name, x0, x1, z0, z1, col, hole=(-DRIVE, DRIVE)):
    """A level surface over x0..x1, z0..z1, flush with the drive and cut round it (a ring of four strips; `hole` is
    the drive's z sides). The ring tucks 4 cm under the drive's edge so no ground shows in the seam."""
    d = DRIVE - 0.04
    lo, hi = hole[0] + 0.04, hole[1] - 0.04
    strip_z(f"{name}_back", z0, lo, col, h=LEVEL_H, x0=x0, x1=x1)
    strip_z(f"{name}_front", hi, z1, col, h=LEVEL_H, x0=x0, x1=x1)
    if x0 < -d:
        strip_x(f"{name}_side", x0, -d, col, h=LEVEL_H, z0=lo, z1=hi)
    if x1 > d:
        strip_x(f"{name}_street", d, x1, col, h=LEVEL_H, z0=lo, z1=hi)


def flat(name, x0, x1, z0, z1, col):
    """A piece of the drive's own surface (top -0.05, the room's drive height): baked here with the ground round it
    so the two match in tone; render_house.gd hides the room's own drive surface in the setting shot."""
    return patch(name, [(x0, z1), (x1, z1), (x1, z0), (x0, z0)], col, y=-0.1, h=0.05)


KERB = 3.9  # x of the road's kerb (road_x's x0 in every setting)


def house_drive(col, to=DRIVE):
    """A house's drive: garage-door width (LO..HI) from the house to the pavement (`to`), which runs on across its
    mouth undisturbed; lawn either side of it, and a path along the house front either side of it (to the side gate
    on the left, the front door on the right)."""
    flat("drive", -2.1, to, LO, HI, col)
    flat("path_l", -2.1, -1.3, HI, 2.0, col)
    flat("path_r", -2.1, -1.3, -2.3, LO, col)


def front_lawn(x, z):
    """Where a house setting's ground is level with the drive: everything short of the pavement's far half."""
    return x < DRIVE + 0.25


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


def wire_mesh(n, a0, a1, h, to3d, col="b9bec2", cell=0.16):
    """Diamond chain-link wire between a0 and a1 along the fence, 0..h high; to3d(a, y) gives the Godot point."""
    lo, hi = min(a0, a1), max(a0, a1)
    verts, faces = [], []
    for j in range(int(2 * h / cell) + 1):
        cy = j * cell / 2
        if cy - cell / 2 < 0 or cy + cell / 2 > h:
            continue
        for i in range(int((hi - lo) / cell) + 1):
            cx = lo + i * cell + (j % 2) * cell / 2
            if cx - cell / 2 < lo or cx + cell / 2 > hi:
                continue
            k = len(verts)
            for a, y in ((cx - cell / 2, cy), (cx, cy - cell / 2), (cx + cell / 2, cy), (cx, cy + cell / 2)):
                verts.append(g(*to3d(a, y - 0.08)))
            faces.append((k, k + 1, k + 2, k + 3))
    me = bpy.data.meshes.new(n)
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new(n, me)
    bpy.context.collection.objects.link(ob)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.remove_doubles(threshold=0.001)
    bpy.ops.object.mode_set(mode="OBJECT")
    w = ob.modifiers.new("wire", "WIREFRAME")
    w.thickness = 0.014
    return R.finish(ob, col, bevel=0, subd=0, lump=0)


def chainlink_x(n, x, z0, z1, h=1.4):
    for i in range(int(abs(z1 - z0) / 2.0) + 1):
        tube(f"{n}_post{i}", (x, h / 2 - 0.1, min(z0, z1) + i * 2.0), 0.035, h, "8e9297", lump=0)
    wire_mesh(f"{n}_mesh", z0, z1, h - 0.1, lambda a, y: (x, y, a))
    tube(f"{n}_top", (x, h - 0.12, (z0 + z1) / 2), 0.025, abs(z1 - z0), "8e9297", rot=(math.radians(90), 0, 0), lump=0)


def chainlink_z(n, z, x0, x1, h=1.4):
    for i in range(int(abs(x1 - x0) / 2.0) + 1):
        tube(f"{n}_post{i}", (min(x0, x1) + i * 2.0, h / 2 - 0.1, z), 0.035, h, "8e9297", lump=0)
    wire_mesh(f"{n}_mesh", x0, x1, h - 0.1, lambda a, y: (a, y, z))
    tube(f"{n}_top", ((x0 + x1) / 2, h - 0.12, z), 0.025, abs(x1 - x0), "8e9297", rot=(0, math.radians(90), 0), lump=0)


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
    h = floors * STOREY + 0.2
    box(f"{n}_body", (x, h / 2 - 0.1, z), (w, h, d), col, bevel=0.08, lump=0.008)
    prism(f"{n}_roof", (x, h - 0.1 + 0.9, z), (w + 0.5, 1.8, d + 0.5), roof, along_x=ridge_x, bevel=0.05,
          lump=0.008)
    windows_on(n + "x", "x", (x, z), w, d, h, floors, 2, y0=0.05, fh=STOREY)
    windows_on(n + "z", "z", (x, z), w, d, h, floors, 2, y0=0.05, fh=STOREY)
    box(f"{n}_door", (x + w / 2 + 0.02, 1.0, z + d * 0.05), (0.06, 2.1, 0.95), door, bevel=0.02, lump=0)
    if peel:
        for i in range(4):
            ball(f"{n}_peel{i}", (x + w / 2 + 0.01, 0.4 + rng.random() * (h - 0.8), z + (rng.random() - 0.5) * d * 0.8),
                 0.22, "c9bba0", scale=(0.05, 0.7, 1.1))


def block(n, x, z, w, d, floors, col, win="2f4858", trim="e6dfd2", balcony=False):
    """An apartment block with a flat roof parapet."""
    fh = STOREY
    h = floors * fh + 0.25
    box(f"{n}_body", (x, h / 2 - 0.1, z), (w, h, d), col, bevel=0.08, lump=0.008)
    box(f"{n}_parapet", (x, h - 0.05, z), (w + 0.12, 0.16, d + 0.12), trim, bevel=0.04)
    per_x, per_z = max(2, int(d / 1.6)), max(2, int(w / 1.6))
    windows_on(n + "x", "x", (x, z), w, d, h, floors, per_x, col=win, frame=trim, y0=0.15, fh=fh)
    windows_on(n + "z", "z", (x, z), w, d, h, floors, per_z, col=win, frame=trim, y0=0.15, fh=fh)
    if balcony:
        for f in range(1, floors):
            box(f"{n}_bal{f}", (x + w / 2 + 0.45, 0.15 + f * fh - 0.05, z), (0.9, 0.12, d * 0.4), trim, bevel=0.03)


def lamp(n, x, z, h=2.6):
    tube(f"{n}_pole", (x, h / 2 - 0.1, z), 0.05, h, "3a3d42", lump=0)
    box(f"{n}_head", (x, h - 0.05, z), (0.36, 0.14, 0.2), "3a3d42", bevel=0.04, lump=0)
    ball(f"{n}_bulb", (x, h - 0.16, z), 0.1, "fff3c4", scale=(1.3, 0.5, 0.9), lump=0)


def road_x(x0, x1, kerb_col="cfcac0", walk="d8d2c6", tar="74767c", line=True, crack=False, drive=None, mouth=DRIVE,
           footpath=True):
    """Pavement from the drive's street edge to x0, kerb, then the road out to x1 (along z). With `drive` set the
    kerb drops at the mouth (z within `mouth`); the pavement runs on across it undisturbed (`footpath`), or, for a
    flat's bay, the caller's surface runs on across the pavement to x0 in one piece, 1 cm under it either side."""
    if drive and footpath:
        lo, hi = (-mouth, mouth) if isinstance(mouth, float) else mouth
        strip_x("pavement", DRIVE, x0, walk)
        strip_x("kerb_drop", x0, x0 + 0.18, kerb_col, h=0.05, z0=lo, z1=hi)
        strip_x("kerb", x0, x0 + 0.18, kerb_col, h=0.1, z1=lo)
        strip_x("kerb_b", x0, x0 + 0.18, kerb_col, h=0.1, z0=hi)
    elif drive:
        lo, hi = (-mouth, mouth) if isinstance(mouth, float) else mouth
        strip_x("pavement", DRIVE, x0, walk, z1=lo)
        strip_x("pavement_b", DRIVE, x0, walk, z0=hi)
        strip_x("kerb_drop", x0, x0 + 0.18, kerb_col, h=0.05, z0=lo, z1=hi)
        strip_x("kerb", x0, x0 + 0.18, kerb_col, h=0.1, z1=lo)
        strip_x("kerb_b", x0, x0 + 0.18, kerb_col, h=0.1, z0=hi)
    else:
        strip_x("pavement", DRIVE, x0, walk)
        strip_x("kerb", x0, x0 + 0.18, kerb_col, h=0.1)
    strip_x("road", x0 + 0.18, x1, tar, h=0.02)  # top -0.08
    if line:
        mid = (x0 + 0.18 + x1) / 2
        for i in range(-8, 6):
            box(f"dash{i}", (mid, -0.075, i * 1.6), (0.12, 0.02, 0.8), "f2efe6", bevel=0.01, subd=1, lump=0)
    if crack:
        for i in range(5):  # on the road, clear of the kerb
            c = box(f"crack{i}", (x0 + 0.6 + rng.random() * 0.8, -0.078, -3 + i * 1.5),
                    (0.03, 0.01, 0.5 + rng.random()), "55575c", bevel=0.005, subd=0, lump=0)
            turn(c, 2, rng.random() - 0.5)


def bay_lines(zs, x=0.0, length=3.4):
    for i, z in enumerate(zs):
        box(f"bayline{i}", (x, -0.045, z), (length, 0.02, 0.1), "f2efe6", bevel=0.01, subd=1, lump=0)


def tufts(n, area, count, col="7f9a48", tall=0.35, far=-HORIZON + 0.4):
    (xa, xb), (za, zb) = area
    for i in range(count):
        x, z = xa + rng.random() * (xb - xa), za + rng.random() * (zb - za)
        if abs(x) < 2.4 and abs(z) < 2.4 or x + z < far:
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


def home_body(col, h, roof=None, trim=None, floors=0, win="2f4858", chim=None):
    """The home the driveway belongs to: its body stands flush behind the room's wall (x -2.3..-2.0, z -2.3..2.0,
    2.8 high), so that wall reads as the house's garage side and not a lone panel. `floors` window rows above it."""
    x0, x1, z0, z1 = -6.4, -2.02, -2.3, 2.0
    w, d, cx, cz = x1 - x0, z1 - z0, (x0 + x1) / 2, (z0 + z1) / 2
    box("home_body", (cx, h / 2 - 0.1, cz), (w, h, d), col, bevel=0.08, lump=0.008)
    if roof:
        prism("home_roof", (cx, h - 0.1 + 0.9, cz), (w + 0.5, 1.8, d + 0.5), roof, along_x=False, bevel=0.05,
              lump=0.008)
    if trim:
        box("home_parapet", (cx, h - 0.05, cz), (w + 0.12, 0.16, d + 0.12), trim, bevel=0.04)
    if floors:
        fh = (h - 3.0) / floors
        windows_on("home_x", "x", (cx, cz), w, d, h, floors, 3, col=win, y0=2.9, fh=fh)
    windows_on("home_z", "z", (cx, cz), w, d, h, max(1, floors + 1), 2, col=win, y0=0.05, fh=(h - 0.3) / (floors + 1))
    if chim:
        chimney("home_chim", -4.6, h + 0.5, chim)


def next_door(n, col, roof, peel=False):
    """The house next door on the right (beyond the plot line at z -2.3), set back in line with this one, so the
    ground over the drive's far side runs to a house front and not to open sky."""
    house(n, -4.6, -5.8, 4.0, 4.4, col, roof, ridge_x=False, peel=peel)  # x -6.6..-2.6, z -8.0..-3.6


def neighbour(n, col, roof, peel=False, x_front=-3.0):
    """The house next door on the left, its roof and chimney rising over the left wall."""
    house(n, x_front - 2.0, 1.6, 4.0, 4.4, col, roof, ridge_x=False, peel=peel)
    chimney(f"{n}_chim", x_front - 1.2, 3.0, 2.6)


def suburb(young=False):
    """Family house and childhood home: a suburban street with fences, lawns and big trees. Starter house (young):
    the same street newer, with small trees and low fences."""
    ground("86b05e" if young else "7aa85a", lawn=front_lawn)
    drive = "b9b1a3" if young else "c8bfae"
    house_drive(drive)
    road_x(KERB, 12, drive=drive, mouth=(LO, HI))
    if young:
        picket_z("front", 3.3, -7.0, 2.0, h=0.5, col="f4f0e6")
        home_body("c4785a", 3.2, roof="b5654a")
        tree("tr", -0.4, -3.4, h=4.0, r=0.85, kind="young")
        tree("tr2", 1.8, -4.6, h=3.6, r=0.75, kind="young")
        bush("b0", -4.2, 2.9, 0.3)
        next_door("nd", "d9cbb0", "8f6a52")
    else:
        picket_z("front", 3.3, -7.0, 2.0)
        home_body("b8694c", 6.0, roof="8f4f3a", floors=1, chim=-1.0)
        tree("tr", -0.3, -3.4, h=5.5, r=1.5, leaf="5f9447")
        board_fence_z("back", -2.95, -2.4, 2.0, h=1.8)  # the plot line, between the houses, not over the road
        next_door("nd", "e0d2b8", "7c5a48")
        tree("tr2", 3.6, -6.4, h=4.2, r=1.2)
        bush("b0", -4.4, 2.8, 0.36)
        bush("b1", -3.6, 2.85, 0.3, "6a9a4e")


def flats():
    """Small flat: brick apartment blocks in town, a pavement and a street tree."""
    ground("b9b2a6")
    level_round("forecourt", -9, DRIVE, -HORIZON - 9, 12, "b9b2a6", hole=(-1.25, 1.45))  # paved, level with the bay
    flat("bay", -2.1, KERB, -1.25, 1.45, "66676c")  # the bay's tarmac, on across the pavement to the kerb
    bay_lines((-1.2, 1.4))
    road_x(KERB, 12, drive="66676c", mouth=(-1.25, 1.45), footpath=False)
    block("home", -5.25, 1.85, 5.6, 8.3, 6, "e2d6c0", trim="cfc4ac")  # the bay's own block
    block("br", -1.9, -6.2, 7.6, 3.6, 3, "c27a56", trim="ece4d6")  # x -5.7..1.9, behind the pavement
    # its ground-floor entrance, left of the tree's crown (screen x 1.2 vs the crown's 1.7..4.1): the frame top
    # cuts the door ~0.9 m up, so its foot, frame and step show with the door above them
    box("br_doorframe", (-2.6, 1.05, -4.37), (1.1, 2.2, 0.06), "ece4d6", bevel=0.02, lump=0)
    box("br_door", (-2.6, 1.0, -4.33), (0.9, 2.0, 0.05), "2f4858", bevel=0.015, subd=1, lump=0)
    box("br_step", (-2.6, 0.02, -4.12), (1.4, 0.14, 0.46), "cfc8bc", bevel=0.03)
    # the forecourt tree stands between the bay and the entrance path, 4.3 m from the door, clear of both
    box("grate", (1.4, -0.05, -2.7), (0.9, 0.012, 0.9), "4a4c52", bevel=0.004, lump=0)  # 1 cm proud: set in
    tree("st0", 1.4, -2.7, h=5.0, r=1.2, leaf="6a9a4c")
    box("planter", (-3.6, 0.15, 3.0), (1.6, 0.5, 0.6), "8a8378", bevel=0.05)
    bush("pb0", -3.9, 3.0, 0.3, "6a9a4a")
    bush("pb1", -3.3, 3.0, 0.28, "5f8f4a")


def lowrise():
    """Rental: the tenant's bay is one of a row in front of the block, in a level car park; a plain aisle runs past
    the bays' open ends (+x); the car park ends at a kerb, grass and a chain-link boundary fence, then the next block."""
    ground("82a05e")
    # the bay's tarmac (6b6b70) bakes 15% lighter in the home than this does in the setting: matched as rendered
    flat("carpark", -2.45, 12, -3.9, 12, "7b7b81")  # one surface, the tenant's bay included
    strip_z("wheel_kerb", -4.05, -3.9, "c9c4b8", h=0.1, x0=-2.45, x1=12)
    bay_lines((-3.8, -1.2, 1.4, 4.0, 6.6, 9.2))  # 2.6 m bays; render_house.gd parks neighbours' cars in two
    block("home", -5.25, 1.85, 5.6, 8.3, 3, "d8cdb8", win="4a5c68", trim="c7bca4")  # the bay's own block
    chainlink_z("fence", -4.6, -2.45, 12, h=1.4)
    block("br", 2.0, -7.2, 7.0, 3.2, 2, "d8ccb2", win="4a5c68", trim="c7bca4")


def tired_street():
    """Fixer-upper: a tired older street, overgrown lawn, a leaning fence and peeling neighbours."""
    ground("8f9e58", lawn=front_lawn)
    house_drive("a49a88")
    road_x(KERB, 12, kerb_col="bcb5a6", walk="c6bfb0", tar="7c7a76", line=False, crack=True, drive="a49a88",
           mouth=(LO, HI))
    next_door("nd", "c9b99a", "6d5a4a", peel=True)
    picket_z("front", 3.3, -7.0, 2.0, col="d8d0bc", lean=0.2)
    home_body("b9a58a", 3.2, roof="6d5a4a", chim=-1.2)
    tube("pole", (-0.6, 4.4, -3.2), 0.13, 9.0, "6b5440")
    box("pole_arm", (-0.6, 8.4, -3.2), (1.6, 0.12, 0.14), "6b5440", bevel=0.02)
    tree("tr", 1.8, -4.4, h=5.2, r=1.3, leaf="7a964e")
    tufts("weed", ((-6.5, 2.0), (2.3, 3.2)), 16, col="9aa850", tall=0.45)
    tufts("weed_b", ((-2.5, 2), (-4.5, -2.5)), 18, col="9aa850", tall=0.5, far=HAZE[0])


def terrace():
    """Town house: a terraced row in the city, black railings and a street lamp."""
    ground("b7b0a4", lawn=front_lawn)
    house_drive("9c9890")
    road_x(KERB, 12, walk="c9c2b5", tar="65676c", drive="9c9890", mouth=(LO, HI))
    railing_z("rail", 3.2, -7.0, 2.0)
    lamp("lamp0", 2.65, -2.6, h=5.5)  # clear of the drive mouth
    home_body("8a5a48", 8.9, trim="efe8dc", floors=2, chim=-1.0)
    block("tl1", -4.21, 3.9, 4.38, 3.8, 3, "9b6a52", trim="efe8dc")  # next door in the row
    block("tr0", -4.21, -4.2, 4.38, 3.8, 3, "86584a", trim="efe8dc")  # next door the other way, on the building line
    chimney("tr0_chim", -5.2, 9.4, -4.6, "86584a")


def band(name, s0, s1, col, y=-0.1, h=0.06, across=24):
    """A piece covering x + z from s0 to s1 (lines the camera sees level), `across` wide."""
    pts = []
    for a, s in ((-across, s0), (across, s0), (across, s1), (-across, s1)):
        b = s / math.sqrt(2)
        pts.append(((a + b) / math.sqrt(2), (b - a) / math.sqrt(2)))
    return patch(name, pts, col, y, h)


def beach():
    """Seaside villa: a coastal road in front, sand and dune grass, the sea out to the horizon behind the villa."""
    shore = -4.8
    ground("e8d7ae", lawn=lambda x, z: front_lawn(x, z) and x + z > shore + 0.9)
    house_drive("e3d7bd")
    road_x(KERB, 12, kerb_col="e2d8c2", walk="e6d6b0", tar="8a8986", drive="e3d7bd", mouth=(LO, HI))
    band("wet_sand", shore + 0.6, shore, "d6c094", y=-0.12, h=0.03)
    band("sea", shore, -HORIZON - 0.01, "5f9ec4", y=-0.12, h=0.05)
    band("foam", shore + 0.1, shore - 0.12, "f4f6f2", y=-0.115, h=0.05)
    home_body("f4f0e6", 6.0, trim="e6e0d2", floors=1, win="4f7f9c")
    ball("dune0", (-1.0, -0.12, 3.7), 0.9, "e2cf9f", scale=(1.6, 0.35, 1.6), lump=0.03)
    tufts("grass0_", ((-2.2, 0.2), (2.5, 4.6)), 9, col="9aaa58", tall=0.45)
    palm("palm0", 0.3, -3.1, h=3.8)  # a young palm: a grown one (6 m+) puts its crown out of frame


def grounds():
    """Mansion: big grounds, a mown lawn, a gravel drive, clipped hedges and tall trees."""
    ground("6f9c50", lawn=front_lawn)
    house_drive("d9c9a6")  # the gravel forecourt carries it on
    strip_x("gravel", DRIVE, 12, "d9cfb8", h=0.05)  # the forecourt, level with the drive (top -0.05)
    for i in range(-3, 4):  # mown stripes on the lawn, kept out of the haze and off the drive and paths
        z0, z1 = i * 1.6 + 2.6, i * 1.6 + 3.4
        if z1 > -2.3 and z0 < 2.0:
            continue
        strip_z(f"stripe{i}", z0, z1, "7aa85a", y=-0.06, h=0.008, x0=-HORIZON - 9, x1=DRIVE - 0.05)
    box("hedge_f", (-2.6, 0.22, 3.2), (8.0, 0.65, 0.5), "4f7f3e", bevel=0.18, lump=0.02)
    for i, (x, z) in enumerate(((-3.2, -3.2),)):
        tube(f"cone_pot{i}", (x, 0.1, z), 0.3, 0.4, "d8cfb8")
        ball(f"cone{i}", (x, 0.95, z), 0.35, "4a7a3a", scale=(1, 2.4, 1), lump=0.02)
    home_body("d8cfb8", 8.9, roof="5a5f66", floors=2, chim=-1.0)
    tree("oak", -0.4, -3.6, h=6.0, r=1.8, leaf="5f8f45")
    for i, x in enumerate((2.2, 4.2)):
        tree(f"pr{i}", x, -3.6, h=8.0, r=1.0, kind="poplar", leaf="5a8545")
    for i, (x, z) in enumerate(((-0.6, -6.2), (-3.4, -4.6), (1.8, -7.4))):  # the belt of trees across the grounds
        tree(f"belt{i}", x, z, h=7.0, r=1.7, leaf="5a8a44")


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
    n = 96  # fine rows, so the colour at the horizon is the horizon colour, not a blend
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
        t = min(max((sy - horizon_sy - 0.15) / 1.6, 0.0), 1.0) ** 0.8  # horizon colour held just past the line
        cols[i].color = tuple(hz[k] + (zn[k] - hz[k]) * t for k in range(3)) + (1.0,)
        p = centre + CAM_X * (v.co.x * 16) + CAM_Y * sy
        v.co = g(p.x, p.y, p.z)
    ob["no_bake"] = True
    return ob


def bake_and_haze(horizon):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    R.use_gpu(scene)
    scene.render.bake.target = "VERTEX_COLORS"
    # No stand-ins for the room: the drive's surface is baked here now (a slab stand-in would black it out), the
    # garage wall stands flush against home_body, and a flat's bay has no wall at all.
    occ = []
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
        # ground pieces (nothing above the drive) dissolve into the sky over the last EDGE before the horizon, so
        # the ground has no hard far edge; standing things keep the light haze only
        low = max((mw @ v.co).z for v in ob.data.vertices) < 0.0
        if low:  # smooth shading bends a slab's top into its cut far edge, darkening the last metre
            ob.data.set_sharp_from_angle(angle=math.radians(45))
        for i, d in enumerate(ob.data.color_attributes["Col"].data):
            p = mw @ ob.data.vertices[i].co
            s = p.x + (-p.y)  # Godot x + z
            t = min(max((s - HAZE[0]) / (HAZE[1] - HAZE[0]), 0.0), 1.0)
            t = t * t * (3 - 2 * t) * HAZE_MAX
            if low:
                e = min(max((s + HORIZON - EDGE) / -EDGE, 0.0), 1.0)
                t = max(t, e * e * (3 - 2 * e))
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
    E.track(globals())
    SETTINGS[kind]()
    if "--edit" in args:  # the director's hand edits (docs/SETTING_EDITS.md): out is the .blend to edit in
        E.open_for_editing(kind, out, R.hexc)
    else:
        E.apply(kind)
        for ob in bpy.context.scene.objects:
            ob.name = "set__" + ob.name
        horizon, zenith = SKY.get(kind, SKY["default"])
        sky_card(horizon, zenith)
        bake_and_haze(horizon)
        bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_vertex_color="ACTIVE",
                                  export_materials="NONE", export_texcoords=False)
        print("SETTING", kind, len(bpy.context.scene.objects))
