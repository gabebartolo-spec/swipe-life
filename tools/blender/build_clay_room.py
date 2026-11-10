"""Build the claymation bedroom (director's reference image 5) and export it for Godot.

Run headless:
  blender --background --factory-startup --python tools/blender/build_clay_room.py -- <out.glb>

Every prop is modelled soft (bevel + subdivision + low-frequency lumps), then Cycles bakes
ambient occlusion into a colour attribute that is multiplied with the prop's clay colour.
Godot reads that attribute as COLOR, so contact shadows ship without needing SSAO on mobile.
Same axes as the Godot scene: floor 0..6 on X and Godot Z; Blender Y = -Godot Z.
"""

import math
import sys

import bpy
from mathutils import Vector



def hexc(h):
    h = h.lstrip("#")
    srgb = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, 1.0)


def g2b(x, y, z):
    """Godot position (y up, z toward camera) to Blender (z up)."""
    return Vector((x, -z, y))


def finish(ob, color, bevel=0.06, subd=2, lump=0.012, seed=0):
    ob["clay_color"] = color
    if bevel > 0:
        m = ob.modifiers.new("bevel", "BEVEL")
        m.width = bevel
        m.segments = 3
        m.limit_method = "NONE"
    if subd:
        m = ob.modifiers.new("subd", "SUBSURF")
        m.levels = subd
        m.render_levels = subd
    if lump > 0:
        tex = bpy.data.textures.new(f"lump{seed}", "CLOUDS")
        tex.noise_scale = 0.35
        m = ob.modifiers.new("lump", "DISPLACE")
        m.texture = tex
        m.texture_coords = "GLOBAL"
        m.strength = lump
        m.mid_level = 0.5
    return ob


def box(name, center, size, color, **kw):
    bpy.ops.mesh.primitive_cube_add(location=g2b(*center))
    ob = bpy.context.object
    ob.name = name
    ob.scale = (size[0] / 2, size[2] / 2, size[1] / 2)
    bpy.ops.object.transform_apply(scale=True)
    return finish(ob, color, **kw)


def ball(name, center, radius, color, scale=(1, 1, 1), **kw):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=g2b(*center), segments=32, ring_count=16)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (scale[0], scale[2], scale[1])
    bpy.ops.object.transform_apply(scale=True)
    kw.setdefault("bevel", 0)
    kw.setdefault("subd", 1)
    return finish(ob, color, **kw)


def pillow(name, center, size, color, **kw):
    """Plump cushion: a flat slab bulging at the middle and pinched at the corners, size = Godot
    (x, y, z) extents; the thinnest axis is the thickness (flat pillow, upright cushion)."""
    import bmesh

    bpy.ops.mesh.primitive_cube_add(location=g2b(*center))
    ob = bpy.context.object
    ob.name = name
    half = (size[0] / 2, size[2] / 2, size[1] / 2)  # Blender local x, y, z
    k = min(range(3), key=lambda i: half[i])
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=9, use_grid_fill=True)
    for v in bm.verts:
        u = list(v.co)
        a, b = [i for i in range(3) if i != k]
        # square -> rounded rectangle, then the thickness follows the distance from the middle
        pa = 0.5 * (u[a] + u[a] * math.sqrt(1 - u[b] ** 2 / 2))
        pb = 0.5 * (u[b] + u[b] * math.sqrt(1 - u[a] ** 2 / 2))
        r2 = pa * pa + pb * pb
        fall = max(0.0, 1 - r2 / 1.3) ** 0.7
        w = u[k] * half[k] * (0.25 + 0.75 * fall)
        if k == 2:  # a head-shaped dip in the top of a pillow lying flat
            w -= half[k] * 0.3 * math.exp(-3 * r2) * max(u[k], 0.0)
        co = [0.0, 0.0, 0.0]
        co[a], co[b], co[k] = pa * half[a], pb * half[b], w
        v.co = Vector(co)
    bm.to_mesh(ob.data)
    bm.free()
    kw.setdefault("bevel", 0)
    kw.setdefault("subd", 1)
    kw.setdefault("lump", 0.018)
    ob.rotation_euler.z = 0.12 * ((kw.get("seed", 0) % 3) - 1)  # not squared to the bed
    ob.data.shade_smooth()
    return finish(ob, color, **kw)


def tube(name, center, radius, depth, color, rot=(0, 0, 0), **kw):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=g2b(*center), rotation=rot, vertices=24)
    ob = bpy.context.object
    ob.name = name
    kw.setdefault("bevel", min(radius * 0.4, 0.04))
    return finish(ob, color, **kw)


def cloth(name, center, size, color, folds=0.04, droop=0.0, **kw):
    """Soft slab with wave folds and edges that droop over the sides (duvet, throw, curtain)."""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=40, size=1, location=(0, 0, 0))
    ob = bpy.context.object
    ob.name = name
    sx, sz = size[0], size[2]
    for v in ob.data.vertices:
        u, w = v.co.x * sx, v.co.y * sz
        fold = folds * (math.sin(u * 7.0 + w * 2.0) * 0.6 + math.sin(w * 11.0 - u * 3.0) * 0.4)
        edge = max(abs(v.co.x) * 2, 0.0) ** 6
        v.co = Vector((u, w, fold - droop * edge))
    ob.location = g2b(*center)
    m = ob.modifiers.new("solid", "SOLIDIFY")
    m.thickness = size[1]
    m.offset = 0
    kw.setdefault("bevel", 0)
    kw.setdefault("subd", 1)
    return finish(ob, color, **kw)


def build():
    WOOD, WALL, CREAM = "c98a55", "e6d9c6", "f3ead8"
    # shell: thick rounded walls and a planked floor
    box("floor_base", (3, -0.25, 3), (6.4, 0.5, 6.4), WALL, bevel=0.15)
    for i in range(12):
        tint = ["c98a55", "bf7f4a", "d29560"][i % 3]
        box(f"plank{i}", (0.25 + i * 0.5, 0.03, 3), (0.46, 0.1, 6.0), tint, bevel=0.035, seed=i)
    box("wall_left", (-0.2, 2.0, 3), (0.4, 4.5, 6.4), WALL, bevel=0.18)
    box("wall_back", (3, 2.0, -0.2), (6.4, 4.5, 0.4), WALL, bevel=0.18)
    box("skirting_l", (0.04, 0.16, 3), (0.08, 0.22, 6.0), "efe4d4", bevel=0.03)
    box("skirting_b", (3, 0.16, 0.04), (6.0, 0.22, 0.08), "efe4d4", bevel=0.03)
    cloth("rug", (3.1, 0.1, 3.5), (2.8, 0.05, 2.2), "d9a3a0", folds=0.006)
    cloth("rug_inner", (3.1, 0.13, 3.5), (2.3, 0.03, 1.7), "e6c0b4", folds=0.006)
    # bed
    box("bed_frame", (1.0, 0.3, 1.75), (2.0, 0.42, 2.9), "b8743f", bevel=0.08)
    box("headboard", (1.0, 0.9, 0.32), (2.0, 1.35, 0.18), "b8743f", bevel=0.09)
    box("mattress", (1.0, 0.63, 1.8), (1.86, 0.3, 2.66), CREAM, bevel=0.12)
    cloth("duvet", (1.05, 0.83, 2.25), (1.95, 0.12, 1.75), "9fb6d2", folds=0.035, droop=0.28)
    cloth("throw", (1.05, 0.93, 2.8), (2.0, 0.07, 0.7), "d8c3a5", folds=0.02, droop=0.32)
    pillow("pillow_a", (0.6, 0.88, 0.75), (0.7, 0.24, 0.5), "fbf6ec")
    pillow("pillow_b", (1.4, 0.88, 0.8), (0.7, 0.24, 0.5), "a9c2a2", seed=1)
    # window on the left wall
    box("win_frame", (0.04, 2.3, 2.0), (0.14, 1.45, 1.55), "fbf8f2", bevel=0.05)
    box("win_pane", (0.13, 2.3, 2.0), (0.06, 1.2, 1.3), "fff3d6", bevel=0.01, subd=0, lump=0)
    box("win_bar_v", (0.16, 2.3, 2.0), (0.06, 1.2, 0.07), "fbf8f2", bevel=0.02)
    box("win_bar_h", (0.16, 2.3, 2.0), (0.06, 0.07, 1.3), "fbf8f2", bevel=0.02)
    box("sill", (0.18, 1.58, 2.0), (0.34, 0.09, 1.75), "fbf8f2", bevel=0.04)
    for n, z in (("curtain_a", 1.1), ("curtain_b", 2.9)):
        c = cloth(n, (0.2, 2.25, z), (0.36, 0.05, 1.75), "e8dccb", folds=0.05)
        c.rotation_euler = (math.radians(90), 0, math.radians(90))
    tube("rod", (0.26, 3.12, 2.0), 0.035, 2.5, "8a6a55", rot=(math.radians(90), 0, 0))
    for i, z in enumerate((1.6, 2.4)):
        tube(f"sill_pot{i}", (0.2, 1.72, z), 0.08, 0.2, "d07a50")
        ball(f"sill_plant{i}", (0.2, 1.9, z), 0.11, ["7fae6a", "e0a24a"][i], lump=0.02, seed=i)
    # desk, laptop, lamp, mug, shelf, books, poster
    box("desk_top", (4.2, 1.3, 0.55), (2.3, 0.12, 1.0), WOOD, bevel=0.04)
    box("desk_drawers", (4.95, 0.64, 0.55), (0.75, 1.2, 0.92), "bf7f4a", bevel=0.06)
    box("drawer_line", (4.95, 0.9, 1.02), (0.55, 0.03, 0.03), "8a5a35", bevel=0.01)
    box("drawer_knob", (4.95, 0.75, 1.03), (0.12, 0.05, 0.05), "8a5a35", bevel=0.02)
    for i, z in enumerate((0.18, 0.92)):
        box(f"desk_leg{i}", (3.2, 0.64, z), (0.12, 1.2, 0.12), "bf7f4a", bevel=0.04)
    box("laptop_base", (4.0, 1.39, 0.68), (0.86, 0.05, 0.56), "c4c7cc", bevel=0.02)
    box("laptop_lid", (4.0, 1.66, 0.4), (0.86, 0.56, 0.05), "9fa4ab", bevel=0.02)
    box("laptop_screen", (4.0, 1.66, 0.43), (0.74, 0.44, 0.02), "dfe8f0", bevel=0.01, subd=1, lump=0)
    tube("mug", (3.4, 1.46, 0.8), 0.08, 0.2, "f4efe6")
    box("lamp_base", (5.1, 1.4, 0.4), (0.3, 0.06, 0.3), CREAM, bevel=0.03)
    tube("lamp_stem", (5.1, 1.7, 0.4), 0.025, 0.6, CREAM)
    ball("lamp_shade", (5.0, 1.98, 0.48), 0.17, CREAM, scale=(1, 0.75, 1))
    box("shelf", (4.3, 2.55, 0.22), (1.7, 0.08, 0.42), WOOD, bevel=0.03)
    books = ["5c7a5a", "c45c4a", "e0b45a", "4e6a8a", "8a5a7a", "6a8a5a", "d07a50"]
    for i, col in enumerate(books):
        h = 0.34 + 0.05 * (i % 3)
        box(f"book{i}", (3.65 + i * 0.15, 2.59 + h / 2, 0.22), (0.13, h, 0.32), col, bevel=0.025, seed=i)
    box("poster", (2.5, 2.55, 0.03), (0.86, 1.06, 0.05), "f6efe2", bevel=0.02)
    box("poster_art", (2.5, 2.55, 0.06), (0.7, 0.9, 0.03), "e58f5a", bevel=0.015)
    ball("poster_sun", (2.5, 2.65, 0.09), 0.2, "f3d36b", scale=(1, 1, 0.25))
    pts = []
    for i in range(16):
        x = 1.9 + i * 0.27
        y = 3.75 - 0.22 * math.sin(math.pi * (i % 8) / 8)
        pts.append((x, y))
        ball(f"fairy{i}", (x, y, 0.1), 0.055, "ffc860", lump=0, seed=i)
    # chair
    box("chair_seat", (4.2, 0.78, 1.55), (0.8, 0.15, 0.76), CREAM, bevel=0.07)
    box("chair_back", (4.2, 1.25, 1.92), (0.8, 0.8, 0.15), CREAM, bevel=0.07)
    tube("chair_stem", (4.2, 0.42, 1.55), 0.05, 0.65, "5a5a62")
    box("chair_base", (4.2, 0.1, 1.55), (0.66, 0.06, 0.66), "5a5a62", bevel=0.03)
    # plant
    tube("plant_pot", (5.3, 0.32, 5.25), 0.3, 0.62, "c8693f")
    leaves = [(0, 0.95, 0), (0.22, 0.8, 0.1), (-0.2, 0.85, -0.1), (0.05, 1.2, 0.15), (-0.1, 1.1, 0.25), (0.2, 1.1, -0.2)]
    for i, o in enumerate(leaves):
        ball(f"leaf{i}", (5.3 + o[0], o[1], 5.25 + o[2]), 0.24, "6f9e57", scale=(1, 0.55, 1), seed=i)
    # floor clutter: backpack beside the bed, slippers, a dropped sweater and jeans, books
    box("backpack", (1.6, 0.36, 3.95), (0.52, 0.66, 0.34), "b88a5a", bevel=0.16)
    box("backpack_pocket", (1.6, 0.26, 4.15), (0.38, 0.28, 0.1), "a77a4c", bevel=0.05)
    box("slipper_a", (3.9, 0.17, 4.55), (0.2, 0.11, 0.38), CREAM, bevel=0.05)
    box("slipper_b", (4.15, 0.17, 4.5), (0.2, 0.11, 0.38), CREAM, bevel=0.05)
    cloth("sweater_floor", (1.9, 0.14, 4.4), (0.7, 0.1, 0.5), "5a7aa0", folds=0.06)
    cloth("jeans_floor", (2.45, 0.14, 4.8), (0.55, 0.1, 0.45), "6f9a6a", folds=0.06)
    box("floor_book_a", (2.3, 0.17, 3.7), (0.5, 0.1, 0.36), "7a6a9a", bevel=0.03)
    box("floor_book_b", (2.3, 0.27, 3.7), (0.42, 0.1, 0.3), "c4a35a", bevel=0.03)


def bake_ao():
    """Bake AO per vertex, multiply by clay colour, store in attribute 'Col'."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    scene.cycles.device = "CPU"
    obs = [o for o in scene.objects if o.type == "MESH"]
    for ob in obs:
        bpy.context.view_layer.objects.active = ob
        for m in list(ob.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
        # mobile budget: cap each prop at ~1500 vertices (collapse keeps the soft silhouette)
        if len(ob.data.vertices) > 1500:
            d = ob.modifiers.new("budget", "DECIMATE")
            d.ratio = 1500 / len(ob.data.vertices)
            bpy.ops.object.modifier_apply(modifier="budget")
        ob.data.shade_smooth()
        ob.data.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        ob.data.attributes.active_color = ob.data.color_attributes["Col"]
        mat = bpy.data.materials.new(ob.name)
        ob.data.materials.append(mat)
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = obs[0]
    scene.render.bake.target = "VERTEX_COLORS"
    bpy.ops.object.bake(type="AO")
    for ob in obs:
        base = hexc(ob["clay_color"])
        col = ob.data.color_attributes["Col"]
        for d in col.data:
            ao = 0.35 + 0.65 * d.color[0]
            d.color = (base[0] * ao, base[1] * ao, base[2] * ao, 1.0)
        ob.data.materials.clear()


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    build()
    bake_ao()
    bpy.ops.export_scene.gltf(filepath=sys.argv[sys.argv.index("--") + 1], export_format="GLB", export_vertex_color="ACTIVE", export_materials="NONE", export_texcoords=False
    )
    print("EXPORTED", len(bpy.context.scene.objects))
