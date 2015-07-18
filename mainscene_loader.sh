#!/bin/sh

# prevent crashes (known)
PULSE_LATENCY_MSEC=
export PULSE_LATENCY_MSEC

if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
	echo "usage: mainscene_loader.sh [BLENDER OPTIONS] - [GAME OPTIONS] -l BACKUP_FILE
BLENDER OPTIONS:
-w  WIDTH HEIGHT     set window width and height
-f                   start in fullscreen mode
-g [show_framerate = 1] [show_properties = 1] [show_profile = 1]  some debug options

GAME OPTIONS:
-n  ADDRESS PORT USERNAME PASSWORD   connect to a server
"
else
	# launch
	$(cat blenderplayer_path.txt)/blenderplayer scenes/main.blend "$@" 
fi
