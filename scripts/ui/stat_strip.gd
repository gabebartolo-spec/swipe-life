class_name StatStrip
extends GridContainer
## Stat bars under the dollhouse (GDD Â§4.3â€“4.4, Â§10.5). Karma is hidden; Money is a number.
## The two spectrums (GDD Â§4.6) are a track with a marker, low end named on the left.

const SHORT := {
	"health": "HP",
	"happiness": "Joy",
	"career": "Skill",
	"relationships": "Love",
	"smarts": "IQ",
	"looks": "Looks",
	"stress": "Stress",
}
const SPECTRUMS := {"boldness": ["Safe", "Bold"], "sociability": ["Shy", "Social"]}
const MARK_W := 22.0

var bars := {}
var values := {}
var money_label: Label
var marks := {}


func _ready() -> void:
	columns = 5
	add_theme_constant_override("h_separation", 14)
	add_theme_constant_override("v_separation", 6)
	var back := ClayTheme.groove()
	for s in SHORT:
		var box := VBoxContainer.new()
		box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		box.add_theme_constant_override("separation", 0)
		var name_label := Label.new()
		name_label.add_theme_font_size_override("font_size", 22)
		var bar := ProgressBar.new()
		bar.show_percentage = false
		bar.custom_minimum_size.y = 22
		bar.add_theme_stylebox_override("fill", ClayTheme.bar_fill(s))
		bar.add_theme_stylebox_override("background", back)
		box.add_child(name_label)
		box.add_child(bar)
		add_child(box)
		bars[s] = bar
		values[s] = name_label
	for s in SPECTRUMS:
		var box := VBoxContainer.new()
		box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		box.add_theme_constant_override("separation", 0)
		var ends := HBoxContainer.new()
		for i in 2:
			var end := Label.new()
			end.text = SPECTRUMS[s][i]
			end.add_theme_font_size_override("font_size", 22)
			end.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			end.horizontal_alignment = [HORIZONTAL_ALIGNMENT_LEFT, HORIZONTAL_ALIGNMENT_RIGHT][i]
			ends.add_child(end)
		var track := Panel.new()
		track.custom_minimum_size.y = 22
		track.add_theme_stylebox_override("panel", back)
		var mark := Panel.new()
		mark.add_theme_stylebox_override("panel", ClayTheme.bar_fill("happiness"))
		mark.size = Vector2(MARK_W, 22)
		track.add_child(mark)
		marks[s] = mark
		track.resized.connect(_place.bind(s))
		box.add_child(ends)
		box.add_child(track)
		add_child(box)
	money_label = Label.new()
	money_label.add_theme_font_size_override("font_size", 30)
	money_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	money_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	money_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(money_label)
	refresh()


func refresh() -> void:
	for s in bars:
		var bar: ProgressBar = bars[s]
		if is_inside_tree() and int(bar.value) != int(GameState.stats[s]):
			_pulse(bar.get_parent())
		var t := create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		t.tween_property(bar, "value", GameState.stats[s], 0.5)
		values[s].text = "%s %d" % [SHORT[s], GameState.stats[s]]
	money_label.text = Finance.money_text(GameState.stats.money)
	var debt := Finance.total_debt(GameState)
	if debt > 0:
		money_label.text += "\nDebt " + Finance.money_text(debt)
	money_label.add_theme_font_size_override("font_size", 22 if debt > 0 else 30)
	if GameState.stats.money < 0 or debt > 0:
		money_label.add_theme_color_override("font_color", Color(0.85, 0.2, 0.2))
	else:
		money_label.remove_theme_color_override("font_color")
	for s in marks:
		_place(s)


func _place(s: String) -> void:
	var mark: Control = marks[s]
	var x: float = (mark.get_parent().size.x - MARK_W) * GameState.stats[s] / 100.0
	create_tween().tween_property(mark, "position:x", x, 0.3)


## Drag preview (GDD Â§15.2): the stats this choice will move glow green (better) or red (worse).
## Only the sure effects show, never the size or the hidden risk.
func preview(effects: Dictionary) -> void:
	for s in values:
		var d := int(effects.get(s, 0))
		var box: Control = values[s].get_parent()
		if d == 0:
			box.modulate = Color.WHITE
			continue
		var good: bool = (d < 0) == (s == "stress")
		box.modulate = Color(0.6, 1.4, 0.7) if good else Color(1.5, 0.6, 0.55)
	var m := int(effects.get("money", 0))
	money_label.modulate = (
		Color.WHITE if m == 0 else (Color(0.6, 1.4, 0.7) if m > 0 else Color(1.5, 0.6, 0.55))
	)


## A changed stat squishes like poked clay (GDD §15.3).
func _pulse(box: Control) -> void:
	box.pivot_offset = box.size / 2
	var t := box.create_tween().set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	box.scale = Vector2(1.12, 0.88)
	t.tween_property(box, "scale", Vector2.ONE, 0.6)
