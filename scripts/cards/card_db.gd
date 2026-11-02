class_name CardDB
extends RefCounted
## Loads and validates card JSON files (schema: docs/CARD_SCHEMA.md).

const CARD_DIR := "res://data/cards"
const MAX_AGE := 17  # first playable ends at 18 (docs/ROADMAP.md)
const CARD_KEYS := [
	"id", "text", "ages", "weight", "requires", "left", "right", "up", "once", "room"
]
const CHOICE_KEYS := [
	"label",
	"effects",
	"set_flags",
	"clear_flags",
	"result",
	"risk",
	"death",
	"job",
	"coworker",
	"partner"
]
const REQUIRES_KEYS := ["stats", "flags", "not_flags", "job", "rank", "coworker"]
const JOB_KEYS := ["performance", "rank", "meter", "leave", "date"]  # docs/CAREERS.md
const ROLES := ["boss", "rival", "crush", "friend"]
const STATS: Array = preload("res://scripts/autoload/game_state.gd").STATS

var cards: Array = []
var errors: PackedStringArray = []


func load_dir(dir: String = CARD_DIR) -> void:
	var ids := {}
	for file in DirAccess.get_files_at(dir):
		if file.get_extension() == "json":
			load_file(dir.path_join(file), ids)


func load_file(path: String, ids: Dictionary = {}) -> void:
	var data = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not data is Array:
		errors.append("%s: not a JSON array of cards" % path)
		return
	for i in data.size():
		var where := "%s[%d]" % [path.get_file(), i]
		var card = data[i]
		if not card is Dictionary:
			errors.append("%s: not an object" % where)
			continue
		var before := errors.size()
		_check_card(card, where, ids)
		if errors.size() == before:
			cards.append(card)


func _check_card(c: Dictionary, where: String, ids: Dictionary) -> void:
	_unknown_keys(c, CARD_KEYS, where)
	for k in ["id", "text", "ages", "left", "right"]:
		if not c.has(k):
			errors.append("%s: missing '%s'" % [where, k])
	if c.has("id"):
		where = "%s (%s)" % [where, c.id]
		if ids.has(c.id):
			errors.append("%s: duplicate id, also in %s" % [where, ids[c.id]])
		ids[c.id] = where
	var ages = c.get("ages")
	if not (
		ages is Array
		and ages.size() == 2
		and 0 <= ages[0]
		and ages[0] <= ages[1]
		and ages[1] <= MAX_AGE
	):
		errors.append("%s: 'ages' must be [min, max] within 0-%d" % [where, MAX_AGE])
	if c.has("room") and not c.room in ["bedroom", "bathroom", "living", "kitchen"]:
		errors.append("%s: unknown room '%s'" % [where, c.room])
	if c.has("weight") and not (c.weight is float and c.weight > 0):
		errors.append("%s: 'weight' must be a positive number" % where)
	if c.has("requires"):
		_unknown_keys(c.requires, REQUIRES_KEYS, where + ".requires")
		for s in c.requires.get("stats", {}):
			_check_stat(s, where + ".requires")
		var rank = c.requires.get("rank", [0, 0])
		if not (rank is Array and rank.size() == 2 and 0 <= rank[0] and rank[0] <= rank[1]):
			errors.append("%s.requires: 'rank' must be [min, max]" % where)
		if c.requires.has("rank") and not c.requires.has("job"):
			errors.append("%s.requires: 'rank' needs 'job'" % where)
		for role in c.requires.get("coworker", {}):
			_check_role(role, where + ".requires.coworker")
		if c.requires.has("coworker") and not c.requires.has("job"):
			errors.append("%s.requires: 'coworker' needs 'job'" % where)
		var job_card: bool = c.requires.has("job")
		for side in ["left", "right", "up"]:
			var ch = c.get(side, {})
			if ch is Dictionary and (ch.has("job") or ch.has("coworker")) and not job_card:
				errors.append("%s.%s: job effects need requires.job" % [where, side])
	for side in ["left", "right", "up"]:
		if c.has(side):
			_check_choice(c[side], "%s.%s" % [where, side])


func _check_choice(ch, where: String) -> void:
	if not ch is Dictionary:
		errors.append("%s: not an object" % where)
		return
	_unknown_keys(ch, CHOICE_KEYS, where)
	if not ch.has("label"):
		errors.append("%s: missing 'label'" % where)
	for s in ch.get("effects", {}):
		_check_stat(s, where)
	if ch.has("risk"):
		_unknown_keys(ch.risk, ["chance", "effects", "result"], where + ".risk")
		_check_chance(ch.risk.get("chance"), where + ".risk")
		for s in ch.risk.get("effects", {}):
			_check_stat(s, where + ".risk")
	for k in ch.get("job", {}):
		if k not in JOB_KEYS:
			errors.append("%s.job: unknown key '%s'" % [where, k])
	if ch.has("partner") and ch.partner != "end":
		errors.append("%s: 'partner' must be \"end\"" % where)
	for role in ch.get("coworker", {}):
		_check_role(role, where + ".coworker")
	if ch.has("death"):
		_unknown_keys(ch.death, ["chance", "cause"], where + ".death")
		_check_chance(ch.death.get("chance"), where + ".death")
		if not ch.death.has("cause"):
			errors.append("%s.death: missing 'cause'" % where)


func _check_chance(v, where: String) -> void:
	if not (v is float and v >= 0.0 and v <= 1.0):
		errors.append("%s: 'chance' must be 0-1" % where)


func _check_role(role: String, where: String) -> void:
	if role not in ROLES:
		errors.append("%s: unknown coworker role '%s'" % [where, role])


func _check_stat(s: String, where: String) -> void:
	if s not in STATS:
		errors.append("%s: unknown stat '%s'" % [where, s])


func _unknown_keys(d: Dictionary, allowed: Array, where: String) -> void:
	for k in d:
		if k not in allowed:
			errors.append("%s: unknown key '%s'" % [where, k])
