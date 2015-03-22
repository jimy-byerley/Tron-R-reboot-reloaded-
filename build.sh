#!/bin/sh

if [ "$1" == "-h" ]; then 
	echo "simple sh script used to optimize the game installation.
This program will remove several files that are useless for pure game runtime.
useless files
	.xcf	gimp files (textures)
	.blend1	blender backups files
	all files or directory found in projects.lst
use:
	./build.sh [PATH]

ONRROR: see README.md
"
	return
fi

extensions='*.xcf *.blend1 *.bat'

for ext in $extensions; do
	listfiles=$(find . -name "$ext")
	for filename in $listfile; do
		rm $filename
	done
done

listfile=$(cat projects.lst)
for filename in $listfile; do
	rm -r $filename
done
