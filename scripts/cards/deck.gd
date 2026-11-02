class_name Deck
extends RefCounted
## Draws cards by age, requirements and weight, and applies a chosen side (GDD §2–§3, §5.3b).

var cards: Array
var rng := RandomNumberGenerator.new()


func _init(card_list: Array, seed_value: int = -1) -> void:
	cards = card_list
	if seed_value >= 0:
		rng.seed = seed_value
	else:
		rng.randomize()


func eligible(state) -> Array:
	var out := []
	for c in cards:
		if c.get("once", true) and state.used.has(c.id):
			continue
		if state.age < c.ages[0] or state.age > c.ages[1]:
			continue
		if meets(c.get("requires", {}), state):
			out.append(c)
	return out


func draw(state):
	var pool := eligible(state)
	if pool.is_empty():
		return null
	var total := 0.0
	for c in pool:
		total += c.get("weight", 10.0)
	var roll := rng.randf() * total
	for c in pool:
		roll -= c.get("weight", 10.0)
		if roll <= 0.0:
			state.used[c.id] = true
			return personalise(c, state)
	state.used[pool[-1].id] = true
	return personalise(pool[-1], state)


## A copy of the card with {boss}, {rival}, {crush}, {friend}, {job} and {partner} filled in.
## A job card also records which career slot it is about in "slot".
static func personalise(card: Dictionary, state) -> Dictionary:
	var names := {}
	var slot := job_slot(card.get("requires", {}), state)
	if slot != "":
		var entry: Dictionary = state.careers[slot]
		for role in entry.coworkers:
			names[role] = entry.coworkers[role].name
		names["job"] = CareerRules.title(entry)
	if not state.partner.is_empty():
		names["partner"] = state.partner.name
	if names.is_empty():
		return card
	var c := card.duplicate(true)
	if slot != "":
		c["slot"] = slot
	c.text = c.text.format(names)
	for side in ["left", "right", "up"]:
		if c.has(side):
			c[side].label = c[side].label.format(names)
			if c[side].has("result"):
				c[side].result = c[side].result.format(names)
			if c[side].has("risk") and c[side].risk.has("result"):
				c[side].risk.result = c[side].risk.result.format(names)
	return c


## Applies the chosen side ("left", "right" or "up") to state.
## Returns {results: Array[String], died: bool, cause: String}.
func choose(card: Dictionary, side: String, state) -> Dictionary:
	var ch: Dictionary = card[side]
	var out := {"results": [], "died": false, "cause": ""}
	var slot: String = card.get("slot", job_slot(card.get("requires", {}), state))
	_apply(ch, state, slot)
	if ch.has("result"):
		out.results.append(ch.result)
	if ch.has("risk") and rng.randf() < ch.risk.chance:
		_apply(ch.risk, state, slot)
		if ch.risk.has("result"):
			out.results.append(ch.risk.result)
	if ch.has("death") and rng.randf() < ch.death.chance:
		out.died = true
		out.cause = ch.death.cause
	elif state.stats.health <= 0:  # GDD §5.3a
		out.died = true
		out.cause = "Your health gave out"
	return out


func _apply(ch: Dictionary, state, slot := "") -> void:
	for s in ch.get("effects", {}):
		state.change_stat(s, int(ch.effects[s]))
	for f in ch.get("set_flags", []):
		state.flags[f] = true
	for f in ch.get("clear_flags", []):
		state.flags.erase(f)
	if slot == "" or not state.careers.has(slot):
		return
	var entry: Dictionary = state.careers[slot]
	for role in ch.get("coworker", {}):
		Coworkers.change(entry.coworkers, role, int(ch.coworker[role]))
	var job: Dictionary = ch.get("job", {})
	CareerRules.change_performance(entry, int(job.get("performance", 0)))
	CareerRules.change_meter(entry, int(job.get("meter", 0)))
	CareerRules.change_rank(entry, int(job.get("rank", 0)))
	if job.get("date", false):
		CareerRules.date_crush(state, slot)
	if job.has("leave"):
		CareerRules.leave(state, slot, job.leave)


## The career slot a job card is about: requires.job names a career id, a slot ("job" /
## "special") or "any"; rank and coworker gates must pass in that slot. "" when none fits.
static func job_slot(req: Dictionary, state) -> String:
	if not req.has("job"):
		return ""
	for slot in state.careers:
		var entry: Dictionary = state.careers[slot]
		if req.job not in ["any", slot, entry.id]:
			continue
		var rank: Array = req.get("rank", [0, 99])
		if entry.rank < rank[0] or entry.rank > rank[1]:
			continue
		var ok := true
		for role in req.get("coworker", {}):
			var a: int = entry.coworkers[role].affinity
			ok = ok and req.coworker[role][0] <= a and a <= req.coworker[role][1]
		if ok:
			return slot
	return ""


## True when state passes a card's (or career's) "requires" block.
static func meets(req: Dictionary, state) -> bool:
	if req.has("job") and job_slot(req, state) == "":
		return false
	for s in req.get("stats", {}):
		var r: Array = req.stats[s]
		if state.stats[s] < r[0] or state.stats[s] > r[1]:
			return false
	for f in req.get("flags", []):
		if not state.flags.has(f):
			return false
	for f in req.get("not_flags", []):
		if state.flags.has(f):
			return false
	return true
