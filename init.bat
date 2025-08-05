@REM cmd /c init.bat
@echo off
REM Copies files and folders except Binaries and Intermediate from source to destination

set "SRC=E:\CINEVStudio\CINEVStudio\Plugins\UnrealMCP\Source\UnrealMCP"
set "DST=MCPGameProject\Plugins\UnrealMCP\Source\UnrealMCP"

REM Create destination folder if it doesn't exist
if not exist "%DST%" (
	mkdir "%DST%"
)

REM Use robocopy to copy everything except Binaries and Intermediate folders
robocopy "%SRC%" "%DST%" /E /XD "Binaries" "Intermediate"

REM /E copies all subfolders including empty ones
REM /XD excludes directories named Binaries and Intermediate

echo Copy complete.