class_name Family
extends RefCounted
## Partners, marriage, children and parents (GDD §6.3, §6.9). Each People action names what it does
## in its "do" key; everything here is plain data on GameState, so it saves as it is.

const DATE_CHANCE := 0.5
const EVENT_CHANCE := 0.2
const PROPOSE_AT := 50  # partner affinity a yes needs
const CAUGHT_CHANCE := 0.4
const LEAVES_BELOW := 10  # a partner this unhappy walks out at year end
const CHILD_COST := 4000  # a year, for each child under 18
const ADULT := 18
const PARENTS_FRAIL_FROM := 40  # player's age; parents' death chance rises from here
const PARENTS_CHANCE_STEP := 0.01
const TIME_APART := -3  # a partner's affinity each year on its own
const SKIN_NOISE := 0.03
const GREY_HAIR := "8a8a8a"
const AFFINITY := {"partner_talk": 8, "partner_gift": 12, "partner_argue": -15}
const CHILD_AFFINITY := {"child_time": 10, "child_gift": 12}


## True when this life can use an action with these needs.
static func meets(needs: Array, state) -> bool:
	for need: String in needs:
		var ok := true
		match need:
			"single":
				ok = state.partner.is_empty()
			"partner":
				ok = not state.partner.is_empty()
			"unmarried":
				ok = not state.partner.get("married", false)
			"married":
				ok = state.partner.get("married", false)
			"child":
				ok = not state.children.is_empty()
			"parents":
				ok = state.parents_alive
		if not ok:
			return false
	return true


## Applies an action's "do". Returns the line to show, or "" to show the action's own result.
static func act(what: String, state, rng: RandomNumberGenerator) -> String:
	if AFFINITY.has(what):
		state.partner.affinity = clampi(int(state.partner.affinity) + AFFINITY[what], 0, 100)
		return ""
	if CHILD_AFFINITY.has(what):
		for child: Dictionary in state.children:
			child.affinity = clampi(int(child.affinity) + CHILD_AFFINITY[what], 0, 100)
		return ""
	match what:
		"date":
			if rng.randf() < DATE_CHANCE:
				return _meet(state, "a date", rng)
		"event":
			if state.partner.is_empty() and rng.randf() < EVENT_CHANCE:
				return _meet(state, "a party", rng)
		"breakup":
			var ex: String = state.partner.name
			end_partner(state)
			return "You and %s are done. The group chat has picked sides." % ex
		"divorce":
			var ex: String = state.partner.name
			end_partner(state)
			return "Divorced from %s. The lawyers are delighted." % ex
		"propose":
			return _propose(state)
		"try_child":
			return _try_child(state, rng)
		"adopt":
			return _welcome(state, false, rng)
		"cheat":
			return _cheat(state, rng)
	return ""


## However a relationship ends: from the menu, a card or a walkout.
static func end_partner(state) -> void:
	state.partner = {}
	state.flags.erase("dating_work_partner")
	state.flags.erase("married")


static func child_age(child: Dictionary, state) -> int:
	return state.age - int(child.born_at)


## The year's family news; runs with the money at year end (Finance.year_end).
static func year_end(state, rng: RandomNumberGenerator, lines: Array) -> void:
	if not state.partner.is_empty():
		state.partner.affinity = clampi(int(state.partner.affinity) + TIME_APART, 0, 100)
		if int(state.partner.affinity) < LEAVES_BELOW:
			lines.append("%s left. They took the good pan." % state.partner.name)
			end_partner(state)
			state.change_stat("happiness", -10)
	var at_home := 0
	for child: Dictionary in state.children:
		if child_age(child, state) < ADULT:
			at_home += 1
	if at_home > 0:
		state.change_stat("money", -CHILD_COST * at_home)
		lines.append("Raising the kids: %s." % Finance.money_text(-CHILD_COST * at_home))
	var frail: int = state.age - PARENTS_FRAIL_FROM
	if state.parents_alive and frail >= 0 and rng.randf() < (frail + 1) * PARENTS_CHANCE_STEP:
		state.parents_alive = false
		state.change_stat("happiness", -15)
		state.change_stat("stress", 10)
		lines.append("Your parents have died. The house still smells of their cooking.")


## A child's look: skin between both parents' with a little of its own (GDD §10.7), hair from one.
static func blend_look(a: Dictionary, b: Dictionary, rng: RandomNumberGenerator) -> Dictionary:
	var look := Looks.random()
	var skin := Color(a.skin).lerp(Color(b.skin), rng.randf_range(0.3, 0.7))
	var noise := rng.randf_range(-SKIN_NOISE, SKIN_NOISE)
	skin = Color(skin.r + noise, skin.g + noise, skin.b + noise)
	look.skin = skin.to_html(false)
	look.hair_colour = a.hair_colour if rng.randf() < 0.5 else b.hair_colour
	return look


static func _meet(state, where: String, rng: RandomNumberGenerator) -> String:
	var who: String = Coworkers.NAMES[rng.randi() % Coworkers.NAMES.size()]
	state.partner = {"name": who, "affinity": 55, "met": "out", "look": Looks.random()}
	state.flags["dating_work_partner"] = true  # the one-partner gate on dating cards
	return "You met %s at %s. They laughed at the right bit." % [who, where]


static func _propose(state) -> String:
	if int(state.partner.affinity) < PROPOSE_AT:
		state.change_stat("happiness", -8)
		state.change_stat("relationships", -5)
		state.partner.affinity = maxi(0, int(state.partner.affinity) - 10)
		return "%s said no, in front of the waiter." % state.partner.name
	state.partner.married = true
	state.flags["married"] = true
	state.change_stat("happiness", 12)
	return "%s said yes. You are now legally each other's problem." % state.partner.name


static func _try_child(state, rng: RandomNumberGenerator) -> String:
	var over := maxi(0, state.age - 35)
	if rng.randf() >= 0.6 - over * 0.05:
		return "Not this year. The calendar app has stopped being subtle."
	return _welcome(state, true, rng)


## A new child. Born children blend both parents; adopted ones keep their own look.
static func _welcome(state, born: bool, rng: RandomNumberGenerator) -> String:
	var who: String = Coworkers.NAMES[rng.randi() % Coworkers.NAMES.size()]
	var look := Looks.random()
	if born:
		if not state.partner.has("look"):
			state.partner["look"] = Looks.random()
		if state.look.is_empty():
			state.look = Looks.random()
		look = blend_look(state.look, state.partner.look, rng)
	if look.hair_colour == GREY_HAIR:
		look.hair_colour = Looks.HAIR_COLOURS[0]  # nobody is born grey
	state.children.append(
		{"name": who, "born_at": state.age, "affinity": 70, "look": look, "adopted": not born}
	)
	state.flags["parent"] = true
	state.change_stat("happiness", 10)
	state.change_stat("stress", 10)
	return "Meet %s. Sleep was nice while it lasted." % who


static func _cheat(state, rng: RandomNumberGenerator) -> String:
	if rng.randf() >= CAUGHT_CHANCE:
		return "Nobody knows. You check your phone face down now."
	var ex: String = state.partner.name
	end_partner(state)
	state.change_stat("happiness", -12)
	state.change_stat("relationships", -10)
	return "%s found out. Your clothes are on the lawn." % ex
