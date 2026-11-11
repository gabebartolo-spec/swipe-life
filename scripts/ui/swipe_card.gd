class_name SwipeCard
extends Panel
## A decision card: drag left or right to choose, up to super like (GDD §3). Snaps back early.

signal chosen(side: String)
signal previewing(side: String)  # "" when no side is previewed

const THRESHOLD := 140.0
const PREVIEW_AT := 40.0

var card: Dictionary
var can_super := false
var drag := Vector2.ZERO
var dragging := false
var snap: Tween
var locked := false
var home := Vector2.ZERO
var text_label := Label.new()
var hint_label := Label.new()
var shown_side := ""
var squish: Tween
var gone := false  # committed: the fly-off must not re-light the stat preview


func _ready() -> void:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(1, 0.99, 0.96)
	style.set_corner_radius_all(28)
	style.border_width_bottom = 12  # clay slab thickness (GDD §15.18)
	style.border_color = Color(0.86, 0.8, 0.7)
	style.shadow_size = 12
	style.shadow_color = Color(0, 0, 0, 0.25)
	add_theme_stylebox_override("panel", style)
	for l in [text_label, hint_label]:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT, Control.PRESET_MODE_MINSIZE, 32)
		l.add_theme_color_override("font_color", Color(0.15, 0.15, 0.18))
		add_child(l)
	text_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	text_label.add_theme_font_size_override("font_size", 34)
	hint_label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	hint_label.add_theme_font_size_override("font_size", 30)
	pivot_offset = size / 2


func show_card(c: Dictionary, super_ok: bool) -> void:
	card = c
	can_super = super_ok and c.has("up")
	text_label.text = c.text
	hint_label.text = ""
	drag = Vector2.ZERO
	locked = false
	home = position
	pivot_offset = size / 2
	rotation = 0
	scale = Vector2.ONE
	shown_side = ""
	gone = false
	modulate.a = 0
	create_tween().tween_property(self, "modulate:a", 1.0, 0.2)


func _gui_input(event: InputEvent) -> void:
	if locked or card.is_empty():
		return
	if event is InputEventScreenTouch:
		if event.pressed:
			if snap:
				snap.kill()  # grab the card mid snap-back: keep dragging from here
			dragging = true
			_squish(Vector2(1.05, 0.95), 0.12)
		elif dragging:
			dragging = false
			_squish(Vector2.ONE, 0.35, true)
			_release()
	elif event is InputEventScreenDrag and dragging:
		set_drag(drag + event.relative)


func set_drag(d: Vector2) -> void:
	drag = d
	position = home + drag
	rotation = drag.x * 0.0008
	# heavy clay: the card leans and stretches the way it is pulled, and sags under its weight
	var pull := clampf(drag.length() / 600.0, 0.0, 0.12)
	if dragging:
		scale = (
			Vector2(1.0 + pull * 0.5, 1.0 - pull * 0.4)
			if absf(drag.x) > absf(drag.y)
			else Vector2(1.0 - pull * 0.4, 1.0 + pull * 0.5)
		)
	var side := "" if gone else side_for(drag, PREVIEW_AT)
	if side != shown_side:
		shown_side = side
		previewing.emit(side)
		if side != "":
			Feel.buzz(15)
	hint_label.text = card[side].label if side != "" else ""
	hint_label.add_theme_color_override(
		"font_color", Color(0.85, 0.55, 0.1) if side == "up" else Color(0.2, 0.35, 0.7)
	)


func side_for(d: Vector2, at: float) -> String:
	if can_super and -d.y > at and -d.y > absf(d.x):
		return "up"
	if d.x < -at:
		return "left"
	if d.x > at:
		return "right"
	return ""


func _release() -> void:
	var side := side_for(drag, THRESHOLD)
	if side == "":
		snap = create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		snap.tween_method(set_drag, drag, Vector2.ZERO, 0.25)
		return
	commit(side)


func commit(side: String) -> void:
	locked = true
	gone = true
	shown_side = ""
	previewing.emit("")
	if side == "up":
		_super_moment()
		return
	Feel.buzz(40)
	var out := {"left": Vector2(-900, 80), "right": Vector2(900, 80), "up": Vector2(0, -1200)}
	var t := create_tween()
	t.tween_method(set_drag, drag, out[side], 0.25)
	t.tween_callback(chosen.emit.bind(side))


## Autoplay / captures: drag visibly towards side, pause on the preview, then commit.
func auto_swipe(side: String) -> void:
	locked = true
	var target := {"left": Vector2(-110, 10), "right": Vector2(110, 10), "up": Vector2(0, -120)}
	var t := create_tween()
	t.tween_method(set_drag, Vector2.ZERO, target[side], 0.4)
	t.tween_interval(0.5)
	t.tween_callback(commit.bind(side))


## Wobbles the card's scale towards `to`; `bounce` springs like clay settling.
func _squish(to: Vector2, time: float, bounce := false) -> void:
	if squish:
		squish.kill()
	squish = create_tween().set_trans(Tween.TRANS_ELASTIC if bounce else Tween.TRANS_QUAD)
	squish.set_ease(Tween.EASE_OUT)
	squish.tween_property(self, "scale", to, time)


## The super swipe (GDD §15.2): the card swells, gold bursts, it hangs in slow motion, flies off.
func _super_moment() -> void:
	Feel.buzz(180)
	var flash := ColorRect.new()
	flash.color = Color(1, 0.82, 0.3, 0.0)
	flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	flash.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	get_parent().add_child(flash)
	var burst := CPUParticles2D.new()
	burst.position = size / 2
	burst.amount = 48
	burst.one_shot = true
	burst.explosiveness = 1.0
	burst.lifetime = 0.9
	burst.spread = 180.0
	burst.initial_velocity_min = 300.0
	burst.initial_velocity_max = 700.0
	burst.gravity = Vector2(0, 600)
	burst.scale_amount_min = 8.0
	burst.scale_amount_max = 16.0
	burst.color = Color(1, 0.75, 0.2)
	add_child(burst)
	burst.emitting = true
	var t := create_tween()
	t.tween_property(self, "scale", Vector2(1.18, 1.18), 0.18).set_trans(Tween.TRANS_BACK).set_ease(
		Tween.EASE_OUT
	)
	t.parallel().tween_property(flash, "color:a", 0.55, 0.12)
	t.parallel().tween_method(set_drag, drag, Vector2(0, -60), 0.18)
	t.tween_property(self, "rotation", 0.06, 0.45)  # the slow-motion hang
	t.parallel().tween_property(flash, "color:a", 0.0, 0.45)
	(
		t
		. tween_method(set_drag, Vector2(0, -60), Vector2(0, -1400), 0.3)
		. set_trans(Tween.TRANS_QUAD)
		. set_ease(Tween.EASE_IN)
	)
	t.tween_callback(flash.queue_free)
	t.tween_callback(burst.queue_free)
	t.tween_callback(func(): scale = Vector2.ONE)
	t.tween_callback(chosen.emit.bind("up"))
