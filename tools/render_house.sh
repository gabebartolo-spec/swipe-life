#!/usr/bin/env bash
# Build the clay dollhouse GLB in Blender, then render the age-band stills in Godot.
# Usage: tools/render_house.sh [out_dir]   (default docs/m5)
set -euo pipefail
cd "$(dirname "$0")/.."
BLENDER="${BLENDER:-/c/Program Files/Blender Foundation/Blender 5.2/blender.exe}"
GODOT="${GODOT:-/c/Users/DANTE/Desktop/Godot_v4.7.2-stable_win64.exe/Godot_v4.7.2-stable_win64_console.exe}"
OUT="${1:-docs/m5}"
"$BLENDER" -b --factory-startup --python tools/blender/build_clay_house.py -- "$(pwd -W)/assets/house/house.glb" 2>&1 \
  | grep -E "HOUSE|Traceback|Error" -A4 || true
"$GODOT" --path . --headless --import > /dev/null 2>&1 || true
"$GODOT" --path . --resolution 1080x900 -s tools/godot/render_house.gd -- "$(pwd -W)/$OUT" 2>&1 | grep -E "saved|ERROR"
ls -la assets/house/house.glb
