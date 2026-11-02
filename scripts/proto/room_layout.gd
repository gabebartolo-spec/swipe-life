class_name RoomLayout
## One bedroom shared by both art-style prototypes (GDD §10.4), so they show the same room.
## Units: floor runs 0..6 on x and z, y is up. Back walls sit on x = 0 and z = 0.

const SKIN := Color("f1c27d")
const HAIR := Color("5b3a29")
const SHIRT := Color("f4a259")
const PANTS := Color("3d405b")
const INK := Color("2b2024")

## Character feet position (x, z) on the floor.
const CHARACTER_POS := Vector2(2.6, 3.4)

## Boxes: pos = min corner (x, y, z), size = (x, y, z).
const BOXES := [
	{"pos": Vector3(0, -0.2, 0), "size": Vector3(6, 0.2, 6), "color": Color("e8c39e")},
	{"pos": Vector3(-0.2, -0.2, -0.2), "size": Vector3(0.2, 4.2, 6.2), "color": Color("8fb8de")},
	{"pos": Vector3(0, -0.2, -0.2), "size": Vector3(6, 4.2, 0.2), "color": Color("a7c7e7")},
	# rug
	{"pos": Vector3(1.6, 0, 2.4), "size": Vector3(2.8, 0.04, 2.2), "color": Color("e07a5f")},
	# bed
	{"pos": Vector3(0, 0, 3.3), "size": Vector3(2.0, 0.5, 2.5), "color": Color("6d4c41")},
	{"pos": Vector3(0.05, 0.5, 3.35), "size": Vector3(1.9, 0.25, 2.4), "color": Color("f4f1de")},
	{"pos": Vector3(0.75, 0.55, 3.35), "size": Vector3(1.25, 0.25, 2.4), "color": Color("3d5a80")},
	{"pos": Vector3(0.12, 0.75, 3.75), "size": Vector3(0.5, 0.18, 1.6), "color": Color("ffffff")},
	# window on left wall
	{"pos": Vector3(-0.04, 1.6, 3.5), "size": Vector3(0.06, 1.4, 2.0), "color": Color("fdf6e3")},
	{"pos": Vector3(-0.02, 1.7, 3.6), "size": Vector3(0.06, 1.2, 1.8), "color": Color("bde0fe")},
	# poster on back wall
	{"pos": Vector3(0.8, 1.5, -0.03), "size": Vector3(1.0, 1.3, 0.05), "color": Color("f2cc8f")},
	{"pos": Vector3(0.95, 1.65, -0.01), "size": Vector3(0.7, 0.7, 0.05), "color": Color("81b29a")},
	# desk
	{"pos": Vector3(2.9, 1.3, 0.05), "size": Vector3(2.4, 0.15, 1.1), "color": Color("8d6e63")},
	{"pos": Vector3(3.0, 0, 0.15), "size": Vector3(0.12, 1.3, 0.12), "color": Color("6d4c41")},
	{"pos": Vector3(5.08, 0, 0.15), "size": Vector3(0.12, 1.3, 0.12), "color": Color("6d4c41")},
	{"pos": Vector3(3.0, 0, 0.93), "size": Vector3(0.12, 1.3, 0.12), "color": Color("6d4c41")},
	{"pos": Vector3(5.08, 0, 0.93), "size": Vector3(0.12, 1.3, 0.12), "color": Color("6d4c41")},
	# laptop
	{"pos": Vector3(3.7, 1.45, 0.45), "size": Vector3(0.8, 0.05, 0.5), "color": Color("6c757d")},
	{"pos": Vector3(3.7, 1.5, 0.4), "size": Vector3(0.8, 0.5, 0.05), "color": Color("343a40")},
	# shelf with books
	{"pos": Vector3(3.2, 2.5, -0.01), "size": Vector3(1.8, 0.1, 0.4), "color": Color("8d6e63")},
	{"pos": Vector3(3.3, 2.6, 0.02), "size": Vector3(0.18, 0.5, 0.32), "color": Color("e63946")},
	{"pos": Vector3(3.5, 2.6, 0.02), "size": Vector3(0.18, 0.42, 0.32), "color": Color("457b9d")},
	{"pos": Vector3(3.7, 2.6, 0.02), "size": Vector3(0.18, 0.55, 0.32), "color": Color("f4a261")},
	# chair
	{"pos": Vector3(3.6, 0.75, 1.3), "size": Vector3(0.8, 0.1, 0.8), "color": Color("f2cc8f")},
	{"pos": Vector3(3.6, 0.85, 2.0), "size": Vector3(0.8, 0.9, 0.1), "color": Color("f2cc8f")},
	{"pos": Vector3(3.65, 0, 1.35), "size": Vector3(0.08, 0.75, 0.08), "color": Color("6d4c41")},
	{"pos": Vector3(4.27, 0, 1.35), "size": Vector3(0.08, 0.75, 0.08), "color": Color("6d4c41")},
	{"pos": Vector3(3.65, 0, 1.97), "size": Vector3(0.08, 0.75, 0.08), "color": Color("6d4c41")},
	{"pos": Vector3(4.27, 0, 1.97), "size": Vector3(0.08, 0.75, 0.08), "color": Color("6d4c41")},
	# plant pot
	{"pos": Vector3(5.0, 0, 4.9), "size": Vector3(0.6, 0.6, 0.6), "color": Color("c1666b")},
]

## Spheres: center, radius.
const SPHERES := [
	{"center": Vector3(5.3, 1.05, 5.2), "radius": 0.5, "color": Color("81b29a")},
	{"center": Vector3(5.1, 1.45, 5.1), "radius": 0.32, "color": Color("6a9e85")},
]
