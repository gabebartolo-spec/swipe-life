extends VBoxContainer
## Layout (GDD §10.5) and year loop (GDD §2): 4 cards, the between-year menu, then age +1.
## Run with `-- --autoplay` to swipe automatically (captures and soak tests).

const MARGIN := 40.0
const RESULT_TIME := 1.4

var deck: Deck
var strip := StatStrip.new()
var swipe_card := SwipeCard.new()
var message := Label.new()
var year_button := Button.new()
var autoplay := "--autoplay" in OS.get_cmdline_user_args()


func _ready() -> void:
	if not SaveSystem.load_life():
		GameState.new_life()
	var db := CardDB.new()
	db.load_dir()
	for e in db.errors:
		push_error(e)
	deck = Deck.new(db.cards)

	strip.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT, Control.PRESET_MODE_MINSIZE, 10)
	$StatStrip.add_child(strip)
	$Card.add_child(swipe_card)
	swipe_card.chosen.connect(_on_chosen)

	message.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	message.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	message.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	message.add_theme_font_size_override("font_size", 34)
	message.add_theme_color_override("font_color", Color(0.15, 0.15, 0.18))
	message.set_anchors_and_offsets_preset(
		Control.PRESET_FULL_RECT, Control.PRESET_MODE_MINSIZE, 48
	)
	$Card.add_child(message)

	year_button.text = "Next year"  # placeholder for the between-year menu (roadmap M4)
	year_button.add_theme_font_size_override("font_size", 36)
	year_button.custom_minimum_size = Vector2(320, 96)
	year_button.pressed.connect(_next_year)
	$Card.add_child(year_button)

	await get_tree().process_frame
	var area: Vector2 = $Card.size
	swipe_card.position = Vector2(MARGIN, MARGIN)
	swipe_card.size = area - Vector2(MARGIN, MARGIN) * 2
	year_button.position = (area - year_button.custom_minimum_size) / 2 + Vector2(0, 120)
	_deal()


func _update_age() -> void:
	$Dollhouse/AgeLabel.text = (
		"Age %d  ·  %s"
		% [
			GameState.age,
			["Spring", "Summer", "Autumn", "Winter", "Year end"][mini(GameState.quarter, 4)]
		]
	)
	strip.refresh()


func _deal() -> void:
	_update_age()
	message.text = ""
	year_button.hide()
	if GameState.quarter >= 4:
		_year_end()
		return
	var c = deck.draw(GameState)
	if c == null:  # nothing eligible at this age yet: skip the quarter
		GameState.quarter += 1
		_deal()
		return
	swipe_card.show()
	swipe_card.position = Vector2(MARGIN, MARGIN)
	swipe_card.show_card(c, GameState.super_like_available)
	if autoplay:
		await get_tree().create_timer(0.6).timeout
		var sides := ["left", "right"]
		if swipe_card.can_super and randf() < 0.3:
			sides = ["up"]
		swipe_card.auto_swipe(sides.pick_random())


func _on_chosen(side: String) -> void:
	swipe_card.hide()
	if side == "up":
		GameState.super_like_available = false
	var out := deck.choose(swipe_card.card, side, GameState)
	strip.refresh()
	if out.died:
		_end("You died at %d.\n%s." % [GameState.age, out.cause])
		return
	GameState.quarter += 1
	if not out.results.is_empty():
		message.text = "\n".join(out.results)
		await get_tree().create_timer(RESULT_TIME).timeout
	_deal()


func _year_end() -> void:
	swipe_card.hide()
	message.text = "Year %d is over." % GameState.age
	year_button.show()
	if autoplay:
		await get_tree().create_timer(0.8).timeout
		_next_year()


func _next_year() -> void:
	GameState.age += 1
	GameState.quarter = 0
	GameState.super_like_available = true  # GDD §3.3
	if GameState.age > CardDB.MAX_AGE:
		_end("You turned 18.\nTo be continued...")
		return
	_deal()


func _end(text: String) -> void:
	swipe_card.hide()
	year_button.hide()
	message.text = text
	_update_age()
