extends Node3D
## GDD §10.4 art test: claymation bedroom (director's reference image 5), built from code.
## Floor runs 0..6 on x and z, y is up; back walls on x = 0 and z = 0.

const CLAY := preload("res://shaders/clay.gdshader")
const WOOD := Color("c98a55")
const WALL := Color("e6d9c6")
const CREAM := Color("f3ead8")
const SKIN := Color("f2c9a5")
const HAIR := Color("6b4430")

const GLOWS := {"fairy": 3.0, "win_pane": 0.9, "laptop_screen": 0.25}

## Room modelled in Blender with baked AO (tools/blender/build_clay_room.py); empty = code props.
@export var baked_room: PackedScene
## Clay girl sculpted in Blender (tools/blender/build_clay_girl.py); empty = code character.
@export var baked_girl: PackedScene

var _materials := {}


func _ready() -> void:
	get_viewport().msaa_3d = Viewport.MSAA_4X
	$Sun.look_at_from_position(Vector3(9, 12, 8), Vector3(3, 0, 3))
	if baked_room:
		_use_baked(baked_room.instantiate())

	else:
		_build_shell()
		_build_bed()
		_build_window()
		_build_desk()
		_build_props()
	var feet := Vector3(3.1, 0.06, 3.6)
	if baked_girl:
		var girl: Node3D = baked_girl.instantiate()
		girl.position = feet
		girl.rotation.y = PI / 4
		_use_baked(girl)
	else:
		_build_character(feet)
	if "--front" in OS.get_cmdline_user_args():  # close-up for checking the character
		$Camera.size = 3.0
		$Camera.look_at_from_position(feet + Vector3(6, 1.1, 6), feet + Vector3(0, 1.1, 0))


func _use_baked(room: Node3D) -> void:
	add_child(room)
	for mi: MeshInstance3D in room.find_children("*", "MeshInstance3D"):
		var glow := 0.0
		for prefix: String in GLOWS:
			if mi.name.begins_with(prefix):
				glow = GLOWS[prefix]
		var m := ShaderMaterial.new()
		m.shader = CLAY
		m.set_shader_parameter("albedo", Color.WHITE)
		m.set_shader_parameter("use_vertex_color", true)
		m.set_shader_parameter("contact_ao", 0.0)
		m.set_shader_parameter("emission", glow)
		if mi.name.begins_with("skin"):  # fingerprint ridges read as wrinkles on a face
			m.set_shader_parameter("bump", 0.15)
		mi.material_override = m


func _build_shell() -> void:
	_box(Vector3(3, -0.2, 3), Vector3(6.3, 0.4, 6.3), WALL, 0.12, 0.0)
	for i in range(12):
		var tint := WOOD.darkened(0.06 * (i % 3)) if i % 2 == 0 else WOOD.lightened(0.05)
		_box(Vector3(0.25 + i * 0.5, 0.02, 3), Vector3(0.47, 0.1, 6.0), tint, 0.04, 0.0)
	_box(Vector3(-0.15, 2.0, 3), Vector3(0.3, 4.4, 6.3), WALL, 0.12, 0.0)
	_box(Vector3(3, 2.0, -0.15), Vector3(6.3, 4.4, 0.3), WALL, 0.12, 0.0)
	_box(Vector3(3.1, 0.09, 3.5), Vector3(2.8, 0.05, 2.2), Color("d9a3a0"), 0.03)
	_box(Vector3(3.1, 0.1, 3.5), Vector3(2.4, 0.05, 1.8), Color("e6c0b4"), 0.03)


func _build_bed() -> void:
	_box(Vector3(1.0, 0.3, 1.75), Vector3(2.0, 0.42, 2.9), WOOD.darkened(0.1), 0.1)
	_box(Vector3(1.0, 0.85, 0.32), Vector3(2.0, 1.3, 0.16), WOOD.darkened(0.1), 0.08)
	_box(Vector3(1.0, 0.63, 1.8), Vector3(1.85, 0.3, 2.65), CREAM, 0.12)
	_box(Vector3(1.05, 0.83, 2.25), Vector3(1.95, 0.2, 1.75), Color("9fb6d2"), 0.1)
	_box(Vector3(1.05, 0.95, 2.75), Vector3(2.02, 0.1, 0.8), Color("d8c3a5"), 0.05)
	_box(Vector3(0.6, 0.92, 0.75), Vector3(0.7, 0.24, 0.5), CREAM.lightened(0.3), 0.12)
	_box(Vector3(1.4, 0.92, 0.78), Vector3(0.7, 0.24, 0.5), Color("a9c2a2"), 0.12)


func _build_window() -> void:
	_box(Vector3(0.02, 2.3, 2.0), Vector3(0.12, 1.4, 1.5), Color.WHITE, 0.05)
	_box(Vector3(0.06, 2.3, 2.0), Vector3(0.06, 1.2, 1.3), Color("fff3d6"), 0.02, 1.0, 0.9)
	_box(Vector3(0.1, 2.3, 2.0), Vector3(0.06, 1.2, 0.07), Color.WHITE, 0.03)
	_box(Vector3(0.1, 2.3, 2.0), Vector3(0.06, 0.07, 1.3), Color.WHITE, 0.03)
	_box(Vector3(0.16, 1.58, 2.0), Vector3(0.3, 0.08, 1.7), Color.WHITE, 0.04)
	_box(Vector3(0.18, 2.25, 1.1), Vector3(0.14, 1.7, 0.35), Color("e8dccb"), 0.07)
	_box(Vector3(0.18, 2.25, 2.9), Vector3(0.14, 1.7, 0.35), Color("e8dccb"), 0.07)
	_capsule(Vector3(0.24, 3.12, 2.0), 0.04, 2.4, Color("8a6a55"), Vector3(PI / 2, 0, 0))
	_capsule(Vector3(0.2, 1.72, 1.6), 0.08, 0.2, Color("d07a50"))
	_ball(Vector3(0.2, 1.88, 1.6), 0.1, Color("7fae6a"))
	_capsule(Vector3(0.2, 1.72, 2.4), 0.08, 0.2, Color("d07a50"))
	_ball(Vector3(0.2, 1.88, 2.4), 0.1, Color("e0a24a"))


func _build_desk() -> void:
	_box(Vector3(4.2, 1.3, 0.55), Vector3(2.3, 0.12, 1.0), WOOD, 0.05)
	_box(Vector3(4.95, 0.64, 0.55), Vector3(0.75, 1.2, 0.92), WOOD.darkened(0.05), 0.06)
	_box(Vector3(4.95, 0.9, 1.02), Vector3(0.5, 0.08, 0.04), WOOD.darkened(0.3), 0.02)
	for z in [0.18, 0.92]:
		_box(Vector3(3.2, 0.64, z), Vector3(0.12, 1.2, 0.12), WOOD.darkened(0.05), 0.05)
	_box(Vector3(4.0, 1.39, 0.65), Vector3(0.85, 0.05, 0.55), Color("c4c7cc"), 0.03)
	_box(Vector3(4.0, 1.66, 0.35), Vector3(0.85, 0.55, 0.05), Color("9fa4ab"), 0.03)
	_box(Vector3(4.0, 1.66, 0.38), Vector3(0.72, 0.42, 0.02), Color("dfe8f0"), 0.01, 1.0, 0.25)
	_capsule(Vector3(3.4, 1.46, 0.8), 0.08, 0.2, Color("f4efe6"))
	_box(Vector3(5.1, 1.4, 0.4), Vector3(0.28, 0.06, 0.28), CREAM, 0.03)
	_capsule(Vector3(5.1, 1.7, 0.4), 0.03, 0.62, CREAM)
	_ball(Vector3(5.0, 1.98, 0.48), 0.16, CREAM, Vector3(1, 0.75, 1), 0.3)
	# shelf with books
	_box(Vector3(4.3, 2.55, 0.22), Vector3(1.7, 0.08, 0.42), WOOD, 0.03)
	var books := ["5c7a5a", "c45c4a", "e0b45a", "4e6a8a", "8a5a7a", "6a8a5a", "d07a50"]
	for i in books.size():
		var h := 0.34 + 0.05 * (i % 3)
		_box(
			Vector3(3.65 + i * 0.15, 2.59 + h * 0.5, 0.22),
			Vector3(0.13, h, 0.32),
			Color(books[i]),
			0.03,
			0.0
		)
	# poster
	_box(Vector3(2.5, 2.55, 0.03), Vector3(0.85, 1.05, 0.05), Color("f6efe2"), 0.02)
	_box(Vector3(2.5, 2.55, 0.06), Vector3(0.7, 0.9, 0.03), Color("e58f5a"), 0.02)
	_ball(Vector3(2.5, 2.65, 0.09), 0.2, Color("f3d36b"), Vector3(1, 1, 0.3))
	# fairy lights along the back wall
	for i in range(16):
		var x := 1.9 + i * 0.27
		var y := 3.75 - 0.22 * sin(PI * fmod(float(i), 8.0) / 8.0)
		_ball(Vector3(x, y, 0.08), 0.05, Color("ffc860"), Vector3.ONE * 1.6, 3.0, 0.0)


func _build_props() -> void:
	# desk chair
	_box(Vector3(4.2, 0.78, 1.55), Vector3(0.8, 0.14, 0.75), CREAM, 0.07)
	_box(Vector3(4.2, 1.25, 1.92), Vector3(0.8, 0.8, 0.14), CREAM, 0.07)
	_capsule(Vector3(4.2, 0.42, 1.55), 0.05, 0.65, Color("5a5a62"))
	_box(Vector3(4.2, 0.1, 1.55), Vector3(0.65, 0.06, 0.65), Color("5a5a62"), 0.03)
	# plant
	_box(Vector3(5.3, 0.32, 5.25), Vector3(0.62, 0.62, 0.62), Color("c8693f"), 0.16)
	var leaves := [
		Vector3(0, 0.95, 0),
		Vector3(0.22, 0.8, 0.1),
		Vector3(-0.2, 0.85, -0.1),
		Vector3(0.05, 1.2, 0.15),
		Vector3(-0.1, 1.1, 0.25),
		Vector3(0.2, 1.1, -0.2)
	]
	for o: Vector3 in leaves:
		_ball(Vector3(5.3, 0, 5.25) + o, 0.24, Color("6f9e57"), Vector3(1, 0.6, 1))
	# backpack, slippers, clothes, floor books
	_box(Vector3(2.35, 0.35, 3.4), Vector3(0.5, 0.62, 0.32), Color("b88a5a"), 0.16)
	_box(Vector3(2.35, 0.25, 3.6), Vector3(0.36, 0.28, 0.1), Color("a77a4c"), 0.06)
	_box(Vector3(3.9, 0.15, 4.55), Vector3(0.18, 0.1, 0.36), CREAM, 0.05)
	_box(Vector3(4.15, 0.15, 4.5), Vector3(0.18, 0.1, 0.36), CREAM, 0.05)
	_box(Vector3(1.9, 0.11, 4.4), Vector3(0.65, 0.08, 0.45), Color("5a7aa0"), 0.04)
	_box(Vector3(2.4, 0.11, 4.75), Vector3(0.5, 0.08, 0.4), Color("6f9a6a"), 0.04)
	_box(Vector3(0.45, 0.17, 3.7), Vector3(0.5, 0.1, 0.35), Color("7a6a9a"), 0.03)
	_box(Vector3(0.45, 0.27, 3.7), Vector3(0.42, 0.1, 0.3), Color("c4a35a"), 0.03)


func _build_character(feet: Vector3) -> void:
	var root := Node3D.new()
	root.position = feet
	root.rotation.y = PI / 4  # face the camera (+x +z)
	add_child(root)
	for side in [-1.0, 1.0]:
		_box(
			Vector3(0.15 * side, 0.07, 0.04),
			Vector3(0.22, 0.14, 0.32),
			Color.WHITE,
			0.07,
			1.0,
			0.0,
			root
		)
		_capsule(Vector3(0.15 * side, 0.45, 0), 0.13, 0.7, Color("6f8fb5"), Vector3.ZERO, root)
		_capsule(
			Vector3(0.43 * side, 0.98, 0),
			0.11,
			0.6,
			Color("e8d6bd"),
			Vector3(0, 0, 0.12 * side),
			root
		)
		_ball(Vector3(0.47 * side, 0.66, 0), 0.1, SKIN, Vector3.ONE, 0.0, 1.0, root)
	_box(Vector3(0, 1.0, 0), Vector3(0.72, 0.66, 0.46), Color("e8d6bd"), 0.2, 1.0, 0.0, root)
	_box(Vector3(0, 0.74, 0), Vector3(0.62, 0.14, 0.4), Color("6f8fb5"), 0.06, 1.0, 0.0, root)
	_ball(Vector3(0, 1.68, 0), 0.43, SKIN, Vector3(1.05, 0.96, 1), 0.0, 1.0, root)
	_ball(Vector3(0, 1.8, -0.08), 0.44, HAIR, Vector3(1.04, 0.92, 1), 0.0, 1.0, root)
	_ball(Vector3(0, 1.98, 0.1), 0.3, HAIR, Vector3(1.3, 0.5, 1), 0.0, 1.0, root)
	for side in [-1.0, 1.0]:
		_ball(Vector3(0.36 * side, 1.5, -0.04), 0.17, HAIR, Vector3(0.8, 1.6, 1), 0.0, 1.0, root)
		_ball(Vector3(0.14 * side, 1.64, 0.4), 0.045, Color("2b2024"), Vector3.ONE, 0.0, 0.0, root)
		_ball(
			Vector3(0.25 * side, 1.55, 0.35),
			0.06,
			Color("f0a0a0"),
			Vector3(1, 0.6, 0.4),
			0.0,
			0.0,
			root
		)
	_capsule(Vector3(0, 1.52, 0.41), 0.018, 0.12, Color("8a3a3a"), Vector3(0, 0, PI / 2), root)


func _mat(color: Color, emission: float, ao: float) -> ShaderMaterial:
	var key := "%s|%s|%s" % [color.to_html(), emission, ao]
	if not _materials.has(key):
		var m := ShaderMaterial.new()
		m.shader = CLAY
		m.set_shader_parameter("albedo", color)
		m.set_shader_parameter("emission", emission)
		m.set_shader_parameter("contact_ao", ao)
		_materials[key] = m
	return _materials[key]


func _add(
	mesh: Mesh, at: Vector3, color: Color, emission: float, ao: float, parent: Node3D
) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.position = at
	mi.material_override = _mat(color, emission, ao)
	(parent if parent else self).add_child(mi)
	return mi


func _box(
	at: Vector3,
	size: Vector3,
	color: Color,
	radius: float,
	ao := 1.0,
	emission := 0.0,
	parent: Node3D = null
) -> void:
	_add(_rounded_box(size, radius), at, color, emission, ao, parent)


func _ball(
	at: Vector3,
	radius: float,
	color: Color,
	scale_by := Vector3.ONE,
	emission := 0.0,
	ao := 1.0,
	parent: Node3D = null
) -> void:
	var mesh := SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 2.0
	_add(mesh, at, color, emission, ao, parent).scale = scale_by


func _capsule(
	at: Vector3,
	radius: float,
	height: float,
	color: Color,
	rot := Vector3.ZERO,
	parent: Node3D = null
) -> void:
	var mesh := CapsuleMesh.new()
	mesh.radius = radius
	mesh.height = maxf(height, radius * 2.0)
	_add(mesh, at, color, 0.0, 1.0, parent).rotation = rot


## Rounded box: a sphere split along each axis and pushed out to the box size.
func _rounded_box(size: Vector3, radius: float) -> ArrayMesh:
	var r := minf(radius, minf(size.x, minf(size.y, size.z)) * 0.5)
	var sphere := SphereMesh.new()
	sphere.radius = r
	sphere.height = r * 2.0
	sphere.radial_segments = 24
	sphere.rings = 12
	var arrays := sphere.get_mesh_arrays()
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var half := size * 0.5 - Vector3(r, r, r)
	for i in verts.size():
		var v := verts[i]
		verts[i] = v + Vector3(signf(v.x) * half.x, signf(v.y) * half.y, signf(v.z) * half.z)
	arrays[Mesh.ARRAY_VERTEX] = verts
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh
