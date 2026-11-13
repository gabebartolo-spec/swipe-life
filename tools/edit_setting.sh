#!/usr/bin/env bash
# Move, turn, resize or remove pieces of a driveway setting by hand, then re-bake it and re-render its driveway
# still (docs/SETTING_EDITS.md).
# Usage: tools/edit_setting.sh <kind>            Blender opens on the setting: edit, save (Ctrl+S), close Blender
#        tools/edit_setting.sh <kind> --render   no Blender: bake and render from the saved edits
# kind: suburb new_suburb flats lowrise tired_street terrace beach grounds
# The edits land in tools/blender/setting_edits/<kind>.json; the still in build/settings/<kind>.png.
set -euo pipefail
cd "$(dirname "$0")/.."
BLENDER="${BLENDER:-/c/Program Files/Blender Foundation/Blender 5.2/blender.exe}"
GODOT="${GODOT:-/c/Users/DANTE/Desktop/Godot_v4.7.2-stable_win64.exe/Godot_v4.7.2-stable_win64_console.exe}"
KIND="${1:?kind: suburb new_suburb flats lowrise tired_street terrace beach grounds}"
declare -A HOME_OF=([suburb]=family_house [new_suburb]=starter_house [flats]=small_flat [lowrise]=rental
  [tired_street]=fixer_upper [terrace]=town_house [beach]=seaside_villa [grounds]=mansion)
HOME="${HOME_OF[$KIND]:?unknown kind $KIND}"
ROOT="$(pwd -W)"
BLEND="$ROOT/build/settings/$KIND.blend"
mkdir -p build/settings

touch build/settings/.gdignore  # Godot must not try to import the .blend

if [ "${2:-}" != "--render" ]; then
  "$BLENDER" -b --factory-startup --python tools/blender/build_clay_setting.py -- "$KIND" "$BLEND" --edit 2>&1 \
    | grep -E "SETTING EDIT OPEN|Traceback|Error" -A4
  echo "Blender opens on $KIND: move (G), turn (R then Z), resize (S), delete (X); Ctrl+S to save, then close it."
  "$BLENDER" --factory-startup "$BLEND" > /dev/null 2>&1
  "$BLENDER" -b --factory-startup "$BLEND" --python tools/blender/setting_edit.py -- harvest "$KIND" 2>&1 \
    | grep -E "SETTING EDITS SAVED|Traceback|Error" -A4
fi

echo "Baking $KIND..."
"$BLENDER" -b --factory-startup --python tools/blender/build_clay_setting.py -- "$KIND" \
  "$ROOT/assets/house/homes/setting_$KIND.glb" 2>&1 | grep -E "^SETTING|Traceback|Error" -A4
if [ ! -f "assets/house/homes/$HOME.glb" ]; then
  echo "Building the $HOME home (first time only)..."
  "$BLENDER" -b --factory-startup --python tools/blender/build_clay_home.py -- "$HOME" \
    "$ROOT/assets/house/homes/$HOME.glb" 2>&1 | grep -E "^HOME|Traceback|Error" -A4
fi
"$GODOT" --path . --headless --import > /dev/null 2>&1 || true
echo "Rendering the $HOME driveway..."
"$GODOT" --path . --resolution 1080x900 -s tools/godot/render_house.gd -- "$ROOT/build/settings/$KIND" \
  "res://assets/house/homes/$HOME.glb" "$HOME" driveway 2>&1 | grep -E "saved|ERROR"
cp "build/settings/$KIND/room_driveway_$HOME.png" "build/settings/$KIND.png"
echo "Done: build/settings/$KIND.png"
[ -z "${NO_OPEN:-}" ] && command -v cmd.exe > /dev/null && cmd.exe /c start "" "$(cygpath -w "build/settings/$KIND.png")" || true
