class_name ActionDB
extends RefCounted
## Loads and validates the between-year actions (GDD §6). Tabs unlock by age (§6.7); every action
## changes Stress (§6.6): effort adds it (its time cost), fun and rest lower it. Money is the only
## other limit (§6.5).

const ACTION_DIR := "res://data/actions"
const TABS := {"activities": 5, "people": 10, "jobs": 14, "shop": 18, "money": 18}  # §6.7
const TAB_NAMES := {
	"activities": "Activities",
	"people": "People",
	"jobs": "Career",
	"shop": "Shop",
	"money": "Money",
}
const KEYS := ["id", "tab", "label", "ages", "cost", "effects", "result"]
const STATS: Array = preload("res://scripts/autoload/game_state.gd").STATS

var actions: Array = []
var errors: PackedStringArray = []


func load_dir(dir: String = ACTION_DIR) -> void:
	var ids := {}
	for file in DirAccess.get_files_at(dir):
		if file.get_extension() == "json":
			load_file(dir.path_join(file), ids)


func load_file(path: String, ids: Dictionary = {}) -> void:
	var data = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not data is Array:
		errors.append("%s: not a JSON array of actions" % path)
		return
	for i in data.size():
		var a = data[i]
		var where := "%s[%d]" % [path.get_file(), i]
		if not a is Dictionary:
			errors.append("%s: not an object" % where)
			continue
		var before := errors.size()
		_check(a, where, ids)
		if errors.size() == before:
			actions.append(a)


func _check(a: Dictionary, where: String, ids: Dictionary) -> void:
	for k in a:
		if k not in KEYS:
			errors.append("%s: unknown key '%s'" % [where, k])
	for k in ["id", "tab", "label", "ages", "effects"]:
		if not a.has(k):
			errors.append("%s: missing '%s'" % [where, k])
	if a.has("id"):
		where = "%s (%s)" % [where, a.id]
		if ids.has(a.id):
			errors.append("%s: duplicate id" % where)
		ids[a.id] = true
	if not TABS.has(a.get("tab")):
		errors.append("%s: 'tab' must be one of %s" % [where, TABS.keys()])
	var ages = a.get("ages")
	if not (ages is Array and ages.size() == 2 and 0 <= ages[0] and ages[0] <= ages[1]):
		errors.append("%s: 'ages' must be [min, max]" % where)
	elif TABS.has(a.get("tab")) and ages[0] < TABS[a.tab]:
		errors.append("%s: starts before its tab unlocks at %d" % [where, TABS[a.tab]])
	if a.has("cost") and not (a.cost is float and a.cost >= 0):
		errors.append("%s: 'cost' must be a number >= 0" % where)
	var fx = a.get("effects", {})
	for s in fx:
		if s not in STATS:
			errors.append("%s: unknown stat '%s'" % [where, s])
	if fx.get("stress", 0) == 0:
		errors.append("%s: every action must change stress (GDD §6.6)" % where)


## Tabs open at this age, in menu order.
static func tabs_at(age: int) -> Array:
	return TABS.keys().filter(func(t): return age >= TABS[t])


func available(tab: String, age: int) -> Array:
	return actions.filter(func(a): return a.tab == tab and a.ages[0] <= age and age <= a.ages[1])


## Pays and applies the action. Returns false when the player can't afford it.
static func perform(a: Dictionary, state) -> bool:
	var cost := int(a.get("cost", 0))
	if state.stats.money < cost:
		return false
	state.change_stat("money", -cost)
	for s in a.effects:
		state.change_stat(s, int(a.effects[s]))
	return true
