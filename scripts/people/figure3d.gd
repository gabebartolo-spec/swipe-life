class_name Figure3D
extends Node3D
## A person as real 3D clay pieces (director 2026-11-09): lives in the room at room scale, seen from
## any angle. Rigid pieces turn about their joints, driven by Mixamo clips (tools/blender/people).

const SCALE_IN_ROOM := 0.6  # body units to room metres: an adult stands about 1.6 m
const DIR := "res://assets/people3d"
const CLAY := preload("res://shaders/figure_clay.gdshader")
const SHADOW := preload("res://shaders/figure_shadow.gdshader")
const BLEND_TIME := 0.25
const VERTEX_GREY := 1.25  # pieces are baked in light grey clay; this brings a tint back to itself
const PARENT := {
	"chest": "pelvis",
	"head": "chest",
	"upper_arm_l": "chest",
	"forearm_l": "upper_arm_l",
	"hand_l": "forearm_l",
	"upper_arm_r": "chest",
	"forearm_r": "upper_arm_r",
	"hand_r": "forearm_r",
	"thigh_l": "pelvis",
	"shin_l": "thigh_l",
	"foot_l": "shin_l",
	"thigh_r": "pelvis",
	"shin_r": "thigh_r",
	"foot_r": "shin_r",
}
## Skin under these clothes is hidden so it cannot poke through.
const COVERED := {
	"trousers": ["pelvis", "thigh_l", "thigh_r", "shin_l", "shin_r"],
	"tee": ["chest"],
	"sweater": ["chest", "upper_arm_l", "upper_arm_r", "forearm_l", "forearm_r"],
	"onesie": ["pelvis", "chest", "thigh_l", "thigh_r"],
}

var _pieces := {}  # piece -> Node3D
var _pivot := {}  # piece -> Vector3
var _align := {}  # piece -> Quaternion from the body's rest pose to the T-pose
var _waist_off := Vector3.ZERO
var _hip_height := 1.0
var _clip := {}
var _time := 0.0
var _in_place := true
var _materials: Array[ShaderMaterial] = []
var _shadow := MeshInstance3D.new()
var _last := {}  # piece -> Transform3D, the pose a new clip blends from
var _blend_left := 0.0


## look: tints per layer, plus "hair" (a cut with a built mesh).
## shape: folder under assets/people3d.
func build(shape: String, look: Dictionary) -> void:
	scale = Vector3.ONE * SCALE_IN_ROOM
	var meta: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("%s/%s/body.json" % [DIR, shape])
	)
	var hips := Vector3.ZERO
	for side in ["l", "r"]:
		hips += _vec(meta.pieces["thigh_" + side].pivot) / 2.0
	var ground: float = meta.ground
	_hip_height = hips.y - ground
	_waist_off = _vec(meta.pieces.pelvis.pivot) - hips
	for piece: String in meta.pieces:
		var node := Node3D.new()
		node.name = piece
		add_child(node)
		_pieces[piece] = node
		_pivot[piece] = _vec(meta.pieces[piece].pivot)
		_align[piece] = _rest_align(piece, meta.pieces[piece])
	var hidden := {}
	for layer: String in COVERED:
		if look.has(layer):
			for piece: String in COVERED[layer]:
				hidden[piece] = true
	_add_meshes("%s/%s/body.glb" % [DIR, shape], look, hidden)
	var quad := QuadMesh.new()
	quad.size = Vector2(1.5, 1.5)
	quad.orientation = PlaneMesh.FACE_Y
	_shadow.mesh = quad
	_shadow.position.y = 0.02
	_shadow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var shade := ShaderMaterial.new()
	shade.shader = SHADOW
	_shadow.material_override = shade
	_materials.append(shade)
	add_child(_shadow)
	var hair_path := "%s/%s/hair/%s.glb" % [DIR, shape, look.get("hair", "")]
	if ResourceLoader.exists(hair_path):
		_add_meshes(hair_path, look, {})


func play(clip_name: String, in_place := true) -> void:
	_clip = JSON.parse_string(FileAccess.get_file_as_string("%s/clips/%s.json" % [DIR, clip_name]))
	_time = 0.0
	_in_place = in_place
	if not _last.is_empty():
		_blend_left = BLEND_TIME
	_pose()


## Hides this figure behind the room's furniture (FigureStage).
func set_room_depth(tex: Texture2D, origin: Vector3, axis: Vector3, span: float) -> void:
	for m in _materials:
		m.set_shader_parameter("room_depth", tex)
		m.set_shader_parameter("room_origin", origin)
		m.set_shader_parameter("room_axis", axis)
		m.set_shader_parameter("depth_span", span)


func set_shadow(on: bool) -> void:
	_shadow.visible = on


## How high the current clip holds the hips above the feet, in room metres.
func hip_lift() -> float:
	return float(_clip.hips[1]) * _hip_height * SCALE_IN_ROOM


## How high above the root the lowest part of the body sits in this clip's first pose: lying clips.
func pelvis_floor() -> float:
	return float(_clip.hips[1]) * _hip_height * SCALE_IN_ROOM - 0.1


func advance(delta: float) -> void:
	_time += delta
	_blend_left = maxf(0.0, _blend_left - delta)
	_pose()


func _process(delta: float) -> void:
	if not _clip.is_empty():
		advance(delta)


func _pose() -> void:
	var frames: int = _clip.frames
	var at: float = fmod(_time * _clip.fps, float(frames))
	var a := int(at)
	var b := (a + 1) % frames
	var t := at - a
	var world := {}
	for piece: String in _pieces:
		var rots: Array = _clip.rot[piece]
		var q := _quat(rots, a).slerp(_quat(rots, b), t)
		world[piece] = (q * _align[piece]).normalized()
	var h: Array = _clip.hips
	var hip := Vector3(h[a * 3], h[a * 3 + 1], h[a * 3 + 2]).lerp(
		Vector3(h[b * 3], h[b * 3 + 1], h[b * 3 + 2]), t
	)
	if _in_place:
		hip.x = 0
		hip.z = 0
	var at_world := {"pelvis": hip * _hip_height + world.pelvis * _waist_off}
	for piece: String in PARENT:  # listed parents first
		var up: String = PARENT[piece]
		at_world[piece] = at_world[up] + world[up] * (_pivot[piece] - _pivot[up])
	var mix := 1.0 - _blend_left / BLEND_TIME
	for piece: String in _pieces:
		var pose := Transform3D(Basis(world[piece]), at_world[piece])
		if _blend_left > 0.0:
			_pieces[piece].transform = _last[piece].interpolate_with(pose, mix)
		else:
			_pieces[piece].transform = pose
			_last[piece] = pose


func _add_meshes(path: String, look: Dictionary, hidden: Dictionary) -> void:
	var scene: Node = (load(path) as PackedScene).instantiate()
	for mi: MeshInstance3D in scene.find_children("*", "MeshInstance3D", true, false):
		var parts := String(mi.name).split("__")
		var layer := parts[0]
		var piece := parts[1]
		if layer in ["tee", "sweater", "onesie", "trousers"] and not look.has(layer):
			continue
		if layer == "body" and hidden.has(piece):
			continue
		var copy := MeshInstance3D.new()
		copy.mesh = mi.mesh
		copy.position = -_pivot[piece]
		copy.material_override = _material(layer, parts[2], look)
		_pieces[piece].add_child(copy)
	scene.free()


func _material(layer: String, mask: String, look: Dictionary) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = CLAY
	var tint := Color.WHITE
	if look.has(layer):
		var cols: Array = look[layer]
		tint = cols[mini(1 if mask == "G" else 0, cols.size() - 1)]
		tint = Color(tint.r * VERTEX_GREY, tint.g * VERTEX_GREY, tint.b * VERTEX_GREY)
	m.set_shader_parameter("albedo", tint)
	m.set_shader_parameter("use_vertex_color", true)
	m.set_shader_parameter("contact_ao", 0.0)
	m.set_shader_parameter("boil_fps", 0.0)
	m.set_shader_parameter("lump", 0.0)
	_materials.append(m)
	return m


func _rest_align(piece: String, data: Dictionary) -> Quaternion:
	var target := Vector3.ZERO
	if piece.begins_with("upper_arm") or piece.begins_with("forearm") or piece.begins_with("hand"):
		target = Vector3.RIGHT if piece.ends_with("_l") else Vector3.LEFT
	elif piece.begins_with("thigh") or piece.begins_with("shin"):
		target = Vector3.DOWN
	if target == Vector3.ZERO or data.end == null:
		return Quaternion.IDENTITY
	return Quaternion((_vec(data.end) - _vec(data.pivot)).normalized(), target)


static func _vec(a: Array) -> Vector3:
	return Vector3(a[0], a[1], a[2])


static func _quat(r: Array, i: int) -> Quaternion:
	var s := i * 4
	return Quaternion(r[s + 1], r[s + 2], r[s + 3], r[s]).normalized()  # stored rounded
