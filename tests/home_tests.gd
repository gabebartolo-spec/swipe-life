class_name HomeTests
extends RefCounted
## Shop items and the home (GDD §6.1, §10.2, §15.5). Run from run_tests.gd.

const GameStateScript := preload("res://scripts/autoload/game_state.gd")

var _check: Callable


func _init(check: Callable) -> void:
	_check = check


## Shop items load, sell once, charge and apply effects, show in their room and survive a save.
func run() -> void:
	var shop := Items.new()
	shop.load_all()
	for e in shop.errors:
		printerr(e)
	_check.call(shop.errors.is_empty() and shop.items.size() >= 10, "items.json invalid")
	var state := GameStateScript.new()
	state.new_life()
	state.age = 30
	state.stats.money = 10000
	var sofa := shop.get_item("sofa")
	_check.call(shop.available(state).has(sofa), "sofa not on sale")
	var before: int = state.stats.happiness
	_check.call(shop.buy(state, sofa) != "", "sofa not bought")
	_check.call(state.stats.money == 10000 - int(sofa.price), "sofa price not charged")
	_check.call(state.stats.happiness > before, "sofa effects not applied")
	_check.call(shop.buy(state, sofa) == "", "sofa bought twice")
	_check.call(not shop.available(state).has(sofa), "owned sofa still on sale")
	_check.call(
		shop.items_for(state) == [{"id": "sofa", "room": "living", "slot": "sofa"}],
		"item not in room"
	)
	var copy := GameStateScript.new()
	copy.new_life()
	copy.from_dict(JSON.parse_string(JSON.stringify(state.to_dict())))
	_check.call(copy.items == ["sofa"], "items lost in save")
	state.stats.money = 10000  # slots (GDD §15.5): a new sofa takes over; swap back for free
	shop.buy(state, shop.get_item("sofa_leather"))
	var swaps: Array = shop.swappable(state).get("sofa", [])
	shop.place(state, sofa)
	shop.buy(state, shop.get_item("cat"))
	copy.from_dict(JSON.parse_string(JSON.stringify(state.to_dict())))
	var ok: bool = swaps.size() == 2 and copy.home_slots.sofa == "sofa"
	_check.call(ok and shop.items_for(state).size() == 2, "sofa slot swap or pet failed")
	state.free()
	copy.free()
	var poor := GameStateScript.new()
	poor.new_life()
	poor.age = 30
	poor.stats.money = 5
	_check.call(shop.buy(poor, sofa) == "", "bought without money")
	poor.free()
