class_name Feel
extends RefCounted
## Swipe feedback (GDD §15.2–15.3): floating stat numbers, the calendar flip and haptics.

const GOOD := Color(0.2, 0.6, 0.3)
const BAD := Color(0.8, 0.25, 0.2)
const FLOAT_TIME := 1.1


## Phone vibration; does nothing on desktop or web.
static func buzz(ms: int) -> void:
	if OS.has_feature("mobile"):
		Input.vibrate_handheld(ms)


## Stat changes between two snapshots, as [[label, delta, good], ...]; money in dollars.
static func diff(before: Dictionary, after: Dictionary) -> Array:
	var out := []
	for s in StatStrip.SHORT:
		var d := int(after.get(s, 0)) - int(before.get(s, 0))
		if d != 0:
			out.append([StatStrip.SHORT[s], d, (d < 0) == (s == "stress")])
	var m := int(after.get("money", 0)) - int(before.get("money", 0))
	if m != 0:
		out.append(["$", m, m > 0])
	return out


## "+5 Joy" labels rising from the middle of `host`, staggered so they don't overlap.
static func float_changes(host: Control, changes: Array) -> void:
	var i := 0
	for c in changes:
		var l := Label.new()
		var sgn := "+" if c[1] > 0 else "-"
		if c[0] == "$":
			l.text = sgn + Finance.money_text(absi(c[1]))
		else:
			l.text = "%s%d %s" % [sgn, absi(c[1]), c[0]]
		l.add_theme_font_size_override("font_size", 40)
		l.add_theme_color_override("font_color", GOOD if c[2] else BAD)
		l.add_theme_color_override("font_outline_color", Color(1, 1, 1))
		l.add_theme_constant_override("outline_size", 10)
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		host.add_child(l)
		var col := i % 2
		var row := i / 2
		l.position = Vector2(host.size.x * (0.3 + 0.4 * col) - 70, host.size.y * 0.55 + row * 52)
		l.modulate.a = 0
		var t := l.create_tween()
		t.tween_interval(0.08 * i)
		t.tween_property(l, "modulate:a", 1.0, 0.12)
		t.parallel().tween_property(l, "position:y", l.position.y - 90, FLOAT_TIME)
		t.parallel().tween_property(l, "modulate:a", 0.0, 0.4).set_delay(FLOAT_TIME - 0.4)
		t.tween_callback(l.queue_free)
		i += 1


## A tear-off calendar page over `host`: the old age folds away, the new one drops in.
static func calendar_flip(host: Control, from_age: int, to_age: int) -> void:
	var page := Panel.new()
	var style := StyleBoxFlat.new()
	style.bg_color = Color(1, 0.98, 0.93)
	style.set_corner_radius_all(18)
	style.border_width_top = 34
	style.border_color = Color(0.85, 0.3, 0.25)
	style.shadow_size = 10
	style.shadow_color = Color(0, 0, 0, 0.3)
	page.add_theme_stylebox_override("panel", style)
	page.size = Vector2(260, 280)
	page.position = (host.size - page.size) / 2
	page.pivot_offset = Vector2(page.size.x / 2, 0)
	page.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var l := Label.new()
	l.text = str(from_age)
	l.add_theme_font_size_override("font_size", 120)
	l.add_theme_color_override("font_color", Color(0.2, 0.18, 0.16))
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	l.offset_top = 30
	page.add_child(l)
	host.add_child(page)
	page.modulate.a = 0
	var t := page.create_tween()
	t.tween_property(page, "modulate:a", 1.0, 0.15)
	t.tween_interval(0.2)
	t.tween_property(page, "scale:y", 0.0, 0.18).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	t.tween_callback(func(): l.text = str(to_age))
	t.tween_property(page, "scale:y", 1.0, 0.3).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	t.tween_interval(0.45)
	t.tween_property(page, "modulate:a", 0.0, 0.25)
	t.tween_callback(page.queue_free)
