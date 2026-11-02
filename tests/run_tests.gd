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
	_test_dollhouse()
	_test_careers_valid()
	_test_bad_careers_rejected()
	_test_career_year_end()
	_test_career_cards()
	_test_career_menu()
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
	var jobs := {}
	for life in LIVES:
		var state := GameStateScript.new()
		state.new_life()
		var deck := Deck.new(db.cards, life)
		var dead := false
		var careers := CareerDB.new()
		careers.load_dir()
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
			if not dead:
				var open := careers.available(state)
				if state.careers.size() < 2 and not open.is_empty():
					CareerRules.apply(open[deck.rng.randi() % open.size()], state, deck.rng)
				CareerRules.year_end(state, careers, deck.rng)
				for entry in state.careers.values():
					jobs[entry.id] = true
			if not dead and LifeRules.year_end(state, deck.rng).died:
				deaths += 1
				dead = true
			state.age += 1
		state.free()
	print(
		"sim: %d lives, %d cards drawn, %d empty slots, %d deaths" % [LIVES, drawn, empty, deaths]
	)
	_check(drawn > 0, "sim drew no cards")
	_check(jobs.size() >= 6, "sim lives held only %d kinds of job" % jobs.size())


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
	# pocket money: none before 6, $10 from 6, $20 from 10 (GDD §4.3)
	state.new_life()
	for a in [[5, 0], [6, 10], [10, 20]]:
		state.age = a[0]
		var before: int = state.stats.money
		LifeRules.year_end(state, rng)
		_check(state.stats.money - before == a[1], "pocket money at %d" % a[0])
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
	var rng := RandomNumberGenerator.new()
	var cafe := {"id": "cafe", "kind": "job", "ranks": [{"title": "Dishwasher"}]}
	CareerRules.apply(cafe, a, rng)
	a.careers.job.performance = 77
	CareerRules.date_crush(a, "job")
	b.from_dict(JSON.parse_string(JSON.stringify(a.to_dict())))
	var job: Dictionary = b.careers.get("job", {})
	_check(job.get("id") == "cafe" and job.get("performance") == 77, "save lost the job")
	_check(job.get("performance") is int, "job numbers came back as floats")
	_check(job.coworkers.crush.name == a.careers.job.coworkers.crush.name, "save lost coworkers")
	_check(b.partner.get("name") == a.partner.name, "save lost the partner")
	a.free()
	b.free()


func _test_actions() -> void:
	var db := ActionDB.new()
	db.load_dir()
	_check(db.errors.is_empty(), "action errors: %s" % "; ".join(db.errors))
	print("actions: %d valid" % db.actions.size())
	# age gates (GDD §6.7): a 3-year-old has nothing, a 15-year-old has clubs, study and the career tab
	_check(ActionDB.tabs_at(3).is_empty(), "a 3-year-old sees a menu tab")
	var ids := []
	for t in ActionDB.tabs_at(15):
		for a in db.available(t, 15):
			ids.append(a.id)
	for want in ["club", "study"]:
		_check(want in ids, "15-year-old can't see %s" % want)
	_check("jobs" in ActionDB.tabs_at(15), "no career tab at 15")
	_check("shop" not in ActionDB.tabs_at(17), "shop open before 18")
	# money limits actions (§6.5); effort adds Stress, fun lowers it (§6.6)
	var state := GameStateScript.new()
	state.new_life()
	var doctor: Dictionary = db.actions.filter(func(a): return a.id == "doctor")[0]
	_check(not ActionDB.perform(doctor, state), "doctor without money")
	state.stats.money = 25
	_check(ActionDB.perform(doctor, state) and state.stats.money == 5, "doctor cost wrong")
	_check(state.stats.stress > 0, "action added no stress")
	var stressed: int = state.stats.stress
	var toys: Dictionary = db.actions.filter(func(a): return a.id == "play_toys")[0]
	ActionDB.perform(toys, state)
	_check(state.stats.stress < stressed, "playing with toys didn't lower stress")
	state.free()
	# the validator rejects an action without stress or with a bad tab
	var bad := ActionDB.new()
	bad._check({"id": "x", "tab": "moon", "label": "x", "ages": [1, 2], "effects": {}}, "x", {})
	_check(bad.errors.size() >= 2, "bad action passed")


func _test_dollhouse() -> void:
	var bands := []
	for age in [0, 3, 4, 12, 13, 17]:
		bands.append(Dollhouse.band_for(age))
	_check(bands == ["baby", "baby", "child", "child", "teen", "teen"], "age bands %s" % [bands])
	for room in Dollhouse.ROOMS:
		for band in ["baby", "child", "teen"]:
			var path := Dollhouse.texture_path(room, band)
			_check(ResourceLoader.exists(path), "missing room still " + path)


func _make_state(age := 15):
	var state := GameStateScript.new()
	state.new_life()
	state.age = age
	return state


func _test_careers_valid() -> void:
	var db := CareerDB.new()
	db.load_dir()
	_check(db.errors.is_empty(), "career errors: %s" % "; ".join(db.errors))
	var kinds := {"job": 0, "special": 0}
	for c in db.careers:
		kinds[c.kind] += 1
	print("careers: %d jobs, %d specials" % [kinds.job, kinds.special])
	_check(kinds.job >= 6 and kinds.special >= 6, "expected 6 jobs and 6 specials")
	# every career is open to someone: stats in the middle of each required range
	for c in db.careers:
		var state = _make_state(c.ages[0])
		for s in c.get("requires", {}).get("stats", {}):
			var r: Array = c.requires.stats[s]
			state.stats[s] = int((r[0] + r[1]) / 2.0)
		_check(c in db.available(state), "nobody can take " + c.id)
		state.free()
	var kid = _make_state(13)
	_check(db.available(kid).is_empty(), "a 13-year-old can take a job")
	kid.free()


func _test_bad_careers_rejected() -> void:
	var db := CareerDB.new()
	var bad := [
		{"id": "a", "label": "x", "kind": "boss", "ages": [14, 17], "ranks": [{"title": "t"}]},
		{"id": "b", "label": "x", "kind": "job", "ages": [14, 17], "meter": "luck", "ranks": []},
		{
			"id": "c",
			"label": "x",
			"kind": "job",
			"ages": [14, 17],
			"ranks": [{"title": "t", "pay": 1, "stress": 1}, {"title": "u", "pay": 1, "stress": 0}]
		},
	]
	var counts := []
	for c in bad:
		var before := db.errors.size()
		db.check(c, c.id)
		counts.append(db.errors.size() - before)
	_check(not 0 in counts, "bad careers passed: %s" % [counts])


func _test_career_year_end() -> void:
	var db := CareerDB.new()
	db.load_dir()
	var rng := RandomNumberGenerator.new()
	rng.seed = 3
	var state = _make_state()
	# F1 costs $140 up front, so only a rich teen can join: money is the only limit (GDD §6.5)
	state.stats.money = 119
	_check(not CareerRules.apply(db.by_id.formula1, state, rng), "F1 without money")
	# one regular job and one special at once; a second job replaces the first
	_check(CareerRules.apply(db.by_id.retail, state, rng), "can't take the retail job")
	_check(CareerRules.apply(db.by_id.cafe, state, rng), "can't swap to the café")
	state.stats.money = 30
	_check(CareerRules.apply(db.by_id.actor, state, rng), "can't add a special career")
	_check(state.careers.keys().size() == 2, "expected a job and a special")
	_check(state.careers.job.id == "cafe", "the café didn't replace retail")
	var job: Dictionary = state.careers.job
	var names := {}
	for role in Coworkers.ROLES:
		names[job.coworkers[role].name] = true
	_check(names.size() == 4, "coworkers missing or share a name")
	# promotion is asked for: refused below promote_at, granted at or above
	job.performance = 60
	var line := CareerRules.ask_promotion(state, "job", db)
	_check(job.rank == 0 and job.performance == 55, "early ask: " + line)
	job.performance = 100
	line = CareerRules.ask_promotion(state, "job", db)
	_check(job.rank == 1 and CareerRules.title(job) == "Barista", "promotion: " + line)
	# year end pays every career and adds stress
	var money: int = state.stats.money
	var stress: int = state.stats.stress
	CareerRules.year_end(state, db, rng)
	_check(state.stats.money == money + 85 + 30, "pay was %d" % (state.stats.money - money))
	_check(state.stats.stress > stress, "work added no stress")
	# a work crush you date stays your partner after you're fired
	state.flags["work_job_dating"] = true
	CareerRules.date_crush(state, "job")
	var crush: String = state.careers.job.coworkers.crush.name
	state.careers.job.performance = 0
	CareerRules.year_end(state, db, rng)
	_check(not state.careers.has("job") and state.flags.has("fired"), "not fired at 0")
	_check(not state.flags.has("work_job_dating"), "work flags survived leaving")
	_check(state.partner.get("name") == crush, "partner lost with the job")
	_check(state.flags.has("dating_work_partner"), "dating set no partner flag")
	_check(state.careers.has("special"), "firing the job ended the special too")
	# a gang career heats up until the police step in: juvie and a record
	state.stats.karma = 10
	CareerRules.apply(db.by_id.gangster, state, rng)
	var years := 0
	while state.careers.has("special") and years < 100:
		state.careers.special.performance = 50
		CareerRules.year_end(state, db, rng)
		years += 1
	_check(state.flags.has("juvie") and state.flags.has("criminal_record"), "no juvie")
	state.stats.health = 80
	state.stats.karma = 80
	_check(not db.by_id.lifeguard in db.available(state), "lifeguard hires with a record")
	state.free()


func _test_career_cards() -> void:
	var rng := RandomNumberGenerator.new()
	var db := CareerDB.new()
	db.load_dir()
	var state = _make_state()
	var card := {
		"id": "t",
		"text": "{boss} wants you, {job}.",
		"ages": [14, 17],
		"requires": {"job": "job", "rank": [0, 0], "coworker": {"crush": [0, 100]}},
		"left": {"label": "Tell {friend}", "job": {"performance": 20, "rank": 1}},
		"right":
		{
			"label": "Kiss {crush}",
			"coworker": {"crush": 30},
			"job": {"date": true, "leave": "quit"}
		},
	}
	var cdb := CardDB.new()
	cdb._check_card(card, "t", {})
	_check(cdb.errors.is_empty(), "job card rejected: %s" % "; ".join(cdb.errors))
	var bad_card := {"id": "u", "requires": {"rank": [0, 1]}, "left": {"job": {"x": 1}}}
	cdb._check_card(bad_card, "u", {})
	_check(cdb.errors.size() >= 4, "bad job card passed")
	var deck := Deck.new([card], 1)
	state.stats.money = 50
	CareerRules.apply(db.by_id.musician, state, rng)
	_check(deck.draw(state) == null, "a 'job' card drawn with only a special career")
	CareerRules.apply(db.by_id.retail, state, rng)
	state.used = {}
	var c = deck.draw(state)
	var boss: String = state.careers.job.coworkers.boss.name
	var want := "%s wants you, Shelf Stacker." % boss
	_check(c != null and c.text == want, "names not filled in: %s" % (c.text if c else "null"))
	deck.choose(c, "left", state)
	var job: Dictionary = state.careers.job
	_check(job.performance == 70 and job.rank == 1, "job effects not applied")
	var crush: String = job.coworkers.crush.name
	deck.choose(c, "right", state)
	_check(not state.careers.has("job") and state.flags.has("quit"), "leave effect")
	_check(state.partner.get("name") == crush, "date effect")
	_check(state.careers.special.id == "musician", "leaving the job touched the special")
	var breakup := {"id": "b", "left": {"label": "End it", "partner": "end"}}
	state.flags["dating_work_partner"] = true
	deck.choose(breakup, "left", state)
	_check(state.partner.is_empty(), "breakup kept the partner")
	_check(not state.flags.has("dating_work_partner"), "breakup kept the dating flag")
	state.partner = {"name": "Sam"}
	var fail := {"id": "r", "left": {"label": "Plead", "risk": {"chance": 1.0, "partner": "end"}}}
	deck.choose(fail, "left", state)
	_check(state.partner.is_empty(), "failed risk kept the partner")
	cdb.errors.clear()
	cdb._check_card({"id": "p", "left": {"label": "x", "partner": "keep"}}, "p", {})
	_check(not cdb.errors.is_empty(), "bad 'partner' value passed")
	state.free()


func _test_career_menu() -> void:
	var db := CareerDB.new()
	db.load_dir()
	var state = _make_state()
	CareerRules.apply(db.by_id.cafe, state, RandomNumberGenerator.new())
	var job: Dictionary = state.careers.job
	var stress: int = state.stats.stress
	CareerRules.work_hard(state, "job")
	_check(job.performance == 60 and state.stats.stress > stress, "work hard")
	_check("flirt" not in CareerRules.staff_acts("boss"), "can flirt with the boss")
	_check(CareerRules.staff(state, "job", "boss", "gift") == "", "gift without money")
	CareerRules.staff(state, "job", "rival", "argue")
	_check(job.coworkers.rival.affinity == -35 and job.performance == 57, "argue")
	job.coworkers.crush.affinity = 50
	CareerRules.staff(state, "job", "crush", "flirt")
	_check(state.partner.get("name") == job.coworkers.crush.name, "flirting never led to a date")
	state.free()
