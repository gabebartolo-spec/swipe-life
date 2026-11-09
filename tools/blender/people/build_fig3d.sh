#!/usr/bin/env bash
# Builds every 3D figure mesh into assets/people3d, skipping what exists.
# Run from the repo root: bash tools/blender/people/build_fig3d.sh <work_dir> [jobs]
WORK=$1
JOBS=${2:-4}
export WORK
export B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
mkdir -p "$WORK"

one() {  # shape age sex hair ("" = body)
	local shape=$1 age=$2 sex=$3 hair=$4 out src
	if [ -n "$hair" ]; then
		out=assets/people3d/$shape/hair/$hair.glb
		src=$WORK/${shape}_hair_$hair.glb
	else
		out=assets/people3d/$shape/body.glb
		src=$WORK/${shape}_body.glb
	fi
	[ -f "$out" ] && return 0
	mkdir -p "$(dirname "$out")"
	if [ -n "$hair" ]; then
		"$B" -b --factory-startup --python tools/blender/people/body.py -- "$src" "$age" "$sex" "hair=$hair" hair_only >/dev/null 2>&1
	else
		"$B" -b --factory-startup --python tools/blender/people/body.py -- "$src" "$age" "$sex" >/dev/null 2>&1
	fi
	"$B" -b --factory-startup --python tools/blender/people/fig3d.py -- "$src" "$out" 2>&1 | grep FACES | sed "s|^|$out |"
	rm -f "$src"
}
export -f one

CUTS=$(ls assets/people/adult_f_skinny/hair)
{
	echo "baby baby f -"
	echo "baby baby f wisp"
	for age in child teen adult; do
		for sex in f m; do
			echo "${age}_${sex}_skinny $age $sex -"
			for cut in $CUTS; do
				echo "${age}_${sex}_skinny $age $sex $cut"
			done
		done
	done
} | xargs -P "$JOBS" -L 1 bash -c 'h=$3; [ "$h" = "-" ] && h=""; one "$0" "$1" "$2" "$h"'
echo ALLDONE
