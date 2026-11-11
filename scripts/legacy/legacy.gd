class_name Legacy
extends RefCounted
## Legacy (GDD §9.3): after death, play on as your child. The heir gets the money less a tax, the
## house and its items, part of the parent's Looks, Smarts and Health, and the family: siblings
## and the other parent. Balance comes in M13; the numbers here are placeholders.

const TAX := 0.4  # share of the estate the state takes
const HEIR_FROM := 18  # a child younger than this can't take over
const INHERITED := ["looks", "smarts", "health"]  # pulled halfway toward the parent's value


## The child who carries on: the oldest grown-up one, {} when there is none.
static func heir(state) -> Dictionary:
	var best := {}
	for child: Dictionary in state.children:
		if Family.child_age(child, state) < HEIR_FROM:
			continue
		if best.is_empty() or child.born_at < best.born_at:
			best = child
	return best


## Money left for the heir: cash, savings and investments less every debt, less the tax.
static func estate(state) -> int:
	var net: int = (
		int(state.stats.money) + state.savings + state.investments - Finance.total_debt(state)
	)
	return int(maxf(0.0, net) * (1.0 - TAX))


## Rebuilds `state` as the heir's life. Returns the heir's name ("" when there is none).
static func continue_as_heir(state) -> String:
	var child := heir(state)
	if child.is_empty():
		return ""
	var old_stats: Dictionary = state.stats.duplicate()
	var cash := estate(state)
	var home: Dictionary = state.housing.duplicate() if state.housing.kind == "own" else {}
	var items: Array = state.items.duplicate()
	var siblings := []
	for other: Dictionary in state.children:
		if other != child:
			siblings.append({"name": other.name, "look": other.look})
	var other_parent_alive: bool = not state.partner.is_empty()
	var generation: int = int(state.flags.get("generation", 1)) + 1
	var heir_age := Family.child_age(child, state)
	var name: String = child.name
	var look: Dictionary = child.look
	state.new_life()
	state.age = heir_age
	state.look = look
	state.flags["generation"] = generation
	state.flags["heir"] = true
	state.stats.money = cash
	# GDD §15.11: fame outlives you; the family name carries half of it, and a quarter of the shame.
	state.stats.fame = int(old_stats.get("fame", 0) / 2.0)
	state.stats.infamy = int(old_stats.get("infamy", 0) / 4.0)
	state.flags["family_fame"] = int(old_stats.get("fame", 0))
	for s in INHERITED:
		state.stats[s] = int((50 + old_stats[s]) / 2.0)
	if not home.is_empty():
		home.erase("mortgage")
		state.housing = home
		state.flags["moved_out"] = true
	state.items = items
	state.siblings = siblings
	state.parents_alive = other_parent_alive
	return name
