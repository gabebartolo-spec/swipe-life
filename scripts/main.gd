extends VBoxContainer
## Screen layout (GDD §10.5): dollhouse ~45% on top, stat strip, card in the bottom half.


func _ready() -> void:
	if not SaveSystem.load_life():
		GameState.new_life()
	print("Swipe Life started, age %d" % GameState.age)
