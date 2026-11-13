class_name Dollhouse
extends ColorRect
## The home scene (GDD §10.2, §10.6): one prerendered clay room at a time. A card's `room` picks the
## room (default bedroom); the view slides across the house to it. At the parents' the bedroom
## changes with age band; a rental or a bought house shows that home's own rooms.

const ROOMS := {
	"bedroom": Vector2(0, 0),
	"bathroom": Vector2(1, 0),
	"living": Vector2(0, 1),
	"kitchen": Vector2(1, 1),
	"driveway": Vector2(2, 1),
}
const ADULT_ONLY := ["driveway"]  # the parents' house has no driveway still
const PAN_TIME := 0.4
const MAX_KIDS_SHOWN := 2  # a small room stays readable
const ROOM_DIR := "res://assets/house/rooms"

var room := ""
var band := ""
var _view: TextureRect
var _tween: Tween
var _stage := FigureStage.new()
var _people_key := ""
var _arrows: Array[Button] = []
var _browse := {}  # {age, housing} while the player may walk the house (between years)


func _ready() -> void:
	clip_contents = true
	resized.connect(_fit_views)
	add_child(_stage)
	move_child(_stage, 0)  # under AgeLabel
	_stage.size = size
	_view = _make_view()
	for i in 2:
		var b := Button.new()
		b.text = ["<", ">"][i]
		b.add_theme_font_size_override("font_size", 40)
		b.custom_minimum_size = Vector2(76, 76)
		b.pressed.connect(_step_room.bind(-1 if i == 0 else 1))
		b.hide()
		add_child(b)
		_arrows.append(b)
	_fit_views()


## Age band of the bedroom (director 2026-11-03): baby 0–3, child 4–12, teen 13–17.
static func band_for(age: int) -> String:
	if age <= 3:
		return "baby"
	return "child" if age <= 12 else "teen"


## Which set of room stills to show. The parents' home keeps the teen rooms past 18.
static func home_for(age: int, housing: Dictionary) -> String:
	match housing.get("kind", "parents"):
		"rent":
			return "rental"
		"own":
			return housing.get("house", "rental")
	return band_for(age)


static func texture_path(room_id: String, band_id: String) -> String:
	return ROOM_DIR.path_join("room_%s_%s.png" % [room_id, band_id])


func show_room(age: int, room_id: String = "bedroom", housing: Dictionary = {}) -> void:
	var new_band := home_for(age, housing)
	if not ROOMS.has(room_id) or (room_id in ADULT_ONLY and new_band in ["baby", "child", "teen"]):
		room_id = "bedroom"
	if room_id == room and new_band == band:
		return
	var tex := load(texture_path(room_id, new_band)) as Texture2D
	if room == "" or room_id == room:  # first show or same room at a new age: no pan
		_view.texture = tex
	else:
		_pan_to(tex, ROOMS[room_id] - ROOMS[room])
	room = room_id
	band = new_band
	_stage.set_room(room_id, new_band)


## The player, the partner if any and the children still at home, living in the room (GDD §10.2,
## §10.7). Partners are any sex, whatever the player's; one gets a random look on first showing.
func show_people(age: int, look: Dictionary, partner: Dictionary, children: Array = []) -> void:
	if look.is_empty():
		return
	if not partner.is_empty() and not partner.has("look"):
		partner["look"] = Looks.random()
	var kids := []
	for child: Dictionary in children:
		var child_age := age - int(child.born_at)
		if child_age < Family.ADULT and kids.size() < MAX_KIDS_SHOWN:
			kids.append([child.look, child_age])
	var key := "%s|%s|%s|%s" % [Looks.shape_for(age, look.sex), look, partner.get("look"), kids]
	if key == _people_key:
		return
	_people_key = key
	var people := [_person(look, age)]
	if not partner.is_empty():
		people.append(_person(partner.look, age))
	for kid: Array in kids:
		people.append(_person(kid[0], kid[1]))
	_stage.set_people(people)


## Bought items, [{id, room}] (GDD §10.2): clay props standing in their room's free floor.
func show_items(items: Array) -> void:
	_stage.set_items(items)


func _person(look: Dictionary, age: int) -> Dictionary:
	return {
		"shape": Looks.shape_for(age, look.sex), "look": Looks.figure_look(look, age), "age": age
	}


## Slides the old room out and the new one in along the iso direction between them on the 2x2
## plan: world +x reads as screen right-down, world +z as screen left-down.
func _pan_to(tex: Texture2D, step: Vector2) -> void:
	if _tween:
		_tween.kill()
		for v in get_children():
			if v is TextureRect and v != _view and v != _stage:
				v.queue_free()
	var dir := Vector2(step.x - step.y, (step.x + step.y) * 0.5).normalized() * size
	var old := _view
	_view = _make_view()
	_view.texture = tex
	_view.position = dir
	_tween = create_tween().set_parallel().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_property(old, "position", -dir, PAN_TIME)
	_tween.tween_property(_view, "position", Vector2.ZERO, PAN_TIME)
	_stage.hide()
	_tween.chain().tween_callback(old.queue_free)
	_tween.chain().tween_callback(_stage.show)


func _make_view() -> TextureRect:
	var v := TextureRect.new()
	v.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	v.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(v)
	move_child(v, 0)  # stay under AgeLabel
	v.size = size
	return v


func _fit_views() -> void:
	for v in get_children():
		if v is TextureRect:
			v.size = size
	for i in _arrows.size():
		var b := _arrows[i]
		b.position = Vector2(16 if i == 0 else size.x - 92, size.y - 92)


## Between years the player can walk the house room by room (GDD §15.5). Free; cards still pick
## their own room.
func set_browsing(on: bool, age := 0, housing: Dictionary = {}) -> void:
	_browse = {"age": age, "housing": housing} if on else {}
	for b in _arrows:
		b.visible = on


func _step_room(step: int) -> void:
	if _browse.is_empty():
		return
	var ids := ROOMS.keys()
	if band in ["baby", "child", "teen"]:
		ids = ids.filter(func(r): return r not in ADULT_ONLY)
	var i := (ids.find(room) + step + ids.size()) % ids.size()
	show_room(_browse.age, ids[i], _browse.housing)
