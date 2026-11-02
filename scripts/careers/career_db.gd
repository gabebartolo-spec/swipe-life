class_name CareerDB
extends RefCounted
## Loads and validates careers (docs/CAREERS.md). A career is a ladder of ranks; regular jobs and
## special careers share the format, specials also track one meter (fame, heat or fitness).

const CAREER_DIR := "res://data/careers"
const KEYS := ["id", "label", "kind", "ages", "requires", "cost", "ranks", "meter"]
const RANK_KEYS := ["title", "pay", "stress", "promote_at"]
const KINDS := ["job", "special"]
const METERS := ["fame", "heat", "fitness"]
const STATS: Array = preload("res://scripts/autoload/game_state.gd").STATS

var careers: Array = []
var by_id := {}
var errors: PackedStringArray = []


func load_dir(dir: String = CAREER_DIR) -> void:
	for file in DirAccess.get_files_at(dir):
		if file.get_extension() == "json":
			load_file(dir.path_join(file))


func load_file(path: String) -> void:
	var data = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not data is Array:
		errors.append("%s: not a JSON array of careers" % path)
		return
	for i in data.size():
		var c = data[i]
		var where := "%s[%d]" % [path.get_file(), i]
		if not c is Dictionary:
			errors.append("%s: not an object" % where)
			continue
		var before := errors.size()
		check(c, where)
		if errors.size() == before:
			careers.append(c)
			by_id[c.id] = c


func check(c: Dictionary, where: String) -> void:
	for k in c:
		if k not in KEYS:
			errors.append("%s: unknown key '%s'" % [where, k])
	for k in ["id", "label", "kind", "ages", "ranks"]:
		if not c.has(k):
			errors.append("%s: missing '%s'" % [where, k])
	if c.has("id"):
		where = "%s (%s)" % [where, c.id]
		if by_id.has(c.id):
			errors.append("%s: duplicate id" % where)
	if c.get("kind") not in KINDS:
		errors.append("%s: 'kind' must be one of %s" % [where, KINDS])
	if c.has("meter") and c.meter not in METERS:
		errors.append("%s: 'meter' must be one of %s" % [where, METERS])
	var ages = c.get("ages")
	if not (ages is Array and ages.size() == 2 and 0 <= ages[0] and ages[0] <= ages[1]):
		errors.append("%s: 'ages' must be [min, max]" % where)
	if c.has("cost") and not (c.cost is float and c.cost >= 0):
		errors.append("%s: 'cost' must be a number >= 0" % where)
	for k in c.get("requires", {}):
		if k not in ["stats", "flags", "not_flags"]:
			errors.append("%s.requires: unknown key '%s'" % [where, k])
	for s in c.get("requires", {}).get("stats", {}):
		if s not in STATS:
			errors.append("%s.requires: unknown stat '%s'" % [where, s])
	var ranks = c.get("ranks")
	if not (ranks is Array and not ranks.is_empty()):
		errors.append("%s: 'ranks' must be a non-empty array" % where)
		return
	for r in ranks.size():
		_check_rank(ranks[r], "%s.ranks[%d]" % [where, r], r == ranks.size() - 1)


func _check_rank(r, where: String, last: bool) -> void:
	if not r is Dictionary:
		errors.append("%s: not an object" % where)
		return
	for k in r:
		if k not in RANK_KEYS:
			errors.append("%s: unknown key '%s'" % [where, k])
	for k in ["title", "pay", "stress"]:
		if not r.has(k):
			errors.append("%s: missing '%s'" % [where, k])
	if not r.get("stress", 0) > 0:
		errors.append("%s: every rank must add stress (GDD §6.6)" % where)
	if not last and not r.has("promote_at"):
		errors.append("%s: missing 'promote_at' (only the top rank has none)" % where)
	if last and r.has("promote_at"):
		errors.append("%s: the top rank can't have 'promote_at'" % where)


## Careers open to this player now: age, stat and flag gates. Cost is checked on apply.
func available(state) -> Array:
	return careers.filter(
		func(c):
			return (
				c.ages[0] <= state.age
				and state.age <= c.ages[1]
				and Deck.meets(c.get("requires", {}), state)
			)
	)
