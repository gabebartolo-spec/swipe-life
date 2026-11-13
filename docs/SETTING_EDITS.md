# Moving things in a driveway setting by hand

Each home's driveway still sits in a setting (street, trees, fences, the house next door) that the code builds.
You can move, turn, resize or delete any piece of it in Blender; your changes are kept on every rebuild.

## Do it

In a terminal at the project folder (Git Bash), run:

```bash
tools/edit_setting.sh suburb
```

Settings and the home each belongs to: `suburb` (family house), `new_suburb` (starter house), `flats` (small flat),
`lowrise` (rental), `tired_street` (fixer-upper), `terrace` (town house), `beach` (seaside villa), `grounds` (mansion).

1. Blender opens looking through the game's camera: the frame is the driveway still's frame. The room itself is
   not shown; it sits on the drive.
2. Click a piece (a whole tree, fence, bush, house, the street...) and:
   - **G** to move it (then **X**, **Y** or **Z** to keep it on one line), click to drop;
   - **R** then **Z** to turn it (pieces only turn about the vertical);
   - **S** to resize it (then **Z** to make it only taller or shorter);
   - **X** then Delete to remove it;
   - **Ctrl+Z** undoes. Middle-drag orbits the view, the scroll wheel zooms, **Numpad 0** goes back to the game
     camera.
3. **Ctrl+S** to save, then close Blender.
4. The terminal bakes the setting and renders the driveway still (2 to 3 minutes), then opens it:
   `build/settings/suburb.png`. The very first time on a computer it also builds the home itself, which adds
   up to half an hour.

To re-render without opening Blender: `tools/edit_setting.sh suburb --render`.

## What is kept

Your changes are written to `tools/blender/setting_edits/<setting>.json`, one line per piece you changed, as a
nudge on top of where the code puts it:

```json
{
 "b1": {"remove": true},
 "tr": {"move": [-1.0, 0.0, 0.0], "turn": 0.0, "scale": [0.75, 0.75, 0.75]}
}
```

`move` is metres (x toward the street, y up, z toward the garden), `turn` is degrees, `scale` is times the size.
Delete a line (or the file) to put a piece back where the code had it. Commit the file like any other change.

## Good to know

- A piece is everything one line of the setting's code makes: a tree's trunk and crown move together, the street
  is the road, kerb and pavement together, a fence is all its posts and rails.
- New pieces (a second postbox, another tree) need a line of code; ask for them. Shift+D copies are not kept.
- If the code renames a piece, its saved change no longer matches; the bake prints `no piece ... edit skipped`.
- Resizing is about the middle of the piece's foot, so a tree grows up from the ground, not into it.
