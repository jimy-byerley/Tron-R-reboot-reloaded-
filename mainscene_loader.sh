#!/bin/sh

# prevent crashes (known)
PULSE_LATENCY_MSEC=
export PULSE_LATENCY_MSEC

# launch
$(cat blenderplayer_path.txt)/blenderplayer scenes/main.blend "$@"

