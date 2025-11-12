# NLP Asset Command Examples

## How the AI Should Now Interpret Asset Queries

### ✅ CORRECT: Get Selected Assets

**User Input:** "get selected assets"

**AI Should Generate:**
```json
{
  "explanation": "Retrieving list of currently selected assets in Content Browser with their metadata",
  "commands": [
    {
      "type": "get_selected_assets",
      "params": {}
    }
  ],
  "expectedResult": "A list of selected assets showing their type, name, and path"
}
```

**NOT:** ~~take_screenshot~~ ❌

---

### ✅ CORRECT: Fix Asset Prefix/Casing (2-STEP WORKFLOW)

**User Input:** "fix assets' prefix"

**STEP 1 - AI Should Generate (First Call):**
```json
{
  "explanation": "Getting selected assets to analyze their naming. I'll show you what changes need to be made to fix the prefixes according to Unreal naming conventions.",
  "commands": [
    {
      "type": "get_selected_assets",
      "params": {}
    }
  ],
  "expectedResult": "List of selected assets with their current names, types, and paths"
}
```

**STEP 2 - AI Analyzes Response and Shows Preview:**
Based on the response from get_selected_assets:
```
Current Assets:
- wall (Texture2D) → Should be: T_Wall
- floor_mat (Material) → Should be: M_FloorMat
- cube_mesh (StaticMesh) → Should be: SM_CubeMesh

Say 'okay' or 'apply' to rename these assets.
```

**STEP 3 - User Confirms:** "okay"

**STEP 4 - AI Executes Rename:**
```json
{
  "explanation": "Renaming 3 assets with proper Unreal Engine naming conventions",
  "commands": [
    {
      "type": "rename_assets_batch",
      "params": {
        "operations": [
          {
            "old_path": "/Game/Textures/wall",
            "new_name": "T_Wall"
          },
          {
            "old_path": "/Game/Materials/floor_mat",
            "new_name": "M_FloorMat"
          },
          {
            "old_path": "/Game/Meshes/cube_mesh",
            "new_name": "SM_CubeMesh"
          }
        ]
      }
    }
  ],
  "expectedResult": "Assets renamed successfully with proper prefixes"
}
```

---

### ✅ CORRECT: Fix Capitalization (2-STEP WORKFLOW)

**User Input:** "fix capitalization"

**Follow the same 2-step workflow:**
1. Call `get_selected_assets` first
2. Show preview of old_name → new_name
3. Wait for user confirmation
4. Call `rename_assets_batch` with operations

---

### ✅ CORRECT: List Assets Variations

All these should use `get_selected_assets`:

```
User: "show my selected assets"
User: "list selected assets"
User: "what assets are selected"
User: "get asset info"
User: "show asset metadata"
```

**NOT:** take_screenshot for any of these! ❌

---

## Why This Matters

### Before (Wrong):
```
User: "get selected assets"
AI: "Let me take a screenshot to show you"
Command: take_screenshot ❌
Result: Image of viewport (not what user wanted)
```

### After (Correct):
```
User: "get selected assets"
AI: "Retrieving selected assets metadata"
Command: get_selected_assets ✓
Result:
{
  "assets": [
    {
      "name": "t_wall",
      "type": "Texture2D",
      "path": "/Game/Textures/t_wall"
    }
  ],
  "count": 1
}
```

---

## Key Phrases That Trigger Asset Commands

### get_selected_assets (STEP 1 of rename workflow):
- "get selected assets"
- "show selected assets"
- "list selected assets"
- "what assets are selected"
- "selected asset info"
- "asset metadata"

### Rename Workflow (2-STEP: get_selected_assets → rename_assets_batch):
**These trigger STEP 1 (get_selected_assets):**
- "fix casing"
- "fix capitalization"
- "fix assets' prefix"
- "fix prefix"
- "make names properly capitalized"
- "fix asset names"
- "rename assets with proper prefixes"

**After preview, these trigger STEP 2 (rename_assets_batch):**
- "okay"
- "apply"
- "execute"
- "do it"
- "confirm"

### take_screenshot (should NOT trigger for asset queries):
- "take screenshot" ✓
- "capture viewport" ✓
- "screenshot of scene" ✓
- BUT NOT: "get assets" ❌
