@echo off

if exist blenderplayer_path.txt (
	set /P location="" < blenderplayer_path.txt
	set blenderplayer=%location%\blenderplayer.exe
	if exist %blenderplayer% (
		@echo on
		%blenderplayer% scenes/menu.blend

		@echo off
		pause
)
) else (
	echo Game have not been builded !! run "build.bat" before.

	echo press Q to close.

	pause

)
