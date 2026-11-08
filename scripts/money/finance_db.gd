class_name FinanceDB
extends RefCounted
## Loads houses and courses (GDD §12.2: data lives in JSON).

const HOUSES := "res://data/property/houses.json"
const COURSES := "res://data/courses/courses.json"
const HOUSE_KEYS := ["id", "label", "price", "min_age", "upkeep", "growth"]
const COURSE_KEYS := ["id", "label", "type", "years", "yearly", "flag"]

var houses: Array = []
var courses: Array = []
var errors: PackedStringArray = []


func load_all() -> void:
	houses = _load(HOUSES, HOUSE_KEYS)
	courses = _load(COURSES, COURSE_KEYS)


func _load(path: String, keys: Array) -> Array:
	var data = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not data is Array:
		errors.append("%s: not a JSON array" % path)
		return []
	var ids := {}
	for row in data:
		for k in keys:
			if not row.has(k):
				errors.append("%s: %s is missing '%s'" % [path, row.get("id", "?"), k])
		if ids.has(row.get("id")):
			errors.append("%s: duplicate id %s" % [path, row.get("id")])
		ids[row.get("id")] = true
	return data


## Courses open now: entry gates pass, and not already finished.
func courses_open(state) -> Array:
	return courses.filter(
		func(c): return not state.flags.has(c.flag) and Deck.meets(c.get("requires", {}), state)
	)
