class_name ClayTheme
extends RefCounted
## The clay UI (GDD §15.18): every button is a thick rounded slab of plasticine that presses down
## when tapped. One Theme on the root, so every menu, tab and button picks it up.

const INK := Color(0.22, 0.17, 0.13)
const SLAB := Color(0.97, 0.86, 0.66)  # warm clay buttons
const ACTIVE := Color(0.95, 0.62, 0.35)  # chosen tab
const DEPTH := 9  # slab thickness in px; pressing squashes it to 2
const STAT_COLOURS := {
	"health": Color(0.88, 0.36, 0.36),
	"happiness": Color(0.98, 0.78, 0.3),
	"career": Color(0.45, 0.6, 0.85),
	"relationships": Color(0.92, 0.5, 0.7),
	"smarts": Color(0.55, 0.45, 0.85),
	"looks": Color(0.4, 0.75, 0.7),
	"stress": Color(0.6, 0.55, 0.5),
}


## A clay slab: rounded, darker underside for thickness, soft drop shadow.
static func slab(colour: Color, depth := DEPTH, radius := 22) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = colour
	s.set_corner_radius_all(radius)
	s.border_width_bottom = depth
	s.border_color = colour.darkened(0.28)
	s.shadow_size = 6 if depth > 3 else 2
	s.shadow_offset = Vector2(0, 3)
	s.shadow_color = Color(0.25, 0.15, 0.05, 0.25)
	s.anti_aliasing_size = 1.5
	s.content_margin_left = 22
	s.content_margin_right = 22
	s.content_margin_top = 10 + (DEPTH - depth)  # pressing moves the label down with the top
	s.content_margin_bottom = 10
	return s


static func make() -> Theme:
	var t := Theme.new()
	t.set_stylebox("normal", "Button", slab(SLAB))
	t.set_stylebox("hover", "Button", slab(SLAB.lightened(0.06)))
	t.set_stylebox("pressed", "Button", slab(ACTIVE, 2))
	t.set_stylebox("hover_pressed", "Button", slab(ACTIVE.lightened(0.05), 2))
	t.set_stylebox("disabled", "Button", slab(Color(0.85, 0.82, 0.78), 4))
	t.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_hover_pressed_color"]:
		t.set_color(c, "Button", INK)
	t.set_color("font_focus_color", "Button", INK)
	t.set_color("font_disabled_color", "Button", Color(0.55, 0.5, 0.45))
	t.set_color("font_color", "Label", INK)
	return t


## Stat bar fill and groove: a rolled clay sausage in a pressed-in channel.
static func bar_fill(stat: String) -> StyleBoxFlat:
	var c: Color = STAT_COLOURS.get(stat, SLAB)
	var s := StyleBoxFlat.new()
	s.bg_color = c
	s.set_corner_radius_all(12)
	s.border_width_bottom = 4
	s.border_color = c.darkened(0.3)
	s.anti_aliasing_size = 1.5
	return s


static func groove() -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = Color(0.36, 0.29, 0.24)
	s.set_corner_radius_all(12)
	s.border_width_top = 3
	s.border_color = Color(0.2, 0.15, 0.12)
	s.anti_aliasing_size = 1.5
	return s
