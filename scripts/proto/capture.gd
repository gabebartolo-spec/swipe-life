extends Node
## Saves a screenshot and quits when the game is run with `-- --capture=<path.png>`.

const WAIT_FRAMES := 20


func _ready() -> void:
	var path := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--capture="):
			path = arg.trim_prefix("--capture=")
	if path.is_empty():
		return
	for i in WAIT_FRAMES:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path)
	get_tree().quit()
