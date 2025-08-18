@REM cmd /c init-server.bat
@echo off
echo Select what to import:
echo 1. Import Server
echo 2. Import Bridge
echo 3. Export Bridge
echo 4. Export UI and Server
echo 5. Close
echo.
set /p choice="Enter your choice (1, 2, 3, or 4): "

if "%choice%"=="1" goto import_server
if "%choice%"=="2" goto import_bridge
if "%choice%"=="3" goto export_bridge
if "%choice%"=="4" goto export_ui_and_server
if "%choice%"=="5" goto close
echo Invalid choice. Please run the script again and select 1, 2, 3, or 4.
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

:export_bridge
echo Exporting Bridge...
set "SRC=MCPGameProject\Plugins\UnrealMCP\Source\UnrealMCP"
set "DST=E:\CINEVStudio\CINEVStudio\Plugins\UnrealMCP\Source\UnrealMCP"
if not exist "%DST%" (
	mkdir "%DST%"
)
del /Q "%DST%\*" 2>nul
for /d %%d in ("%DST%\*") do rmdir /s /q "%%d" 2>nul
robocopy "%SRC%" "%DST%" /E /XD "Binaries" "Intermediate"
echo Bridge export complete.
goto end

:export_ui_and_server
echo Exporting UI and Server...
set "SRC_FRONTEND=Frontend"
set "DST_FRONTEND=D:\vs\unreal-mcp\ummm\Frontend"
set "SRC_PYTHON=Python"
set "DST_PYTHON=D:\vs\unreal-mcp\ummm\Python"

REM Delete and recreate Frontend folder
if exist "%DST_FRONTEND%" (
	rmdir /s /q "%DST_FRONTEND%"
)
if not exist "D:\vs\unreal-mcp\ummm" (
	mkdir "D:\vs\unreal-mcp\ummm"
)
robocopy "%SRC_FRONTEND%" "%DST_FRONTEND%" /E /XD "node_modules" ".next"

REM Delete and recreate Python folder
if exist "%DST_PYTHON%" (
	rmdir /s /q "%DST_PYTHON%"
)
robocopy "%SRC_PYTHON%" "%DST_PYTHON%" /E /XD ".vscode" "unreal_mcp.egg-info" ".venv"

echo UI and Server export complete.
goto end

:end
pause
exit /b 0

:close
echo Goodbye!
exit /b 0