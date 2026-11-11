extends Node
## Saves a frame every 1/12 s to `--frames=<dir>` for `--frames_for=<s>` seconds, then quits.

var dir := ""
var duration := 8.0
var t := 0.0
var n := 0


func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--frames="):
			dir = arg.trim_prefix("--frames=")
		elif arg.begins_with("--frames_for="):
			duration = float(arg.trim_prefix("--frames_for="))
	if dir.is_empty():
		queue_free()


func _process(delta: float) -> void:
	t += delta
	if t < n / 12.0:
		return
	get_viewport().get_texture().get_image().save_png("%s/f%04d.png" % [dir, n])
	n += 1
	if t > duration:
		get_tree().quit()
