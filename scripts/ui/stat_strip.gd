class_name StatStrip
extends GridContainer
## Stat bars under the dollhouse (GDD §4.3–4.4, §10.5). Karma is hidden; Money is a number.
## The two spectrums (GDD §4.6) are a track with a marker, low end named on the left.

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
const MARK_W := 10.0

var bars := {}
var values := {}
var money_label: Label
var marks := {}


func _ready() -> void:
	columns = 5
	add_theme_constant_override("h_separation", 14)
	add_theme_constant_override("v_separation", 6)
	var fill := StyleBoxFlat.new()
	fill.bg_color = Color(0.98, 0.78, 0.4)
	fill.set_corner_radius_all(4)
	var back := StyleBoxFlat.new()
	back.bg_color = Color(0.18, 0.19, 0.23)
	back.set_corner_radius_all(4)
	for s in SHORT:
		var box := VBoxContainer.new()
		box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		box.add_theme_constant_override("separation", 0)
		var name_label := Label.new()
		name_label.add_theme_font_size_override("font_size", 22)
		var bar := ProgressBar.new()
		bar.show_percentage = false
		bar.custom_minimum_size.y = 16
		bar.add_theme_stylebox_override("fill", fill)
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
		track.custom_minimum_size.y = 16
		track.add_theme_stylebox_override("panel", back)
		var mark := ColorRect.new()
		mark.color = fill.bg_color
		mark.size = Vector2(MARK_W, 16)
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
		create_tween().tween_property(bars[s], "value", GameState.stats[s], 0.3)
		values[s].text = "%s %d" % [SHORT[s], GameState.stats[s]]
	money_label.text = money_text(GameState.stats.money)
	for s in marks:
		_place(s)


func _place(s: String) -> void:
	var mark: ColorRect = marks[s]
	var x: float = (mark.get_parent().size.x - MARK_W) * GameState.stats[s] / 100.0
	create_tween().tween_property(mark, "position:x", x, 0.3)


static func money_text(m: int) -> String:
	return "-$%d" % -m if m < 0 else "$%d" % m
