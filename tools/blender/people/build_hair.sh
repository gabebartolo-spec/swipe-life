#!/usr/bin/env bash
# Build hair cuts into assets/people/<shape>/hair/<cut>/ (body.py HAIRS, docs/PEOPLE.md).
# Usage: tools/blender/people/build_hair.sh <shape> <cut>...   e.g. child_f_skinny bob crop
# Each cut is built with only the head (occluder) and chest (light level), so its sprites line up
# with the shape's body on the same canvas; the non-hair sprites are deleted after the render.
set -e
B=${BLENDER:-"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"}
shape=$1; shift
age=${shape%%_*}; sex=f
[[ $shape == *_m_* ]] && sex=m
tmp=$(mktemp -d)
for cut in "$@"; do
  out=assets/people/$shape/hair/$cut
  "$B" -b --factory-startup --python tools/blender/people/body.py -- "$tmp/$cut.glb" "$age" "$sex" hair="$cut" hair_only >/dev/null
  rm -rf "$out"
  "$B" -b --factory-startup --python tools/blender/people/render.py -- "$tmp/$cut.glb" "$out" | grep RENDERED
  python tools/blender/people/prune_hair.py "$out"
done
rm -rf "$tmp"
