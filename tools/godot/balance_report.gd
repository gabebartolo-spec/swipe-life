extends SceneTree
## Balance report (M13): plays N lives with a sensible player and prints the numbers the balance
## pass tunes against. Run: godot --headless --script res://tools/godot/balance_report.gd
## -- [lives] [trace life] [lazy]  ("lazy" never visits the doctor or friends).

const GameStateScript := preload("res://scripts/autoload/game_state.gd")


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var lives := int(args[0]) if args.size() > 0 else 1000
	var lazy := args.size() > 2 and args[2] == "lazy"
	var db := CardDB.new()
	db.load_dir()
	var careers := CareerDB.new()
	careers.load_dir()
	var fdb := FinanceDB.new()
	fdb.load_all()
	var actions := ActionDB.new()
	actions.load_dir()
	var death_ages := []
	var worth := []
	var causes := {}
	var owners := 0
	var employed_years := 0
	var adult_years := 0
	var max_debt := 0
	var broke_years := 0
	var kids := 0
	var big_debt := []
	var partnered := 0
	for life in lives:
		var state := GameStateScript.new()
		state.new_life()
		var deck := Deck.new(db.cards, life)
		var dead := false
		var cause := ""
		var peak_debt := 0
		var trace := args.size() > 1 and life == int(args[1])
		while not dead and state.age <= 150:
			for q in 4:
				var card = deck.draw(state)
				if card == null:
					continue
				if deck.choose(card, ["left", "right"][deck.rng.randi() % 2], state).died:
					dead = true
					cause = "card"
					break
			if dead:
				break
			var open := careers.available(state)
			if not state.careers.has("job") and not open.is_empty():
				CareerRules.apply(open[deck.rng.randi() % open.size()], state, deck.rng)
			if state.age >= 18:
				adult_years += 1
				if state.careers.has("job"):
					employed_years += 1
				if state.housing.kind == "parents":
					Finance.rent(state)
				var opening: Array = fdb.courses_open(state)
				if state.course.is_empty() and not opening.is_empty():
					Finance.enrol(state, opening[deck.rng.randi() % opening.size()], true)
				if state.housing.kind == "rent" and Finance.can_buy(state, fdb.houses[0]):
					Finance.buy(state, fdb.houses[0])
				if state.stats.money < 0:
					broke_years += 1
			for a in [] if lazy else actions.actions:
				if a.id in ["doctor", "friends"] and a.ages[0] <= state.age:
					ActionDB.perform(a, state)
			CareerRules.year_end(state, careers, deck.rng)
			Finance.year_end(state, careers, deck.rng)
			peak_debt = maxi(peak_debt, Finance.total_debt(state))
			if trace and state.age >= 18:
				print(
					(
						"  age %d money %d pay %d house %s debts %s"
						% [
							state.age,
							state.stats.money,
							Finance.yearly_pay(state, careers),
							state.housing.kind,
							state.debts
						]
					)
				)
			var ending := LifeRules.year_end(state, deck.rng)
			if ending.died:
				dead = true
				cause = ending.cause
			else:
				state.age += 1
				CareerRules.outgrown(state, careers)
		death_ages.append(state.age)
		causes[cause] = int(causes.get(cause, 0)) + 1
		worth.append(Legacy.estate(state))
		max_debt = maxi(max_debt, peak_debt)
		if peak_debt > 1000000:
			big_debt.append(life)
		if state.housing.kind == "own":
			owners += 1
		kids += state.children.size()
		if not state.partner.is_empty():
			partnered += 1
		state.free()
	death_ages.sort()
	worth.sort()
	print("lives %d; peak debt over 1M in lives %s" % [lives, big_debt.slice(0, 8)])
	print("death age p5/p25/p50/p75/p95: %s" % [_pct(death_ages, [5, 25, 50, 75, 95])])
	print(
		(
			"died before 18: %d%%, before 40: %d%%, after 90: %d%%"
			% [
				_share(death_ages, func(a): return a < 18),
				_share(death_ages, func(a): return a < 40),
				_share(death_ages, func(a): return a > 90),
			]
		)
	)
	print("estate p5/p25/p50/p75/p95: %s" % [_pct(worth, [5, 25, 50, 75, 95])])
	print(
		(
			"own a home at death: %d%%, partnered: %d%%, children avg %.1f"
			% [owners * 100 / lives, partnered * 100 / lives, float(kids) / lives]
		)
	)
	print(
		(
			"employed share of adult years: %d%%, years in the red: %d%%, max debt %d"
			% [
				employed_years * 100 / maxi(adult_years, 1),
				broke_years * 100 / maxi(adult_years, 1),
				max_debt
			]
		)
	)
	print("causes: %s" % [causes])
	quit()


func _pct(sorted: Array, ps: Array) -> Array:
	return ps.map(func(p): return sorted[mini(sorted.size() - 1, sorted.size() * p / 100)])


func _share(a: Array, f: Callable) -> int:
	return a.filter(f).size() * 100 / a.size()
