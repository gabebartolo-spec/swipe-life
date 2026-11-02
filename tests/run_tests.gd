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
	_test_life_rules()
	_test_save_round_trip()
	_test_actions()
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
			if not dead and LifeRules.year_end(state, deck.rng).died:
				deaths += 1
				dead = true
			state.age += 1
		state.free()
	print(
		"sim: %d lives, %d cards drawn, %d empty slots, %d deaths" % [LIVES, drawn, empty, deaths]
	)
	_check(drawn > 0, "sim drew no cards")


func _test_life_rules() -> void:
	var state := GameStateScript.new()
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	# a risky card's death roll ends a life (GDD §5.3b)
	state.new_life()
	var deck := Deck.new([], 1)
	var card := {"left": {"death": {"chance": 1.0, "cause": "Test"}}}
	_check(deck.choose(card, "left", state).died, "risky card did not kill")
	# Health 0 ends a life (GDD §5.3a)
	state.new_life()
	_check(deck.choose({"left": {"effects": {"health": -100}}}, "left", state).died, "HP 0 lived")
	# high Stress starts anxiety; it holds while Stress stays high, and drains Health
	state.new_life()
	state.age = 10
	state.stats.stress = 100
	var years := 0
	while not state.flags.has("anxiety") and years < 50:
		LifeRules.year_end(state, rng)
		years += 1
	_check(state.flags.has("anxiety"), "stress 100 never caused anxiety")
	state.stats.health = 100
	for y in 10:
		LifeRules.year_end(state, rng)
	_check(state.flags.has("anxiety"), "anxiety lifted while stress was high")
	_check(
		state.stats.health == 70,
		"anxiety drained %d health, expected 30" % (100 - state.stats.health)
	)
	# no onset before age 6
	state.new_life()
	state.stats.happiness = 0
	for y in 6:
		state.age = y
		LifeRules.year_end(state, rng)
	_check(not state.flags.has("depression"), "depression before age 6")
	state.free()


func _test_save_round_trip() -> void:
	var a := GameStateScript.new()
	a.new_life()
	a.age = 7
	a.flags["anxiety"] = true
	a.used["baby_first_word"] = true
	a.change_stat("money", 120)
	var b := GameStateScript.new()
	b.from_dict(JSON.parse_string(JSON.stringify(a.to_dict())))
	_check(b.age == 7 and b.stats.money == 120, "save lost age or money")
	_check(
		b.flags.has("anxiety") and b.used.has("baby_first_word"), "save lost flags or used cards"
	)
	a.free()
	b.free()


func _test_actions() -> void:
	var db := ActionDB.new()
	db.load_dir()
	_check(db.errors.is_empty(), "action errors: %s" % "; ".join(db.errors))
	print("actions: %d valid" % db.actions.size())
	# age gates (GDD §6.7): a 3-year-old has nothing, a 15-year-old has clubs, study and a job
	_check(ActionDB.tabs_at(3).is_empty(), "a 3-year-old sees a menu tab")
	var ids := []
	for t in ActionDB.tabs_at(15):
		for a in db.available(t, 15):
			ids.append(a.id)
	for want in ["club", "study", "part_time"]:
		_check(want in ids, "15-year-old can't see %s" % want)
	_check("shop" not in ActionDB.tabs_at(17), "shop open before 18")
	# money limits actions (§6.5); every action adds Stress (§6.6)
	var state := GameStateScript.new()
	state.new_life()
	var doctor: Dictionary = db.actions.filter(func(a): return a.id == "doctor")[0]
	_check(not ActionDB.perform(doctor, state), "doctor without money")
	state.stats.money = 25
	_check(ActionDB.perform(doctor, state) and state.stats.money == 5, "doctor cost wrong")
	_check(state.stats.stress > 0, "action added no stress")
	state.free()
	# the validator rejects an action without stress or with a bad tab
	var bad := ActionDB.new()
	bad._check({"id": "x", "tab": "moon", "label": "x", "ages": [1, 2], "effects": {}}, "x", {})
	_check(bad.errors.size() >= 2, "bad action passed")
