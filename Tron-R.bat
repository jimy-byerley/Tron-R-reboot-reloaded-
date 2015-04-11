@echo off

if exist softwares\blender (
	softwares\blender\blenderplayer.exe scenes\menu.blend
) else (
	echo Game have not been builded !! run "build.bat" before.
	echo press Q to close.
	pause
)