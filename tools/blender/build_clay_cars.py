"""Build the cars (GDD 15.5 driveway) as clay props, separate from items.glb to keep both small.

Run headless:
  blender -b --factory-startup --python tools/blender/build_clay_cars.py -- <out.glb>

One mesh per car id in data/property/items.json (slot "car"), facing +z, origin at the middle of its base.
Each fits the 4 x 4 m driveway: length <= 4.4 m along z.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_clay_items as I  # noqa: E402

box, ball, tube = I.box, I.ball, I.tube
at, n, p, car = I.at, I.n, I.p, I._car
DARK, CHROME, CREAM = "26282d", "c9ccd1", "f4efe4"


def stripes(y, z, length, col=CREAM, gap=0.4):
    for i, dx in enumerate((-gap, gap)):
        box(n(f"stripe{i}"), p(dx, y, z), (0.14, 0.02, length), col, bevel=0.01)


def spoiler(y, z, w=1.4, base=None):
    """A rear wing at height y on two stalks standing on the deck (or on `base`)."""
    base = CUR["top"] - 0.04 if base is None else base
    ball(n("spoiler"), p(0, y, z), 0.2, DARK, scale=(w / 0.4, 0.2, 0.95), lump=0)  # curved aerofoil
    for i, sx in enumerate((-1, 1)):
        box(n(f"endplate{i}"), p(sx * w / 2, y - 0.03, z), (0.03, 0.2, 0.42), DARK, bevel=0.012, lump=0)
    for i, dx in enumerate((-w / 3, w / 3)):
        box(n(f"stalk{i}"), p(dx, (y + base) / 2, z + 0.02), (0.06, y - base + 0.04, 0.12), DARK, bevel=0.02, lump=0)


def rails(y, z, length=1.6):
    """Roof rack: two side rails and three cross bars."""
    for i, dx in enumerate((-0.45, 0.45)):
        box(n(f"rail{i}"), p(dx, y, z), (0.06, 0.06, length), DARK, bevel=0.02, lump=0)
    for i, dz in enumerate((-length / 3, 0, length / 3)):
        box(n(f"cross{i}"), p(0, y + 0.04, z + dz), (1.0, 0.04, 0.06), DARK, bevel=0.015, lump=0)


def bull_bar(hl, wr, h):
    for i, sx in enumerate((-0.35, 0.35)):
        rod(f"bull{i}", (sx, wr * 0.5, hl + 0.12), (sx, wr + h * 0.75, hl + 0.12), 0.045, DARK)
    rod("bull_top", (-0.4, wr + h * 0.75, hl + 0.12), (0.4, wr + h * 0.75, hl + 0.12), 0.045, DARK)


def bed(w, wheel_r, h, z0, z1, col):
    """An open pickup bed from z0 to z1 behind the cab. Its walls sink 0.15 into the body, whose rounded top edge
    otherwise drops away under them and leaves a see-through slit."""
    y = wheel_r + h
    yc, hh = y + 0.125, 0.55  # wall centre and height: top at y + 0.4, bottom 0.15 inside the body
    for i, sx in enumerate((-1, 1)):
        box(n(f"bedside{i}"), p(sx * (w / 2 - 0.06), yc, (z0 + z1) / 2), (0.12, hh, z1 - z0), col, bevel=0.04)
    box(n("tailgate"), p(0, yc, z0 + 0.06), (w - 0.1, hh, 0.12), col, bevel=0.04)
    box(n("bulkhead"), p(0, yc, z1 - 0.15), (w - 0.1, hh, 0.14), col, bevel=0.04)  # closes the bed to the cab
    # The cab's back leans forward above the deck, so fill on into the cab (narrower than its glass) to leave no gap.
    box(n("bed_fill"), p(0, yc, z1 + 0.15), (w - 0.35, hh, 0.5), col, bevel=0.04)


# id: (body colour, length, width, body height, cabin (back z, front z), roof y, wheel radius, trim, extras)
CARS = {
    "car_banger": ("a89a7c", 3.0, 1.45, 0.52, (-1.2, 0.5), 1.4, 0.28, "4a4a48", "banger"),
    "car_microcar": ("e8c84a", 2.4, 1.3, 0.5, (-0.9, 0.55), 1.45, 0.24, DARK, None),
    "car_used": ("b8c4a0", 3.2, 1.5, 0.55, (-1.3, 0.55), 1.45, 0.3, DARK, "used"),
    "car_pickup_old": ("9c5a3c", 3.9, 1.6, 0.6, (-0.2, 0.9), 1.6, 0.33, "5a5a58", "pickup_old"),
    "car_hatch": ("6a9ac8", 3.0, 1.5, 0.55, (-1.3, 0.6), 1.5, 0.29, DARK, None),
    "car_city": ("e2766a", 2.8, 1.45, 0.55, (-1.1, 0.6), 1.5, 0.27, DARK, None),
    "car_estate": ("7a8a6a", 3.9, 1.6, 0.6, (-1.85, 0.6), 1.55, 0.31, DARK, "rails"),
    "car_camper_old": ("f0a868", 3.8, 1.7, 0.9, (-1.8, 1.2), 2.2, 0.32, CREAM, "camper_old"),
    "car_saloon": ("b0b6bc", 4.0, 1.6, 0.58, (-1.0, 0.8), 1.5, 0.31, DARK, None),
    "car_family": ("4f78a8", 3.5, 1.6, 0.7, (-1.55, 0.75), 1.75, 0.33, DARK, "rails"),
    "car_hot_hatch": ("f2f0ea", 3.1, 1.55, 0.5, (-1.25, 0.55), 1.38, 0.3, DARK, "hot_hatch"),
    "car_mpv": ("8a6aa0", 3.9, 1.65, 0.75, (-1.8, 1.1), 1.95, 0.32, DARK, None),
    "car_compact_suv": ("c87a4a", 3.6, 1.65, 0.72, (-1.5, 0.75), 1.8, 0.36, DARK, "rails"),
    "car_hybrid": ("8fb8a8", 3.8, 1.6, 0.55, (-1.2, 0.8), 1.45, 0.3, DARK, None),
    "car_offroad": ("6a7a4a", 3.6, 1.7, 0.8, (-1.55, 0.6), 1.95, 0.42, DARK, "offroad"),
    "car_electric": ("e8eef0", 3.2, 1.55, 0.55, (-1.3, 0.75), 1.5, 0.3, "3a8ac8", "electric"),
    "car_pickup": ("3a4a6a", 4.3, 1.75, 0.72, (-0.2, 1.1), 1.85, 0.38, DARK, "pickup"),
    "car_rx": ("3a5ac8", 3.8, 1.65, 0.46, (-1.15, 0.45), 1.05, 0.3, DARK, "rx"),
    "car_wrx": ("2a4ab0", 3.7, 1.6, 0.55, (-1.0, 0.75), 1.45, 0.32, "e8c050", "wrx"),
    "car_convertible": ("4ab0b8", 3.7, 1.6, 0.5, (-0.6, 0.6), 1.1, 0.3, CREAM, "convertible"),
    "car_camper": ("f2efe4", 4.3, 1.75, 1.0, (-2.0, 1.4), 2.45, 0.34, "5a9ac8", "camper"),
    "car_suv": ("2c2e33", 4.2, 1.8, 0.8, (-1.85, 0.85), 1.95, 0.4, CHROME, "rails"),
    "car_muscle": ("e0a030", 4.2, 1.7, 0.55, (-0.9, 0.4), 1.3, 0.33, DARK, "muscle"),
    "car_classic": ("e8dcc0", 3.6, 1.5, 0.5, (-0.9, 0.2), 1.15, 0.3, CHROME, "classic"),
    "car_sports": ("c0c4c8", 3.6, 1.65, 0.42, (-0.9, 0.5), 1.12, 0.29, DARK, "sports"),
    "car_exec": ("1e2a3a", 4.3, 1.7, 0.6, (-1.0, 0.9), 1.55, 0.33, CHROME, "exec"),
    "car_electric_lux": ("c8ccd4", 4.2, 1.7, 0.52, (-1.4, 0.9), 1.4, 0.33, DARK, "electric"),
    "car_luxury_suv": ("f2f0ea", 4.3, 1.85, 0.82, (-1.9, 0.85), 2.0, 0.41, CHROME, "exec"),
    "car_gt": ("2f5a46", 4.2, 1.75, 0.45, (-1.0, 0.3), 1.12, 0.32, CHROME, "gt"),
    "car_vintage": ("6a1e2a", 4.1, 1.6, 0.55, (-1.0, 0.3), 1.5, 0.36, CHROME, "vintage"),
    "car_limo": ("1a1a1e", 4.4, 1.7, 0.58, (-1.7, 1.0), 1.5, 0.31, CHROME, "limo"),
    "car_super": ("f0c020", 4.0, 1.8, 0.38, (-0.6, 0.6), 1.0, 0.31, DARK, "super"),
    "car_hyper": ("d8202a", 4.2, 1.85, 0.34, (-0.5, 0.7), 0.95, 0.31, DARK, "hyper"),
}


def extras(kind, c):
    body, length, width, h, cabin, roof_y, wr, trim = c[:8]
    hl, top = length / 2, wr + h
    if kind == "banger":
        ball(n("rust"), p(0.7, top - 0.15, -0.9), 0.16, "8a4a2a", scale=(0.2, 0.8, 1.3))
        box(n("door_odd"), p(-width / 2 - 0.01, top - 0.25, 0.1), (0.04, 0.4, 0.9), "c8b07a", bevel=0.02)
    elif kind == "used":
        ball(n("rust"), p(0.74, 0.55, -0.9), 0.14, "a0643a", scale=(0.2, 0.8, 1.2))
    elif kind == "rails":
        rails(roof_y + 0.08, cabin[0] + (cabin[1] - cabin[0]) / 2 - 0.05, cabin[1] - cabin[0] - 0.4)
    elif kind in ("pickup_old", "pickup"):
        bed(width, wr, h, -hl + 0.1, cabin[0] + 0.1, body)  # runs into the cab: no gap
        if kind == "pickup":
            bull_bar(hl, wr, h)
            box(n("grille"), p(0, top - 0.25, hl + 0.01), (width - 0.5, 0.3, 0.04), CHROME, bevel=0.02)
    elif kind in ("camper_old", "camper"):
        box(n("band"), p(0, top - 0.1, 0), (width + 0.02, 0.18, length - 0.3), trim, bevel=0.04)
        box(n("roof_box"), p(0, roof_y + 0.15, -0.3), (width - 0.4, 0.2, 1.6), CREAM, bevel=0.06)
    elif kind == "hot_hatch":
        stripes(top + 0.02, 0.6, 1.0, "d8402e", gap=0.3)
        spoiler(roof_y + 0.08, cabin[0] + 0.15, w=1.2, base=roof_y - 0.04)
    elif kind == "offroad":
        bull_bar(hl, wr, h)
        box(n("spare"), p(0, wr + h * 0.6, -hl - 0.12), (0.7, 0.7, 0.2), "2a2b2e", bevel=0.25)
        box(n("bar"), p(0, roof_y + 0.12, -0.2), (width - 0.2, 0.08, 1.6), DARK, bevel=0.03)
    elif kind == "electric":
        box(n("strip"), p(0, top - 0.05, hl - 0.01), (width - 0.3, 0.06, 0.04), trim, bevel=0.02)
    elif kind == "rx":  # rear-hinged back doors, twin exhausts
        for i, sx in enumerate((-1, 1)):
            box(n(f"seam{i}"), p(sx * (width / 2 + 0.01), top - 0.25, -0.05), (0.02, 0.45, 0.03), DARK, bevel=0.01)
            tube(n(f"exhaust{i}"), p(sx * 0.35, wr + 0.1, -hl - 0.02), 0.06, 0.12, CHROME, rot=(math.pi / 2, 0, 0))
        spoiler(top + 0.07, -hl + 0.22, w=1.15)  # small ducktail
        ball(n("bulge"), p(0, top - 0.1, 0.95), 0.35, body, scale=(0.9, 0.3, 1.5))
    elif kind == "wrx":  # bonnet scoop, big wing, gold wheels
        box(n("scoop"), p(0, top + 0.06, 1.0), (0.6, 0.12, 0.5), body, bevel=0.05)
        spoiler(top + 0.3, -hl + 0.2, w=1.4)
    elif kind == "convertible":
        box(n("seats"), p(0, top + 0.18, -0.2), (width - 0.4, 0.4, 0.5), "8a4a2a", bevel=0.1)
        box(n("hood_folded"), p(0, top + 0.08, -0.85), (width - 0.3, 0.16, 0.4), "3a3a3e", bevel=0.06)
    elif kind == "muscle":
        stripes(top + 0.01, 0.0, length - 0.3, DARK)
        box(n("scoop"), p(0, top + 0.08, 1.2), (0.5, 0.14, 0.7), DARK, bevel=0.05)
    elif kind == "classic":
        box(n("grille"), p(0, top - 0.2, hl + 0.01), (0.7, 0.3, 0.04), CHROME, bevel=0.02)
        tube(n("spare"), p(0, top + 0.05, -hl + 0.05), 0.3, 0.12, CHROME, rot=(math.pi / 2, 0, 0))
    elif kind == "sports":
        spoiler(0.95, -1.62)
        stripes(0.73, 0.9, 1.6)
    elif kind == "exec":
        box(n("grille"), p(0, top - 0.22, hl + 0.01), (0.9, 0.34, 0.04), CHROME, bevel=0.02)
        ball(n("badge"), p(0, top + 0.02, hl - 0.25), 0.06, CHROME)
    elif kind == "gt":
        box(n("grille"), p(0, top - 0.2, hl + 0.01), (0.8, 0.24, 0.04), CHROME, bevel=0.02)
        stripes(top + 0.01, 0.8, 1.6, CREAM, gap=0.15)
    elif kind == "vintage":
        for i, sx in enumerate((-1, 1)):  # running boards and sweeping wings
            box(n(f"board{i}"), p(sx * (width / 2 + 0.08), wr + 0.05, 0), (0.18, 0.06, length - 1.4), DARK, bevel=0.03)
        box(n("grille"), p(0, top - 0.1, hl + 0.01), (0.6, 0.5, 0.04), CHROME, bevel=0.02)
        tube(n("mascot"), p(0, top + 0.1, hl - 0.1), 0.04, 0.2, CHROME)
    elif kind == "limo":
        pass
    elif kind == "super":
        spoiler(top + 0.25, -hl + 0.25, w=1.6)
        for i, sx in enumerate((-1, 1)):
            box(n(f"intake{i}"), p(sx * (width / 2 + 0.01), top - 0.12, -0.6), (0.04, 0.2, 0.6), DARK, bevel=0.02)
    elif kind == "hyper":
        spoiler(top + 0.3, -hl + 0.2, w=1.7)
        box(n("fin"), p(0, roof_y - 0.1, -1.2), (0.06, 0.35, 1.0), body, bevel=0.03)
        stripes(top + 0.01, 1.2, 1.0, "f2c02a", gap=0.35)


def taper(ob, length=1.0, width=1.0, shift=0.0):
    """Pull a box's top face in: length/width scale it, shift slides it along +z (Godot). Rakes windscreens."""
    vs = ob.data.vertices
    cx, cy, cz = (sum(v.co[i] for v in vs) / len(vs) for i in range(3))  # box() bakes its position into the mesh
    for v in vs:
        if v.co.z > cz:
            v.co.x = cx + (v.co.x - cx) * width
            v.co.y = cy + (v.co.y - cy) * length - shift
    return ob


GLASS = "8fb3c8"
CUR = {"top": 0.0}  # deck height of the car being built, for wing stalks
# Silhouette per car: rake = roof length / cabin base, tum = roof width / cabin base, nose = bonnet top length,
# drop = bonnet front lowered (m), cab/body = bevel (roundness).
BASE_SHAPE = dict(rake=0.6, tum=0.86, nose=0.9, drop=0.06, cab=0.07, body=0.12)
WEDGE_SHAPE = dict(rake=0.38, tum=0.8, nose=0.72, drop=0.2, cab=0.08, body=0.1)
_UTE = dict(rake=0.85, tum=0.92, nose=0.95, drop=0.02)
_SUV = dict(rake=0.78, tum=0.9, drop=0.04)
_BUBBLE = dict(rake=0.32, tum=0.72, nose=0.65, drop=0.26, cab=0.12)
_TALL = dict(rake=0.7, tum=0.86, nose=0.8, drop=0.12)
_ROUND = dict(rake=0.6, tum=0.8, cab=0.14, body=0.22)
SHAPE = {
    "van_rv": dict(rake=0.95, tum=0.95, nose=1.0, drop=0.0),
    "van_food": dict(rake=0.85, tum=0.92, nose=1.0, drop=0.0),
    "car_beatle": dict(rake=0.5, tum=0.75, nose=0.8, drop=0.15, cab=0.22, body=0.3),
    "car_gwagone": dict(rake=0.95, tum=0.97, nose=0.99, drop=0.0, cab=0.03, body=0.05),
    "car_offroad": dict(rake=0.9, tum=0.95, nose=0.97, drop=0.02, cab=0.04, body=0.06),
    "car_camper": dict(rake=0.92, tum=0.95, nose=0.97, drop=0.0, cab=0.06),
    "car_camper_old": dict(rake=0.92, tum=0.95, nose=0.97, drop=0.0, cab=0.08, body=0.18),
    "car_mpv": dict(rake=0.7, nose=0.8, drop=0.1),
    "car_rx": dict(rake=0.3, tum=0.76, nose=0.78, drop=0.14, cab=0.14),
    "car_wrx": dict(rake=0.55, tum=0.84, drop=0.08),
    "car_muscle": dict(rake=0.45, tum=0.82, nose=0.95, drop=0.02, body=0.08),
    "car_civic": dict(rake=0.55, nose=0.85, drop=0.12),
    "car_audy": dict(rake=0.42, tum=0.8, nose=0.7, drop=0.2),
    "car_limo": dict(rake=0.88, tum=0.9),
    "car_classic": _ROUND, "car_vintage": _ROUND,
    "car_pickup": _UTE, "car_pickup_old": _UTE,
    "car_suv": _SUV, "car_luxury_suv": _SUV, "car_kio": _SUV, "car_compact_suv": _SUV, "car_family": _SUV,
    "car_mcclaren": _BUBBLE, "car_super": _BUBBLE, "car_hyper": _BUBBLE, "car_bugotti": _BUBBLE,
    "car_matiz": _TALL, "car_microcar": _TALL, "car_city": _TALL,
}
RIM = {"car_wrx": "e8c050", "car_bugotti": "c8ccd4", "car_classic": CHROME, "car_vintage": CHROME}
GRILLE_KINDS = {"pickup", "classic", "exec", "gt", "vintage", "gwagone", "bugotti"}


def frustum(name, yb, yt, bot, top, col, ytf=None, budget=450, **kw):
    """A box from yb to yt whose bottom/top are (half width, back z, front z); ytf lowers the top's front edge."""
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    ob = bpy.context.object
    ob.name = n(name)
    for v in ob.data.vertices:
        sx, front, up = (1 if v.co.x > 0 else -1), v.co.y < 0, v.co.z > 0  # Blender -y = Godot +z
        hw, z0, z1 = top if up else bot
        y = (ytf if (front and ytf is not None) else yt) if up else yb
        v.co = I.R.g2b(*p(sx * hw, y, z1 if front else z0))
    ob["budget"] = budget
    return I.R.finish(ob, col, **kw)


def pane(name, quad, hint, u=(0.08, 0.92), v=(0.2, 0.86), col=GLASS, out=0.014, shade=True):
    """A glass slab on a quad face (Godot points: bottom-a, bottom-b, top-b, top-a), inset to u/v, just outside."""
    from mathutils import Vector

    a, b, c, d = (Vector(q) for q in quad)

    def at_uv(s, t):
        return (a.lerp(b, s)).lerp(d.lerp(c, s), t)

    pts = [at_uv(u[0], v[0]), at_uv(u[1], v[0]), at_uv(u[1], v[1]), at_uv(u[0], v[1])]
    nrm = (pts[1] - pts[0]).cross(pts[3] - pts[0]).normalized()
    if nrm.dot(Vector(hint)) < 0:
        nrm = -nrm
    verts = [I.R.g2b(*p(*(q + nrm * (out + s)))) for s in (0.014, -0.014) for q in pts]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])
    me.validate()
    ob = bpy.data.objects.new(n(name), me)
    bpy.context.collection.objects.link(ob)
    import bmesh

    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob["budget"] = 80
    if col == GLASS and shade:
        dv = v[1] - v[0]
        du = u[1] - u[0]
        pane(name + "_lo", quad, hint, u, (v[0], v[0] + dv * 0.42), "56758c", out + 0.004, False)
        pane(name + "_hi", quad, hint, (u[0] + du * 0.2, u[0] + du * 0.3), (v[0] + dv * 0.5, v[1] - dv * 0.08),
             "dce9f0", out + 0.006, False)
    return I.R.finish(ob, col, bevel=0.008, subd=1, lump=0)


def rim_wheel(name, x, y, z, r, rim):
    tube(n(name), p(x, y, z), r, 0.24, "2a2b2e", rot=(0, math.pi / 2, 0))["budget"] = 90
    sx = 1 if x > 0 else -1
    for part, rr, off, col in (("rim", 0.72, 0.13, rim), ("dish", 0.6, 0.135, "3a3c40"), ("cap", 0.2, 0.14, rim)):
        tube(n(f"{name}_{part}"), p(x + sx * off, y, z), r * rr, 0.03, col, rot=(0, math.pi / 2, 0), lump=0)["budget"] = 60


def car(cid, body, length, width, height, cabin, roof_y, wheel_r, trim, kind):
    s = dict(WEDGE_SHAPE if cid in WEDGES else BASE_SHAPE)
    s.update(SHAPE.get(cid, {}))
    hl, hw, top = length / 2, width / 2, wheel_r + height
    CUR["top"] = top
    s["drop"] = min(s["drop"], max(0.0, top - (2 * wheel_r + 0.12)))  # bonnet never dips below the wheel tops
    zf_top = hl * s["nose"]
    frustum("body", wheel_r * 0.55, top, (hw, -hl, hl), (hw * 0.94, -hl * 0.97, zf_top), body,
            ytf=top - s["drop"], bevel=s["body"], lump=0.022)

    def deck(z):  # body top height at z
        return top - s["drop"] * max(0.0, (z + hl * 0.97) / (zf_top + hl * 0.97))

    def zf(frac):  # front face z at height fraction
        return hl - (hl - zf_top) * frac

    c0, c1 = cabin
    cl = c1 - c0
    yb = min(deck(c0), deck(c1)) - 0.04
    hb = hw - 0.06
    ht = hb * s["tum"]
    tz1 = c1 - cl * (1 - s["rake"]) * 0.75
    tz0 = tz1 - cl * s["rake"]
    rear_win = 0.08 if kind not in ("pickup", "pickup_old") else 0.2
    if kind == "convertible":  # open top: windscreen frame only
        yt = roof_y
        quad = [(-hb, yb, c1), (hb, yb, c1), (ht, yt, c1 - 0.35), (-ht, yt, c1 - 0.35)]
        pane("frame", quad, (0, 0.3, 1), u=(0.0, 1.0), v=(0.3, 1.0), col=DARK, out=0.0)
        pane("screen", quad, (0, 0.3, 1), u=(0.07, 0.93), v=(0.38, 0.92))
    else:
        frustum("cabin", yb, roof_y, (hb, c0, c1), (ht, tz0, tz1), body, bevel=s["cab"], lump=0.016)
        pane("screen", [(-hb, yb, c1), (hb, yb, c1), (ht, roof_y, tz1), (-ht, roof_y, tz1)], (0, 0.3, 1),
             v=(0.22, 0.86))
        pane("rear", [(hb, yb, c0), (-hb, yb, c0), (-ht, roof_y, tz0), (ht, roof_y, tz0)], (0, 0.3, -1),
             u=(0.1, 0.9), v=(0.22 + rear_win, 0.86))
        cuts = (0.06, 0.47, 0.53, 0.94) if cl < 2.4 else (0.05, 0.31, 0.36, 0.64, 0.69, 0.95)
        for sx in (-1, 1):
            quad = [(sx * hb, yb, c0), (sx * hb, yb, c1), (sx * ht, roof_y, tz1), (sx * ht, roof_y, tz0)]
            for i in range(0, len(cuts), 2):
                pane(f"side{sx}_{i}", quad, (sx, 0, 0), u=(cuts[i], cuts[i + 1]), v=(0.24, 0.86))
    for i, (sx, sz) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        z = sz * (hl - wheel_r - 0.25)
        rim_wheel(f"wheel{i}", sx * (hw - 0.08), wheel_r, z, wheel_r, RIM.get(cid, CHROME))
        fy = min(wheel_r * 1.55, deck(z) - (wheel_r + 0.12) * 0.45 - 0.03)  # never above the deck
        ball(n(f"flare{i}"), p(sx * (hw - 0.01), fy, z), wheel_r + 0.12, body,
             scale=(0.24, 0.45, 1.0), lump=0.01)
    ly = wheel_r * 0.55 + (top - wheel_r * 0.55) * 0.62
    for i, sx in enumerate((-1, 1)):
        ball(n(f"lamp{i}"), p(sx * (hw - 0.26), ly, zf(0.62) - 0.02), 0.12, "fff3c4", scale=(1.5, 0.75, 0.55), lump=0)
        ball(n(f"tail{i}"), p(sx * (hw - 0.22), ly, -hl * 0.985 + 0.02), 0.1, "d8443a", scale=(1.5, 0.7, 0.5), lump=0)
        ball(n(f"mirror{i}"), p(sx * (hb + 0.1), yb + 0.14, c1 - 0.12), 0.08, body, scale=(0.9, 0.8, 0.6))
        # door seams and handles
        doors = (c1 + 0.05, c0 + cl * 0.5) if cid not in WEDGES and cl > 1.2 else (c1 + 0.05, c0 + 0.05)
        for j, dz in enumerate(doors):
            box(n(f"seam{i}{j}"), p(sx * (hw * 0.965 - 0.01), (wheel_r * 0.9 + top) / 2, dz), (0.03, top - wheel_r * 0.9 - 0.08, 0.025),
                DARK, bevel=0.006, subd=0, lump=0)
            box(n(f"handle{i}{j}"), p(sx * (hw * 0.965 + 0.005), top - 0.14, dz - 0.18), (0.03, 0.04, 0.14), CHROME, bevel=0.012,
                subd=1, lump=0)
    if kind not in GRILLE_KINDS:
        box(n("grille"), p(0, ly - 0.02, zf(0.6)), (width * 0.38, 0.12, 0.05), DARK, bevel=0.03, lump=0)
    for i, sz in enumerate((-1, 1)):
        bump = trim if trim == CHROME else body
        box(n(f"bumper{i}"), p(0, wheel_r * 0.75, sz * (hl - 0.04)), (width + 0.04, 0.2, 0.24), bump, bevel=0.09, lump=0.008)
        box(n(f"lip{i}"), p(0, wheel_r * 0.75 - 0.11, sz * (hl - 0.02)), (width - 0.12, 0.05, 0.26), DARK, bevel=0.02, lump=0)
        box(n(f"plate{i}"), p(0, wheel_r * 0.75 + 0.01, sz * (hl + 0.085)), (0.5, 0.13, 0.03), "f4f1e6", bevel=0.012,
            subd=1, lump=0)
        box(n(f"plate_txt{i}"), p(0, wheel_r * 0.75 + 0.01, sz * (hl + 0.1)), (0.34, 0.05, 0.01), "2f3136", bevel=0.004,
            subd=0, lump=0)


# Extra cars (spoofs): id -> (body, length, width, height, cabin, roof, wheel, trim, extras)
MORE_CARS = {
    "car_matiz": ("8ac0e0", 2.6, 1.4, 0.55, (-1.0, 0.55), 1.55, 0.25, DARK, None),
    "car_peejo": ("c03a3a", 2.9, 1.5, 0.52, (-1.2, 0.5), 1.42, 0.28, DARK, None),
    "car_beatle": ("f0d060", 3.0, 1.5, 0.6, (-0.9, 0.5), 1.55, 0.3, CHROME, "beatle"),
    "car_kio": ("6a8a9a", 3.6, 1.65, 0.7, (-1.5, 0.75), 1.75, 0.35, DARK, "rails"),
    "car_civic": ("f4f2ec", 3.5, 1.6, 0.48, (-1.2, 0.5), 1.32, 0.3, "c02a2a", "civic"),
    "car_audy": ("b8bcc4", 3.6, 1.75, 0.42, (-0.7, 0.55), 1.12, 0.31, DARK, "wedge"),
    "car_mazerotti": ("1e3a6a", 4.3, 1.7, 0.52, (-1.1, 0.7), 1.38, 0.33, CHROME, "exec"),
    "car_gwagone": ("1c1c1e", 3.9, 1.8, 0.85, (-1.8, 0.6), 2.15, 0.4, CHROME, "gwagone"),
    "car_mcclaren": ("f08020", 4.1, 1.85, 0.36, (-0.5, 0.6), 0.98, 0.31, DARK, "wedge"),
    "car_bugotti": ("1a2a6a", 4.3, 1.9, 0.38, (-0.4, 0.6), 1.0, 0.32, "c8ccd4", "bugotti"),
}
WEDGES = {"car_sports", "car_super", "car_hyper", "car_gt", "car_audy", "car_mcclaren", "car_bugotti", "car_muscle",
          "car_classic", "car_rx", "car_convertible"}


def more_extras(kind, c):
    body, length, width, h, cabin, roof_y, wr, trim = c[:8]
    hl, top = length / 2, wr + h
    if kind == "beatle":  # round body: running boards
        for i, sx in enumerate((-1, 1)):
            box(n(f"board{i}"), p(sx * (width / 2 + 0.04), wr + 0.02, 0), (0.12, 0.05, length - 1.6), DARK, bevel=0.02)
    elif kind == "civic":
        spoiler(top + 0.35, -hl + 0.2, w=1.3)
        box(n("splitter"), p(0, wr - 0.02, hl - 0.05), (width - 0.2, 0.04, 0.2), trim, bevel=0.02)
    elif kind == "wedge":
        box(n("diffuser"), p(0, wr, -hl + 0.05), (width - 0.4, 0.12, 0.1), DARK, bevel=0.02)
    elif kind == "gwagone":
        bull_bar(hl, wr, h)
        box(n("spare"), p(0, wr + h * 0.6, -hl - 0.14), (0.75, 0.75, 0.22), "2a2b2e", bevel=0.28)
        box(n("grille"), p(0, top - 0.25, hl + 0.01), (1.0, 0.36, 0.04), CHROME, bevel=0.02)
    elif kind == "bugotti":
        box(n("horseshoe"), p(0, top - 0.2, hl + 0.01), (0.34, 0.26, 0.05), CHROME, bevel=0.1)
        box(n("two_tone"), p(0, top - 0.1, -0.4), (width + 0.02, 0.3, 1.6), "4a7ad0", bevel=0.06)
    else:
        extras(kind, c)


def wheel(name, x, y, z, r, w=0.12, rim=CHROME, spokes=False):
    tube(n(name), p(x, y, z), r, w, "2a2b2e", rot=(0, math.pi / 2, 0))
    tube(n(name + "_hub"), p(x, y, z), r * (0.75 if spokes else 0.45), w + 0.02, rim, rot=(0, math.pi / 2, 0))
    if spokes:
        tube(n(name + "_in"), p(x, y, z), r * 0.65, w + 0.04, "3a3c40", rot=(0, math.pi / 2, 0))


def rod(name, a, b, r, col):
    """A thin bar from point a to b (Godot coords)."""
    from mathutils import Vector

    d = math.dist(a, b)
    ob = tube(n(name), p((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2), r, d, col)
    v = Vector((b[0] - a[0], -(b[2] - a[2]), b[1] - a[1])).normalized()  # Blender direction
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(v)
    return ob


def motorbike(body, kind, length=2.1, wr=0.32, seat="2a2b2e"):
    """A motorbike facing +z: two wheels, engine block, tank, seat, bars and lamp."""
    zf, zr = length / 2 - wr, -length / 2 + wr
    wheel("wf", 0, wr, zf, wr, 0.14, spokes=kind != "scooter")
    wheel("wr", 0, wr, zr, wr, 0.18, spokes=kind != "scooter")
    if kind == "scooter":
        box(n("body"), p(0, wr + 0.25, zr + 0.35), (0.42, 0.55, 0.9), body, bevel=0.18)
        box(n("floor"), p(0, wr + 0.05, 0.1), (0.36, 0.08, 0.6), DARK, bevel=0.03)
        box(n("shield"), p(0, wr + 0.45, zf - 0.25), (0.4, 0.9, 0.12), body, bevel=0.1)
        box(n("seat"), p(0, wr + 0.58, zr + 0.4), (0.36, 0.1, 0.7), seat, bevel=0.05)
        bar_y, bar_z = wr + 1.0, zf - 0.3
    else:
        box(n("engine"), p(0, wr + 0.12, -0.05), (0.42, 0.42, 0.55), "6a6c70", bevel=0.08)
        rod("fork", (0, wr, zf), (0, wr + 0.85, zf - 0.3), 0.04, CHROME)
        rod("swing", (0, wr, zr), (0, wr + 0.15, -0.2), 0.05, DARK)
        tank_y = wr + 0.55 + (0.1 if kind == "sport" else 0)
        ball(n("tank"), p(0, tank_y, 0.2), 0.26, body, scale=(0.75, 0.65, 1.3))
        if kind == "sport":
            taper(box(n("fairing"), p(0, wr + 0.55, zf - 0.35), (0.5, 0.6, 0.6), body, bevel=0.15), 0.6, 0.7, -0.1)
            box(n("tail"), p(0, wr + 0.62, zr + 0.35), (0.3, 0.2, 0.6), body, bevel=0.08)
        if kind == "cruiser":
            box(n("fender"), p(0, wr * 2 - 0.02, zr), (0.3, 0.1, 0.7), body, bevel=0.05)
            rod("exhaust", (0.25, wr, 0.2), (0.25, wr + 0.05, zr - 0.2), 0.05, CHROME)
        if kind == "adventure":
            box(n("pannier0"), p(-0.32, wr + 0.3, zr + 0.25), (0.22, 0.4, 0.5), "3a3c40", bevel=0.05)
            box(n("pannier1"), p(0.32, wr + 0.3, zr + 0.25), (0.22, 0.4, 0.5), "3a3c40", bevel=0.05)
        if kind == "dirt":
            box(n("number"), p(0, wr + 0.75, zf - 0.25), (0.3, 0.3, 0.05), "f4efe4", bevel=0.05)
            box(n("mudguard"), p(0, wr * 2 + 0.05, zf), (0.18, 0.05, 0.5), body, bevel=0.03)
        box(n("seat"), p(0, wr + 0.62 + (0.08 if kind == "sport" else 0), -0.3), (0.3, 0.1, 0.65), seat, bevel=0.05)
        bar_y, bar_z = wr + 0.95, zf - 0.28
    rod("bars", (-0.35, bar_y, bar_z), (0.35, bar_y, bar_z), 0.025, DARK)
    ball(n("lamp"), p(0, bar_y - 0.15, bar_z + 0.12), 0.1, "fff3c4", scale=(1, 1, 0.6))


def bicycle(frame, kind, wr=0.34, length=1.7, rim=CHROME):
    """A bicycle facing +z: thin wheels, a frame of rods, saddle and bars."""
    if kind == "bmx":
        wr, length = 0.26, 1.4
    zf, zr = length / 2 - wr, -length / 2 + wr
    thin = 0.1 if kind == "mountain" else 0.06
    wheel("wf", 0, wr, zf, wr, thin, rim=rim, spokes=True)
    wheel("wr", 0, wr, zr, wr, thin, rim=rim, spokes=True)
    seat = (0, wr + 0.62, zr + 0.3)
    head = (0, wr + 0.6, zf - 0.2)
    crank = (0, wr, -0.05)
    if kind in ("shopper", "folding"):  # step-through frame
        rod("down", head, (0, wr + 0.1, -0.05), 0.035, frame)
    else:
        rod("top", seat, head, 0.03, frame)
        rod("down", head, crank, 0.035, frame)
    rod("seattube", seat, crank, 0.03, frame)
    rod("stay", seat, (0, wr, zr), 0.022, frame)
    rod("chain", crank, (0, wr, zr), 0.022, frame)
    rod("fork", head, (0, wr, zf), 0.025, frame)
    tube(n("crank"), p(0.05, wr, -0.05), 0.09, 0.04, "3a3c40", rot=(0, math.pi / 2, 0))
    box(n("saddle"), p(0, seat[1] + 0.06, seat[2]), (0.14, 0.06, 0.26), "2a2b2e", bevel=0.03)
    bar_y = head[1] + (0.02 if kind in ("road", "fixie") else 0.12)
    rod("stem", head, (0, bar_y, head[2] - 0.05), 0.025, frame)
    rod("bars", (-0.28, bar_y, head[2] - 0.05), (0.28, bar_y, head[2] - 0.05), 0.02, DARK)
    if kind == "shopper":
        box(n("basket"), p(0, bar_y - 0.1, zf + 0.05), (0.36, 0.26, 0.3), "c8a060", bevel=0.04)
    if kind == "cargo":
        box(n("box"), p(0, wr + 0.3, zf + 0.15), (0.6, 0.45, 0.65), "c8a060", bevel=0.05)
    if kind == "ebike":
        box(n("battery"), p(0, wr + 0.35, zf - 0.6), (0.12, 0.12, 0.4), "2a2b2e", bevel=0.03)
    if kind == "tandem":
        rod("top2", seat, (0, wr + 0.6, zr - 0.6), 0.03, frame)
        box(n("saddle2"), p(0, wr + 0.68, zr - 0.55), (0.14, 0.06, 0.26), "2a2b2e", bevel=0.03)
    if kind == "rusty":
        ball(n("rust"), p(0, wr + 0.4, 0.1), 0.06, "8a4a2a")


MOTORBIKES = {  # id -> (colour, kind, length)
    "moto_cub": ("c03a3a", "scooter", 1.8),
    "moto_vesper": ("9ad0c0", "scooter", 1.8),
    "moto_kawasucky": ("50b040", "sport", 2.1),
    "moto_yamahaha": ("2a4ab0", "sport", 2.1),
    "moto_ducatty": ("d02020", "sport", 2.1),
    "moto_hayabooza": ("c8ccd4", "sport", 2.2),
    "moto_triumphant": ("2a4a3a", "naked", 2.1),
    "moto_fatboi": ("1c1c1e", "cruiser", 2.4),
    "moto_gs": ("e8e4da", "adventure", 2.3),
    "moto_muddog": ("f08020", "dirt", 2.1),
}
BICYCLES = {  # id -> (frame colour, kind)
    "bike_rusty": ("8a7a6a", "rusty"),
    "bike_bmx": ("40c0e0", "bmx"),
    "bike_shopper": ("e8b0c0", "shopper"),
    "bike_fixie": ("f0d040", "fixie"),
    "bike_tandem": ("3a8a5a", "tandem"),
    "bike_mountain": ("e05a2a", "mountain"),
    "bike_folding": ("2a5ab0", "folding"),
    "bike_road": ("d02a2a", "road"),
    "bike_ebike": ("e8e4da", "ebike"),
    "bike_cargo": ("3a6a8a", "cargo"),
}
SPECIALS = ("van_rv", "van_food", "truck_monster", "buggy_dune", "truck_semi")


def special(vid):
    if vid == "van_rv":
        car("van_rv", "f2efe4", 4.4, 1.9, 1.5, (-2.1, 1.6), 2.75, 0.36, "6a6c70", None)
        box(n("stripe"), p(0, 1.3, 0), (1.92, 0.2, 4.0), "c87a3a", bevel=0.05)
        box(n("awning"), p(0.98, 2.3, -0.4), (0.08, 0.1, 2.2), "3a7ab0", bevel=0.03)
        box(n("ac"), p(0, 2.9, -0.8), (0.8, 0.22, 0.8), CREAM, bevel=0.06)
    elif vid == "van_food":
        car("van_food", "f0c040", 4.2, 1.8, 1.3, (0.6, 1.9), 2.5, 0.35, DARK, None)
        # The kitchen box behind the cab, full height; hatch, awning and counter on its -x side (the camera side
        # when parked), every part fixed to the box wall.
        box(n("kitchen"), p(0, 2.05, -0.75), (1.7, 0.95, 2.7), "f0c040", bevel=0.08, lump=0.01)
        box(n("hatch"), p(-0.86, 2.0, -0.75), (0.04, 0.55, 1.6), "2a2b2e", bevel=0.02)
        box(n("awning"), p(-1.0, 2.36, -0.75), (0.3, 0.05, 1.8), "e04a3a", bevel=0.02)
        box(n("counter"), p(-0.95, 1.7, -0.75), (0.2, 0.05, 1.7), "c9ccd1", bevel=0.015)
        box(n("band"), p(0, 2.42, -0.75), (1.72, 0.1, 2.72), "e04a3a", bevel=0.03)
    elif vid == "truck_monster":  # a real pickup (cab, doors, lamps, bed) lifted onto a monster chassis
        c = ("50a040", 3.6, 1.7, 0.72, (-0.35, 0.8), 1.85, 0.38, DARK, "pickup")
        car(vid, *c)
        extras("pickup", c)
        lift = 1.22  # body underside (0.21) sits just above the big tyres (top 1.4)
        for ob in list(bpy.context.scene.collection.objects):
            if "__wheel" in ob.name or "__flare" in ob.name:
                bpy.data.objects.remove(ob, do_unlink=True)
            else:
                ob.location.z += lift
        for i, (sx, sz) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
            wheel(f"big{i}", sx * 1.05, 0.7, sz * 1.25, 0.7, 0.5, rim="e0c020")
        box(n("chassis"), p(0, 1.15, 0), (1.3, 0.3, 3.2), DARK, bevel=0.05)
        for i, sz in enumerate((-1, 1)):
            rod(f"axle{i}", (-0.85, 0.7, sz * 1.25), (0.85, 0.7, sz * 1.25), 0.07, "3a3c40")
            for j, sx in enumerate((-1, 1)):
                rod(f"shock{i}{j}", (sx * 0.55, 0.72, sz * 1.25), (sx * 0.5, 1.35, sz * 1.0), 0.06, "e0c020")
        for i, sx in enumerate((-1, 1)):  # flames along the front wings
            box(n(f"flames{i}"), p(sx * 0.86, 1.72, 1.25), (0.03, 0.22, 0.8), "f08020", bevel=0.01, subd=1, lump=0)
    elif vid == "buggy_dune":
        for i, (sx, sz, r) in enumerate(((-1, -1, 0.42), (1, -1, 0.42), (-1, 1, 0.33), (1, 1, 0.33))):
            wheel(f"w{i}", sx * 0.8, r, sz * 1.05, r, 0.3, rim="f0c020")
        taper(box(n("tub"), p(0, 0.55, 0.1), (1.2, 0.35, 2.6), "f08030", bevel=0.14), 0.75, 0.9, 0.2)
        for i, sx in enumerate((-0.5, 0.5)):
            rod(f"cage{i}", (sx, 0.7, 0.5), (sx * 0.9, 1.55, -0.1), 0.04, DARK)
            rod(f"cage_b{i}", (sx * 0.9, 1.55, -0.1), (sx, 0.7, -0.8), 0.04, DARK)
        rod("cage_top", (-0.45, 1.55, -0.1), (0.45, 1.55, -0.1), 0.04, DARK)
        box(n("seat"), p(0, 0.85, -0.2), (0.7, 0.4, 0.4), "2a2b2e", bevel=0.08)
        box(n("engine"), p(0, 0.75, -1.05), (0.6, 0.4, 0.4), "6a6c70", bevel=0.08)
    elif vid == "truck_semi":
        for i, (sx, sz) in enumerate(((-1, -1.35), (1, -1.35), (-1, -0.6), (1, -0.6), (-1, 1.35), (1, 1.35))):
            wheel(f"w{i}", sx * 0.95, 0.48, sz, 0.48, 0.35, rim=CHROME)
        box(n("chassis"), p(0, 0.6, -0.3), (1.6, 0.3, 3.8), DARK, bevel=0.05)
        box(n("hood"), p(0, 1.15, 1.45), (1.7, 0.9, 1.3), "c02a2a", bevel=0.12)
        box(n("cab"), p(0, 1.75, 0.2), (2.0, 2.1, 1.4), "c02a2a", bevel=0.14)
        box(n("glass"), p(0, 2.3, 0.92), (1.85, 0.7, 0.06), "8fb3c8", bevel=0.03)
        box(n("grille"), p(0, 1.15, 2.11), (1.0, 0.8, 0.04), CHROME, bevel=0.03)
        box(n("fifth"), p(0, 0.82, -1.2), (1.0, 0.1, 1.0), "3a3c40", bevel=0.03)
        for i, sx in enumerate((-1, 1)):
            tube(n(f"stack{i}"), p(sx * 0.95, 2.4, -0.55), 0.08, 2.0, CHROME)
            box(n(f"tank{i}"), p(sx * 0.9, 0.7, -0.3), (0.3, 0.5, 0.9), CHROME, bevel=0.15)


if __name__ == "__main__":
    OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    I.BUDGET = 55
    only = os.environ.get("VEHICLES_ONLY", "").split(",")  # quick look at a few: VEHICLES_ONLY=car_rx,car_wrx
    keep = lambda vid: only == [""] or vid in only  # noqa: E731
    for cid, c in {**CARS, **MORE_CARS}.items():
        if not keep(cid):
            continue
        at(cid)
        car(cid, *c)
        if c[8]:
            more_extras(c[8], c)
    for vid, (col, kind, length) in MOTORBIKES.items():
        if not keep(vid):
            continue
        at(vid)
        motorbike(col, kind, length)
    for vid, (col, kind) in BICYCLES.items():
        if not keep(vid):
            continue
        at(vid)
        bicycle(col, kind)
    for vid in SPECIALS:
        if not keep(vid):
            continue
        at(vid)
        special(vid)
    I.bake()
    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_vertex_color="ACTIVE",
                              export_materials="NONE", export_texcoords=False)
    print("VEHICLES", len(I.ITEMS))
