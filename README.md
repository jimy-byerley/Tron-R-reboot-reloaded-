# Tron-R{reboot||reloaded}
main repository of the Tron-R{reboot||reloaded} game project


#### THE PROJECT

This is the main part of the Tron-R{reboot||reloaded} project which attempt to be a new open-source game 
based on Tron. This game is based on Tron Legacy and Stand for replace the proprietary Tron evolution game 
made after the film.

- several skins
![skin rinzler](screenshots/rinzler-back.png) ![skin tron](screenshots/tron-side.png)
![skin clu](screenshots/clu-side.png)         ![skin monitor](screenshots/monitor-back.png)
![skin flynn](screenshots/flynn-face.png)
- open-world 
![street](screenshots/street.png) ![city](screenshots/city_1.png)
- items
![HUD](screenshots/HUD.png)
- better
![cycle](screenshots/cycle_on_grid.png)
![effects](sreenshots/2d_filters/history_mode.png)

suggestions: jimy.byerley@gmail.com

Facebook page: m.facebook.com/profile.php?id=631385166999031

#### PLAY

Extract the zip file in the installation path

Build/optimize the game
-----------------------

	It will download the blender software from the official repository and remove useless files.
	GNU/Linux: 
		You will need wget to be installed
		# apt-get install wget
		$ ./build.sh
	or
		$ ./build.sh -d       (developer mode: don't remove useless files)
	or
		$ ./build.sh -p PATH  specify to use PATH for blender instead of downloading it. This path is the location where the blenderplayer executable is.

	Windows:
		run build.bat (download blender and remove useless files)
	If you know what you do, you can also change the blenderplayer executable path, by changing value in blenderplayer_path.txt

Launch it!
----------
	GNU/Linux:
	$ ./aperture.sh         (flynn like mode)
	$ ./tron-r              (standard game menu mode)
	$ ./mainscene_loader.sh (manual mode : puts you directly in the virtual world)

	Windows:
	Execute Tron-R.bat executable file

To change game settings, edit config.txt file



#### COMPATIBILITY

OS platform: Linux (tested), Windows, but mabe maxOS should work too.
Blender :  version >= 2.70  (made with blender 2.72 ans 2.75)
(Blender 2.75 is recommended and Blender 2.72 was recomended because newer versions are crashing (except 2.75 of course)), see /blender-versions.txt for blender compatible versions

bugs: jimy.byerley@gmail.com

developement page: http://blenderartists.org/forum/showthread.php?362226-Tron-R-reboot-reloaded-An-open-source-openworld-of-tron

facebook: http://m.facebook.com/profile.php?id=631385166999031