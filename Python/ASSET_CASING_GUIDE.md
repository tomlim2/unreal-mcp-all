# Asset Casing Fix - User Guide

## The Problem

When renaming assets with case-only changes (e.g., `t_wall` → `T_Wall`):
- **Unreal Engine**: Case-insensitive paths (`/Game/t_wall` == `/Game/T_Wall`)
- **Git on Windows/macOS**: Case-insensitive filesystem
- **Result**: Git conflicts, file tracking issues, and Unreal rename failures

## The Solution

The system automatically detects case-only changes and adds a suffix (default: `_RC`) to avoid conflicts.

## How to Use

### Via Natural Language (Recommended)

Simply tell the AI what you want in natural language:

```
User: "fix the casing on my selected assets"
```

```
User: "make asset names properly capitalized"
```

```
User: "rename t_sefdfd_eide to T_Sefdfd_Eide"
```

```
User: "apply title case to my textures"
```

### What Happens

**Step 1: AI Generates Command**
```json
{
  "type": "fix_asset_casing",
  "params": {
    "mode": "preview",
    "case_style": "title_case",
    "case_suffix": "_RC"
  }
}
```

**Step 2: System Shows Preview**
```
Analyzing selected assets...

┌─────────────────┬─────────────────────┬──────────────────────────┐
│ Current         │ Desired             │ Actual (case conflict)   │
├─────────────────┼─────────────────────┼──────────────────────────┤
│ t_sefdfd_eide   │ T_Sefdfd_Eide ⚠️    │ T_Sefdfd_Eide_RC        │
│ m_wood_floor    │ M_Wood_Floor ⚠️     │ M_Wood_Floor_RC         │
│ SM_chair        │ SM_Chair ✓          │ SM_Chair (no conflict)  │
└─────────────────┴─────────────────────┴──────────────────────────┘

⚠️ 2 asset(s) have case-only changes. Git and Windows/macOS filesystems
treat paths as case-insensitive, so '_RC' suffix will be added to avoid
conflicts. Affected: t_sefdfd_eide, m_wood_floor

Proceed with rename? [yes/no]
```

**Step 3: User Confirms**
```
User: "yes"
```

**Step 4: System Executes**
```
Renaming assets...
✓ T_Sefdfd_Eide_RC
✓ M_Wood_Floor_RC
✓ SM_Chair

Success! 3 assets renamed (2 with _RC suffix for case conflict)
```

## Customization Options

### Custom Suffix

```
User: "fix casing but use _Fixed suffix instead"
```

AI generates:
```json
{
  "type": "fix_asset_casing",
  "params": {
    "mode": "preview",
    "case_style": "title_case",
    "case_suffix": "_Fixed"
  }
}
```

Result: `t_wall` → `T_Wall_Fixed`

### Different Case Styles

**Title Case (default):**
```
t_sefdfd_eide → T_Sefdfd_Eide
```

**Pascal Case:**
```
User: "use pascal case without underscores"

t_sefdfd_eide → TSefdfdEide
```

**Proper Prefix Only:**
```
User: "just fix the prefix, keep the rest as-is"

t_myAsset123 → T_myAsset123
```

## Technical Details

### Case Conflict Detection

The system checks if `old_name.lower() == new_name.lower()`:
```python
old_name = "t_wall"
new_name = "T_Wall"

if old_name.lower() == new_name.lower():
    # Case-only change detected!
    actual_name = new_name + "_RC"  # Add suffix
```

### Why Suffix is Required

**Git Behavior:**
```bash
# This doesn't work on Windows/macOS:
git mv Content/t_wall.uasset Content/T_Wall.uasset
# Git sees: No change (case-insensitive)

# This works:
git mv Content/t_wall.uasset Content/T_Wall_RC.uasset
# Git sees: New file (different name)
```

## Command Structure

### Preview Mode (Returns Preview)
```json
{
  "type": "fix_asset_casing",
  "params": {
    "mode": "preview",
    "case_style": "title_case",
    "case_suffix": "_RC"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "preview": [
      {
        "current_name": "t_wall",
        "desired_name": "T_Wall",
        "actual_name": "T_Wall_RC",
        "has_case_conflict": true,
        "needs_rename": true
      }
    ],
    "case_conflict_count": 1,
    "suffix_used": "_RC",
    "explanation": "⚠️ 1 asset(s) have case-only changes...",
    "total_assets": 1,
    "to_rename": 1
  }
}
```

### Execute Mode (Performs Rename)
```json
{
  "type": "fix_asset_casing",
  "params": {
    "mode": "execute",
    "case_style": "title_case",
    "case_suffix": "_RC"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "success": [...],
    "failed": [],
    "success_count": 3,
    "failed_count": 0,
    "case_conflicts_resolved": 2,
    "suffix_used": "_RC"
  }
}
```

## Integration Points

### Works With:
- ✅ Natural Language (via NLP)
- ✅ Web UI (modals with preview)
- ✅ MCP Clients (Claude Desktop, etc.)
- ✅ Direct API calls
- ✅ CLI (future: `mm asset fix-casing`)

### Supported Platforms:
- ✅ Windows (case-insensitive)
- ✅ macOS (case-insensitive by default)
- ✅ Linux (works, but suffix less critical)

## Examples

### Example 1: Mixed Assets
```
Selected: t_wall, M_floor, SM_chair

Result:
- t_wall      → T_Wall_RC (case conflict)
- M_floor     → M_Floor_RC (case conflict)
- SM_chair    → SM_Chair (no conflict)
```

### Example 2: Already Correct
```
User: "fix casing"

Response: "All assets already have correct casing. No changes needed."
```

### Example 3: All Conflicts
```
Selected: t_wall, m_floor, bp_player

All have case-only changes:
- t_wall      → T_Wall_RC
- m_floor     → M_Floor_RC
- bp_player   → BP_Player_RC
```

## Best Practices

1. **Always preview first** - The system defaults to `mode: "preview"`
2. **Use standard suffix** - `_RC` is short and conventional ("ReCased")
3. **Let NLP decide** - The AI will automatically detect case issues
4. **Batch operations** - Select multiple assets for efficiency
5. **Commit afterward** - Git will track as new files correctly

## Troubleshooting

**Q: Why can't you just rename without suffix?**
A: Git and Windows/macOS filesystems don't distinguish `t_wall` from `T_Wall`. The rename would fail or cause tracking issues.

**Q: Can I remove the suffix later?**
A: Yes! Once committed to Git, you can:
1. Rename other assets first (create actual changes)
2. Then rename `T_Wall_RC` → `T_Wall` (now safe)
3. Or keep `_RC` as documentation of re-casing

**Q: What if I don't want the suffix?**
A: Unfortunately, there's no reliable alternative on case-insensitive filesystems. The suffix is required for Git/filesystem compatibility.
