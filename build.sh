#!/bin/bash

if [ "$1" == "-h" ]; then 
	echo "simple sh script used to optimize the game installation.
This program will remove several files that are useless for pure game runtime.
useless files
	.xcf	gimp files (textures)
	.blend1	blender backups files
	all files or directory found in projects.lst
use:
	./build.sh [OPTIONS]
options:
	-p PATH    user defined path where blenderplayer is installed
	-d         developer mode : don't remove 'useless' files
	-h         display this help

ON ERROR: see README.md"
	exit 0
fi

developer_mode=0
blender_path=""
for opt in "$@"; do 
	if [ "$opt" == "-d" ]; then
		developer_mode=1
	elif [ "$opt" == "-p" ]; then
		blender_path='%'
	elif [ "$blender_path" == "%" ]; then
		blender_path=$opt
	fi
done

if [ $developer_mode == 0 ]; then
	echo "removing developement files ..."
	extensions='*.xcf *.blend1 *.bat'

	for ext in $extensions; do
		listfiles=$(find . -name "$ext")
		for filename in $listfile; do
			echo $filename
			rm $filename
		done
	done

	listfile=$(cat projects.lst)
	for filename in $listfile; do
		echo $filename
		rm -r $filename
	done
fi

if [ -n $blenderpath ]; then
	echo "downloading blender from official repository ..."
	
	if $(which arch); then
		arch=$(arch)
	else
		arch=$(uname -m)
	fi
	echo "architecture is $arch."
	
	if [ $arch == "x86_64" ]; then
		wget http://ftp.halifax.rwth-aachen.de/blender/release/Blender2.73/blender-2.73a-linux-glibc211-x86_64.tar.bz2 -O blender.tar.bz2
	else
		wget http://ftp.halifax.rwth-aachen.de/blender/release/Blender2.73/blender-2.73a-linux-glibc211-i686.tar.bz2 -O blender.tar.bz2
	fi
	echo "extracting ..."
	tar xf blender.tar.bz2 -C software/
	mv software/blender-* software/blender
	echo "cleaning local directory ..."
	rm blender.tar.bz2
	blender_path=software/blender
fi
echo $(readlink -m $blender_path) > blenderplayer_path.txt
