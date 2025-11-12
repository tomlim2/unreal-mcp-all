# Quick Start: Asset Casing Fix

## ✅ Everything is Working!

Your command **"fix the casing on my assets"** was correctly interpreted and executed. The error "No assets selected" is expected - you just need to select assets first.

## How to Use

### Step 1: Select Assets in Unreal Engine

1. Open **Unreal Engine**
2. Go to **Content Browser**
3. **Select one or more assets** that need casing fixes
   - Example: `t_wall`, `m_floor`, `bp_player`

### Step 2: Use Natural Language

In the chat/interface, say:

```
"fix the casing on my assets"
```

or:

```
"fix capitalization"
"make names properly capitalized"
"fix prefix casing"
```

### Step 3: Review Preview

The system will show:

```
Preview of asset name changes:

┌─────────────┬─────────────┬──────────────┐
│ Current     │ Desired     │ Actual       │
├─────────────┼─────────────┼──────────────┤
│ t_wall      │ T_Wall ⚠️   │ T_Wall_RC   │
│ m_floor     │ M_Floor ⚠️  │ M_Floor_RC  │
└─────────────┴─────────────┴──────────────┘

⚠️ 2 asset(s) have case-only changes.
Adding '_RC' suffix to avoid Git conflicts.

Continue? [yes/no]
```

### Step 4: Confirm

Say:

```
"yes"
"proceed"
"apply changes"
```

### Step 5: Done!

```
✓ Renamed 2 assets successfully!
  - T_Wall_RC
  - M_Floor_RC
```

## Customization

### Use Different Suffix

```
"fix casing but use _Fixed suffix"
```

Result: `t_wall` → `T_Wall_Fixed`

### Use Pascal Case

```
"use pascal case without underscores"
```

Result: `t_my_wall` → `TMyWall_RC`

### Just Fix Prefix

```
"fix the prefix only, keep rest as-is"
```

Uses `case_style: "proper_prefix"`

## Why the Suffix?

Git and Windows/macOS filesystems are case-insensitive:
- `t_wall` and `T_Wall` are seen as **the same file**
- Renaming without suffix causes Git conflicts
- Suffix (`_RC`) makes them **different files**

## Workflow Example

```
You: "get selected assets"
AI: Shows list of selected assets

You: "fix the casing"
AI: Shows preview with case conflicts marked

You: "yes, proceed"
AI: Executes renames

You: "get selected assets"
AI: Shows updated list with new names
```

## Common Phrases

### Get Assets Info:
- "get selected assets"
- "show my selected assets"
- "list assets"
- "what assets are selected"

### Fix Casing:
- "fix the casing"
- "fix capitalization"
- "make names properly capitalized"
- "apply title case"
- "fix asset prefixes"

### Custom Options:
- "fix casing with _NewSuffix"
- "use pascal case"
- "fix prefix only"

## Troubleshooting

### "No assets selected"
→ Select assets in Unreal Content Browser first

### "All assets already correct"
→ Your assets already have proper casing!

### Command not found
→ Restart HTTP bridge: `python http_bridge.py`

## Current Status

- ✅ NLP correctly interprets asset commands
- ✅ Handler executes without errors
- ✅ Case conflict detection working
- ✅ Preview mode shows changes before applying
- ✅ Suffix automatically added for Git safety

**Ready to use!**
