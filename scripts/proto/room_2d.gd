extends Node2D
## GDD §10.4 (b): the RoomLayout bedroom drawn as 2D flat vector, isometric, with ink outlines.

## Pixels per world unit; matches the 3D prototype's framing at 720×576.
const SCALE := 67.0
const OUTLINE := 3.0
## Painter's order (indices into RoomLayout.BOXES); the character is drawn at -1, spheres last.
const ORDER := [
	0,
	1,
	2,
	8,
	9,
	10,
	11,
	19,
	20,
	21,
	22,
	3,
	13,
	14,
	15,
	16,
	12,
	17,
	18,
	4,
	5,
	6,
	7,
	25,
	26,
	27,
	28,
	23,
	24,
	-1,
	29
]


func _ready() -> void:
	# Draw 1:1 in window pixels so the framing matches the 3D capture.
	get_window().content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	RenderingServer.set_default_clear_color(Color(0.98, 0.94, 0.88))
	var size := Vector2(get_window().size)
	position = size * 0.5 - _iso(Vector3(3, 1.4, 3))
	queue_redraw()


func _iso(p: Vector3) -> Vector2:
	# Same view as the 3D camera: looking down -(1, 1, 1).
	return Vector2((p.x - p.z) * 0.7071, (p.x + p.z) * 0.4082 - p.y * 0.8165) * SCALE


func _draw() -> void:
	for i: int in ORDER:
		if i < 0:
			_draw_character()
		else:
			var b: Dictionary = RoomLayout.BOXES[i]
			_draw_box(b.pos, b.size, b.color)
	for s: Dictionary in RoomLayout.SPHERES:
		_draw_ball(s.center, s.radius, s.color)


func _draw_box(p: Vector3, s: Vector3, c: Color) -> void:
	var q := p + s
	var top := [
		Vector3(p.x, q.y, p.z),
		Vector3(q.x, q.y, p.z),
		Vector3(q.x, q.y, q.z),
		Vector3(p.x, q.y, q.z),
	]
	var right := [
		Vector3(q.x, q.y, p.z),
		Vector3(q.x, q.y, q.z),
		Vector3(q.x, p.y, q.z),
		Vector3(q.x, p.y, p.z),
	]
	var front := [
		Vector3(p.x, q.y, q.z),
		Vector3(q.x, q.y, q.z),
		Vector3(q.x, p.y, q.z),
		Vector3(p.x, p.y, q.z),
	]
	_face(right, c.darkened(0.12))
	_face(front, c.darkened(0.28))
	_face(top, c)


func _face(points: Array, c: Color) -> void:
	var poly := PackedVector2Array()
	for v: Vector3 in points:
		poly.append(_iso(v))
	draw_colored_polygon(poly, c)
	poly.append(poly[0])
	draw_polyline(poly, RoomLayout.INK, OUTLINE, true)


func _draw_ball(center: Vector3, r: float, c: Color) -> void:
	var at := _iso(center)
	var rp := r * SCALE
	draw_circle(at, rp + OUTLINE, RoomLayout.INK)
	draw_circle(at, rp, c.darkened(0.2))
	draw_circle(at + Vector2(-0.15, -0.15) * rp, rp * 0.8, c)


func _draw_character() -> void:
	var feet := _iso(Vector3(RoomLayout.CHARACTER_POS.x, 0, RoomLayout.CHARACTER_POS.y))
	var u := SCALE
	# legs
	_ink_rect(Rect2(feet + Vector2(-0.24, -0.62) * u, Vector2(0.2, 0.62) * u), RoomLayout.PANTS)
	_ink_rect(Rect2(feet + Vector2(0.04, -0.62) * u, Vector2(0.2, 0.62) * u), RoomLayout.PANTS)
	# arms, then body over the shoulders
	_ink_rect(Rect2(feet + Vector2(-0.5, -1.15) * u, Vector2(0.16, 0.5) * u), RoomLayout.SHIRT)
	_ink_rect(Rect2(feet + Vector2(0.34, -1.15) * u, Vector2(0.16, 0.5) * u), RoomLayout.SHIRT)
	_ink_circle(feet + Vector2(-0.42, -0.62) * u, 0.1 * u, RoomLayout.SKIN)
	_ink_circle(feet + Vector2(0.42, -0.62) * u, 0.1 * u, RoomLayout.SKIN)
	_ink_rect(Rect2(feet + Vector2(-0.36, -1.22) * u, Vector2(0.72, 0.66) * u), RoomLayout.SHIRT)
	# head, hair cap, eyes
	var head := feet + Vector2(0, -1.72) * u
	_ink_circle(head, 0.46 * u, RoomLayout.SKIN)
	var hair := PackedVector2Array()
	for k in range(13):
		hair.append(head + Vector2.from_angle(PI + PI * k / 12.0) * 0.46 * u)
	hair.append(head + Vector2(0.2, -0.12) * u)
	draw_colored_polygon(hair, RoomLayout.HAIR)
	draw_arc(head, 0.46 * u, 0, TAU, 40, RoomLayout.INK, OUTLINE, true)
	draw_circle(head + Vector2(-0.15, 0.1) * u, 0.06 * u, RoomLayout.INK)
	draw_circle(head + Vector2(0.15, 0.1) * u, 0.06 * u, RoomLayout.INK)


func _ink_rect(r: Rect2, c: Color) -> void:
	draw_rect(r, c)
	draw_rect(r, RoomLayout.INK, false, OUTLINE)


func _ink_circle(at: Vector2, r: float, c: Color) -> void:
	draw_circle(at, r + OUTLINE, RoomLayout.INK)
	draw_circle(at, r, c)
