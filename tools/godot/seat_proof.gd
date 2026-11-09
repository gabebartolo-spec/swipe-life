extends SceneTree
## Saves one frame per home with a figure forced into each seat clip, plus a sheet of a walk.
## Run: godot --path . --windowed --resolution 1080x900 -s tools/godot/seat_proof.gd -- <out_dir> <age>

const HOMES := [
	"baby",
	"child",
	"teen",
	"rental",
	"small_flat",
	"fixer_upper",
	"starter_house",
	"town_house",
	"family_house",
	"seaside_villa",
	"mansion",
]
const FORCED := {"bedroom": ["sit", "lay_back"], "living": ["sit_talk"]}


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	DirAccess.make_dir_recursive_absolute(a[0])
	var look := Looks.random()
	look.sex = "f"
	look.hair = "bob"
	look.top = "tee"
	var age := int(a[1])
	var stage := FigureStage.new()
	root.add_child(stage)
	stage.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var back := TextureRect.new()
	back.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	back.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(back)
	root.move_child(back, 0)
	for home: String in HOMES:
		for room: String in FORCED:
			back.texture = load(Dollhouse.texture_path(room, home))
			stage.set_room(room, home)
			(
				stage
				. set_people(
					[
						{
							"shape": Looks.shape_for(age, look.sex),
							"look": Looks.figure_look(look, age),
							"age": age,
						}
					]
				)
			)
			for clip: String in FORCED[room]:
				var seat := stage.seat_for(clip)
				print(home, " ", room, " ", clip, " ", seat)
				if seat.is_empty():
					continue
				stage.use_seat(stage.actors()[0], seat)
				await create_timer(0.5).timeout
				root.get_texture().get_image().save_png("%s/%s_%s.png" % [a[0], home, clip])
	quit()
