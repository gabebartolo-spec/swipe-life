extends RefCounted
## M21 tests (GDD §15.11-15.12), kept out of run_tests.gd for its 1,000-line cap.

const GameStateScript := preload("res://scripts/autoload/game_state.gd")

var failures := 0


func _check(ok: bool, msg: String) -> void:
	if not ok:
		failures += 1
		printerr("FAIL: " + msg)


func _make_state(age := 15):
	var state := GameStateScript.new()
	state.new_life()
	state.age = age
	return state


## Fame tiers, fame and infamy gates, old saves, chains, pay and legacy.
func run() -> int:
	var tiers := []
	for f in [0, 4, 5, 19, 20, 40, 60, 79, 80, 95, 100]:
		tiers.append(GameStateScript.tier_of(f))
	_check(tiers == [0, 0, 1, 1, 2, 3, 4, 4, 5, 6, 6], "fame tiers wrong: %s" % [tiers])
	var s = _make_state(30)
	_check(s.stats.fame == 0 and s.stats.infamy == 0, "a new life must start unknown")
	_check(s.fame_tier_name() == "", "fame 0 must have no tier name")
	var star := {"fame_tier": [3, 6]}
	_check(not Deck.meets(star, s), "fame tier gate let a nobody through")
	s.stats.fame = 45
	_check(Deck.meets(star, s) and s.fame_tier_name() == "known", "fame tier gate or name wrong")
	_check(not Deck.meets({"stats": {"infamy": [20, 100]}}, s), "infamy gate let a saint through")
	# old saves have no fame or infamy: both default to 0
	var old := s.to_dict()
	old.stats.erase("fame")
	old.stats.erase("infamy")
	var b := GameStateScript.new()
	b.new_life()
	b.stats.fame = 70
	b.from_dict(JSON.parse_string(JSON.stringify(old)))
	_check(b.stats.fame == 0 and b.stats.infamy == 0, "old save fame/infamy not 0")
	b.free()
	# a chain: step one sets a flag, step two needs it and two years since
	var deck := Deck.new([], 1)
	var step2 := {"flags": ["arc"], "since": {"arc": 2}}
	deck.choose({"right": {"label": "go", "set_flags": ["arc"]}}, "right", s)
	_check(not Deck.meets(step2, s), "chain fired the same year")
	s.age += 1
	_check(not Deck.meets(step2, s), "chain fired a year early")
	s.age += 1
	_check(Deck.meets(step2, s), "chain did not fire two years on")
	b = GameStateScript.new()
	b.from_dict(JSON.parse_string(JSON.stringify(s.to_dict())))
	_check(Deck.meets(step2, b), "chain lost on save and load")
	b.free()
	var db := CardDB.new()
	db.load_dir()
	var ids := {}
	for c in db.cards:
		ids[c.id] = c
	for arc in [
		["fame_rising_memoir", "fame_famous_memoir_tour", "fame_icon_memoir_film"],
		["fame_known_stalker", "fame_star_fan_gate", "fame_icon_stalker_court"],
		["inf_heist_plan", "inf_heist_night", "inf_heist_trial"],
		["inf_doc_pitch", "inf_doc_aired", "inf_doc_sequel"],
	]:
		for i in range(1, 3):
			var need: Array = ids[arc[i]].requires.flags
			var sets: Array = ids[arc[i - 1]].up.get("set_flags", [])
			_check(sets.has(need[0]), "chain %s does not lead to %s" % [arc[i - 1], arc[i]])
	# fame boosts pay; fame and some infamy outlive you
	var careers := CareerDB.new()
	careers.load_dir()
	var rng := RandomNumberGenerator.new()
	var paid := []
	for fame in [0, 100]:
		var w = _make_state(30)
		w.stats.fame = fame
		CareerRules.apply(careers.by_id["cafe"], w, rng)
		var before: int = w.stats.money
		CareerRules.year_end(w, careers, rng)
		paid.append(w.stats.money - before)
		w.free()
	_check(paid[1] > paid[0], "fame did not raise pay: %s" % [paid])
	s.stats.fame = 80
	s.stats.infamy = 40
	s.partner = {"name": "Sam", "affinity": 70, "met": 20}
	s.children = [{"name": "Kit", "born_at": 10, "affinity": 60, "look": {}, "adopted": false}]
	Legacy.continue_as_heir(s)
	_check(s.stats.fame == 40 and s.stats.infamy == 10, "fame did not pass to the heir")
	s.free()
	return failures
