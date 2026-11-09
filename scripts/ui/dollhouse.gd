class_name Dollhouse
extends ColorRect
## The home scene (GDD §10.2, §10.6): one prerendered clay room at a time. A card's `room` picks the
## room (default bedroom); the view slides across the house to it. At the parents' the bedroom
## changes with age band; a rental or a bought house shows that home's own rooms.

const ROOMS := {
	"bedroom": Vector2(0, 0),
	"bathroom": Vector2(1, 0),
	"living": Vector2(0, 1),
	"kitchen": Vector2(1, 1)
}
const PAN_TIME := 0.4
const FIGURE_SCALE := 0.00082  # of the scene height, per sprite pixel
const FIGURE_GAP := 0.24  # of the scene width, between figures
const ROOM_DIR := "res://assets/house/rooms"

var room := ""
var band := ""
var _view: TextureRect
var _tween: Tween
var _figures := Node2D.new()
var _figures_key := ""


func _ready() -> void:
	clip_contents = true
	resized.connect(_fit_views)
	_view = _make_view()
	add_child(_figures)


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
	if not ROOMS.has(room_id):
		room_id = "bedroom"
	var new_band := home_for(age, housing)
	if room_id == room and new_band == band:
		return
	var tex := load(texture_path(room_id, new_band)) as Texture2D
	if room == "" or room_id == room:  # first show or same room at a new age: no pan
		_view.texture = tex
	else:
		_pan_to(tex, ROOMS[room_id] - ROOMS[room])
	room = room_id
	band = new_band


## The player, and the partner beside them, standing in the room (GDD §10.2). Partners are any
## sex, whatever the player's; one gets a random look the first time they appear.
func show_people(age: int, look: Dictionary, partner: Dictionary) -> void:
	if look.is_empty():
		return
	if not partner.is_empty() and not partner.has("look"):
		partner["look"] = Looks.random()
	var key := "%s|%s|%s" % [Looks.shape_for(age, look.sex), look, partner.get("look")]
	if key == _figures_key:
		return
	_figures_key = key
	for f in _figures.get_children():
		f.queue_free()
	var people: Array[Person] = [Looks.make_person(look, age)]
	if not partner.is_empty():
		people.append(Looks.make_person(partner.look, age))
	var gap := FIGURE_GAP * size.x
	for i in people.size():
		people[i].scale = Vector2.ONE * size.y * FIGURE_SCALE
		var x := size.x / 2 + gap * (i - (people.size() - 1) / 2.0)
		people[i].position = Vector2(x, size.y * 0.95)
		_figures.add_child(people[i])


## Slides the old room out and the new one in along the iso direction between them on the 2x2
## plan: world +x reads as screen right-down, world +z as screen left-down.
func _pan_to(tex: Texture2D, step: Vector2) -> void:
	if _tween:
		_tween.kill()
		for v in get_children():
			if v is TextureRect and v != _view:
				v.queue_free()
	var dir := Vector2(step.x - step.y, (step.x + step.y) * 0.5).normalized() * size
	var old := _view
	_view = _make_view()
	_view.texture = tex
	_view.position = dir
	_tween = create_tween().set_parallel().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_property(old, "position", -dir, PAN_TIME)
	_tween.tween_property(_view, "position", Vector2.ZERO, PAN_TIME)
	_tween.chain().tween_callback(old.queue_free)


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
