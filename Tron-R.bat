@echo off

if exist softwares/blender (
	softwares/blender/blenderplayer scenes/main.blend
) else (
	echo Game have not been builded !! run "build.bat" before.
	echo press Q to close.
	pause

)
