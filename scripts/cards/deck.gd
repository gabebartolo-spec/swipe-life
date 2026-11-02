class_name Deck
extends RefCounted
## Draws cards by age, requirements and weight, and applies a chosen side (GDD §2–§3, §5.3b).

var cards: Array
var used := {}  # ids drawn this life ("once" cards never repeat)
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
		if c.get("once", true) and used.has(c.id):
			continue
		if state.age < c.ages[0] or state.age > c.ages[1]:
			continue
		if _meets(c.get("requires", {}), state):
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
			used[c.id] = true
			return c
	used[pool[-1].id] = true
	return pool[-1]


## Applies the chosen side ("left", "right" or "up") to state.
## Returns {results: Array[String], died: bool, cause: String}.
func choose(card: Dictionary, side: String, state) -> Dictionary:
	var ch: Dictionary = card[side]
	var out := {"results": [], "died": false, "cause": ""}
	_apply(ch, state)
	if ch.has("result"):
		out.results.append(ch.result)
	if ch.has("risk") and rng.randf() < ch.risk.chance:
		_apply(ch.risk, state)
		if ch.risk.has("result"):
			out.results.append(ch.risk.result)
	if ch.has("death") and rng.randf() < ch.death.chance:
		out.died = true
		out.cause = ch.death.cause
	return out


func _apply(ch: Dictionary, state) -> void:
	for s in ch.get("effects", {}):
		state.change_stat(s, int(ch.effects[s]))
	for f in ch.get("set_flags", []):
		state.flags[f] = true
	for f in ch.get("clear_flags", []):
		state.flags.erase(f)


func _meets(req: Dictionary, state) -> bool:
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
