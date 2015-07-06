@echo off

if exist blenderplayer_path.txt (
	set /P path="" < blenderplayer_path.txt
	set blenderplayer=%path%\blenderplayer.exe
	if exist %blenderplayer% (
		%blenderplayer% scenes/main.blend
	)
) else (
	echo Game have not been builded !! run "build.bat" before.
	echo press Q to close.
	pause
)
