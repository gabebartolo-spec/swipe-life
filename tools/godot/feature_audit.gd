extends SceneTree
## Feature audit (M13): one launch runs the strategy lives and the per-career runs.
## Run: godot --headless --script res://tools/godot/feature_audit.gd -- [lives] [reps] [strategies]
## reps 0 skips the career runs; strategies is a comma list (default all).

const GameStateScript := preload("res://scripts/autoload/game_state.gd")
const VAL := {"stress": -1, "karma": 0.5}
const GOOD := ["happiness", "health", "smarts", "looks", "relationships", "career"]
const STRATS := ["random", "greedy", "worst", "greedy_frugal", "greedy_spender"]
const EXTRA := ["greedy_super", "super_always"]  # run by name only
const DEATH_COST := 60.0  # score a death is worth, for judging a super swipe
const SUPER_MARGIN := 3.0  # how much better than the best normal swipe a super must look


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var lives := int(args[0]) if args.size() > 0 else 300
	var reps := int(args[1]) if args.size() > 1 else 60
	var db := CardDB.new()
	db.load_dir()
	var careers := CareerDB.new()
	careers.load_dir()
	var fdb := FinanceDB.new()
	fdb.load_all()
	var actions := ActionDB.new()
	actions.load_dir()
	print("== strategies (%d lives each) ==" % lives)
	var only: PackedStringArray = args[2].split(",") if args.size() > 2 else STRATS
	for s in only:
		_strategy(s, lives, db, careers, fdb, actions)
	if reps <= 0:
		quit()
		return
	print("== careers (%d runs each, whole career span, capped 40 years) ==" % reps)
	for c in careers.careers:
		_career(c, reps, careers)
	quit()


func _score(ch: Dictionary) -> float:
	var s := 0.0
	var e: Dictionary = ch.get("effects", {})
	for k in e:
		if k == "money":
			s += e[k] / 2000.0
		elif k in GOOD or k in VAL:
			s += VAL.get(k, 1.0) * e[k]
	return s


func _side(strat: String, card: Dictionary, rng: RandomNumberGenerator) -> String:
	if strat == "random":
		return ["left", "right"][rng.randi() % 2]
	var left_better := _score(card.left) >= _score(card.right)
	if strat == "worst":
		left_better = not left_better
	return "left" if left_better else "right"


## The between-year menu (GDD 6.5): the year's action budget, spent greedily on the best affordable
## actions, at most twice each (a real player mixes study, friends, gym and so on).
func _menu_actions(state, actions) -> void:
	state.actions_left = GameStateScript.actions_per_year(state.age)
	var used := {}
	while state.actions_left > 0:
		var best: Dictionary = {}
		var best_score := 0.0
		for a in actions.actions:
			if a.ages[0] > state.age or state.age > a.ages[1]:
				continue
			if (
				used.get(a.id, 0) >= 2
				or a.get("needs", []).size() > 0
				or state.stats.money < int(a.get("cost", 0))
			):
				continue
			var sc := _score(a) - float(a.get("cost", 0)) / 2000.0
			if sc > best_score:
				best_score = sc
				best = a
		if best.is_empty():
			break
		ActionDB.perform(best, state)
		used[best.id] = used.get(best.id, 0) + 1
		state.actions_left -= 1


## Expected value of a super swipe: its gain, the risk roll's effects, and a death penalty.
func _up_value(up: Dictionary) -> float:
	var v := _score(up)
	if up.has("risk"):
		v += float(up.risk.chance) * _score(up.risk)
	if up.has("death"):
		v -= float(up.death.chance) * DEATH_COST
	return v


## greedy_super spends it when it beats the best normal swipe by a margin (or on the year's last
## card); super_always spends it on the first card, as a baseline.
func _take_super(strat: String, card: Dictionary, last: bool) -> bool:
	if strat == "super_always" or last:
		return true
	var best := maxf(_score(card.left), _score(card.right))
	return _up_value(card.up) - best >= SUPER_MARGIN


func _adult_year(strat: String, state, deck: Deck, careers, fdb) -> void:
	if strat == "greedy_frugal":
		state.flags["frugal"] = true
	if strat == "greedy_spender":
		state.flags["spender"] = true
	if Finance.can_fresh_start(state, careers):
		Finance.fresh_start(state)
	if state.housing.kind == "parents":
		Finance.rent(state)
	var opening: Array = fdb.courses_open(state)
	if state.course.is_empty() and not opening.is_empty():
		Finance.enrol(state, opening[deck.rng.randi() % opening.size()], true)
	if (
		state.housing.kind == "rent"
		and Finance.can_buy(state, fdb.houses[0])
		and Finance.can_afford(state, fdb.houses[0], careers)
	):
		Finance.buy(state, fdb.houses[0])
	if strat == "greedy_spender":
		_spend(state, fdb, careers)


## Buys every shop item it can afford and trades up to the dearest house it can afford.
func _spend(state, fdb, careers) -> void:
	var shop := Items.new()
	shop.load_all()
	for it in shop.available(state):
		if state.stats.money > 2 * int(it.price):
			shop.buy(state, it)
	if state.housing.kind == "parents" or not Finance.can_borrow(state):
		return
	for h in fdb.houses:
		var better: bool = state.housing.kind != "own" or int(h.price) > int(state.housing.value)
		if (
			better
			and Finance.can_afford(state, h, careers)
			and state.stats.money > 2 * Finance.deposit(h)
			and state.age >= int(h.min_age)
		):
			if state.housing.kind == "own":
				Finance.sell(state)
			Finance.buy(state, h)


func _strategy(strat: String, lives: int, db, careers, fdb, actions) -> void:
	var ages := []
	var worth := []
	var h40 := []
	var s40 := []
	var m40 := []
	var hp60 := []
	var debt := 0
	var jobs := 0
	var years := 0
	for life in lives:
		var state := GameStateScript.new()
		state.new_life()
		var deck := Deck.new(db.cards, life)
		var dead := false
		var seen40 := false
		while not dead and state.age <= 150:
			var super_left: bool = strat in ["greedy_super", "super_always"]
			for q in 4:
				var card = deck.draw(state)
				if card == null:
					continue
				var side := _side(strat, card, deck.rng)
				if super_left and card.has("up") and _take_super(strat, card, q == 3):
					side = "up"
					super_left = false
				if deck.choose(card, side, state).died:
					dead = true
					break
			if dead:
				break
			var open: Array = careers.available(state)
			if not state.careers.has("job") and not open.is_empty():
				CareerRules.apply(open[deck.rng.randi() % open.size()], state, deck.rng)
			if state.careers.has("job"):
				var job: Dictionary = state.careers.job
				var rank: Dictionary = careers.by_id[job.id].ranks[int(job.rank)]
				if rank.has("promote_at") and int(job.performance) >= int(rank.promote_at):
					CareerRules.ask_promotion(state, "job", careers)
			if state.age >= 18:
				years += 1
				jobs += 1 if state.careers.has("job") else 0
				_adult_year(strat, state, deck, careers, fdb)
			_menu_actions(state, actions)
			CareerRules.year_end(state, careers, deck.rng)
			Finance.year_end(state, careers, deck.rng)
			debt = maxi(debt, Finance.total_debt(state))
			if state.age == 40 and not seen40:
				seen40 = true
				h40.append(state.stats.happiness)
				s40.append(state.stats.stress)
				m40.append(state.stats.money)
			if state.age == 60:
				hp60.append(state.stats.health)
			if LifeRules.year_end(state, deck.rng).died:
				dead = true
			else:
				state.age += 1
				CareerRules.outgrown(state, careers)
		ages.append(state.age)
		worth.append(Legacy.estate(state))
		state.free()
	ages.sort()
	worth.sort()
	print(
		(
			"%-14s death %s estate %s @40 happy %.0f stress %.0f cash %d hp60 %.0f debt %d job %d%%"
			% [
				strat,
				_pct(ages),
				_pct(worth),
				_avg(h40),
				_avg(s40),
				_avg(m40),
				_avg(hp60),
				debt,
				jobs * 100 / maxi(years, 1)
			]
		)
	)


func _career(c: Dictionary, reps: int, careers) -> void:
	var fired := 0
	var arrested := 0
	var top := 0
	var earned := []
	var ranks := []
	var span := mini(int(c.ages[1]) - int(c.ages[0]) + 1, 40)
	for r in reps:
		var state := GameStateScript.new()
		state.new_life()
		state.age = int(c.ages[0])
		state.stats.money = 100000
		var rng := RandomNumberGenerator.new()
		rng.seed = r + 1
		CareerRules.apply(c, state, rng)
		var total := 0
		var lost := false
		for y in span:
			if not state.careers.has(c.kind):
				lost = true
				break
			var e: Dictionary = state.careers[c.kind]
			var rk: Dictionary = c.ranks[int(e.rank)]
			if int(e.performance) < 60:
				CareerRules.work_hard(state, c.kind)
			elif rk.has("promote_at") and int(e.performance) >= int(rk.promote_at):
				CareerRules.ask_promotion(state, c.kind, careers)
			var before: int = state.stats.money
			CareerRules.year_end(state, careers, rng)
			total += state.stats.money - before
			state.stats.stress = clampi(state.stats.stress - 8, 0, 100)
			state.age += 1
			if state.flags.has("juvie"):
				arrested += 1
				break
		fired += 1 if lost or state.flags.has("fired") else 0
		var reached := 0
		if state.careers.has(c.kind):
			reached = int(state.careers[c.kind].rank)
		ranks.append(reached)
		top += 1 if reached == c.ranks.size() - 1 else 0
		earned.append(total)
		state.free()
	print(
		(
			"%-20s %-7s %s fired %3d%% arrested %2d%% top %3d%% avg rank %.1f earned/yr %d"
			% [
				c.id,
				c.kind,
				c.ages,
				fired * 100 / reps,
				arrested * 100 / reps,
				top * 100 / reps,
				_avg(ranks),
				int(_avg(earned) / span)
			]
		)
	)


func _pct(sorted: Array) -> Array:
	return [sorted[sorted.size() / 20], sorted[sorted.size() / 2], sorted[sorted.size() * 95 / 100]]


func _avg(a: Array) -> float:
	var t := 0.0
	for v in a:
		t += v
	return t / maxf(a.size(), 1)
