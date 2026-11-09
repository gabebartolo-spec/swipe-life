#!/usr/bin/env bash
# Bakes the depth map of every room still into assets/house/depth.
# Run from the repo root behind C:/kt/gpu_slot.sh, with the capture override.cfg in place.
set -uo pipefail
BLENDER="${BLENDER:-/c/Program Files/Blender Foundation/Blender 5.2/blender.exe}"
GODOT="${GODOT:-/c/Users/DANTE/Desktop/Godot_v4.7.2-stable_win64.exe/Godot_v4.7.2-stable_win64_console.exe}"
OUT=assets/house/depth
HOMES="rental small_flat fixer_upper starter_house town_house family_house seaside_villa mansion"
mkdir -p "$OUT" assets/house/homes
for h in $HOMES; do
	"$BLENDER" -b --factory-startup --python tools/blender/build_clay_home.py -- "$h" "$(pwd -W)/assets/house/homes/$h.glb" > /dev/null 2>&1
done
"$GODOT" --path . --headless --import > /dev/null 2>&1
"$GODOT" --path . --windowed --resolution 1080x900 -s tools/godot/render_house.gd -- "$(pwd -W)/$OUT" res://assets/house/house.glb "" depth 2>&1 | grep -E "saved|ERROR"
for h in $HOMES; do
	"$GODOT" --path . --windowed --resolution 1080x900 -s tools/godot/render_house.gd -- "$(pwd -W)/$OUT" "res://assets/house/homes/$h.glb" "$h" depth 2>&1 | grep -E "saved|ERROR"
done
rm -rf assets/house/homes
echo DEPTHDONE
