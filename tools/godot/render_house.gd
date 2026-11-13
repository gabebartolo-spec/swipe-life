extends SceneTree
## Renders assets/house/house.glb with the approved clay look (scenes/proto/clay_room_baked.tscn)
## to one PNG per age band, each with every activity layer shown.
## Run: godot --path . --resolution 1080x900 -s tools/godot/render_house.gd -- <out_dir>
## An adult home: ... -- <out_dir> res://assets/house/homes/<home>.glb <home>
## Depth maps instead of stills: add "depth" as the last argument ("" as home for the age bands).
## Stills sit in the home's setting (GDD 10.9): build it first with
## tools/blender/build_clay_setting.py -- <kind> assets/house/homes/setting_<kind>.glb
## (render-only, never committed). Depth maps leave it out.

const CLAY := preload("res://shaders/clay.gdshader")
const DEPTH := preload("res://shaders/room_depth_bake.gdshader")
const GLOWS := {"fairy": 1.2, "lamp_glow": 1.0, "glow_screen": 0.5}
const BANDS := ["baby", "child", "teen"]
## One room at a time (GDD 10.6): room centre on the floor plan.
const ROOMS := {
	"bedroom": Vector2(2, 2),
	"bathroom": Vector2(6, 2),
	"living": Vector2(2, 6),
	"kitchen": Vector2(6, 6),
	"driveway": Vector2(10, 6),
}
const ROOM_SIZE := 5.6
## Each home's setting (GDD 10.9); the childhood home's age bands sit on the family house's street.
const SETTINGS := {
	"": "suburb",
	"family_house": "suburb",
	"starter_house": "new_suburb",
	"small_flat": "flats",
	"rental": "lowrise",
	"fixer_upper": "tired_street",
	"town_house": "terrace",
	"seaside_villa": "beach",
	"mansion": "grounds",
}

var _house: Node3D
var _cam: Camera3D
var _warm := false
var _bands: Array = BANDS
var _depth := false
var _setting: Node3D


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var out: String = args[0]
	var glb: String = args[1] if args.size() > 1 else "res://assets/house/house.glb"
	if args.size() > 2 and args[2] != "":
		_bands = [args[2]]
	_depth = args.size() > 3 and args[3] == "depth"
	root.use_hdr_2d = _depth
	var root3d := Node3D.new()
	root.add_child(root3d)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.85, 0.86, 0.9)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(1, 0.96, 0.92)
	env.ambient_light_energy = 0.35
	env.tonemap_mode = 2
	if _depth:
		env.tonemap_mode = 0
		env.background_color = Color.BLACK
	var we := WorldEnvironment.new()
	we.environment = env
	root3d.add_child(we)
	var sun := DirectionalLight3D.new()
	sun.light_color = Color(1, 0.95, 0.88)
	sun.light_energy = 0.75
	sun.shadow_enabled = true
	sun.shadow_blur = 2.0
	root3d.add_child(sun)
	sun.look_at_from_position(Vector3(14, 16, 10), Vector3(4, 0, 4))
	for z: float in [1.6, 6.2]:
		var glow := OmniLight3D.new()
		glow.light_color = Color(1, 0.85, 0.6)
		glow.light_energy = 0.7
		glow.omni_range = 4.5
		glow.position = Vector3(1, 2.4, z)
		root3d.add_child(glow)
	_cam = Camera3D.new()
	var cam := _cam
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = ROOM_SIZE
	var basis := Basis(
		Vector3(0.707107, 0, -0.707107),
		Vector3(-0.408248, 0.816497, -0.408248),
		Vector3(0.57735, 0.57735, 0.57735)
	)
	cam.transform = Transform3D(basis, Vector3(4, 0.9, 4) + basis.z * 20.0)
	root3d.add_child(cam)
	root.msaa_3d = Viewport.MSAA_4X
	_house = (load(glb) as PackedScene).instantiate()
	root3d.add_child(_house)
	if not _depth:
		var home: String = args[2] if args.size() > 2 and args[2] not in BANDS else ""
		var path := "res://assets/house/homes/setting_%s.glb" % SETTINGS[home]
		assert(ResourceLoader.exists(path), "build the setting first: " + path)
		_setting = (load(path) as PackedScene).instantiate()
		root3d.add_child(_setting)
	var meshes := _house.find_children("*", "MeshInstance3D", true, false)
	if _setting:
		meshes += _setting.find_children("*", "MeshInstance3D", true, false)
	for mi: MeshInstance3D in meshes:
		if String(mi.name).contains("sky"):  # the backdrop keeps its own colours, unlit
			var sky := StandardMaterial3D.new()
			sky.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			sky.vertex_color_use_as_albedo = true
			sky.cull_mode = BaseMaterial3D.CULL_DISABLED
			mi.material_override = sky
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			continue
		if _depth:
			if "_glass" in String(mi.name):
				mi.layers = 0
			continue
		if "_glass" in String(mi.name):
			var pane := StandardMaterial3D.new()
			pane.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			pane.albedo_color = Color(0.82, 0.93, 0.97, 0.28)
			pane.roughness = 0.2
			mi.material_override = pane
			continue
		var m := ShaderMaterial.new()
		m.shader = CLAY
		m.set_shader_parameter("albedo", Color.WHITE)
		m.set_shader_parameter("use_vertex_color", true)
		m.set_shader_parameter("contact_ao", 0.0)
		m.set_shader_parameter("boil_fps", 0.0)
		for key: String in GLOWS:
			if key in String(mi.name):
				m.set_shader_parameter("emission", GLOWS[key])
		mi.material_override = m
	_render(out)


func _render(out: String) -> void:
	DirAccess.make_dir_recursive_absolute(out)
	for i in 10:
		await process_frame  # let the GLB transforms settle before reading AABBs
	for band: String in _bands:
		for room: String in ROOMS:
			if room == "driveway" and _bands == BANDS:
				continue  # adult homes only
			var c: Vector2 = ROOMS[room]
			_show_room(room, band, c)
			if _setting:
				_setting.position = Vector3(c.x, 0, c.y)
			_cam.transform.origin = Vector3(c.x, 1.0, c.y) + _cam.transform.basis.z * 20.0
			if _depth:
				_paint_depth(c)
			for i in 20 if _warm else 90:
				await process_frame
			var img := root.get_texture().get_image()
			if _depth:
				_save_depth(img, out.path_join("depth_%s_%s.png" % [room, band]))
			else:
				img.save_png(out.path_join("room_%s_%s.png" % [room, band]))
			_warm = true
			print("saved ", room, " ", band)
	quit()


## Shows one room: its own slab and back walls, its props for this age band; hides the shared shell
## pieces and every other room.
func _show_room(room: String, band: String, c: Vector2) -> void:
	for mi: MeshInstance3D in _house.find_children("*", "MeshInstance3D", true, false):
		var n := String(mi.name)
		var p := mi.global_transform * mi.get_aabb().get_center()
		## A home dresses its walls, so a piece 0.02 past the party wall must stay with its own room.
		var reach := 2.1 if _bands == BANDS else 2.0
		var inside := absf(p.x - c.x) < reach and absf(p.z - c.y) < reach
		if n.begins_with("room_"):
			mi.visible = n.begins_with("room_%s__" % room)
		elif (
			n.begins_with("shell__")
			and (n.contains("slab") or n.contains("wall_") or n.contains("iwall"))
		):
			mi.visible = false
		elif n.begins_with("bed_"):
			mi.visible = inside and n.begins_with("bed_%s__" % band)
		else:
			mi.visible = inside


func _paint_depth(c: Vector2) -> void:
	var m := ShaderMaterial.new()
	m.shader = DEPTH
	m.set_shader_parameter("origin", Vector3(c.x, 1.0, c.y))
	m.set_shader_parameter("axis", _cam.transform.basis.z)
	for mi: MeshInstance3D in _house.find_children("*", "MeshInstance3D", true, false):
		mi.material_override = m


## 16 bits across red and green. Exactly black means nothing there.
func _save_depth(img: Image, path: String) -> void:
	var w := img.get_width()
	var h := img.get_height()
	var out := PackedByteArray()
	out.resize(w * h * 2)
	var i := 0
	for y in h:
		for x in w:
			var v := int(clampf(img.get_pixel(x, y).r, 0.0, 1.0) * 65535.0)
			out[i] = v >> 8
			out[i + 1] = v & 255
			i += 2
	Image.create_from_data(w, h, false, Image.FORMAT_RG8, out).save_png(path)
