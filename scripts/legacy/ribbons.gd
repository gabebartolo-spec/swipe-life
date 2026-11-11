class_name Ribbons
extends RefCounted
## Ribbons (GDD §9.1): earned at the end of a life from what that life was. The profile outlives
## lives and lists every ribbon ever earned; each ribbon may name content it unlocks (§9.2).
## Data in data/ribbons/ribbons.json.

const RIBBON_FILE := "res://data/ribbons/ribbons.json"
const PROFILE_PATH := "user://profile.json"
const KEYS := ["id", "label", "text", "when", "unlocks"]
const CONDITIONS := [
	"age_min",
	"age_max",
	"stat",
	"min",
	"max",
	"owns_home",
	"children_min",
	"partnered",
	"generation_min"
]
const UNLOCK_KINDS := ["career", "cards"]
const STATS: Array = preload("res://scripts/autoload/game_state.gd").STATS

var ribbons: Array = []
var errors: PackedStringArray = []


func load_all(path: String = RIBBON_FILE) -> void:
	var data = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not data is Array:
		errors.append("%s: not a JSON array" % path)
		return
	var ids := {}
	for i in data.size():
		var r = data[i]
		var where := "ribbons[%d]" % i
		if not r is Dictionary:
			errors.append("%s: not an object" % where)
			continue
		var before := errors.size()
		for k in r:
			if k not in KEYS:
				errors.append("%s: unknown key '%s'" % [where, k])
		for k in KEYS:
			if not r.has(k):
				errors.append("%s: missing '%s'" % [where, k])
		if r.has("id"):
			if ids.has(r.id):
				errors.append("%s: duplicate id" % where)
			ids[r.id] = true
		for u in r.get("unlocks", []):
			var parts: PackedStringArray = str(u).split(":")
			if parts.size() != 2 or parts[0] not in UNLOCK_KINDS:
				errors.append("%s: unlock '%s' must be career:<id> or cards:<set>" % [where, u])
		var when: Dictionary = r.get("when", {})
		for c in when:
			if c not in CONDITIONS:
				errors.append("%s: unknown condition '%s'" % [where, c])
		if when.has("stat") and when.stat not in STATS:
			errors.append("%s: unknown stat '%s'" % [where, when.stat])
		if when.is_empty():
			errors.append("%s: a ribbon needs a condition" % where)
		if errors.size() == before:
			ribbons.append(r)


## True when the finished life in `state` meets every condition of `when`.
static func meets(when: Dictionary, state) -> bool:
	if state.age < int(when.get("age_min", 0)) or state.age > int(when.get("age_max", 1000)):
		return false
	if when.has("stat"):
		var v: int = state.stats[when.stat]
		if v < int(when.get("min", -2147483648)) or v > int(when.get("max", 2147483647)):
			return false
	if when.get("owns_home", false) and state.housing.kind != "own":
		return false
	if state.children.size() < int(when.get("children_min", 0)):
		return false
	if when.get("partnered", false) and state.partner.is_empty():
		return false
	return int(state.flags.get("generation", 1)) >= int(when.get("generation_min", 0))


## The ribbons this life earned, whether or not they are new.
func earned(state) -> Array:
	return ribbons.filter(func(r): return meets(r.when, state))


## Writes the ribbons to the profile; returns the ones never earned before.
func record(state, path: String = PROFILE_PATH) -> Array:
	var profile := load_profile(path)
	var fresh := []
	for r in earned(state):
		if r.id not in profile.ribbons:
			profile.ribbons.append(r.id)
			fresh.append(r)
	profile.lives = int(profile.lives) + 1
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(profile))
	return fresh


static func load_profile(path: String = PROFILE_PATH) -> Dictionary:
	var out := {"ribbons": [], "lives": 0}
	if not FileAccess.file_exists(path):
		return out
	var d = JSON.parse_string(FileAccess.get_file_as_string(path))
	if d is Dictionary:
		out.ribbons = d.get("ribbons", [])
		out.lives = int(d.get("lives", 0))
	return out


## Every content name any ribbon unlocks, earned or not.
func all_unlocks() -> Array:
	var out := []
	for r in ribbons:
		out.append_array(r.unlocks)
	return out


## Content names unlocked by the ribbons in the profile (e.g. "career:pilot").
func unlocked(path: String = PROFILE_PATH) -> Array:
	var out := []
	var have: Array = load_profile(path).ribbons
	for r in ribbons:
		if r.id in have:
			out.append_array(r.unlocks)
	return out
