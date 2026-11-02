extends VBoxContainer
## Layout (GDD §10.5) and year loop (GDD §2): 4 cards, the between-year menu, then age +1.
## Run with `-- --autoplay` to swipe automatically (captures and soak tests), and
## `-- --set=age=8,health=5,stress=90` to start a new life at that age with those stats

const MARGIN := 40.0
const RESULT_TIME := 1.4

var deck: Deck
var menu: YearMenu
var strip := StatStrip.new()
var swipe_card := SwipeCard.new()
var message := Label.new()
var year_button := Button.new()
var new_life_button := Button.new()
var autoplay := "--autoplay" in OS.get_cmdline_user_args()


func _ready() -> void:
	if not SaveSystem.load_life():  # resume at the last year boundary (GDD §8.2–8.3)
		_new_life()
	var db := CardDB.new()
	db.load_dir()
	for e in db.errors:
		push_error(e)
	deck = Deck.new(db.cards)
	var adb := ActionDB.new()
	adb.load_dir()
	for e in adb.errors:
		push_error(e)
	menu = YearMenu.new(adb)
	menu.acted.connect(strip.refresh)

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

	menu.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT, Control.PRESET_MODE_MINSIZE, 32)
	menu.offset_bottom = -150
	menu.hide()
	$Card.add_child(menu)

	year_button.text = "Next year"
	year_button.add_theme_font_size_override("font_size", 36)
	year_button.custom_minimum_size = Vector2(320, 96)
	year_button.pressed.connect(_next_year)
	$Card.add_child(year_button)

	new_life_button.text = "New life"
	new_life_button.add_theme_font_size_override("font_size", 36)
	new_life_button.custom_minimum_size = year_button.custom_minimum_size
	new_life_button.pressed.connect(_restart)
	new_life_button.hide()
	$Card.add_child(new_life_button)

	await get_tree().process_frame
	var area: Vector2 = $Card.size
	swipe_card.position = Vector2(MARGIN, MARGIN)
	swipe_card.size = area - Vector2(MARGIN, MARGIN) * 2
	# both buttons sit below the message, which keeps the space above them
	year_button.position = Vector2((area.x - year_button.custom_minimum_size.x) / 2, area.y - 140)
	new_life_button.position = year_button.position
	message.offset_bottom = -150
	_deal()


func _new_life() -> void:
	GameState.new_life()
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--set="):
			for pair in arg.trim_prefix("--set=").split(","):
				var kv := pair.split("=")
				if kv[0] == "age":
					GameState.age = int(kv[1])
				else:
					GameState.stats[kv[0]] = int(kv[1])
	SaveSystem.save()


func _update_age(season := true) -> void:
	var text := "Age %d" % GameState.age
	if season:
		text += "  ·  " + ["Spring", "Summer", "Autumn", "Winter", "Year end"][GameState.quarter]
	var ills := []
	for id in LifeRules.ILLNESSES:
		if GameState.flags.has(id):
			ills.append(id.capitalize())
	if not ills.is_empty():
		text += "\n" + ", ".join(ills)
	$Dollhouse/AgeLabel.text = text
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
	var out := LifeRules.year_end(GameState, deck.rng)
	_update_age()
	if out.died:
		_end("You died at %d.\n%s." % [GameState.age, out.cause])
		return
	out.results.append("Year %d is over." % GameState.age)
	menu.open("\n".join(out.results))
	year_button.show()
	if autoplay:
		for i in randi() % 3:
			await get_tree().create_timer(0.8).timeout
			var c := menu.choices()
			if not c.is_empty():
				menu.do_action(c.pick_random())
		await get_tree().create_timer(0.8).timeout
		_next_year()


func _next_year() -> void:
	menu.hide()
	GameState.age += 1
	GameState.quarter = 0
	GameState.super_like_available = true  # GDD §3.3
	if GameState.age > CardDB.MAX_AGE:
		_end("You turned 18.\nTo be continued...")
		return
	SaveSystem.save()  # GDD §8.3: autosave when the between-year menu closes
	_deal()


## Life summary, at death or at 18. The save is cleared: this life is over.
func _end(headline: String) -> void:
	swipe_card.hide()
	year_button.hide()
	menu.hide()
	SaveSystem.clear()
	var lines := []
	for st in StatStrip.SHORT:
		lines.append("%s %d" % [StatStrip.SHORT[st], GameState.stats[st]])
	var text := (
		"%s\n\n%s\n%s\n%s"
		% [
			headline,
			"  ·  ".join(lines.slice(0, 4)),
			"  ·  ".join(lines.slice(4)),
			StatStrip.money_text(GameState.stats.money),
		]
	)
	var ills := []
	for id in LifeRules.ILLNESSES:
		if GameState.flags.has(id):
			ills.append(id)
	if not ills.is_empty():
		text += "\nLiving with " + " and ".join(ills)
	message.add_theme_font_size_override("font_size", 28)
	message.text = text
	_update_age(false)
	new_life_button.show()
	if autoplay:
		await get_tree().create_timer(2.0).timeout
		_restart()


func _restart() -> void:
	new_life_button.hide()
	message.add_theme_font_size_override("font_size", 34)
	_new_life()
	_deal()
