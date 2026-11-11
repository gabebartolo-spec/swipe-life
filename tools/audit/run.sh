#!/bin/bash
# usage: tools/audit/run.sh lives reps strategies  -> prints the feature audit
G="/c/Users/DANTE/Desktop/Godot_v4.7.2-stable_win64.exe/Godot_v4.7.2-stable_win64_console.exe"
timeout 580 "$G" --path . --headless --script res://tools/godot/feature_audit.gd -- "$@" 2>&1 | grep -v "^Godot Engine\|^$" | cut -c1-210
