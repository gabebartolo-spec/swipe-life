class_name CharacterCreator
extends ColorRect
## Start of a life: the player picks their look (director 2026-11-09). Preview is the adult body.

signal done(look: Dictionary)

const FIELDS := [
	["Body", "sex", Looks.SEXES],
	["Skin", "skin", Looks.SKINS],
	["Hair", "hair", Looks.CUTS],
	["Hair colour", "hair_colour", Looks.HAIR_COLOURS],
	["Top", "top", Looks.TOPS],
	["Top colour", "top_colour", Looks.CLOTH_COLOURS],
	["Trousers", "bottom_colour", Looks.CLOTH_COLOURS],
]
const PREVIEW_AGE := 18
const PREVIEW_SCALE := 0.62

var look := Looks.random()
var _labels := {}
var _stage := Node2D.new()
var _person: Person


func _ready() -> void:
	color = Color(0.925, 0.929, 0.953)
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(_stage)
	var box := VBoxContainer.new()
	box.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	box.offset_left = 40
	box.offset_right = -40
	box.offset_top = -640
	box.offset_bottom = -30
	box.add_theme_constant_override("separation", 10)
	add_child(box)
	for f in FIELDS:
		box.add_child(_row(f))
	var start := Button.new()
	start.text = "Start life"
	start.add_theme_font_size_override("font_size", 36)
	start.custom_minimum_size.y = 90
	start.pressed.connect(func(): done.emit(look))
	box.add_child(start)
	await get_tree().process_frame
	_stage.position = Vector2(size.x / 2, size.y - 660)
	_refresh()


func _row(f: Array) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_child(_arrow("<", f, -1))
	var label := Label.new()
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", 28)
	label.add_theme_color_override("font_color", Color(0.15, 0.15, 0.18))
	row.add_child(label)
	_labels[f[1]] = label
	row.add_child(_arrow(">", f, 1))
	return row


func _arrow(text: String, f: Array, step: int) -> Button:
	var b := Button.new()
	b.text = text
	b.add_theme_font_size_override("font_size", 32)
	b.custom_minimum_size = Vector2(90, 62)
	b.pressed.connect(
		func():
			var opts: Array = f[2]
			look[f[1]] = opts[wrapi(opts.find(look[f[1]]) + step, 0, opts.size())]
			_refresh()
	)
	return b


func _refresh() -> void:
	for f in FIELDS:
		var opts: Array = f[2]
		var value: String = look[f[1]]
		var shown := "%d of %d" % [opts.find(value) + 1, opts.size()]
		if f[1] == "sex":
			shown = "Female" if value == "f" else "Male"
		elif f[1] in ["hair", "top"]:
			shown = value.capitalize()
		_labels[f[1]].text = "%s: %s" % [f[0], shown]
	if _person:
		_person.queue_free()
	_person = Looks.make_person(look, PREVIEW_AGE)
	_person.scale = Vector2.ONE * PREVIEW_SCALE
	_stage.add_child(_person)
