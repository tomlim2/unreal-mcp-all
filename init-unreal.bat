@REM cmd /c init-unreal.bat
@echo off
set "SRC=E:\CINEVStudio\CINEVStudio\Plugins\UnrealMCP\Source\UnrealMCP"
set "DST=MCPGameProject\Plugins\UnrealMCP\Source\UnrealMCP"
if not exist "%DST%" (
	mkdir "%DST%"
)
del /Q "%DST%\*"
robocopy "%SRC%" "%DST%" /E /XD "Binaries" "Intermediate"
echo Copy complete.