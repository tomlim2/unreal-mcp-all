# API Key Setup Instructions

## Method 1: Environment Variable (Recommended)

### Set for current session:
```cmd
set ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
```

### Set permanently (requires restart):
```cmd
setx ANTHROPIC_API_KEY "sk-ant-api03-your-actual-key-here"
```

### Verify:
```cmd
echo %ANTHROPIC_API_KEY%
```

## Method 2: .env File (Alternative)

1. Edit the `.env` file in the Python folder
2. Replace `your-api-key-here` with your actual API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
   ```

## Method 3: Start Script with API Key

1. Edit `start_bridge_with_key.bat`
2. Replace `YOUR_API_KEY_HERE` with your actual key
3. Run the batch file instead of `python http_bridge.py`

## Getting Your API Key

1. Go to https://console.anthropic.com/
2. Sign in/create account
3. Go to "API Keys" section
4. Create new key or copy existing one
5. Key format: `sk-ant-api03-...`

## Restart After Setting

After setting the API key, restart:
1. Kill current HTTP bridge (Ctrl+C)
2. Restart: `python http_bridge.py`
3. Test frontend at http://localhost:3000

## Test API Key

```cmd
cd Python
uv run python -c "from tools.nlp_tools import _process_natural_language_impl; result = _process_natural_language_impl('test'); print('✅ API key working!' if 'error' not in result or 'not set' not in result.get('error', '') else '❌ ' + result.get('error', 'Unknown error'))"
```