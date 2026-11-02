extends Node
## Autosave once per year, when the between-year menu closes (GDD §8.3). One slot, no manual saves.

const PATH := "user://life.json"


func save() -> void:
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	f.store_string(JSON.stringify(GameState.to_dict()))


func has_save() -> bool:
	return FileAccess.file_exists(PATH)


func load_life() -> bool:
	if not has_save():
		return false
	var d = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if not d is Dictionary:
		return false
	GameState.from_dict(d)
	return true


func clear() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path(PATH))
