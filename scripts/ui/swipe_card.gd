class_name SwipeCard
extends Panel
## A decision card: drag left or right to choose, up to super like (GDD §3). Snaps back early.

signal chosen(side: String)

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


func _ready() -> void:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(1, 0.99, 0.96)
	style.set_corner_radius_all(24)
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
		elif dragging:
			dragging = false
			_release()
	elif event is InputEventScreenDrag and dragging:
		set_drag(drag + event.relative)


func set_drag(d: Vector2) -> void:
	drag = d
	position = home + drag
	rotation = drag.x * 0.0008
	var side := side_for(drag, PREVIEW_AT)
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
