@echo off

rem get system architecture
set RegQry=HKLM\Hardware\Description\System\CentralProcessor\0
 
REG.exe Query %RegQry% > checkOS.txt
 
find /i "x86" < CheckOS.txt > StringCheck.txt

if %ERRORLEVEL% == 0 (
    echo "This is 32 Bit Operating system"
    set architecture=32
) ELSE (
    echo "This is 64 Bit Operating System"
    set architecture=64
)
del checkOS.txt
del StringCheck.txt


rem download blender
if %architecture% == 32 (
	wget --progress=bar http://ftp.halifax.rwth-aachen.de/blender/release/Blender2.73/blender-2.73a-windows32.zip -o blender.zip
) else (
	wget --progress=bar http://ftp.halifax.rwth-aachen.de/blender/release/Blender2.73/blender-2.73a-windows64.zip -o blender.zip
)
rem extract blender
7za.exe x blender.zip -o softwares

