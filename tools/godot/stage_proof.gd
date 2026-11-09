extends SceneTree
## Real Dollhouse with people living in it; saves a frame every 2 s.
## Run: godot --path . --windowed --resolution 1080x900 -s tools/godot/stage_proof.gd --
##      <out_dir> <room> <age> <partner 0/1> <housing rent|parents|mansion...> <frames> [sex] [hair]


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	DirAccess.make_dir_recursive_absolute(a[0])
	var house := Dollhouse.new()
	house.color = Color(0.96, 0.97, 0.99)
	root.add_child(house)
	house.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	await process_frame
	var age := int(a[2])
	var housing := {"kind": "parents"}
	if a[4] == "rent":
		housing = {"kind": "rent"}
	elif a[4] != "parents":
		housing = {"kind": "own", "house": a[4]}
	var look := Looks.random()
	look.sex = a[6] if a.size() > 6 else "f"
	look.hair = a[7] if a.size() > 7 else "long_wavy"
	look.top = "tee"
	var partner := {}
	if a[3] == "1":
		partner = {"look": Looks.random()}
		partner.look.sex = look.sex
		partner.look.hair = look.hair
	house.show_room(age, a[1], housing)
	var kids := []
	if a.size() > 8:  # your age when each child arrived, comma separated
		for born: String in a[8].split(","):
			var kid := Looks.random()
			kids.append({"look": kid, "born_at": int(born)})
	house.show_people(age, look, partner, kids)
	for i in int(a[5]):
		await create_timer(2.0).timeout
		root.get_texture().get_image().save_png("%s/f%02d.png" % [a[0], i])
	quit()
