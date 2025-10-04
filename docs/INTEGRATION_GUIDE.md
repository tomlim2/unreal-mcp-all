# Creative Hub Integration Guide

**Version:** 1.0.0
**Last Updated:** 2025-10-04
**Branch:** `feature/creative-hub-architecture`

---

## Quick Start

### 1. Enable Plugin System

Edit `Python/.env`:
```bash
# Enable Creative Hub architecture
FEATURE_PLUGIN_SYSTEM=true
FEATURE_ORCHESTRATOR=true
FEATURE_LEGACY_HANDLERS=true  # Keep enabled during transition
```

### 2. Test Plugin System

```bash
cd Python
python test_plugin_system.py
```

**Expected Output:**
```
✓ Discovered 2 tools: nano_banana, unreal_engine
✓ All tests completed successfully!
```

### 3. Start Backend

```bash
cd Python
python http_bridge.py
```

Server starts on `http://localhost:8080`

### 4. Test API Endpoints

```bash
# Get all tools
curl http://localhost:8080/tools

# Get specific tool info
curl http://localhost:8080/tools/nano_banana

# Check tool health
curl http://localhost:8080/tools/health
```

### 5. Start Frontend

```bash
cd Frontend
npm run dev
```

Frontend starts on `http://localhost:3000`

---

## API Reference

### GET /tools

Returns all available tools.

**Response:**
```json
{
  "tools": [
    {
      "tool_id": "nano_banana",
      "display_name": "Nano Banana",
      "version": "1.0.0",
      "description": "AI-powered image generation & editing",
      "icon": "🍌",
      "status": "available",
      "capabilities": ["image_generation", "image_editing"],
      "requires_connection": true,
      "pricing_tier": "premium"
    }
  ],
  "source": "plugin_registry",
  "plugin_system_enabled": true
}
```

### GET /tools/{tool_id}

Returns detailed information about a specific tool.

**Example:** `GET /tools/nano_banana`

**Response:**
```json
{
  "tool_id": "nano_banana",
  "display_name": "Nano Banana",
  "version": "1.0.0",
  "status": "available",
  "supported_commands": ["generate_image", "edit_image", "style_transfer"]
}
```

### GET /tools/health

Returns health status of all tools.

**Response:**
```json
{
  "plugin_system_enabled": true,
  "tools": {
    "nano_banana": "available",
    "unreal_engine": "available"
  }
}
```

### GET /3d-object/{uid}

Serves a 3D object file.

**Example:** `GET /3d-object/fbx_001`

**Response:** Binary file download (FBX, OBJ, GLTF, GLB)

---

## Frontend Integration

### Using ToolSelector Component

```tsx
import ToolSelector from '@/app/components/ToolSelector';

function MyComponent() {
  const [selectedTool, setSelectedTool] = useState('nano_banana');

  return (
    <ToolSelector
      selectedTool={selectedTool}
      onToolSelect={setSelectedTool}
      disabled={false}
    />
  );
}
```

### Displaying 3D Objects

```tsx
import MessageItem3DResult from '@/app/components/conversation/messages/MessageItem3DResult';

function MyComponent() {
  const result = {
    object_3d: {
      uid: 'fbx_001',
      format: 'fbx',
      file_size: 2048000,
      vertices: 12000,
      faces: 8000
    }
  };

  return <MessageItem3DResult result={result} resultIndex={0} />;
}
```

---

## Migration Checklist

### Phase 1: Preparation
- [x] Read `CREATIVE_HUB_ARCHITECTURE.md`
- [x] Review backend changes (plugin system, resource management)
- [x] Review frontend changes (ToolSelector, 3D display)
- [x] Understand feature flags system

### Phase 2: Testing (Current Phase)
- [x] Run `test_plugin_system.py` - verify all tests pass
- [ ] Start backend with plugin system enabled
- [ ] Test `/tools` API endpoints
- [ ] Start frontend and verify ToolSelector displays
- [ ] Test image upload and transformation
- [ ] Test 3D object display (if available)

### Phase 3: Gradual Rollout
- [ ] Enable plugin system: `FEATURE_PLUGIN_SYSTEM=true`
- [ ] Monitor logs for errors
- [ ] Compare behavior with legacy system
- [ ] Verify all existing features work
- [ ] Test multi-tool workflows with orchestrator

### Phase 4: Full Migration
- [ ] Disable legacy handlers: `FEATURE_LEGACY_HANDLERS=false`
- [ ] Test thoroughly
- [ ] Monitor production for issues
- [ ] Update documentation

### Phase 5: Cleanup
- [ ] Remove deprecated legacy handler code
- [ ] Merge `feature/creative-hub-architecture` to `main`
- [ ] Deploy to production
- [ ] Archive old architecture documentation

---

## Troubleshooting

### Issue: "No tools discovered"

**Cause:** Plugin system not properly initialized or metadata files missing

**Solution:**
1. Verify `tools/nano_banana/metadata.json` exists
2. Verify `tools/unreal_engine/metadata.json` exists
3. Check logs for import errors
4. Run `python test_plugin_system.py`

### Issue: "/tools returns legacy data"

**Cause:** Plugin system feature flag not enabled

**Solution:**
```bash
# In Python/.env
FEATURE_PLUGIN_SYSTEM=true
```

Restart backend: `python http_bridge.py`

### Issue: "Tool status shows 'unavailable'"

**Cause:** Tool plugin failed to initialize or dependencies missing

**Solution:**
1. Check logs for initialization errors
2. For Nano Banana: Verify `GOOGLE_API_KEY` in `.env`
3. For Unreal Engine: Verify Unreal project is open (if requires_connection)
4. Run health check: `curl http://localhost:8080/tools/health`

### Issue: "3D object download fails"

**Cause:** UID not found or file path invalid

**Solution:**
1. Verify UID exists: Check `Python/tools/ai/session_management/uid_data/uid_state.json`
2. Verify file path in UID mapping is valid
3. Check file permissions
4. Review logs: `Python/http_bridge_debug.log`

### Issue: "ToolSelector shows loading forever"

**Cause:** Backend not running or CORS issue

**Solution:**
1. Verify backend is running: `curl http://localhost:8080/tools`
2. Check browser console for CORS errors
3. Verify `Access-Control-Allow-Origin: *` in response headers
4. Check `NEXT_PUBLIC_BACKEND_URL` in `Frontend/.env.local`

---

## Configuration Reference

### Environment Variables

**Python (`Python/.env`):**
```bash
# API Keys
ANTHROPIC_API_KEY=your_key
GOOGLE_API_KEY=your_key

# Server Configuration
HTTP_PORT=8080
UNREAL_TCP_PORT=55557
UNREAL_TCP_HOST=127.0.0.1

# Creative Hub Feature Flags
FEATURE_PLUGIN_SYSTEM=true
FEATURE_ORCHESTRATOR=true
FEATURE_LEGACY_HANDLERS=true
FEATURE_NANO_BANANA=true
FEATURE_UNREAL_ENGINE=true
FEATURE_VIDEO_RESOURCES=true
FEATURE_3D_RESOURCES=true

# Paths
UNREAL_PROJECT_PATH=/path/to/your/project
```

**Frontend (`Frontend/.env.local`):**
```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8080
```

### Feature Flag Reference

| Flag | Default | Description |
|------|---------|-------------|
| `FEATURE_PLUGIN_SYSTEM` | `false` | Enable plugin-based tool system |
| `FEATURE_ORCHESTRATOR` | `false` | Enable multi-tool workflows |
| `FEATURE_LEGACY_HANDLERS` | `true` | Keep old command handlers |
| `FEATURE_NANO_BANANA` | `true` | Enable Nano Banana tool |
| `FEATURE_UNREAL_ENGINE` | `true` | Enable Unreal Engine tool |
| `FEATURE_VIDEO_RESOURCES` | `true` | Enable video resource processing |
| `FEATURE_3D_RESOURCES` | `true` | Enable 3D object processing |

---

## Testing Scenarios

### Scenario 1: Tool Discovery
```bash
# Test: Verify tools are discovered
python test_plugin_system.py

# Expected: 2 tools discovered (nano_banana, unreal_engine)
```

### Scenario 2: API Integration
```bash
# Start backend
python http_bridge.py

# In another terminal:
curl http://localhost:8080/tools | jq .

# Expected: JSON with 2 tools, plugin_system_enabled: true
```

### Scenario 3: Frontend Integration
```bash
# Start frontend
cd Frontend && npm run dev

# Open http://localhost:3000/app
# Expected: ToolSelector appears in UI
# Expected: Clicking shows dropdown with tools
```

### Scenario 4: 3D Object Serving
```bash
# Prerequisite: Have a 3D object with UID (e.g., fbx_001)

# Test download
curl http://localhost:8080/3d-object/fbx_001 --output test.fbx

# Expected: File downloaded successfully
```

---

## Performance Considerations

### Lazy Loading
- Tools load on first use, not at startup
- Improves startup time
- Reduces memory usage for unused tools

### Caching
- Tool metadata cached after discovery
- Health status cached (check periodically)
- 3D object files served with long cache headers

### Optimization Tips
1. Only enable tools you need via feature flags
2. Use orchestrator for complex multi-tool workflows
3. Monitor tool health endpoints for availability
4. Cache tool registry response in frontend

---

## Next Steps

### Immediate
1. ✅ Run tests: `python test_plugin_system.py`
2. ✅ Start backend with feature flags enabled
3. ✅ Verify `/tools` API works
4. ✅ Test frontend ToolSelector

### Short-term
- [ ] Add Blender tool plugin
- [ ] Add video generation tool plugin
- [ ] Implement workflow builder UI
- [ ] Add WebSocket support for tool status updates

### Long-term
- [ ] Add plugin marketplace
- [ ] Support third-party plugins
- [ ] Add plugin versioning and updates
- [ ] Implement plugin sandboxing

---

## Support & Resources

- **Architecture Guide:** `/CREATIVE_HUB_ARCHITECTURE.md`
- **Main Documentation:** `/CLAUDE.md`
- **Test Script:** `Python/test_plugin_system.py`
- **Example Config:** `Python/.env.example`
- **GitHub Issues:** Report bugs and feature requests

---

## Version History

### v1.0.0 (2025-10-04)
- Initial release
- Plugin system implementation
- Tool registry with auto-discovery
- Frontend ToolSelector component
- 3D object display and serving
- Multi-tool orchestrator
- Comprehensive testing suite
