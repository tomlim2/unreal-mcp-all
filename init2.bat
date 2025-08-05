@REM cmd /c init2.bat
@echo off
REM Copies all files from the source Python directory to the target Python directory

set "SOURCE=E:\UnrealMCP\unreal-mcp-main\unreal-mcp-main\Python"
set "TARGET=Python"

REM Create target directory if it doesn't exist
if not exist "%TARGET%" (
	mkdir "%TARGET%"
)

REM Delete all files in the target directory first
del /Q "%TARGET%\*"

REM Copy all files (not folders) from source to target
copy "%SOURCE%\*" "%TARGET%\" /Y

REM If you want to copy subfolders and their contents as well, use xcopy:
REM xcopy "%SOURCE%\*" "%TARGET%\" /E /I /Y