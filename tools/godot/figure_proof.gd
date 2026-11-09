extends SceneTree
## Figure in a room still, same camera and light as tools/godot/render_house.gd.
## Run: godot --path . --resolution 1080x900 -s tools/godot/figure_proof.gd --
##      <out_dir> <still> <room_x> <room_z> <shape> <clip=x,z,yaw_deg[,y]> ...


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	var out: String = a[0]
	DirAccess.make_dir_recursive_absolute(out)
	var bg := TextureRect.new()
	bg.texture = load(a[1])
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var layer := CanvasLayer.new()
	layer.layer = -1
	root.add_child(layer)
	layer.add_child(bg)
	var c := Vector2(float(a[2]), float(a[3]))
	var w := Node3D.new()
	root.add_child(w)
	var env := Environment.new()
	env.background_mode = Environment.BG_CANVAS
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(1, 0.96, 0.92)
	env.ambient_light_energy = 0.35
	env.tonemap_mode = 2
	var we := WorldEnvironment.new()
	we.environment = env
	w.add_child(we)
	var sun := DirectionalLight3D.new()
	sun.light_color = Color(1, 0.95, 0.88)
	sun.light_energy = 0.75
	w.add_child(sun)
	sun.look_at_from_position(Vector3(14, 16, 10), Vector3(4, 0, 4))
	var cam := Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = 5.6
	var basis := Basis(
		Vector3(0.707107, 0, -0.707107),
		Vector3(-0.408248, 0.816497, -0.408248),
		Vector3(0.57735, 0.57735, 0.57735)
	)
	cam.transform = Transform3D(basis, Vector3(c.x, 1.0, c.y) + basis.z * 20.0)
	w.add_child(cam)
	var look := {
		"hair": "long_wavy",
		"body": [Color("e0ac84")],
		"hair_back": [Color("6b4430")],
		"hair_front": [Color("6b4430")],
		"tee": [Color("d04040"), Color("ffffff")],
		"trousers": [Color("4a4a52")],
	}
	var i := 0
	for spec: String in a.slice(5):
		var kv := spec.split("=")
		var v := kv[1].split(",")
		var f := Figure3D.new()
		w.add_child(f)
		f.build(a[4], look)
		f.position = Vector3(float(v[0]), float(v[3]) if v.size() > 3 else 0.0, float(v[1]))
		f.rotation_degrees.y = float(v[2])
		f.play(kv[0])
		f.set_process(false)
		for j in 3:
			f.advance(0.4)
			for k in 3:
				await process_frame
			root.get_texture().get_image().save_png("%s/%d_%s_%d.png" % [out, i, kv[0], j])
		f.visible = false
		i += 1
	quit()
