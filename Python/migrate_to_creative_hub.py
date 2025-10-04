#!/usr/bin/env python3
"""
Creative Hub Migration Script

Helps migrate from legacy command handlers to the new plugin-based architecture.

Usage:
    python migrate_to_creative_hub.py --check     # Check current status
    python migrate_to_creative_hub.py --enable    # Enable plugin system
    python migrate_to_creative_hub.py --verify    # Verify both systems work
    python migrate_to_creative_hub.py --migrate   # Full migration
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add Python directory to path
sys.path.insert(0, str(Path(__file__).parent))


def check_status():
    """Check current migration status."""
    print("\n" + "=" * 60)
    print("Creative Hub Migration Status")
    print("=" * 60)

    # Check .env file
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("❌ .env file not found")
        print("   Copy .env.example to .env and configure")
        return False

    # Read .env
    env_vars = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value

    # Check feature flags
    plugin_enabled = env_vars.get('FEATURE_PLUGIN_SYSTEM', 'false').lower() == 'true'
    orchestrator_enabled = env_vars.get('FEATURE_ORCHESTRATOR', 'false').lower() == 'true'
    legacy_enabled = env_vars.get('FEATURE_LEGACY_HANDLERS', 'true').lower() == 'true'

    print(f"\nFeature Flags:")
    print(f"  Plugin System:    {'✅ ENABLED' if plugin_enabled else '❌ DISABLED'}")
    print(f"  Orchestrator:     {'✅ ENABLED' if orchestrator_enabled else '❌ DISABLED'}")
    print(f"  Legacy Handlers:  {'✅ ENABLED' if legacy_enabled else '❌ DISABLED'}")

    # Check tool metadata
    tools_dir = Path(__file__).parent / "tools"
    nano_metadata = tools_dir / "nano_banana" / "metadata.json"
    unreal_metadata = tools_dir / "unreal_engine" / "metadata.json"

    print(f"\nTool Metadata:")
    print(f"  Nano Banana:      {'✅ EXISTS' if nano_metadata.exists() else '❌ MISSING'}")
    print(f"  Unreal Engine:    {'✅ EXISTS' if unreal_metadata.exists() else '❌ MISSING'}")

    # Check plugin files
    nano_plugin = tools_dir / "nano_banana" / "plugin.py"
    unreal_plugin = tools_dir / "unreal_engine" / "plugin.py"

    print(f"\nPlugin Files:")
    print(f"  Nano Banana:      {'✅ EXISTS' if nano_plugin.exists() else '❌ MISSING'}")
    print(f"  Unreal Engine:    {'✅ EXISTS' if unreal_plugin.exists() else '❌ MISSING'}")

    # Migration status
    print(f"\n" + "=" * 60)
    if plugin_enabled and orchestrator_enabled and legacy_enabled:
        print("Status: TRANSITION MODE")
        print("  Both plugin system and legacy handlers are active")
        print("  Ready for gradual migration")
    elif plugin_enabled and not legacy_enabled:
        print("Status: FULLY MIGRATED")
        print("  Plugin system active, legacy handlers disabled")
    elif not plugin_enabled and legacy_enabled:
        print("Status: LEGACY MODE")
        print("  Using legacy handlers only")
    else:
        print("Status: UNKNOWN")
        print("  Check your feature flags configuration")

    print("=" * 60 + "\n")
    return True


def enable_plugin_system():
    """Enable the plugin system in .env."""
    print("\n" + "=" * 60)
    print("Enabling Plugin System")
    print("=" * 60)

    env_path = Path(__file__).parent / ".env"

    # Read current .env
    lines = []
    if env_path.exists():
        with open(env_path) as f:
            lines = f.readlines()

    # Update or add feature flags
    flags = {
        'FEATURE_PLUGIN_SYSTEM': 'true',
        'FEATURE_ORCHESTRATOR': 'true',
        'FEATURE_LEGACY_HANDLERS': 'true'  # Keep legacy enabled for transition
    }

    updated_flags = set()
    for i, line in enumerate(lines):
        for flag, value in flags.items():
            if line.strip().startswith(flag + '='):
                lines[i] = f"{flag}={value}\n"
                updated_flags.add(flag)
                print(f"✓ Updated {flag}={value}")

    # Add missing flags
    for flag, value in flags.items():
        if flag not in updated_flags:
            lines.append(f"{flag}={value}\n")
            print(f"✓ Added {flag}={value}")

    # Write back
    with open(env_path, 'w') as f:
        f.writelines(lines)

    print("\n✓ Plugin system enabled")
    print("  Restart your backend server for changes to take effect")
    print("=" * 60 + "\n")


def verify_systems():
    """Verify both plugin and legacy systems work."""
    print("\n" + "=" * 60)
    print("Verifying Systems")
    print("=" * 60)

    try:
        from core import get_registry, get_config

        config = get_config()

        print(f"\nConfiguration:")
        print(f"  Plugin System: {config.features.enable_plugin_system}")
        print(f"  Orchestrator: {config.features.enable_orchestrator}")
        print(f"  Legacy: {config.features.enable_legacy_handlers}")

        if config.features.enable_plugin_system:
            registry = get_registry()
            metadata = registry.get_all_metadata()

            print(f"\nDiscovered Tools:")
            for tool_id, meta in metadata.items():
                print(f"  ✓ {tool_id}: {meta.display_name} v{meta.version}")

            # Test health
            health = registry.get_health_status()
            print(f"\nTool Health:")
            for tool_id, status in health.items():
                print(f"  {tool_id}: {status.value}")

        print("\n✓ Systems verified successfully")

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("=" * 60 + "\n")
    return True


def full_migration():
    """Run full migration process."""
    print("\n" + "=" * 60)
    print("Full Migration to Creative Hub")
    print("=" * 60)

    # Step 1: Check status
    print("\n[Step 1/4] Checking current status...")
    if not check_status():
        return False

    input("Press Enter to continue...")

    # Step 2: Enable plugin system
    print("\n[Step 2/4] Enabling plugin system...")
    enable_plugin_system()

    input("Press Enter to continue...")

    # Step 3: Verify systems
    print("\n[Step 3/4] Verifying systems...")
    if not verify_systems():
        print("\n❌ Verification failed. Migration aborted.")
        return False

    input("Press Enter to continue to final step...")

    # Step 4: Instructions for disabling legacy
    print("\n[Step 4/4] Final Migration Steps")
    print("-" * 60)
    print("After verifying everything works correctly:")
    print("1. Monitor your application for any issues")
    print("2. Test all critical functionality")
    print("3. When ready, disable legacy handlers:")
    print("   Edit .env: FEATURE_LEGACY_HANDLERS=false")
    print("4. Restart backend server")
    print("5. Test again to ensure plugin system handles all commands")
    print("-" * 60)

    print("\n✓ Migration process complete!")
    print("  Follow the instructions above to complete the transition")
    print("=" * 60 + "\n")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Creative Hub Migration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate_to_creative_hub.py --check     # Check status
  python migrate_to_creative_hub.py --enable    # Enable plugin system
  python migrate_to_creative_hub.py --verify    # Verify systems
  python migrate_to_creative_hub.py --migrate   # Full migration
        """
    )

    parser.add_argument('--check', action='store_true', help='Check migration status')
    parser.add_argument('--enable', action='store_true', help='Enable plugin system')
    parser.add_argument('--verify', action='store_true', help='Verify systems')
    parser.add_argument('--migrate', action='store_true', help='Run full migration')

    args = parser.parse_args()

    if args.check:
        check_status()
    elif args.enable:
        enable_plugin_system()
    elif args.verify:
        verify_systems()
    elif args.migrate:
        full_migration()
    else:
        parser.print_help()
        print("\n" + "=" * 60)
        print("Quick Start:")
        print("  python migrate_to_creative_hub.py --migrate")
        print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
