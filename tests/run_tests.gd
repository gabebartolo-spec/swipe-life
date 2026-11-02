extends SceneTree
## Headless tests: godot --headless --script res://tests/run_tests.gd
## Validates card files, checks bad cards are rejected, simulates lives from birth to 18.

const GameStateScript := preload("res://scripts/autoload/game_state.gd")
const LIVES := 100

var failures := 0


func _init() -> void:
	_test_cards_valid()
	_test_bad_cards_rejected()
	_test_sim()
	print("TESTS %s (%d failures)" % ["PASSED" if failures == 0 else "FAILED", failures])
	quit(1 if failures else 0)


func _check(ok: bool, msg: String) -> void:
	if not ok:
		failures += 1
		printerr("FAIL: " + msg)


func _test_cards_valid() -> void:
	var db := CardDB.new()
	db.load_dir()
	for e in db.errors:
		printerr(e)
	_check(db.errors.is_empty(), "data/cards has %d errors" % db.errors.size())
	_check(not db.cards.is_empty(), "no cards loaded")
	print("cards: %d valid" % db.cards.size())


func _test_bad_cards_rejected() -> void:
	var db := CardDB.new()
	db.load_file("res://tests/fixtures/bad_cards.json")
	# every card in the fixture is broken except the first "dup"
	_check(db.cards.size() == 1, "validator accepted %d bad cards" % (db.cards.size() - 1))
	_check(db.errors.size() >= 6, "validator found only %d errors" % db.errors.size())


func _test_sim() -> void:
	var db := CardDB.new()
	db.load_dir()
	var drawn := 0
	var empty := 0
	var deaths := 0
	for life in LIVES:
		var state := GameStateScript.new()
		state.new_life()
		var deck := Deck.new(db.cards, life)
		var dead := false
		while state.age <= CardDB.MAX_AGE and not dead:
			state.super_like_available = true
			for q in 4:
				state.quarter = q
				var card = deck.draw(state)
				if card == null:
					empty += 1
					continue
				drawn += 1
				var side: String = ["left", "right"][deck.rng.randi() % 2]
				if card.has("up") and state.super_like_available and deck.rng.randf() < 0.3:
					side = "up"
					state.super_like_available = false
				var out := deck.choose(card, side, state)
				for s in state.stats:
					if s not in GameStateScript.UNBOUNDED_STATS:
						_check(state.stats[s] >= 0 and state.stats[s] <= 100, "%s out of range" % s)
				if out.died:
					deaths += 1
					dead = true
					break
			state.age += 1
		state.free()
	print(
		"sim: %d lives, %d cards drawn, %d empty slots, %d deaths" % [LIVES, drawn, empty, deaths]
	)
	_check(drawn > 0, "sim drew no cards")
