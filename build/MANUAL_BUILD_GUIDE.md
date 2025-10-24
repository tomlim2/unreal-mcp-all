# MegaMelange - Beginner-Friendly Manual Build Guide

This guide explains how to manually rebuild MegaMelange when you make code changes.

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [When to Rebuild What](#when-to-rebuild-what)
3. [Step-by-Step Build Instructions](#step-by-step-build-instructions)
4. [Common Scenarios](#common-scenarios)
5. [Troubleshooting](#troubleshooting)

---

## Quick Reference

| What Changed | What to Rebuild | Command |
|--------------|----------------|---------|
| Python backend code | Backend only | `cd Python && build_backend.bat` |
| Frontend code (React/Next.js) | Frontend only | `cd Frontend && npm run build` |
| Both backend & frontend | Both | `cd build && package.bat` |
| Want to create deployment ZIP | Full package | `cd build && package.bat` |

---

## When to Rebuild What

### Backend Changes (Python/)
**When to rebuild:**
- Modified any `.py` files
- Changed command handlers
- Updated plugin system
- Modified API endpoints

**How to rebuild:**
```batch
cd Python
build_backend.bat
```

**Output:** `Python/dist/MegaMelangeBackend.exe`

### Frontend Changes (Frontend/)
**When to rebuild:**
- Modified React components
- Changed UI styling
- Updated API calls
- Modified Next.js configuration

**How to rebuild:**
```batch
cd Frontend
npm run build
```

**Output:** `Frontend/.next/standalone/`

### Full Package (Both + ZIP)
**When to create:**
- Ready to deploy to users
- Want to test the complete package
- Preparing a release

**How to build:**
```batch
cd build
package.bat
```

**Output:** `MegaMelange-v1.0.0.zip` and `dist-package/` folder

---

## Step-by-Step Build Instructions

### Option 1: Backend Only (Fastest - 2-5 minutes)

**Use this when:** You only changed Python code

```batch
# Step 1: Navigate to Python folder
cd D:\vs\unreal-mcp\unreal-mcp\Python

# Step 2: Run build script
build_backend.bat

# Step 3: Verify output
dir dist\MegaMelangeBackend.exe
```

**Expected output:**
```
========================================
Build Complete!
========================================

Executable location: dist\MegaMelangeBackend.exe
Size: ~50 MB
```

### Option 2: Frontend Only (Medium - 2-3 minutes)

**Use this when:** You only changed frontend code

```batch
# Step 1: Navigate to Frontend folder
cd D:\vs\unreal-mcp\unreal-mcp\Frontend

# Step 2: Run build
npm run build

# Step 3: Verify output
dir .next\standalone\server.js
```

**Expected output:**
```
✓ Compiled successfully
✓ Collecting page data
✓ Generating static pages
✓ Finalizing page optimization

Route (app)                              Size     First Load JS
┌ ○ /                                    5.2 kB         95.3 kB
└ ○ /api/chat                            0 B                0 B
```

### Option 3: Full Package (Slowest - 8-15 minutes)

**Use this when:** Creating deployment package for distribution

```batch
# Step 1: Navigate to build folder
cd D:\vs\unreal-mcp\unreal-mcp\build

# Step 2: Run package script
package.bat

# Step 3: Verify output
dir ..\MegaMelange-v1.0.0.zip
```

**Expected output:**
```
========================================
  Build Complete!
========================================

Package created: MegaMelange-v1.0.0.zip
Size: ~67 MB

Distribution folder: dist-package\
```

---

## Common Scenarios

### Scenario 1: Fixed a Bug in Python Command Handler

**What you did:** Modified `Python/tools/ai/command_handlers/actor/light.py`

**What to do:**
```batch
cd D:\vs\unreal-mcp\unreal-mcp\Python
build_backend.bat
```

**Test the fix:**
```batch
cd ..
START.bat
# Open browser to http://localhost:3000
# Test the light command
```

### Scenario 2: Updated Frontend UI Component

**What you did:** Modified `Frontend/src/app/components/UnrealAIChat.tsx`

**What to do:**
```batch
cd D:\vs\unreal-mcp\unreal-mcp\Frontend
npm run build
```

**Test the change:**
```batch
cd ..
START.bat
# Open browser to http://localhost:3000
# Check the UI changes
```

### Scenario 3: Ready to Share with Others

**What you did:** Fixed multiple bugs, ready to share

**What to do:**
```batch
cd D:\vs\unreal-mcp\unreal-mcp\build
package.bat
```

**Share the package:**
1. Upload `MegaMelange-v1.0.0.zip` to Google Drive / GitHub
2. Share the download link
3. Recipients extract and run `START.bat`

### Scenario 4: Changed Both Backend and Frontend

**What you did:** Modified both Python and Frontend code

**Option A - Rebuild separately (faster iteration):**
```batch
# Backend
cd D:\vs\unreal-mcp\unreal-mcp\Python
build_backend.bat

# Frontend
cd ..\Frontend
npm run build
```

**Option B - Full package (for distribution):**
```batch
cd D:\vs\unreal-mcp\unreal-mcp\build
package.bat
```

---

## Troubleshooting

### Issue: "PyInstaller not found"

**Error message:**
```
ModuleNotFoundError: No module named 'PyInstaller'
```

**Solution:**
```batch
cd Python
pip install pyinstaller
```

### Issue: "npm not found"

**Error message:**
```
'npm' is not recognized as an internal or external command
```

**Solution:**
1. Install Node.js from https://nodejs.org/
2. Restart terminal
3. Verify: `npm --version`

### Issue: Build succeeds but EXE is missing

**Symptom:** Build completes but `MegaMelangeBackend.exe` not found

**Solution:**
```batch
cd Python

# Clean old builds
rmdir /s /q build
rmdir /s /q dist

# Rebuild
build_backend.bat
```

### Issue: Frontend build fails with memory error

**Error message:**
```
JavaScript heap out of memory
```

**Solution:**
```batch
cd Frontend

# Increase Node.js memory
set NODE_OPTIONS=--max-old-space-size=4096

# Rebuild
npm run build
```

### Issue: Package.bat fails at ZIP creation

**Error message:**
```
[ERROR] Failed to create ZIP file!
```

**Solution:**
1. Check disk space (need ~200MB free)
2. Close any programs using the files
3. Delete old ZIP file manually:
   ```batch
   del MegaMelange-v1.0.0.zip
   ```
4. Run `package.bat` again

### Issue: Changes not reflected after rebuild

**Symptom:** Rebuilt but changes don't appear

**Solution:**
```batch
# 1. Stop any running instances
# Close browser, close START.bat window

# 2. Clean build artifacts
cd Python
rmdir /s /q build
rmdir /s /q dist

cd ..\Frontend
rmdir /s /q .next

# 3. Rebuild
cd ..\build
package.bat
```

---

## Build File Reference

### build/ Folder Contents

```
build/
├── package.bat                 # Creates full deployment package + ZIP
├── INSTALL_AND_BUILD.bat       # Builds backend + frontend + Tauri app
├── START_BUILD.bat             # Simplified Tauri build launcher
├── BUILD_NOW.txt               # Quick start guide (Korean)
├── README_BUILD.txt            # Build instructions
├── README.md                   # Build scripts documentation
└── MANUAL_BUILD_GUIDE.md       # This file
```

### What Each Script Does

**package.bat** (5-10 minutes)
- Builds Python backend (PyInstaller)
- Builds Next.js frontend (standalone mode)
- Creates deployment folder structure
- Copies all necessary files
- Creates ZIP archive

**INSTALL_AND_BUILD.bat** (15-25 minutes)
- Checks Rust installation
- Builds Python backend
- Builds Next.js frontend
- Builds Tauri desktop app (takes longest)

**START_BUILD.bat** (15-25 minutes)
- Simplified wrapper for INSTALL_AND_BUILD.bat
- Shows nice progress messages
- Opens release folder when done

---

## Tips for Efficient Development

### 1. Incremental Builds
Only rebuild what changed:
- Backend change → `Python/build_backend.bat`
- Frontend change → `Frontend/npm run build`

### 2. Test Before Packaging
Always test with `START.bat` before creating deployment package:
```batch
# Make changes
cd Python
build_backend.bat

# Test immediately
cd ..
START.bat
# Test in browser

# Only package when ready
cd build
package.bat
```

### 3. Version Control
Before building:
```batch
# Check what changed
git status

# Commit your changes
git add -A
git commit -m "fix: description of your fix"

# Then build
cd build
package.bat
```

### 4. Build Log Review
If build fails, check these logs:
- **Backend:** Terminal output from `build_backend.bat`
- **Frontend:** Terminal output from `npm run build`
- **Package:** Terminal output from `package.bat`

---

## Next Steps

### After Successful Build

**For local testing:**
1. Run `START.bat` from project root
2. Open browser to http://localhost:3000
3. Test your changes
4. Stop with Ctrl+C in terminal

**For distribution:**
1. Extract `MegaMelange-v1.0.0.zip` to test folder
2. Edit `config.json` with API keys
3. Run `START.bat` to test
4. If works, share the ZIP file

### Getting Help

If you encounter issues not covered here:

1. **Check logs:** Look for error messages in terminal
2. **Search docs:** See docs/CLAUDE.md for architecture details
3. **Discord:** (Add community Discord link here)

---

## Glossary

- **Backend:** Python server that processes commands (MegaMelangeBackend.exe)
- **Frontend:** Web interface (Next.js React app)
- **PyInstaller:** Tool that packages Python into standalone EXE
- **Standalone mode:** Next.js build that includes its own Node.js server
- **Distribution package:** Complete folder ready for users (backend + frontend + config)
- **Deployment package:** ZIP file containing distribution package

---

**Last Updated:** 2025-01-XX
**For:** MegaMelange v1.0.0
