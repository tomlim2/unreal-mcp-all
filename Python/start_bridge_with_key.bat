@echo off
echo Starting HTTP Bridge with API key...

REM Replace YOUR_API_KEY_HERE with your actual Anthropic API key
set ANTHROPIC_API_KEY=YOUR_API_KEY_HERE

REM Verify the key is set
echo API Key check: %ANTHROPIC_API_KEY%

REM Start the HTTP bridge
uv run python http_bridge.py

pause