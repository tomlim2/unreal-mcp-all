@REM cmd /c init2.bat
@echo off
set "SOURCE=E:\UnrealMCP\unreal-mcp-main\unreal-mcp-main\Python"
set "TARGET=Python"
if not exist "%TARGET%" (
	mkdir "%TARGET%"
)
del /Q "%TARGET%\*"
copy "%SOURCE%\*" "%TARGET%\" /Y