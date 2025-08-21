@REM cmd /c init.bat
@echo off
echo Select what to import:
echo 1. Import Unreal Bridge
echo 2. Export Unreal Bridge
echo 3. Export UI and Server to Project
echo 4. Export Project to ummm
echo 5. Close
echo.
set /p choice="Enter your choice (1, 2, 3, 4, or 5): "

if "%choice%"=="1" goto import_unreal_bridge
if "%choice%"=="2" goto export_unreal_bridge
if "%choice%"=="3" goto export_ui_and_server_to_project
if "%choice%"=="4" goto export_mcp_project_to_ummm
if "%choice%"=="5" goto close
echo Invalid choice. Please run the script again and select 1, 2, 3, 4, or 5.
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

:import_unreal_bridge
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

:export_unreal_bridge
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

:export_ui_and_server_to_project
echo Exporting UI and Server...
set "SRC_FRONTEND=Frontend"
set "DST_FRONTEND=E:\CINEVStudio\MegaMelange\Frontend"
set "SRC_PYTHON=Python"
set "DST_PYTHON=E:\CINEVStudio\MegaMelange\Python"

REM Delete and recreate Frontend folder
if exist "%DST_FRONTEND%" (
	rmdir /s /q "%DST_FRONTEND%"
)
if not exist "E:\CINEVStudio\MegaMelange" (
	mkdir "E:\CINEVStudio\MegaMelange"
)
robocopy "%SRC_FRONTEND%" "%DST_FRONTEND%" /E /XD "node_modules" ".next"

REM Delete and recreate Python folder
if exist "%DST_PYTHON%" (
	rmdir /s /q "%DST_PYTHON%"
)
robocopy "%SRC_PYTHON%" "%DST_PYTHON%" /E /XD ".vscode" "unreal_mcp.egg-info" ".venv"

echo UI and Server export complete.
goto end

:export_mcp_project_to_ummm
echo Exporting Core Components to ummm...
set "DST=D:\vs\unreal-mcp\ummm"

REM Delete specific folders only (preserve .git and other files)
if exist "%DST%\Python" (
	rmdir /s /q "%DST%\Python"
)
if exist "%DST%\Frontend" (
	rmdir /s /q "%DST%\Frontend"
)
if exist "%DST%\MCPGameProject\Plugins\UnrealMCP" (
	rmdir /s /q "%DST%\MCPGameProject\Plugins\UnrealMCP"
)
if not exist "%DST%" (
	mkdir "%DST%"
)

echo Exporting Python MCP Server...
robocopy "Python" "%DST%\Python" /E /XD "__pycache__" ".pytest_cache" ".venv" "node_modules" ".git" /XF "*.pyc" "*.pyo" "*.log"

echo Exporting Frontend...
robocopy "Frontend" "%DST%\Frontend" /E /XD "node_modules" ".next" ".git" "build" "dist" "cache" /XF "*.log"

echo Exporting UnrealMCP Plugin...
mkdir "%DST%\MCPGameProject\Plugins"
robocopy "MCPGameProject\Plugins\UnrealMCP" "%DST%\MCPGameProject\Plugins\UnrealMCP" /E /XD "Binaries" "Intermediate" ".git" /XF "*.log"

echo Core components export complete.
goto end

:end
pause
exit /b 0

:close
echo Goodbye!
exit /b 0