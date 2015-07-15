@echo off

if exist softwares\blender (
	softwares\blender\blenderplayer scenes\menu.blend
) else (
	echo Game have not been built !! run "build.bat" before.
	echo press Q to close.
	pause
)
