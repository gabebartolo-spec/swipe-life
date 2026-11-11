class_name Items
extends RefCounted
## Shop items (GDD §6.1, §10.2): bought once, kept for the life, and shown in their room of the
## home scene. Data in data/property/items.json.

const ITEM_FILE := "res://data/property/items.json"
const KEYS := ["id", "label", "room", "price", "min_age", "effects"]
const OPTIONAL := ["slot", "pet"]  # slot: items sharing one fill it in turn (GDD §15.5)
const ROOMS := ["bedroom", "bathroom", "living", "kitchen"]
const STATS: Array = preload("res://scripts/autoload/game_state.gd").STATS

var items: Array = []
var errors: PackedStringArray = []


func load_all(path: String = ITEM_FILE) -> void:
	var data = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not data is Array:
		errors.append("%s: not a JSON array" % path)
		return
	var ids := {}
	for i in data.size():
		var it = data[i]
		var where := "items[%d]" % i
		if not it is Dictionary:
			errors.append("%s: not an object" % where)
			continue
		var before := errors.size()
		_check(it, where, ids)
		if errors.size() == before:
			items.append(it)


func _check(it: Dictionary, where: String, ids: Dictionary) -> void:
	for k in it:
		if k not in KEYS and k not in OPTIONAL:
			errors.append("%s: unknown key '%s'" % [where, k])
	for k in KEYS:
		if not it.has(k):
			errors.append("%s: missing '%s'" % [where, k])
	if it.has("id") and ids.has(it.id):
		errors.append("%s: duplicate id" % where)
	if it.has("id"):
		ids[it.id] = true
	if it.get("room") not in ROOMS:
		errors.append("%s: 'room' must be one of %s" % [where, ROOMS])
	if not (it.get("price") is float and it.price > 0):
		errors.append("%s: 'price' must be a number > 0" % where)
	for s in it.get("effects", {}):
		if s not in STATS:
			errors.append("%s: unknown stat '%s'" % [where, s])


func get_item(id: String) -> Dictionary:
	for it in items:
		if it.id == id:
			return it
	return {}


## Items the player is old enough for and does not own yet.
func available(state) -> Array:
	return items.filter(func(it): return state.age >= int(it.min_age) and it.id not in state.items)


## Owned item ids that live in a room.
func owned_in(state, room: String) -> Array:
	var out := []
	for id: String in state.items:
		var it := get_item(id)
		if not it.is_empty() and it.room == room:
			out.append(it)
	return out


static func slot_of(it: Dictionary) -> String:
	return it.get("slot", it.id)


## The owned item filling each slot: the player's pick, else the newest bought (GDD §15.5).
func shown(state) -> Array:
	var by_slot := {}
	for id: String in state.items:
		var it := get_item(id)
		if not it.is_empty():
			by_slot[slot_of(it)] = it
	for slot: String in state.home_slots:
		var pick := get_item(state.home_slots[slot])
		if by_slot.has(slot) and not pick.is_empty() and pick.id in state.items:
			by_slot[slot] = pick
	return by_slot.values()


## Slots where the player owns more than one item to choose from: {slot: [items]}.
func swappable(state) -> Dictionary:
	var out := {}
	for id: String in state.items:
		var it := get_item(id)
		if not it.is_empty():
			out.get_or_add(slot_of(it), []).append(it)
	for slot in out.keys():
		if out[slot].size() < 2:
			out.erase(slot)
	return out


## Puts an owned item in its slot. Free: it is arranging, not doing (GDD §6.5).
func place(state, it: Dictionary) -> String:
	state.home_slots[slot_of(it)] = it.id
	return "The %s goes back in." % it.label.to_lower()


## Shown items as [{id, room}] for the home scene.
func items_for(state) -> Array:
	return shown(state).map(func(it): return {"id": it.id, "room": it.room, "slot": slot_of(it)})


func can_buy(state, it: Dictionary) -> bool:
	return state.stats.money >= int(it.price) and it.id not in state.items


## Pays, applies the effects, and returns the line to show ("" when it can't be bought).
func buy(state, it: Dictionary) -> String:
	if not can_buy(state, it):
		return ""
	state.change_stat("money", -int(it.price))
	for s in it.effects:
		state.change_stat(s, int(it.effects[s]))
	state.items.append(it.id)
	state.home_slots[slot_of(it)] = it.id
	if it.get("pet", false):
		return "You bring home the %s. It already owns the place." % it.label.to_lower()
	return "You buy the %s. It looks right at home." % it.label.to_lower()
