class_name Looks
extends RefCounted
## A person's look (GDD §10.7) as plain JSON-safe data, and building a Person from it.

const SEXES := ["f", "m"]
const SKINS := ["f2c9a5", "e0ac84", "c58c66", "9c6644", "7a4a32", "4f2f20"]
const HAIR_COLOURS := ["1e1a18", "6b4430", "a8703a", "d9a441", "b5482a", "8a8a8a"]
const CLOTH_COLOURS := [
	"d04040", "f2d04a", "3d6e4a", "6f8fb5", "e07a9a", "1a1a1c", "e8d6bd", "4a4a52"
]
const TOPS := ["tee", "sweater"]
const CUTS := [
	"afro",
	"bob",
	"bowl_cut",
	"buzz",
	"cornrows",
	"crew_cut",
	"crop",
	"curly_bob",
	"curly_top",
	"curtains",
	"dreadlocks",
	"half_up",
	"high_ponytail",
	"long_curly",
	"long_straight",
	"long_wavy",
	"low_ponytail",
	"man_bun",
	"mohawk",
	"mullet",
	"pigtails",
	"pixie",
	"pompadour",
	"quiff",
	"shag",
	"side_part",
	"single_braid",
	"slick_back",
	"space_buns",
	"spiky",
	"top_knot",
	"two_braids",
	"undercut"
]


static func random() -> Dictionary:
	return {
		"sex": SEXES.pick_random(),
		"skin": SKINS.pick_random(),
		"hair": CUTS.pick_random(),
		"hair_colour": HAIR_COLOURS.pick_random(),
		"top": TOPS.pick_random(),
		"top_colour": CLOTH_COLOURS.pick_random(),
		"bottom_colour": CLOTH_COLOURS.pick_random(),
	}


## Body folder under assets/people for this age (bands as Dollhouse.band_for, adult from 18).
static func shape_for(age: int, sex: String) -> String:
	if age <= 3:
		return "baby"
	var band := "child" if age <= 12 else ("teen" if age <= 17 else "adult")
	return "%s_%s_skinny" % [band, sex]


static func make_person(look: Dictionary, age: int) -> Person:
	var p := Person.new()
	p.shape = shape_for(age, look.sex)
	var skin := Color(look.skin)
	var hair := Color(look.hair_colour)
	if p.shape == "baby":  # one baby body: a onesie and a wisp of hair
		p.hair = "wisp"
		p.look = {"body": [skin], "hair_front": [hair], "onesie": [Color(look.top_colour)]}
		return p
	p.hair = look.hair
	p.look = {
		"body": [skin],
		"hair_back": [hair],
		"hair_front": [hair],
		look.top: [Color(look.top_colour), Color("ffffff")],
		"trousers": [Color(look.bottom_colour)],
	}
	return p
