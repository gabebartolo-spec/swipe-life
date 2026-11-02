class_name YearMenu
extends VBoxContainer
## Between-year menu (GDD §6): tabs unlock by age (§6.7), each action costs money and Stress.

signal acted

var db: ActionDB
var tab := ""
var tabs_row := HBoxContainer.new()
var info := Label.new()
var list := VBoxContainer.new()


func _init(action_db: ActionDB) -> void:
	db = action_db


func _ready() -> void:
	add_theme_constant_override("separation", 12)
	tabs_row.add_theme_constant_override("separation", 8)
	add_child(tabs_row)
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	info.add_theme_font_size_override("font_size", 26)
	info.add_theme_color_override("font_color", Color(0.15, 0.15, 0.18))
	add_child(info)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list.add_theme_constant_override("separation", 8)
	scroll.add_child(list)
	add_child(scroll)


## Opens the menu for this year with a headline (the year-end results).
func open(headline: String) -> void:
	info.text = headline
	var tabs := ActionDB.tabs_at(GameState.age)
	if tab not in tabs:
		tab = tabs[0] if not tabs.is_empty() else ""
	_build()
	show()


func _build() -> void:
	for c in tabs_row.get_children() + list.get_children():
		c.queue_free()
	for t in ActionDB.tabs_at(GameState.age):
		var b := Button.new()
		b.text = ActionDB.TAB_NAMES[t]
		b.toggle_mode = true
		b.button_pressed = t == tab
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.add_theme_font_size_override("font_size", 26)
		b.pressed.connect(
			func():
				tab = t
				_build()
		)
		tabs_row.add_child(b)
	if tab == "":
		_note("Too young for plans. Just grow.")
		return
	for a in db.available(tab, GameState.age):
		var b := Button.new()
		var cost := int(a.get("cost", 0))
		b.text = a.label + ("   $%d" % cost if cost else "")
		b.disabled = GameState.stats.money < cost
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size.y = 64
		b.add_theme_font_size_override("font_size", 26)
		b.pressed.connect(do_action.bind(a))
		list.add_child(b)


func _note(text: String) -> void:
	var l := Label.new()
	l.text = text
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", 26)
	l.add_theme_color_override("font_color", Color(0.4, 0.38, 0.35))
	list.add_child(l)


func do_action(a: Dictionary) -> void:
	if ActionDB.perform(a, GameState):
		info.text = a.get("result", a.label)
		acted.emit()
		_build()


## Everything the player could do right now (autoplay).
func choices() -> Array:
	var out := []
	for t in ActionDB.tabs_at(GameState.age):
		for a in db.available(t, GameState.age):
			if GameState.stats.money >= int(a.get("cost", 0)):
				out.append(a)
	return out
