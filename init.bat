@REM cmd /c init-server.bat
@echo off
echo Select what to import:
echo 1. Import Server
echo 2. Import Bridge
echo 3. Close
echo.
set /p choice="Enter your choice (1, 2, or 3): "

if "%choice%"=="1" goto import_server
if "%choice%"=="2" goto import_bridge
if "%choice%"=="3" goto close
echo Invalid choice. Please run the script again and select 1, 2, or 3.
pause
exit /b 1

:import_server
echo Importing Server...
set "SOURCE=E:\UnrealMCP\unreal-mcp-main\unreal-mcp-main\Python"
set "TARGET=Python"
if not exist "%TARGET%" (
	mkdir "%TARGET%"
)
del /Q "%TARGET%\*" 2>nul
for /d %%d in ("%TARGET%\*") do rmdir /s /q "%%d" 2>nul
robocopy "%SOURCE%" "%TARGET%" /E /XD "Binaries" "Intermediate" "__pycache__" ".venv"
echo Server import complete.
goto end

:import_bridge
echo Importing Bridge...
set "SRC=E:\CINEVStudio\CINEVStudio\Plugins\UnrealMCP\Source\UnrealMCP"
set "DST=MCPGameProject\Plugins\UnrealMCP\Source\UnrealMCP"
if not exist "%DST%" (
	mkdir "%DST%"
)
del /Q "%DST%\*"
robocopy "%SRC%" "%DST%" /E /XD "Binaries" "Intermediate"
echo Bridge import complete.
goto end

:end
pause
exit /b 0

:close
echo Goodbye!
exit /b 0