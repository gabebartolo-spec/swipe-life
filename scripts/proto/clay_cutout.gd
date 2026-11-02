extends Node2D
## Flat clay cut-out girl: pre-rendered clay pieces (tools/blender/render_cutouts.py)
## turned on their joints, pose by pose on twos,
## copying the Mixamo wave's 2D joint angles from cutout.json.

const DIR := "res://assets/clay2d/"
const SIDES := ["Left", "Right"]
const BONES := ["Arm", "ForeArm", "Hand"]

var _poses: Array = []
var _pieces := {}
var _frame := 0


func _ready() -> void:
	RenderingServer.set_default_clear_color(Color("e9dcc8"))
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIR + "cutout.json"))
	_poses = data["poses"]
	var pivots: Dictionary = data["pivots"]
	var shader: Shader = load("res://shaders/clay_cutout.gdshader")
	var body := _piece("body", pivots, Vector2.ZERO, shader)
	# feet at the bottom centre of the stretched viewport; the girl (~560 px) fills ~85% of it
	var view := get_viewport_rect().size
	body.position = Vector2(view.x / 2, view.y * 0.94)
	body.scale = Vector2.ONE * view.y * 0.85 / 560.0
	add_child(body)
	for side in SIDES:
		var parent := body
		var parent_pivot: Vector2 = _px(pivots["body"])
		for bone in BONES:
			var name: String = side + bone
			var piece := _piece(name, pivots, parent_pivot, shader)
			parent.add_child(piece)
			_pieces[name] = piece
			parent = piece
			parent_pivot = _px(pivots[name])
	var timer := Timer.new()
	timer.wait_time = 1.0 / 12.0
	timer.timeout.connect(_step)
	add_child(timer)
	timer.start()
	_apply()


func _px(p: Array) -> Vector2:
	return Vector2(p[0], p[1])


func _piece(name: String, pivots: Dictionary, parent_pivot: Vector2, shader: Shader) -> Sprite2D:
	var s := Sprite2D.new()
	s.name = name
	s.texture = load(DIR + name + ".png")
	s.centered = false
	s.offset = -_px(pivots[name])
	s.position = _px(pivots[name]) - parent_pivot
	var mat := ShaderMaterial.new()
	mat.shader = shader
	mat.set_shader_parameter("seed", float(name.hash() % 97))
	s.material = mat
	return s


func _step() -> void:
	_frame = (_frame + 1) % _poses.size()
	_apply()


func _apply() -> void:
	var pose: Dictionary = _poses[_frame]
	for name in _pieces:
		_pieces[name].rotation = pose[name]
