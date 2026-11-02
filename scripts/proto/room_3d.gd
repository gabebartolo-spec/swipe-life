extends Node3D
## Prototype (a) for GDD §10.4: 3D cel-shaded room with ink outlines, isometric camera.

const TOON := preload("res://shaders/toon.gdshader")
const OUTLINE := preload("res://shaders/outline.gdshader")


func _ready() -> void:
	for b in RoomLayout.BOXES:
		var mesh := BoxMesh.new()
		mesh.size = b.size
		_add(mesh, b.pos + b.size / 2.0, b.color)
	for s in RoomLayout.SPHERES:
		var mesh := SphereMesh.new()
		mesh.radius = s.radius
		mesh.height = s.radius * 2.0
		_add(mesh, s.center, s.color)
	_build_character()
	$Sun.look_at_from_position(Vector3(10, 12, 4), Vector3.ZERO)


func _add(mesh: Mesh, pos: Vector3, color: Color, parent: Node3D = self) -> MeshInstance3D:
	var mat := ShaderMaterial.new()
	mat.shader = TOON
	mat.set_shader_parameter("albedo", color)
	var outline := ShaderMaterial.new()
	outline.shader = OUTLINE
	mat.next_pass = outline
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.material_override = mat
	node.position = pos
	parent.add_child(node)
	return node


func _capsule(radius: float, height: float) -> CapsuleMesh:
	var mesh := CapsuleMesh.new()
	mesh.radius = radius
	mesh.height = height
	return mesh


func _sphere(radius: float) -> SphereMesh:
	var mesh := SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 2.0
	return mesh


func _build_character() -> void:
	# Chibi standing pose: arms down at the sides, facing the camera.
	var root := Node3D.new()
	root.position = Vector3(RoomLayout.CHARACTER_POS.x, 0, RoomLayout.CHARACTER_POS.y)
	root.rotation.y = deg_to_rad(45)
	add_child(root)
	for side in [-1, 1]:
		_add(_capsule(0.11, 0.6), Vector3(0.13 * side, 0.3, 0), RoomLayout.PANTS, root)
		_add(_capsule(0.09, 0.62), Vector3(0.36 * side, 0.92, 0), RoomLayout.SHIRT, root)
		_add(_sphere(0.09), Vector3(0.36 * side, 0.58, 0), RoomLayout.SKIN, root)
	_add(_capsule(0.3, 0.85), Vector3(0, 0.95, 0), RoomLayout.SHIRT, root)
	_add(_sphere(0.46), Vector3(0, 1.75, 0), RoomLayout.SKIN, root)
	_add(_sphere(0.48), Vector3(0, 1.95, -0.14), RoomLayout.HAIR, root)
	for side in [-1, 1]:
		_add(_sphere(0.06), Vector3(0.16 * side, 1.78, 0.42), RoomLayout.INK, root)
