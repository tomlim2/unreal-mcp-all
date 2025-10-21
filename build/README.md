# Build Scripts

This directory contains scripts and configuration for building and packaging MegaMelange.

## Scripts

### `package.bat`
Creates a complete deployment package (MegaMelange-v*.zip) ready for distribution.

**Usage:**
```bash
cd build
package.bat
```

**Output:**
- Creates `MegaMelange-v1.0.0/` directory with:
  - Backend executable (MegaMelangeBackend.exe)
  - Frontend standalone build
  - Configuration files (config.json.example)
  - User documentation (README.txt)
  - Start script (START.bat)
- Generates `MegaMelange-v1.0.0.zip` (67MB)

### `INSTALL_AND_BUILD.bat`
Comprehensive build script that:
1. Installs Python dependencies
2. Builds backend with PyInstaller
3. Installs Frontend dependencies
4. Builds Frontend in standalone mode

### `init.bat`
Initializes development environment (Python virtual environment, npm packages)

### `START_BUILD.bat`
Quick rebuild script for development

## Configuration

### `../Python/build_backend.spec`
PyInstaller configuration for backend packaging.

**Key settings:**
- Hidden imports for plugin system
- Data files inclusion (tools/, data_storage/)
- Exclusions for unused packages
- Icon and manifest settings

## Build Process

### Development Build
```bash
# Backend only
cd Python
python -m PyInstaller build_backend.spec

# Frontend only
cd Frontend
npm run build
```

### Production Package
```bash
cd build
package.bat
```

## Troubleshooting

### Common Issues

**Backend build fails:**
- Check Python virtual environment is activated
- Verify all dependencies installed: `pip install -r requirements.txt`

**Frontend build fails:**
- Delete `node_modules` and `.next` directories
- Reinstall: `npm install`

**Package script fails:**
- Ensure both backend and frontend are built first
- Check disk space (needs ~200MB free)

## Related Documentation

- Build guide: `BUILD_NOW.txt`
- Build documentation: `README_BUILD.txt`
- Developer guide: `../docs/CLAUDE.md`
