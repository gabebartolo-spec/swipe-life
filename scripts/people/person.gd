class_name Person
extends Node2D
## A modular clay person (GDD §10.7, docs/PEOPLE.md): one bone Node2D per body piece
## (rotation only), each with a Layers child holding that piece's sprites (skin, garments,
## hair), tinted by person_clay.gdshader. A clip of world angles drives the bones on twos
## (12 fps). The node's origin is the point between the feet on the floor.

const DIR := "res://assets/people/slice"
const SHADER := preload("res://shaders/person_clay.gdshader")
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
## Draw order (PEOPLE.md §5): a z per body part, +1 for garments over skin, +2 for outerwear.
const PART_Z := {
	"pelvis": 16,
	"chest": 20,
	"head": 32,
	"upper_arm": 28,
	"forearm": 28,
	"hand": 28,
	"thigh": 8,
	"shin": 8,
	"foot": 8
}
const LAYER_Z := {"body": 0, "trousers": 1, "tee": 1, "sweater": 1, "face": 4}
const FIXED_Z := {"hair_back": 0, "hair_front": 44}
## A hand this far (m) in front of the head in the clip draws its whole arm over the head and hair.
const FRONT_M := 0.35
const ARM_FRONT_Z := 40

## Colours per layer: [c1, c2, c3]. Layers missing here are not worn.
@export var look := {
	"body": [Color("f2c9a5")],
	"hair_back": [Color("6b4430")],
	"hair_front": [Color("6b4430")],
	"tee": [Color("e8d6bd"), Color("ffffff")],
	"trousers": [Color("6f8fb5")],
}

var _bones := {}
var _rest := {}
var _clip := {}
var _frame := 0


func _ready() -> void:
	var text := FileAccess.get_file_as_string(DIR.path_join("manifest.json"))
	var m: Dictionary = JSON.parse_string(text)
	var pivots: Dictionary = m.pivots
	_rest = m.rest_deg
	var ground := Vector2(m.res / 2.0, m.res / 2.0 + 1.2 * float(m.px_per_m))
	for piece in ["pelvis"] + PARENT.keys():
		var bone := Node2D.new()
		bone.name = piece
		var parent: Node2D = self if piece == "pelvis" else _bones[PARENT[piece]]
		var from: Vector2 = ground if piece == "pelvis" else _arr(pivots[PARENT[piece]])
		bone.position = _arr(pivots[piece]) - from
		parent.add_child(bone)
		var layers := Node2D.new()
		layers.name = "Layers"
		bone.add_child(layers)
		_bones[piece] = bone
	var seed := 0
	for sprite_name in m.sprites:
		var s: Dictionary = m.sprites[sprite_name]
		if not look.has(s.layer) and s.layer != "face":
			continue
		var spr := Sprite2D.new()
		spr.texture = load(DIR.path_join(sprite_name + ".png"))
		spr.centered = false
		spr.offset = Vector2(s.rect[0], s.rect[1]) - _arr(pivots[s.piece])
		var part: String = s.piece.trim_suffix("_l").trim_suffix("_r")
		spr.z_index = FIXED_Z.get(s.layer, PART_Z[part] + LAYER_Z.get(s.layer, 1))
		var mat := ShaderMaterial.new()
		mat.shader = SHADER
		mat.set_shader_parameter("raw", s.raw)
		mat.set_shader_parameter("seed", float(seed % 97))
		var cols: Array = look.get(s.layer, [])
		for i in cols.size():
			mat.set_shader_parameter("c%d" % (i + 1), cols[i])
		spr.material = mat
		_bones[s.piece].get_node("Layers").add_child(spr)
		seed += 13


## Plays a clip of world angles (tools/blender/people/clip.py) on twos, looping.
func play(path: String) -> void:
	_clip = JSON.parse_string(FileAccess.get_file_as_string(path))
	_frame = 0
	var t := Timer.new()
	t.wait_time = 1.0 / float(_clip.fps)
	t.timeout.connect(_step)
	add_child(t)
	t.start()
	_step()


func _step() -> void:
	var turn := {}  # piece -> world turn from rest (degrees, counter-clockwise)
	for piece in _bones:
		var track: Array = _clip.bones.get(piece, [])
		turn[piece] = float(track[_frame]) - float(_rest[piece]) if track else 0.0
	for piece in _bones:
		var up: float = turn[PARENT[piece]] if PARENT.has(piece) else 0.0
		_bones[piece].rotation = -deg_to_rad(wrapf(turn[piece] - up, -180.0, 180.0))  # y down: flip
	var front: Dictionary = _clip.get("front", {})
	for side in front:
		var z := ARM_FRONT_Z if float(front[side][_frame]) > FRONT_M else 0
		for part in ["upper_arm_", "forearm_", "hand_"]:
			_bones[part + side].get_node("Layers").z_index = z
	_frame = (_frame + 1) % int(_clip.frames)


static func _arr(a: Array) -> Vector2:
	return Vector2(a[0], a[1])
