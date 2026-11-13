"""Hand edits to a driveway setting (docs/SETTING_EDITS.md): move, turn, resize or remove its pieces in Blender.

build_clay_setting.py builds a setting in code; this module lets the director's edits ride on top of it:
- track() tags every object with the piece it belongs to (a tree's trunk and crown are one piece "tr");
- apply() moves, turns, scales or removes pieces as tools/blender/setting_edits/<kind>.json says, before the bake;
- open_for_editing() (the --edit build) joins each piece into one object you can grab, applies the saved edits so
  they show, points the view down the game camera and saves the scene as a .blend;
- harvest (run on that saved .blend) writes the pieces' new places back to the JSON.

An edit is relative to where the code puts the piece, about the middle of its foot:
  "tr": {"move": [x, y, z], "turn": degrees about the vertical, "scale": [x, y, z]}  (Godot axes, metres)
  "b0": {"remove": true}
so a piece the code later moves keeps the director's nudge on top.

Harvest: blender -b <edit.blend> --python tools/blender/setting_edit.py -- harvest <kind>
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

EDITS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setting_edits")
# Helpers whose outermost call is one piece. A label replaces the first argument as the piece's name where that
# argument is not a name. Helpers left out (house_drive, level_round, next_door) only call these, so their parts
# are pieces of their own: a drive and its paths move apart.
PIECES = {
    "ground": "ground",
    "home_body": "home",
    "road_x": "street",
    "bay_lines": "bay_lines",
    "neighbour": None,
    "house": None,
    "block": None,
    "tree": None,
    "palm": None,
    "bush": None,
    "lamp": None,
    "chimney": None,
    "picket_x": None,
    "picket_z": None,
    "board_fence_x": None,
    "board_fence_z": None,
    "railing_x": None,
    "railing_z": None,
    "chainlink_x": None,
    "chainlink_z": None,
    "tufts": None,
    "band": None,
    "flat": None,
    "patch": None,
    "strip_x": None,
    "strip_z": None,
    "prism": None,
    "box": None,
    "ball": None,
    "tube": None,
}
_depth = 0


def _gb(v):
    """Godot (x, y, z) to Blender."""
    return Vector((v[0], -v[2], v[1]))


def _bg(v):
    return [v[0], v[2], -v[1]]


def track(ns):
    """Wraps the setting's helpers in its module namespace `ns`, so each object they make is tagged with its piece.
    A piece named like an earlier one plus "_..." ("br_door" after "br") joins it."""

    def wrap(fn, label):
        def run(*a, **kw):
            global _depth
            before = None if _depth else {o.as_pointer() for o in bpy.data.objects}
            _depth += 1
            try:
                return fn(*a, **kw)
            finally:
                _depth -= 1
                if before is not None:
                    name = label or (a[0] if a and isinstance(a[0], str) else fn.__name__)
                    used = {o["piece"] for o in bpy.data.objects if "piece" in o}
                    name = next((u for u in used if name.startswith(u + "_")), name)
                    for o in bpy.data.objects:
                        if o.as_pointer() not in before:
                            o["piece"] = name

        return run

    for fn_name, label in PIECES.items():
        if fn_name in ns:
            ns[fn_name] = wrap(ns[fn_name], label)


def pieces():
    out = {}
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and "piece" in o:
            out.setdefault(o["piece"], []).append(o)
    return out


def foot(obs):
    """The middle of a piece's foot (Blender coordinates), from its modelled mesh: the point it turns and scales
    about, so a tree grows up from the ground."""
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in obs:
        for v in o.data.vertices:
            p = o.matrix_world @ v.co
            lo = Vector(map(min, lo, p))
            hi = Vector(map(max, hi, p))
    return Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))


def load(kind):
    path = os.path.join(EDITS, kind + ".json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def matrix(e, pivot):
    """The edit `e` as a Blender matrix about `pivot`."""
    s = e.get("scale", [1, 1, 1])
    scale = Matrix.Diagonal((s[0], s[2], s[1], 1))
    turn = Matrix.Rotation(math.radians(e.get("turn", 0)), 4, "Z")
    move = Matrix.Translation(pivot + _gb(e.get("move", [0, 0, 0])))
    return move @ turn @ scale @ Matrix.Translation(-pivot)


def apply(kind):
    """Applies the saved edits to the built setting, into the meshes (a clay bevel keeps its size when a piece
    grows)."""
    edits, have = load(kind), pieces()
    for name, e in edits.items():
        if name not in have:
            print("SETTING EDIT: no piece", name, "in", kind, "(renamed in the code?); edit skipped")
            continue
        if e.get("remove"):
            for o in have[name]:
                bpy.data.objects.remove(o, do_unlink=True)
            continue
        m = matrix(e, foot(have[name]))
        for o in have[name]:
            o.data.transform(o.matrix_world)
            o.matrix_world = Matrix.Identity(4)
            o.data.transform(m)
    print("SETTING EDITS", kind, len(edits))


def open_for_editing(kind, blend, hexc):
    """Turns the built setting into one grabbable object per piece, with the saved edits showing, and saves it."""
    edits, have = load(kind), pieces()
    dg = bpy.context.evaluated_depsgraph_get()
    for name, obs in have.items():
        pivot = foot(obs)
        for o in obs:
            me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
            me.transform(o.matrix_world)
            col = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
            c = hexc(o.get("clay_color", "cccccc"))
            for d in col.data:
                d.color = c
            o.modifiers.clear()
            o.data = me
            o.matrix_world = Matrix.Identity(4)
        top = obs[0]
        if len(obs) > 1:
            with bpy.context.temp_override(active_object=top, selected_editable_objects=obs):
                bpy.ops.object.join()
        top.name = name
        top.data.transform(Matrix.Translation(-pivot))
        top["piece"], top["foot"] = name, list(pivot)
        top.lock_rotation = (True, True, False)  # turn about the vertical only
        e = edits.get(name, {})
        if e.get("remove"):
            bpy.data.objects.remove(top, do_unlink=True)
            continue
        sc = e.get("scale", [1, 1, 1])
        top.location = pivot + _gb(e.get("move", [0, 0, 0]))
        top.rotation_euler.z = math.radians(e.get("turn", 0))
        top.scale = (sc[0], sc[2], sc[1])
    for o in [o for o in bpy.context.scene.objects if o.type != "MESH"]:
        bpy.data.objects.remove(o, do_unlink=True)
    # the game camera (render_house.gd: orthographic, 5.6 m tall at 1080x900, the setting lifted 0.1): Numpad 0
    # shows exactly the driveway still's frame
    scene = bpy.context.scene
    cam = bpy.data.objects.new("game_camera", bpy.data.cameras.new("game_camera"))
    scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 5.6 * 1080 / 900
    cam.data.clip_end = 100
    rot = Matrix(((0.707107, -0.408248, 0.57735), (0.707107, 0.408248, -0.57735), (0, 0.816497, 0.57735)))
    cam.matrix_world = Matrix.Translation(_gb((0, 0.9, 0)) + rot.col[2] * 20) @ rot.to_4x4()
    cam.hide_select = True
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = 1080, 900
    for area in (a for s in bpy.data.screens for a in s.areas):  # saved with the file: Blender opens on it
        if area.type == "VIEW_3D":
            sp = area.spaces.active
            sp.shading.type = "SOLID"
            sp.shading.color_type = "VERTEX"
            sp.region_3d.view_perspective = "CAMERA"
            sp.region_3d.view_camera_zoom = 8  # the frame fills a full-screen window
    bpy.context.scene["setting_pieces"] = sorted(have)
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print("SETTING EDIT OPEN", kind, blend, len(have), "pieces")


def harvest(kind):
    """Writes the edited .blend's piece places back to setting_edits/<kind>.json (only pieces that changed)."""
    out, seen = {}, set()
    for o in bpy.context.scene.objects:
        if "foot" not in o:
            continue
        name = o["piece"]
        seen.add(name)
        move = _bg(o.location - Vector(o["foot"]))
        s = o.scale
        e = {
            "move": [round(v, 3) + 0.0 for v in move],  # + 0.0: no -0.0
            "turn": round(math.degrees(o.rotation_euler.z), 1),
            "scale": [round(v, 3) for v in (s.x, s.z, s.y)],
        }
        if any(abs(v) > 0.002 for v in e["move"]) or abs(e["turn"]) > 0.05 or any(abs(v - 1) > 0.002 for v in
                                                                                    e["scale"]):
            out[name] = e
    for name in bpy.context.scene["setting_pieces"]:
        if name not in seen:
            out[name] = {"remove": True}  # deleted in Blender (or removed in an earlier edit)
    os.makedirs(EDITS, exist_ok=True)
    path = os.path.join(EDITS, kind + ".json")
    if out:
        lines = [f" {json.dumps(n)}: {json.dumps(e)}" for n, e in sorted(out.items())]  # one line a piece
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("{\n" + ",\n".join(lines) + "\n}\n")
    elif os.path.exists(path):
        os.remove(path)
    print("SETTING EDITS SAVED", kind, len(out), path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:]
    if args[0] == "harvest":
        harvest(args[1])
