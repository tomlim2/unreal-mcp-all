========================================
MegaMelange Standalone App - BUILD INSTRUCTIONS
========================================

STEP 1: Install Rust (if not done yet)
---------------------------------------
1. Visit: https://rustup.rs/
2. Download and run rustup-init.exe
3. Press 1 or Enter for default installation
4. Wait for installation (5-10 minutes)
5. ** CLOSE ALL TERMINAL WINDOWS **
6. Open a NEW terminal/PowerShell/CMD

STEP 2: Verify Rust Installation
---------------------------------------
In a NEW terminal, run:
   rustc --version
   cargo --version

If both commands show version numbers, proceed!
If not, restart terminal and try again.

STEP 3: Build the App
---------------------------------------
Double-click: build\START_BUILD.bat

Or in terminal:
   cd D:\vs\unreal-mcp\unreal-mcp
   build\START_BUILD.bat

Build time: 15-25 minutes (first time)

STEP 4: Find Your App
---------------------------------------
After successful build:

Executable:
   Frontend\src-tauri\target\release\megamelange-desktop.exe

Windows Installer:
   Frontend\src-tauri\target\release\bundle\msi\

========================================
TROUBLESHOOTING
========================================

"rustc not found"
--> Terminal not restarted after Rust install
--> Close ALL terminals and open NEW one

Build errors
--> See detailed guides:
    - RUST_INSTALL_GUIDE.md
    - BUILD_STANDALONE_APP.md
    - QUICK_START.md

========================================
