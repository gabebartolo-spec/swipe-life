class_name LifeRules
extends RefCounted
## Year-end rules (GDD §4.5, §5.3a, §5.3c): illness and old age. High Stress or low Joy can start
## a mental illness that is hard to shake: it stays until the stat recovers, then lifts only
## by chance. Tuning lives here.

const ONSET_MIN_AGE := 6
const ILLNESSES := {
	"anxiety":
	{
		"onset": ["stress", 70, 1],  # stat, threshold, direction (+1: at or above)
		"safe": ["stress", 40, -1],  # recovery is possible only below this
		"effects": {"stress": 5, "health": -1},
		"start": "You can't stop worrying. You have anxiety.",
		"end": "The worrying has eased. Your anxiety is gone.",
	},
	"depression":
	{
		"onset": ["happiness", 30, -1],
		"safe": ["happiness", 60, 1],
		"effects": {"happiness": -5, "health": -1},
		"start": "Everything feels grey. You have depression.",
		"end": "Colour is coming back. Your depression has lifted.",
	},
}
const ONSET_PER_POINT := 0.01  # +1% onset chance per point past threshold, from 10% at it
const RECOVERY_CHANCE := 0.15
# pocket money: [from age, $ a year], highest age first (GDD §4.3)
const POCKET_MONEY := [[10, 20], [6, 10]]
const POCKET_MONEY_UNTIL := 17
# Illness drains Health 1 a year (M13: was 3, which killed anyone who ignored Stress by their 40s).
# adult drift (GDD §6.9): Health a year, highest age first; Stress -2 a year; Joy toward 50.
const HEALTH_DRIFT := [[75, -3], [60, -2], [40, -1]]
const ADULT_FROM := 18
# old age death (GDD §5.3c): 2% at 70, +2% each year after. Placeholder until balance (M13).
const OLD_AGE_FROM := 70
const OLD_AGE_BASE := 0.02
const OLD_AGE_PER_YEAR := 0.02


static func _past(state, rule: Array) -> int:
	return (state.stats[rule[0]] - rule[1]) * rule[2]


static func _adult_drift(state) -> void:
	for band in HEALTH_DRIFT:
		if state.age >= band[0]:
			state.change_stat("health", band[1])
			break
	state.change_stat("stress", -2)
	state.change_stat("happiness", signi(50 - state.stats.happiness))


## Applies the year's illness rules. Returns {results, died, cause} like Deck.choose.
static func year_end(state, rng: RandomNumberGenerator) -> Dictionary:
	var out := {"results": [], "died": false, "cause": ""}
	for band in POCKET_MONEY:
		if state.age >= band[0] and state.age <= POCKET_MONEY_UNTIL:
			state.change_stat("money", band[1])
			break
	if state.age >= ADULT_FROM:
		_adult_drift(state)
	for id in ILLNESSES:
		var ill: Dictionary = ILLNESSES[id]
		if state.flags.has(id):
			for s in ill.effects:
				state.change_stat(s, ill.effects[s])
			if _past(state, ill.safe) > 0 and rng.randf() < RECOVERY_CHANCE:
				state.flags.erase(id)
				out.results.append(ill.end)
		elif state.age >= ONSET_MIN_AGE and _past(state, ill.onset) >= 0:
			if rng.randf() < 0.1 + _past(state, ill.onset) * ONSET_PER_POINT:
				state.flags[id] = true
				out.results.append(ill.start)
	if state.stats.health <= 0:
		out.died = true
		out.cause = "Your health gave out"
	elif state.age >= OLD_AGE_FROM:
		var years: int = state.age - OLD_AGE_FROM
		if rng.randf() < OLD_AGE_BASE + years * OLD_AGE_PER_YEAR:
			out.died = true
			out.cause = "You died peacefully of old age"
	return out
