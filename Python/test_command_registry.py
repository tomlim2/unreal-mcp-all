"""Test script to verify command registration"""
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("Testing Command Registry")
logger.info("=" * 60)

# Import registry
from tools.ai.command_handlers import get_command_registry

registry = get_command_registry()

# Get all supported commands
commands = registry.get_supported_commands()

logger.info(f"\nTotal registered commands: {len(commands)}")
logger.info(f"Commands: {sorted(commands)}\n")

# Check specifically for take_screenshot
if "take_screenshot" in commands:
    logger.info("✓ take_screenshot IS registered")
    handler = registry.get_handler("take_screenshot")
    logger.info(f"  Handler: {handler.__class__.__name__}")
else:
    logger.error("✗ take_screenshot NOT registered")

# Check for our new commands
if "get_selected_assets" in commands:
    logger.info("✓ get_selected_assets IS registered")
else:
    logger.error("✗ get_selected_assets NOT registered")

if "rename_assets_batch" in commands:
    logger.info("✓ rename_assets_batch IS registered")
else:
    logger.error("✗ rename_assets_batch NOT registered")

logger.info("\n" + "=" * 60)
