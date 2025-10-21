========================================
  MegaMelange v1.0.0 - Setup Guide
========================================

MegaMelange is an AI-powered creative hub that enables natural language control for
Unreal Engine, AI image generation, and creative workflows.

========================================
  Quick Start (3 Steps)
========================================

1. Edit config.json
   - Open config.json with Notepad
   - Add your Google API Key (REQUIRED)
   - Add Blender path (if using Roblox features)
   - Save the file

2. Run START.bat
   - Double-click START.bat
   - Wait for services to start (~10 seconds)
   - Browser will open automatically

3. Start Creating!
   - Use natural language commands
   - Generate AI images
   - Control Unreal Engine (if plugin installed)

========================================
  Configuration Details
========================================

config.json Settings:

GOOGLE_API_KEY (REQUIRED)
  - Get your key from: https://makersuite.google.com/app/apikey
  - Used for: NLP processing and AI image generation
  - Example: "GOOGLE_API_KEY": "AIzaSyABC123..."

BLENDER_PATH (Optional - for Roblox features)
  - Path to your Blender installation
  - Default: "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe"
  - Only needed if you want to convert Roblox avatars to FBX

ANTHROPIC_API_KEY (Optional)
  - Alternative NLP provider
  - Get key from: https://console.anthropic.com/

OPENAI_API_KEY (Optional)
  - Future features
  - Get key from: https://platform.openai.com/api-keys

UNREAL_PROJECT_PATH (Optional)
  - Auto-detected in most cases
  - Manually set if screenshots don't load correctly

========================================
  System Requirements
========================================

Minimum:
  - Windows 10/11 (64-bit)
  - 4GB RAM
  - Internet connection (for API calls)

Optional:
  - Unreal Engine 5.3+ (for Unreal features)
  - Blender 3.0+ (for Roblox FBX conversion)

========================================
  Usage
========================================

Starting MegaMelange:
  - Double-click START.bat
  - Wait for browser to open
  - Use the web interface at: http://localhost:34115

Stopping MegaMelange:
  - Press any key in the START.bat window
  - Or close the window directly

========================================
  Features
========================================

AI Image Generation (Nano Banana):
  - Text-to-Image: Generate images from descriptions
  - Image-to-Image: Transform existing images
  - Style Transfer: Apply artistic styles
  - Image Editing: AI-powered modifications

Unreal Engine Integration (requires plugin):
  - Natural language scene control
  - Lighting and camera management
  - Actor creation and manipulation
  - High-resolution screenshot capture

Roblox Pipeline:
  - Download Roblox avatars
  - Convert OBJ to FBX (R6 avatars only)
  - Import to Unreal Engine with rigging

========================================
  Troubleshooting
========================================

"config.json not found"
  → The config.json file must be in the same folder as START.bat

"GOOGLE_API_KEY is required"
  → Open config.json and add your API key
  → Make sure there are no extra spaces

"Backend failed to start"
  → Check if port 8080 is already in use
  → Try closing other applications using that port

"Frontend failed to start"
  → Check if port 34115 is already in use
  → Make sure Node.js is working properly

"Blender executable not found"
  → Update BLENDER_PATH in config.json
  → Use double backslashes in path: C:\\Program Files\\...

Browser doesn't open automatically
  → Manually open: http://localhost:34115
  → Make sure both backend and frontend started successfully

========================================
  File Structure
========================================

MegaMelange/
├── START.bat                   # Main launcher
├── config.json                 # Your configuration
├── README.txt                  # This file
├── MegaMelangeBackend.exe     # Python backend (50MB)
└── frontend/                   # Next.js frontend
    └── server.js               # Frontend server

========================================
  Support & Updates
========================================

For issues or questions:
  - GitHub: https://github.com/chongdashu/unreal-mcp
  - Twitter: @chongdashu

Thank you for using MegaMelange!

========================================
