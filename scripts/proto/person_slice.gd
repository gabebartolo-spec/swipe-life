extends Node2D
## Vertical slice of modular people (docs/PEOPLE.md §10 step 1): three children in the bedroom at
## ~180 px/m, one top tinted three ways, waving. `-- --top=sweater` swaps the top;
## `--ages` lines up baby, child, teen and adult instead (one body each, ~130 px/m).
## `--sex=m` swaps in the male bodies.
## `--seq=<n> --out=<dir>` saves n frames at 24 fps and quits.

const PX_PER_M := 180.0
const AGES := ["baby", "child_f_skinny", "teen_f_skinny", "adult_f_skinny"]
const SKINS := ["f2c9a5", "c58c66", "7a4a32"]
const HAIRS := ["6b4430", "1e1a18", "d9a441"]
const TINTS := {
	"tee": [["d04040", "ffffff"], ["f2d04a", "1d2a4a"], ["1a1a1c", "ffffff"]],
	"sweater": [["3d6e4a", "f2ead8"], ["e07a9a", "ffffff"], ["1a1a1c", "8a8a8a"]],
}


func _ready() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		var kv := a.trim_prefix("--").split("=")
		args[kv[0]] = kv[1] if kv.size() > 1 else ""
	var top: String = args.get("top", "tee")
	var room := TextureRect.new()
	room.texture = load("res://assets/house/rooms/room_bedroom_child.png")
	room.size = Vector2(720, 600)
	room.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	room.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	add_child(room)
	var ages := args.has("ages")
	for n in 4 if ages else 3:
		var i := n % 3
		var p := Person.new()
		var t: Array = TINTS[top][i]
		p.look = {
			"body": [Color(SKINS[i])],
			"hair_back": [Color(HAIRS[i])],
			"hair_front": [Color(HAIRS[i])],
			top: [Color(t[0]), Color(t[1])],
			"trousers": [Color(["6f8fb5", "4a4a52", "8a6a4a"][i])],
		}
		p.position = Vector2(140 + 220 * i, 560)
		p.scale = Vector2.ONE * PX_PER_M / 264.8
		if ages:
			p.shape = AGES[n].replace("_f_", "_" + args.get("sex", "f") + "_")
			if n == 0:  # the baby wears a onesie and a wisp of hair
				p.look = {
					"body": [Color(SKINS[0])],
					"hair_front": [Color(HAIRS[0])],
					"onesie": [Color("f2e6a0")],
				}
			p.position = Vector2(100 + 170 * n, 580)
			p.scale = Vector2.ONE * 130.0 / 264.8
		add_child(p)
		p.play("res://assets/people/clips/wave.json")
	if args.has("seq"):
		DirAccess.make_dir_recursive_absolute(args.out)
		await get_tree().create_timer(0.3).timeout
		for f in int(args.seq):
			get_viewport().get_texture().get_image().save_png(args.out.path_join("f%03d.png" % f))
			await get_tree().create_timer(1.0 / 24.0).timeout
		get_tree().quit()
