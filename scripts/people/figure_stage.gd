class_name FigureStage
extends TextureRect
## Draws people live in 3D over a room still, through the still's own camera and light, and keeps
## them busy: walking the free floor, sitting on the bed and sofa, lying down, on the phone.
## The room's baked depth map hides them behind furniture and says where the floor is free.

const VIEW := Vector2i(1080, 900)
const VIEW_SIZE := 5.6  # metres, top to bottom: the stills' camera
const BASIS_CAM := Basis(
	Vector3(0.707107, 0, -0.707107),
	Vector3(-0.408248, 0.816497, -0.408248),
	Vector3(0.57735, 0.57735, 0.57735)
)
const ROOM_CENTRE := {
	"bedroom": Vector2(2, 2),
	"bathroom": Vector2(6, 2),
	"living": Vector2(2, 6),
	"kitchen": Vector2(6, 6),
}
const DEPTH_SPAN := 16.0
const FLOOR_Y := 0.05
const DEPTH_DIR := "res://assets/house/depth"
const WALK_SPEED := 0.55  # metres a second, matched to the walk clip's stride at room scale
const CRAWL_SPEED := 0.22
const TURN_SPEED := 6.0
const CLEARANCE := 0.28  # metres of free floor around a figure
const STAY_MIN := 4.0
const STAY_MAX := 9.0
const PERSONAL_SPACE := 0.75  # metres between where two people stop
const SEAT_STEP := 0.6  # metres between seats along a bed or sofa
const ITEM_MODELS := "res://assets/house/items/items.glb"
## Floor room an item needs, in metres from its middle. A rug is flat, so people walk over it.
const ITEM_SPACE := {
	"plant": 0.3,
	"bookshelf": 0.55,
	"rug": 0.6,
	"sofa": 0.95,
	"tv": 0.6,
	"piano": 0.8,
	"mattress": 1.0,
	"desk": 0.7,
	"wardrobe": 0.6,
	"espresso": 0.3,
	"cooker": 0.5,
	"spa_bath": 0.9,
}
const FLAT_ITEMS := ["rug"]
const ITEM_GRID := 0.25

var _viewport := SubViewport.new()
var _world := Node3D.new()
var _cam := Camera3D.new()
var _depth: Image
var _depth_tex: Texture2D
var _centre := Vector2.ZERO
var _room := ""
var _actors: Array[Dictionary] = []
var _item_list: Array = []  # [{id, room}] everything bought; this room's are shown
var _item_nodes: Array[Node3D] = []
var _item_spots: Array[Vector3] = []  # x, z, radius of the solid items standing in this room


func _ready() -> void:
	expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_viewport.size = VIEW
	_viewport.own_world_3d = true
	_viewport.transparent_bg = true
	_viewport.msaa_3d = Viewport.MSAA_4X
	_viewport.render_target_update_mode = SubViewport.UPDATE_WHEN_VISIBLE
	add_child(_viewport)
	_viewport.add_child(_world)
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(1, 0.96, 0.92)
	env.ambient_light_energy = 0.35
	env.tonemap_mode = 2
	var we := WorldEnvironment.new()
	we.environment = env
	_world.add_child(we)
	var sun := DirectionalLight3D.new()
	sun.light_color = Color(1, 0.95, 0.88)
	sun.light_energy = 0.75
	_world.add_child(sun)
	sun.look_at_from_position(Vector3(14, 16, 10), Vector3(4, 0, 4))
	_cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	_cam.size = VIEW_SIZE
	_world.add_child(_cam)
	texture = _viewport.get_texture()


## Which room still the figures are in. Everyone starts somewhere new.
func set_room(room: String, home: String) -> void:
	_room = room
	_centre = ROOM_CENTRE[room]
	_cam.transform = Transform3D(BASIS_CAM, Vector3(_centre.x, 1.0, _centre.y) + BASIS_CAM.z * 20.0)
	_depth_tex = load(DEPTH_DIR.path_join("depth_%s_%s.png" % [room, home]))
	_depth = _depth_tex.get_image()
	_rebuild_items()
	for a in _actors:
		_apply_depth(a.fig)
		_place(a)


## Bought items, [{id, room}]. The ones for this room stand on its free floor, the first to the
## back of the room, where nobody needs the space.
func set_items(items: Array) -> void:
	if items == _item_list:
		return
	_item_list = items.duplicate(true)
	_rebuild_items()
	for a in _actors:
		_place(a)


func _rebuild_items() -> void:
	for n in _item_nodes:
		n.queue_free()
	_item_nodes.clear()
	_item_spots.clear()
	if _depth == null:
		return
	var scene: Node = (load(ITEM_MODELS) as PackedScene).instantiate()
	var mine := _item_list.filter(func(it): return it.room == _room)
	mine.sort_custom(func(a, b): return ITEM_SPACE.get(a.id, 0.5) > ITEM_SPACE.get(b.id, 0.5))
	for it: Dictionary in mine:
		var mi := scene.find_child(it.id, true, false) as MeshInstance3D
		var at := _item_spot(it.id)
		if mi == null or at == Vector2.INF:
			continue
		var copy := MeshInstance3D.new()
		copy.mesh = mi.mesh
		copy.material_override = _item_material()
		_world.add_child(copy)
		copy.position = Vector3(at.x, FLOOR_Y, at.y)
		copy.rotation.y = PI / 4.0  # front toward the viewer
		_item_nodes.append(copy)
		if it.id not in FLAT_ITEMS:
			_item_spots.append(Vector3(at.x, at.y, ITEM_SPACE.get(it.id, 0.5)))
	scene.free()


func _item_material() -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = preload("res://shaders/figure_clay.gdshader")
	m.set_shader_parameter("albedo", Color.WHITE)
	m.set_shader_parameter("use_vertex_color", true)
	m.set_shader_parameter("contact_ao", 0.0)
	m.set_shader_parameter("boil_fps", 0.0)
	m.set_shader_parameter("lump", 0.0)
	m.set_shader_parameter("room_depth", _depth_tex)
	m.set_shader_parameter("room_origin", Vector3(_centre.x, 1.0, _centre.y))
	m.set_shader_parameter("room_axis", BASIS_CAM.z)
	m.set_shader_parameter("depth_span", DEPTH_SPAN)
	return m


## The free floor nearest the back wall that has room for this item; Vector2.INF if none.
func _item_spot(id: String) -> Vector2:
	var space: float = ITEM_SPACE.get(id, 0.5)
	var best := Vector2.INF
	var best_rank := INF
	var steps := int(3.4 / ITEM_GRID)
	for i in steps + 1:
		for j in steps + 1:
			var p := _centre + Vector2(-1.7 + i * ITEM_GRID, -1.7 + j * ITEM_GRID)
			var rank := p.x + p.y
			if rank >= best_rank or not is_free(p, space * 0.7):
				continue
			var clear := true
			for s in _item_spots:
				if p.distance_to(Vector2(s.x, s.y)) < s.z + space * 0.8:
					clear = false
					break
			if clear:
				best = p
				best_rank = rank
	return best


## people: [{shape, look (Figure3D tints), age}]. Replaces whoever was here.
func set_people(people: Array) -> void:
	for a in _actors:
		a.fig.queue_free()
	_actors.clear()
	for p: Dictionary in people:
		var fig := Figure3D.new()
		_world.add_child(fig)
		fig.build(p.shape, p.look)
		var actor := {"fig": fig, "age": p.age, "state": "stay", "left": 0.0, "to": Vector3.ZERO}
		_actors.append(actor)
		if _depth:
			_apply_depth(fig)
			_place(actor)


func actors() -> Array[Dictionary]:
	return _actors


func _process(delta: float) -> void:
	if not is_visible_in_tree():
		return
	for a in _actors:
		if a.state == "move":
			_step(a, delta)
		else:
			a.left -= delta
			if a.left <= 0.0:
				_next(a)


func _apply_depth(fig: Figure3D) -> void:
	fig.set_room_depth(_depth_tex, Vector3(_centre.x, 1.0, _centre.y), BASIS_CAM.z, DEPTH_SPAN)


func _place(a: Dictionary) -> void:
	var at := _free_spot(a)
	a.fig.position = Vector3(at.x, FLOOR_Y, at.y)
	a.fig.rotation.y = PI / 4.0 + randf_range(-1.2, 1.2)  # roughly toward the viewer
	a.fig.set_shadow(true)
	_settle(a, _floor_clip(a))


func _next(a: Dictionary) -> void:
	if a.fig.position.y > FLOOR_Y + 0.01 or a.get("seated", false):  # stand up where there is room
		a.seated = false
		a.seat_z = -1.0
		a.lying = false
		var off := _free_near(Vector2(a.fig.position.x, a.fig.position.z))
		a.fig.position = Vector3(off.x, FLOOR_Y, off.y)
		a.fig.set_shadow(true)
	var seat := _seat_choice(a)
	if not seat.is_empty():
		use_seat(a, seat)
		return
	var from := Vector2(a.fig.position.x, a.fig.position.z)
	for i in 20:
		var to := _free_spot(a)
		if to.distance_to(from) > 0.6 and _line_free(from, to):
			a.to = Vector3(to.x, FLOOR_Y, to.y)
			a.state = "move"
			a.fig.play("crawl" if a.age <= 3 else "walk")
			return
	_settle(a, _floor_clip(a))


func _step(a: Dictionary, delta: float) -> void:
	var fig: Figure3D = a.fig
	var gap: Vector3 = a.to - fig.position
	var speed := CRAWL_SPEED if a.age <= 3 else WALK_SPEED
	if gap.length() <= speed * delta:
		fig.position = a.to
		_settle(a, _floor_clip(a))
		return
	var want := atan2(gap.x, gap.z)
	fig.rotation.y = lerp_angle(fig.rotation.y, want, minf(1.0, TURN_SPEED * delta))
	fig.position += gap.normalized() * speed * delta


func _settle(a: Dictionary, clip: String) -> void:
	a.state = "stay"
	a.left = randf_range(STAY_MIN, STAY_MAX)
	a.fig.play(clip)


func _floor_clip(a: Dictionary) -> String:
	if a.age <= 3:
		return "sit_floor"
	var clips := ["idle", "idle"]
	if a.age >= 10:
		clips.append("text")
	if a.age <= 17:
		clips.append("sit_floor")
	return clips.pick_random()


## A seat in this room, one time in two: side of the bed, the sofa; lying on the bed.
func _seat_choice(a: Dictionary) -> Dictionary:
	if a.age <= 3 or randf() < 0.5:
		return {}
	var clip := "sit" if _room == "bedroom" else "sit_talk"
	if _room == "bedroom" and randf() < 0.3:
		clip = "lay_back"
	return seat_for(clip, a)


## Where this clip fits in the current room; empty when the room has no such furniture.
func seat_for(clip: String, who: Dictionary = {}) -> Dictionary:
	var first := {"bedroom": 1.6, "living": 5.95}.get(_room, -1.0) as float
	if first < 0.0:
		return {}
	var z := _open_seat(first, clip, who)
	if z < 0.0:
		return {}
	var edge := _edge_along_x(z)
	if edge < 0.0:
		return {}
	var surface := surface_y(edge - 0.18, z)
	if surface < 0.2:
		return {}
	return {"clip": clip, "x": edge, "z": z, "y": surface}


## The first seat nobody has, or -1: a lying figure takes the whole bed, and needs it empty.
func _open_seat(first: float, clip: String, who: Dictionary) -> float:
	for other in _actors:
		if other != who and other.get("lying", false):
			return -1.0
		if clip == "lay_back" and other != who and other.get("seat_z", -1.0) >= 0.0:
			return -1.0
	for candidate: float in [first, first - SEAT_STEP]:
		var taken := false
		for other in _actors:
			if other != who and absf(other.get("seat_z", -1.0) - candidate) < 0.1:
				taken = true
		if not taken:
			return candidate
	return -1.0


func use_seat(a: Dictionary, seat: Dictionary) -> void:
	var fig: Figure3D = a.fig
	a.seated = true
	a.seat_z = seat.z
	a.lying = seat.clip == "lay_back"
	fig.play(seat.clip)
	fig.set_shadow(false)
	if seat.clip == "lay_back":
		fig.position = Vector3(seat.x - 0.7, seat.y - fig.pelvis_floor(), 1.69)
		fig.rotation.y = 0.0  # head on the pillow, at the wall end of the bed
	else:
		fig.position = Vector3(seat.x - 0.02, seat.y + 0.03 - fig.hip_lift(), seat.z)
		fig.rotation.y = PI / 2
	a.state = "stay"
	a.left = randf_range(STAY_MIN, STAY_MAX) * 1.5


## The first x from the back wall where the floor is free again at this z: the furniture's edge.
func _edge_along_x(z: float) -> float:
	var x := _centre.x - 1.7
	var blocked := false
	while x < _centre.x + 1.7:
		var open := is_free(Vector2(x, z), 0.05)
		if not open:
			blocked = true
		elif blocked:
			return x
		x += 0.05
	return -1.0


## Clear floor nobody else is standing on or heading for.
func _free_spot(who: Dictionary) -> Vector2:
	for i in 40:
		var p := _centre + Vector2(randf_range(-1.7, 1.7), randf_range(-1.7, 1.7))
		if is_free(p) and _has_space(p, who):
			return p
	for i in 40:
		var p := _centre + Vector2(randf_range(-1.7, 1.7), randf_range(-1.7, 1.7))
		if is_free(p):
			return p
	return _centre + Vector2(0.8, 0.8)


func _has_space(p: Vector2, who: Dictionary) -> bool:
	for other in _actors:
		if other == who:
			continue
		var at: Vector3 = other.to if other.state == "move" else other.fig.position
		if p.distance_to(Vector2(at.x, at.z)) < PERSONAL_SPACE:
			return false
	return true


func _free_near(p: Vector2) -> Vector2:
	for r in range(1, 12):
		for i in 8:
			var q := p + Vector2.from_angle(i * TAU / 8.0) * r * 0.12
			if is_free(q):
				return q
	return p


func _line_free(a: Vector2, b: Vector2) -> bool:
	var n := int(a.distance_to(b) / 0.15) + 1
	for i in n + 1:
		if not is_free(a.lerp(b, float(i) / n)):
			return false
	return true


## Is this floor point visible and clear of furniture, with room for a figure around it?
func is_free(p: Vector2, clearance := CLEARANCE) -> bool:
	if absf(p.x - _centre.x) > 1.85 or absf(p.y - _centre.y) > 1.85:
		return false
	for s in _item_spots:
		if p.distance_to(Vector2(s.x, s.y)) < s.z:
			return false
	for off: Vector2 in [
		Vector2.ZERO,
		Vector2(clearance, 0),
		Vector2(-clearance, 0),
		Vector2(0, clearance),
		Vector2(0, -clearance)
	]:
		var w := Vector3(p.x + off.x, FLOOR_Y, p.y + off.y)
		if absf(_baked_at(w) - _toward_cam(w)) > 0.07:
			return false
	return true


## Height of whatever is on top at this floor position.
func surface_y(x: float, z: float) -> float:
	var y := 1.3
	while y > 0.0:
		var w := Vector3(x, y, z)
		if absf(_baked_at(w) - _toward_cam(w)) < 0.05:
			return y
		y -= 0.03
	return 0.0


func _toward_cam(w: Vector3) -> float:
	return (w - Vector3(_centre.x, 1.0, _centre.y)).dot(BASIS_CAM.z)


func _baked_at(w: Vector3) -> float:
	var rel := w - Vector3(_centre.x, 1.0, _centre.y)
	var px := VIEW_SIZE / VIEW.y
	var x := int(VIEW.x / 2.0 + rel.dot(BASIS_CAM.x) / px)
	var y := int(VIEW.y / 2.0 - rel.dot(BASIS_CAM.y) / px)
	if x < 0 or y < 0 or x >= VIEW.x or y >= VIEW.y:
		return -99.0
	var c := _depth.get_pixel(x, y)
	var v := (roundf(c.r * 255.0) * 256.0 + roundf(c.g * 255.0)) / 65535.0
	return (v - 0.5) * DEPTH_SPAN if v > 0.0 else -99.0
