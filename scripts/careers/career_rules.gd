class_name CareerRules
extends RefCounted
## Careers in play (docs/CAREERS.md). A teen holds at most one regular job and one special career
## at once: GameState.careers maps slot ("job" / "special") to an entry
## {id, rank, titles, performance 0-100, years, meter 0-100, coworkers}.
## Promotion is asked for from the career menu; year end pays, fires and (gang) arrests.

const START_PERFORMANCE := 50
const AFTER_PROMOTION := 40  # a new rank starts you lower down
const FIRE_AT := 15  # performance at or below this at year end: fired
const DRIFT := [-8, 12]  # yearly random change in performance
const HEAT_PER_RANK := 6  # a gang job heats up every year, more at higher ranks
const ARREST_PER_HEAT := 0.005  # arrest chance per point of heat (heat 100 = 50%)
const RECORD := "criminal_record"  # set by an arrest; careers can bar it with not_flags
const WORK_HARD := {"performance": 10, "stress": 6}
const DATE_AT := 60  # crush affinity needed for a flirt to turn into dating
## Career menu staff actions: affinity change, stress, and optional cost and performance.
const STAFF := {
	"talk": {"affinity": 8, "stress": 2, "line": "You had a good chat with %s."},
	"gift": {"affinity": 15, "stress": 1, "cost": 10, "line": "%s loved the gift."},
	"argue": {"affinity": -15, "stress": 5, "performance": -3, "line": "You and %s had it out."},
	"flirt": {"affinity": 12, "stress": 3, "line": "%s blushed."},
}


## Starts a career in its slot, replacing what was there. False if already held or unaffordable.
static func apply(career: Dictionary, state, rng: RandomNumberGenerator) -> bool:
	var cost := int(career.get("cost", 0))
	var held: Dictionary = state.careers.get(career.kind, {})
	if state.stats.money < cost or held.get("id") == career.id:
		return false
	state.change_stat("money", -cost)
	state.careers[career.kind] = {
		"id": career.id,
		"rank": 0,
		"titles": career.ranks.map(func(r): return r.title),
		"performance": START_PERFORMANCE,
		"years": 0,
		"meter": 0,
		"coworkers": Coworkers.generate(rng),
	}
	return true


## Ends the career in a slot and clears its "work_<slot>_" flags. `reason` ("fired", "quit")
## is set as a flag.
static func leave(state, slot: String, reason := "") -> void:
	state.careers.erase(slot)
	for f in state.flags.keys():
		if f.begins_with("work_%s_" % slot):
			state.flags.erase(f)
	if reason != "":
		state.flags[reason] = true


static func change_performance(entry: Dictionary, delta: int) -> void:
	entry.performance = clampi(int(entry.performance) + delta, 0, 100)


static func change_meter(entry: Dictionary, delta: int) -> void:
	entry.meter = clampi(int(entry.meter) + delta, 0, 100)


static func change_rank(entry: Dictionary, delta: int) -> void:
	entry.rank = clampi(int(entry.rank) + delta, 0, entry.titles.size() - 1)


static func title(entry: Dictionary) -> String:
	return entry.titles[int(entry.rank)]


## Career menu action: ask the boss for a promotion. It works once performance reaches the rank's
## promote_at; asking early costs performance and the boss's goodwill. Returns the result line.
static func ask_promotion(state, slot: String, db: CareerDB) -> String:
	var entry: Dictionary = state.careers[slot]
	var rank: Dictionary = db.by_id[entry.id].ranks[int(entry.rank)]
	var boss: String = entry.coworkers.boss.name
	if not rank.has("promote_at"):
		return "There's nowhere higher to go here."
	if int(entry.performance) < rank.promote_at:
		change_performance(entry, -5)
		Coworkers.change(entry.coworkers, "boss", -5)
		state.change_stat("stress", 4)
		return "%s says you're not ready yet." % boss
	change_rank(entry, 1)
	entry.performance = AFTER_PROMOTION
	state.change_stat("happiness", 8)
	state.change_stat("stress", 3)
	return "%s promoted you to %s!" % [boss, title(entry)]


## The work crush becomes your partner. They stay your partner after the job ends.
static func date_crush(state, slot: String) -> void:
	var crush: Dictionary = state.careers[slot].coworkers.crush
	state.partner = {"name": crush.name, "affinity": maxi(int(crush.affinity), 50), "met": "work"}
	# the dating and partner card chains key off these flags, however the date started
	state.flags["work_%s_dating" % slot] = true
	state.flags["dating_work_partner"] = true
	state.flags.erase("work_%s_flirting" % slot)


## Pays each career, drifts performance, then fires or (gang) arrests.
## Returns {results, died, cause} like LifeRules.year_end.
static func year_end(state, db: CareerDB, rng: RandomNumberGenerator) -> Dictionary:
	var out := {"results": [], "died": false, "cause": ""}
	for slot in state.careers.keys():
		var entry: Dictionary = state.careers[slot]
		var career: Dictionary = db.by_id.get(entry.id, {})
		if career.is_empty():  # career removed from the data: drop it quietly
			leave(state, slot)
			continue
		_year(state, slot, entry, career, rng, out.results)
	return out


static func _year(state, slot, entry, career, rng, results: Array) -> void:
	var rank: Dictionary = career.ranks[int(entry.rank)]
	var pay := int(rank.pay)
	state.change_stat("money", pay)
	state.change_stat("stress", int(rank.stress))
	state.change_stat("career", 2 + 2 * int(entry.rank))
	if pay > 0:
		results.append("%s paid you $%d this year." % [rank.title, pay])
	elif pay < 0:
		results.append("%s cost you $%d this year." % [rank.title, -pay])
	entry.years = int(entry.years) + 1
	var skill := int((state.stats.career - 50) / 10.0)
	change_performance(entry, rng.randi_range(DRIFT[0], DRIFT[1]) + skill)

	if career.get("meter") == "heat":
		change_meter(entry, HEAT_PER_RANK * (int(entry.rank) + 1))
		if rng.randf() < entry.meter * ARREST_PER_HEAT:
			leave(state, slot, "juvie")  # a juvie card chain picks this flag up
			state.flags[RECORD] = true
			state.change_stat("karma", -10)
			state.change_stat("happiness", -15)
			results.append("The police picked you up. You're headed to juvie.")
			return
	if int(entry.performance) <= FIRE_AT:
		leave(state, slot, "fired")
		state.change_stat("happiness", -10)
		results.append("You were let go from %s." % career.label)


## Career menu: put in extra hours. Performance up, and it costs stress (GDD §6.6).
static func work_hard(state, slot: String) -> String:
	var entry: Dictionary = state.careers[slot]
	change_performance(entry, WORK_HARD.performance)
	state.change_stat("stress", WORK_HARD.stress)
	return "You put in the extra hours as %s." % title(entry)


## Staff actions open to a role (flirting is only with the crush).
static func staff_acts(role: String) -> Array:
	return STAFF.keys().filter(func(a): return a != "flirt" or role == "crush")


## Career menu: talk to, gift, argue with or flirt with a coworker. Returns the result line,
## or "" when the player can't afford it. Flirting with a crush who likes you enough starts dating.
static func staff(state, slot: String, role: String, act: String) -> String:
	var entry: Dictionary = state.careers[slot]
	var fx: Dictionary = STAFF[act]
	if state.stats.money < fx.get("cost", 0):
		return ""
	state.change_stat("money", -fx.get("cost", 0))
	state.change_stat("stress", fx.stress)
	Coworkers.change(entry.coworkers, role, fx.affinity)
	change_performance(entry, fx.get("performance", 0))
	var who: String = entry.coworkers[role].name
	if act == "flirt" and entry.coworkers.crush.affinity >= DATE_AT and state.partner.is_empty():
		date_crush(state, slot)
		state.change_stat("happiness", 10)
		return "%s said yes. You're going out!" % who
	return fx.line % who
