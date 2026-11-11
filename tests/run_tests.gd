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
	_test_traits()
	_test_date_cards_need_single()
	_test_old_save_traits()
	_test_finance()
	_test_adult_sim()
	_test_figures()
	_test_family()
	_test_items()
	_test_legacy()
	_test_ribbons()
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
	var seen := {}
	for life in LIVES:
		var state := GameStateScript.new()
		state.new_life()
		# Every 5th life starts at a trait corner (0/100) so extreme personalities get played too.
		if life % 5 == 0:
			state.stats.boldness = 100 * (life / 5 % 2)
			state.stats.sociability = 100 * (life / 10 % 2)
		var deck := Deck.new(db.cards, life)
		var dead := false
		var careers := CareerDB.new()
		careers.load_dir()
		while state.age <= CardDB.TEEN_MAX_AGE and not dead:
			state.super_like_available = true
			for q in 4:
				state.quarter = q
				var card = deck.draw(state)
				if card == null:
					empty += 1
					continue
				drawn += 1
				seen[card.id] = true
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
	for card in db.cards:
		if _trait_gated(card):
			_check(seen.has(card.id), "trait-gated card never drawn: %s" % card.id)
	_check(jobs.size() >= 6, "sim lives held only %d kinds of job" % jobs.size())


## True when the card's conditions test a personality spectrum (GDD §4.6).
func _trait_gated(card: Dictionary) -> bool:
	var text := JSON.stringify(card.get("conditions", {}))
	for t in GameStateScript.TRAITS:
		if t in text:
			return true
	return false


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
		state.stats.health == 90,
		"anxiety drained %d health, expected 10" % (100 - state.stats.health)
	)
	# no onset before age 6
	state.new_life()
	state.stats.happiness = 0
	for y in 6:
		state.age = y
		LifeRules.year_end(state, rng)
	_check(not state.flags.has("depression"), "depression before age 6")
	# old age (GDD §5.3c): no deaths before 70, then spread over the 70s-90s
	var ages: Array[int] = []
	for life in 1000:
		state.new_life()
		state.age = 60
		while state.age < 130:
			state.stats.health = 100
			state.stats.stress = 0
			state.stats.happiness = 100
			if LifeRules.year_end(state, rng).died:
				break
			state.age += 1
		ages.append(state.age)
	ages.sort()
	_check(ages[0] >= 70, "old age death at %d, before 70" % ages[0])
	_check(ages[-1] < 130, "a life never died of old age")
	var median: int = ages[500]
	_check(median >= 75 and median <= 90, "old age median %d, expected 75-90" % median)
	print("old age deaths: min %d, median %d, max %d" % [ages[0], median, ages[-1]])
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
	_check(Dollhouse.home_for(30, {"kind": "parents"}) == "teen", "parents' home past 18")
	_check(Dollhouse.home_for(30, {"kind": "rent"}) == "rental", "rental home")
	_check(Dollhouse.home_for(30, {"kind": "own", "house": "mansion"}) == "mansion", "bought home")
	var houses_json := FileAccess.get_file_as_string("res://data/property/houses.json")
	var houses: Array = JSON.parse_string(houses_json)
	for home: String in houses.map(func(h: Dictionary) -> String: return h.id) + ["rental"]:
		for room in Dollhouse.ROOMS:
			var still := Dollhouse.texture_path(room, home)
			_check(ResourceLoader.exists(still), "missing home still " + still)


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
		for f in c.get("requires", {}).get("flags", []):  # a finished course
			state.flags[f] = true
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
	state.stats.money = 139
	_check(not CareerRules.apply(db.by_id.formula1, state, rng), "F1 without money")
	# a free job is open even in debt
	state.stats.money = -50
	_check(CareerRules.apply(db.by_id.paper_round, state, rng), "debt blocked a free job")
	state.stats.money = 0
	# one regular job and one special at once; a second job replaces the first
	_check(CareerRules.apply(db.by_id.retail, state, rng), "can't take the retail job")
	_check(CareerRules.apply(db.by_id.cafe, state, rng), "can't swap to the café")
	# swapping jobs ends the old job's story flags
	state.flags["work_job_flirting"] = true
	_check(CareerRules.apply(db.by_id.retail, state, rng), "can't swap back to retail")
	_check(not state.flags.has("work_job_flirting"), "old job's flags survived a swap")
	_check(CareerRules.apply(db.by_id.cafe, state, rng), "can't swap to the café again")
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
	# a second work crush can't replace the partner you have
	CareerRules.date_crush(state, "special")
	_check(state.partner.get("name") == crush, "a card date replaced the partner")
	_check(not state.flags.has("work_special_dating"), "dating flag set while partnered")
	# a gang career heats up until the police step in: juvie and a record
	state.stats.karma = 10
	state.used = {"juvie_release": true, "juvie_first_night": true}  # served juvie once before
	state.flags["juvie_settled"] = true
	CareerRules.apply(db.by_id.gangster, state, rng)
	CareerRules.apply(db.by_id.fast_food, state, rng)
	var years := 0
	while state.careers.has("special") and years < 100:
		for slot in state.careers:
			state.careers[slot].performance = 50
		CareerRules.year_end(state, db, rng)
		years += 1
	_check(state.flags.has("juvie") and state.flags.has("criminal_record"), "no juvie")
	_check(state.careers.is_empty(), "a job kept paying in juvie")
	_check(db.available(state).is_empty(), "careers offered in juvie")
	_check(
		state.used.is_empty() and not state.flags.has("juvie_settled"), "juvie chain can't replay"
	)
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
	state.flags["work_job_dating"] = true
	deck.choose(breakup, "left", state)
	_check(state.partner.is_empty(), "breakup kept the partner")
	_check(not state.flags.has("dating_work_partner"), "breakup kept the dating flag")
	_check(not state.flags.has("work_job_dating"), "breakup kept the work dating chain")
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


## GDD §4.6: spectrums start 40-60, by_trait scales by position, the validator checks it.
func _test_traits() -> void:
	var state = GameStateScript.new()
	for i in 200:
		state.new_life()
		for t in GameStateScript.TRAITS:
			_check(
				state.stats[t] >= 40 and state.stats[t] <= 60,
				"%s starts at %d" % [t, state.stats[t]]
			)
	_check(Deck.trait_delta(100, 6) == 6, "full delta at 100")
	_check(Deck.trait_delta(50, 6) == 0, "no delta at 50")
	_check(Deck.trait_delta(0, 6) == -6, "reversed delta at 0")
	var card := {"id": "t", "left": {"label": "Go", "by_trait": {"sociability": {"happiness": 10}}}}
	var deck := Deck.new([card], 1)
	state.new_life()
	state.stats.sociability = 100
	deck.choose(card, "left", state)
	_check(
		state.stats.happiness == 60, "extrovert happiness %d, expected 60" % state.stats.happiness
	)
	state.stats.happiness = 50
	state.stats.sociability = 0
	deck.choose(card, "left", state)
	_check(
		state.stats.happiness == 40, "introvert happiness %d, expected 40" % state.stats.happiness
	)
	var db := CardDB.new()
	db._check_choice({"label": "x", "by_trait": {"health": {"happiness": 1}}}, "c")
	db._check_choice({"label": "x", "by_trait": {"boldness": {"luck": 1}}}, "c")
	_check(db.errors.size() == 2, "bad by_trait gave %d errors, expected 2" % db.errors.size())
	state.free()


## A card that starts dating the crush must not be drawn while you already have a partner:
## the date is skipped but its dating flags would stick and the next breakup would end the
## old partner instead.
func _test_date_cards_need_single() -> void:
	var db := CardDB.new()
	db.load_dir()
	for c in db.cards:
		for side in ["left", "right", "up"]:
			if c.has(side) and c[side].get("job", {}).get("date", false):
				_check(
					"dating_work_partner" in c.get("requires", {}).get("not_flags", []),
					"%s can date the crush while you already have a partner" % c.id
				)


## Saves from before the spectrums (#49) have no boldness or sociability: they load in range.
func _test_old_save_traits() -> void:
	var a := GameStateScript.new()
	a.new_life()
	var d: Dictionary = JSON.parse_string(JSON.stringify(a.to_dict()))
	for t in GameStateScript.TRAITS:
		d.stats.erase(t)
	var b := GameStateScript.new()
	b.from_dict(d)
	for t in GameStateScript.TRAITS:
		var v = b.stats.get(t)
		_check(v is int and v >= 40 and v <= 60, "old save gave %s = %s" % [t, v])
	a.stats.boldness = 93
	b.from_dict(JSON.parse_string(JSON.stringify(a.to_dict())))
	_check(b.stats.boldness == 93 and b.stats.boldness is int, "save lost boldness")
	a.free()
	b.free()


func _test_finance() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	var db := CareerDB.new()
	db.load_dir()
	_check(db.errors.is_empty(), "career data: %s" % ", ".join(db.errors))
	var fdb := FinanceDB.new()
	fdb.load_all()
	_check(fdb.errors.is_empty(), "finance data: %s" % ", ".join(fdb.errors))
	_check(fdb.houses.size() == 7 and fdb.courses.size() == 26, "houses or courses missing")
	_check(int(db.by_id.corporate.ranks[-1].pay) == 900000, "top career must pay 30E")
	# parents are free; a renter with no income pays rent + living, and it becomes a 10% loan
	var s = _make_state(18)
	s.stats.money = 0
	Finance.year_end(s, db, rng)
	_check(s.stats.money == 0 and s.debts.is_empty(), "living at home must be free")
	Finance.rent(s)
	var lines := Finance.year_end(s, db, rng)
	_check("No income this year." in lines, "no-income line missing")
	_check(s.stats.money == 0, "below zero must convert to a loan")
	_check(Finance.total_debt(s) == Finance.RENT + Finance.LIVING, "wrong first-year loan")
	_check(not Finance.can_borrow(s), "no job must block borrowing")
	# fresh start clears loans and blocks borrowing for 7 years
	_check(Finance.can_fresh_start(s, db), "fresh start should open")
	Finance.fresh_start(s)
	_check(s.debts.is_empty() and s.flags.has("fresh_start"), "fresh start did not clear")
	s.age = s.fresh_start_until
	s.housing = {"kind": "parents"}
	Finance.year_end(s, db, rng)
	_check(not s.flags.has("fresh_start"), "fresh start must expire")
	# mortgage: 10% deposit, payments clear it in 25 years
	var h = _make_state(30)
	var flat: Dictionary = fdb.houses[0]
	h.stats.money = 1000000
	CareerRules.apply(db.by_id.corporate, h, rng)
	Finance.buy(h, flat)
	_check(h.housing.kind == "own", "could not buy")
	_check(Finance.total_debt(h) == int(flat.price * 0.9), "mortgage must be 90% of price")
	for i in Finance.MORTGAGE_YEARS:
		Finance._debt_year(h, db)
	_check(h.debts.is_empty(), "mortgage not cleared in 25 years")
	_check(Finance.sell(h) != "" and h.housing.kind == "rent", "sell failed")
	# repossession after 3 years in debt
	var r = _make_state(30)
	r.housing = {"kind": "own", "label": "x", "value": 1, "upkeep": 1000, "growth": 0.0}
	r.debts = [{"kind": "loan", "balance": 500000, "rate": 0.1, "payment": 0, "taken": 25}]
	for i in Finance.REPOSSESS_AFTER + 1:
		Finance.year_end(r, db, rng)
	_check(r.housing.kind == "rent", "house not repossessed")
	# course: finishing sets the flag that opens the job
	var c = _make_state(18)
	c.stats.smarts = 100
	var course: Array = fdb.courses.filter(func(k): return k.id == "carpentry")
	_check(not db.available(c).any(func(j): return j.id == "carpenter"), "carpenter needs a course")
	Finance.enrol(c, course[0], true)
	var guard := 0
	while not c.course.is_empty() and guard < 50:
		Finance.year_end(c, db, rng)
		guard += 1
	_check(db.available(c).any(func(j): return j.id == "carpenter"), "course must open the job")
	_check(c.debts.any(func(d): return d.kind == "student"), "student loan missing")
	# six course years on loan: medicine (6) is refused after carpentry (2), nursing (3) is not
	var by_course := func(id): return fdb.courses.filter(func(k): return k.id == id)[0]
	_check(Finance.enrol(c, by_course.call("medicine"), true) == "", "loan past the 6-year cap")
	_check(Finance.enrol(c, by_course.call("nursing"), true) != "", "loan inside the cap refused")
	c.course = {}
	_check(Finance.enrol(c, by_course.call("care_cert"), true) != "", "last loan year refused")
	c.course = {}
	_check(Finance.enrol(c, by_course.call("fire"), true) == "", "seventh loan year given")
	c.stats.money = 100000
	_check(
		Finance.enrol(c, by_course.call("fire"), false) != "", "cash course refused after the cap"
	)
	# retail carries on past 18 at an adult wage, with adult-only ranks; other teen jobs end
	var t = _make_state(17)
	CareerRules.apply(db.by_id.retail, t, rng)
	t.careers.job.rank = 2
	t.careers.job.performance = 100
	CareerRules.ask_promotion(t, "job", db)
	_check(t.careers.job.rank == 2, "store manager is for adults")
	t.age = 18
	_check(CareerRules.outgrown(t, db).is_empty(), "retail must carry on past 18")
	# juvie ends at 18 even if the release card never came up, or no job would ever open
	var j = _make_state(18)
	j.flags["juvie"] = true
	_check(db.available(j).is_empty(), "juvie must block jobs")
	CareerRules.outgrown(j, db)
	_check(not db.available(j).is_empty(), "juvie must end at 18")
	_check(Finance.yearly_pay(t, db) == Finance.E, "teen rank must pay E at 18")
	var f = _make_state(17)
	CareerRules.apply(db.by_id.paper_round, f, rng)
	f.age = 18
	CareerRules.outgrown(f, db)
	_check(f.careers.is_empty(), "teen job must end at 18")
	for o in [s, h, r, c, t, f]:
		o.free()


## Lives from birth until death: nobody gets stuck and old age ends every life.
func _test_adult_sim() -> void:
	var db := CardDB.new()
	db.load_dir()
	var careers := CareerDB.new()
	careers.load_dir()
	var fdb := FinanceDB.new()
	fdb.load_all()
	var ages := []
	var houses := 0
	var adult_jobs := {}
	var max_debt := 0
	var actions := ActionDB.new()
	actions.load_dir()
	var careful := []
	var old_age_deaths := []
	var late_cards := {}
	var stuck := 0
	for life in LIVES:
		var state := GameStateScript.new()
		state.new_life()
		var deck := Deck.new(db.cards, life)
		var dead := false
		while not dead and state.age <= CardDB.MAX_AGE + 50:
			for q in 4:
				var card = deck.draw(state)
				if card == null:
					if state.age >= 60:
						stuck += 1
					continue
				if state.age >= 60 and card.id.begins_with("a60_"):
					late_cards[card.id] = true
				if deck.choose(card, ["left", "right"][deck.rng.randi() % 2], state).died:
					dead = true
					break
			if dead:
				break
			var open := careers.available(state)
			if not state.careers.has("job") and not open.is_empty():
				CareerRules.apply(open[deck.rng.randi() % open.size()], state, deck.rng)
			if state.age >= 18:
				for entry in state.careers.values():
					adult_jobs[entry.id] = true
				if state.housing.kind == "parents" and life % 2 == 0:
					Finance.rent(state)
				var opening: Array = fdb.courses_open(state)
				if state.course.is_empty() and not opening.is_empty():
					Finance.enrol(state, opening[deck.rng.randi() % opening.size()], true)
				if state.housing.kind == "rent" and Finance.can_buy(state, fdb.houses[0]):
					Finance.buy(state, fdb.houses[0])
					houses += 1
			if life % 2 == 1:
				for a in actions.actions:
					if a.id in ["doctor", "friends"] and a.ages[0] <= state.age:
						ActionDB.perform(a, state)
			CareerRules.year_end(state, careers, deck.rng)
			Finance.year_end(state, careers, deck.rng)
			max_debt = maxi(max_debt, Finance.total_debt(state))
			var ending := LifeRules.year_end(state, deck.rng)
			if ending.died:
				dead = true
				if ending.cause.contains("old age"):
					old_age_deaths.append(state.age)
			else:
				state.age += 1
				CareerRules.outgrown(state, careers)
		_check(dead, "adult life never ended (age %d)" % state.age)
		(careful if life % 2 == 1 else ages).append(state.age)
		state.free()
	ages.sort()
	careful.sort()
	var median: int = careful[careful.size() / 2]
	# Balance (M13): ignoring health costs years, not the whole life; looking after it adds more.
	_check(
		ages[ages.size() / 2] >= 50, "never-rest lives die too young: %d" % ages[ages.size() / 2]
	)
	_check(median >= 72 and median > ages[ages.size() / 2] + 10, "careful lives gain too little")
	print("adult sim: never-rest lives median death %d" % ages[ages.size() / 2])
	print(
		(
			"adult sim: careful lives median death %d, oldest %d, %d houses, %d jobs, max debt %d"
			% [median, careful[-1], houses, adult_jobs.size(), max_debt]
		)
	)
	_check(max_debt < 1000000, "runaway debt in the sim: %d" % max_debt)
	old_age_deaths.sort()
	print(
		(
			"adult sim: %d old-age deaths, ages %s to %s; %d late-life cards drawn; %d empty draws at 60+"
			% [
				old_age_deaths.size(),
				old_age_deaths[0] if old_age_deaths else "-",
				old_age_deaths[-1] if old_age_deaths else "-",
				late_cards.size(),
				stuck
			]
		)
	)
	_check(not old_age_deaths.is_empty(), "no life died of old age")
	_check(
		old_age_deaths.is_empty() or old_age_deaths[0] >= LifeRules.OLD_AGE_FROM,
		"old age before 70"
	)
	_check(
		old_age_deaths.size() < 2 or old_age_deaths[-1] - old_age_deaths[0] >= 8,
		"old-age deaths not spread"
	)
	_check(late_cards.size() >= 15, "only %d late-life cards ever drawn" % late_cards.size())
	_check(stuck < LIVES * 4, "%d empty draws at 60+ (decks run dry)" % stuck)
	_check(median > 30, "careful lives must get past 30")
	_check(houses > 0, "no life bought a house")
	_check(adult_jobs.size() > 10, "only %d jobs held" % adult_jobs.size())


## Shop items load, sell once, charge and apply effects, show in their room and survive a save.
func _test_items() -> void:
	var shop := Items.new()
	shop.load_all()
	for e in shop.errors:
		printerr(e)
	_check(shop.errors.is_empty() and shop.items.size() >= 10, "items.json invalid")
	var state := GameStateScript.new()
	state.new_life()
	state.age = 30
	state.stats.money = 10000
	var sofa := shop.get_item("sofa")
	_check(shop.available(state).has(sofa), "sofa not on sale")
	var before: int = state.stats.happiness
	_check(shop.buy(state, sofa) != "", "sofa not bought")
	_check(state.stats.money == 10000 - int(sofa.price), "sofa price not charged")
	_check(state.stats.happiness > before, "sofa effects not applied")
	_check(shop.buy(state, sofa) == "", "sofa bought twice")
	_check(not shop.available(state).has(sofa), "owned sofa still on sale")
	_check(shop.items_for(state) == [{"id": "sofa", "room": "living"}], "item not in room")
	var copy := GameStateScript.new()
	copy.new_life()
	copy.from_dict(JSON.parse_string(JSON.stringify(state.to_dict())))
	_check(copy.items == ["sofa"], "items lost in save")
	state.free()
	copy.free()
	var poor := GameStateScript.new()
	poor.new_life()
	poor.age = 30
	poor.stats.money = 5
	_check(shop.buy(poor, sofa) == "", "bought without money")
	poor.free()


## Legacy (GDD §9.3): the oldest grown-up child inherits the estate less tax, the house and items.
func _test_legacy() -> void:
	var s := GameStateScript.new()
	s.new_life()
	s.age = 70
	s.stats.money = 100000
	s.stats.looks = 90
	s.items = ["sofa"]
	s.partner = {"name": "Sam", "affinity": 70}
	s.housing = {"kind": "own", "house": "small_flat", "label": "Small flat", "value": 80000}
	s.children = [
		{"name": "Kid", "born_at": 45, "affinity": 50, "look": {"sex": "f"}},
		{"name": "Elder", "born_at": 40, "affinity": 50, "look": {"sex": "m"}},
		{"name": "Baby", "born_at": 65, "affinity": 50, "look": {"sex": "f"}},
	]
	_check(Legacy.heir(s).name == "Elder", "heir is not the oldest grown-up child")
	_check(Legacy.estate(s) == 60000, "estate tax wrong: %d" % Legacy.estate(s))
	_check(Legacy.continue_as_heir(s) == "Elder", "did not continue as Elder")
	_check(s.age == 30 and s.stats.money == 60000, "heir age or money wrong")
	_check(s.stats.looks == 70, "looks not pulled halfway: %d" % s.stats.looks)
	_check(s.housing.kind == "own" and s.items == ["sofa"], "house or items not inherited")
	_check(s.siblings.size() == 2 and s.children.is_empty(), "siblings not carried")
	_check(s.parents_alive and s.flags.generation == 2, "family or generation wrong")
	var none := GameStateScript.new()
	none.new_life()
	none.age = 70
	_check(Legacy.heir(none).is_empty(), "heir without children")
	_check(Legacy.continue_as_heir(none) == "", "continued without an heir")
	s.free()
	none.free()


## Ribbons load, match the life that ended, and the profile only reports new ones.
func _test_ribbons() -> void:
	var rb := Ribbons.new()
	rb.load_all()
	for e in rb.errors:
		printerr(e)
	_check(rb.errors.is_empty() and rb.ribbons.size() >= 10, "ribbons.json invalid")
	var s := GameStateScript.new()
	s.new_life()
	s.age = 82
	s.stats.money = 2000000
	s.partner = {"name": "Sam"}
	var ids: Array = rb.earned(s).map(func(r): return r.id)
	_check(
		"long_life" in ids and "rich" in ids and "partnered" in ids, "ribbons missed: %s" % [ids]
	)
	_check("gone_young" not in ids and "dynasty" not in ids, "ribbons given wrongly: %s" % [ids])
	var path := "user://test_profile.json"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	_check(rb.record(s, path).size() == ids.size(), "first life should report every ribbon")
	_check(rb.record(s, path).is_empty(), "second life reported old ribbons")
	_check(Ribbons.load_profile(path).lives == 2, "lives not counted")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	_test_unlocks(rb, s)
	s.free()


## Careers a ribbon unlocks stay out of the Jobs tab until the profile has the ribbon (GDD 9.2).
func _test_unlocks(rb: Ribbons, s) -> void:
	var db := CareerDB.new()
	db.load_dir()
	for u in rb.all_unlocks():
		if u.begins_with("career:"):
			_check(db.by_id.has(u.trim_prefix("career:")), "ribbon unlocks missing career %s" % u)
	db.locked = rb.all_unlocks()
	s.new_life()
	s.age = 30
	s.flags["edu_medicine"] = true
	var ids := func(): return db.available(s).map(func(c): return c.id)
	_check("doctor" not in ids.call() and "corporate" not in ids.call(), "locked careers offered")
	_check("cleaner" in ids.call(), "ordinary careers vanished")
	db.unlocked = ["career:doctor"]
	_check("doctor" in ids.call(), "unlocked career not offered")
	var cdb := CardDB.new()
	cdb.load_dir()
	for u in rb.all_unlocks():
		if u.begins_with("cards:"):
			var in_set := cdb.cards.filter(
				func(c): return c.get("set", "") == u.trim_prefix("cards:")
			)
			_check(in_set.size() >= 10, "ribbon unlocks thin card set %s" % u)
	var deck := Deck.new(cdb.cards, 1)
	s.new_life()
	s.age = 40
	s.flags["heir"] = true
	var drawn := func(): return deck.eligible(s).filter(func(c): return c.has("set")).size()
	_check(drawn.call() == 0, "locked card set drawn")
	deck.open_sets = ["dynasty"]
	_check(drawn.call() >= 5, "unlocked card set not drawn")


## Every shape, cut, clip and room depth map the living figures need is there, and a figure poses.
func _test_figures() -> void:
	var dir := Figure3D.DIR
	var cuts := DirAccess.get_files_at(dir + "/adult_f_skinny/hair")
	_check(cuts.size() >= 33, "only %d hair cuts" % cuts.size())
	for shape in ["child", "teen", "adult"]:
		for sex in ["f", "m"]:
			var folder := "%s/%s_%s_skinny" % [dir, shape, sex]
			_check(FileAccess.file_exists(folder + "/body.json"), "no body: " + folder)
			_check(DirAccess.get_files_at(folder + "/hair").size() == cuts.size(), folder + " hair")
	_check(FileAccess.file_exists(dir + "/baby/body.json"), "no baby body")
	var clips := ["idle", "sit", "sit_talk", "text", "crawl", "sit_floor", "walk", "lay_back"]
	var fig := Figure3D.new()
	fig.build("adult_f_skinny", {"hair": "bob", "body": [Color.WHITE]})
	for clip: String in clips:
		_check(FileAccess.file_exists("%s/clips/%s.json" % [dir, clip]), "no clip: " + clip)
		fig.play(clip)
		fig.advance(0.5)
		_check(fig.get_node("head").position.is_finite(), "clip broke the pose: " + clip)
	fig.free()
	var homes := ["baby", "child", "teen", "rental", "small_flat", "fixer_upper"]
	homes.append_array(["starter_house", "town_house", "family_house", "seaside_villa", "mansion"])
	for home: String in homes:
		for room: String in Dollhouse.ROOMS:
			var path := "%s/depth_%s_%s.png" % [FigureStage.DEPTH_DIR, room, home]
			_check(ResourceLoader.exists(path), "no depth map: " + path)


## A life can find a partner, marry, have a child and lose them all (ROADMAP M10).
func _test_family() -> void:
	var db := ActionDB.new()
	db.load_dir()
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var s := GameStateScript.new()
	s.new_life()
	s.age = 25
	s.stats.money = 100000
	var ids := func() -> Array: return db.available("people", s.age, s).map(func(a): return a.id)
	_check("date" in ids.call() and "propose" not in ids.call(), "single menu wrong")
	for i in 50:
		if s.partner.is_empty():
			Family.act("date", s, rng)
	_check(not s.partner.is_empty(), "dating never found a partner")
	_check(s.flags.has("dating_work_partner"), "a partner must close the dating cards")
	_check("date" not in ids.call() and "propose" in ids.call(), "partner menu wrong")
	s.partner.affinity = 80
	Family.act("propose", s, rng)
	_check(s.partner.get("married", false), "a happy partner said no")
	_check("divorce" in ids.call() and "breakup" not in ids.call(), "married menu wrong")
	for i in 50:
		if s.children.is_empty():
			Family.act("try_child", s, rng)
	_check(s.children.size() == 1, "trying never had a child")
	_check("child_time" in ids.call(), "no child actions")
	var d: Dictionary = JSON.parse_string(JSON.stringify(s.to_dict()))
	var b := GameStateScript.new()
	b.new_life()
	b.from_dict(d)
	_check(b.children.size() == 1 and b.children[0].born_at is int, "save lost the child")
	s.age = 30
	_check(Family.child_age(s.children[0], s) == 5, "child did not age")
	var before: int = s.stats.money
	var lines := []
	Family.year_end(s, rng, lines)
	_check(s.stats.money == before - Family.CHILD_COST, "child cost not paid")
	s.partner.affinity = 0
	Family.year_end(s, rng, lines)
	_check(s.partner.is_empty() and not s.flags.has("married"), "an unhappy partner stayed")
	s.age = 99
	for i in 200:
		Family.year_end(s, rng, lines)
	_check(not s.parents_alive, "parents never died")
	_check("parents" not in ids.call(), "can still talk to dead parents")
	s.free()
	b.free()
