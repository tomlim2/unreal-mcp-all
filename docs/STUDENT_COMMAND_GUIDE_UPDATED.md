# Student Guide: Adding New NLP Commands (Updated)

This guide shows you how to add new commands that work through natural language processing based on the latest refactored architecture. Users can say things like "make it rain" and your command will execute automatically with session context support.

## Overview

The refactored NLP system now includes:
- **Session Management** - Commands remember conversation context
- **Unified Processing** - Single entry point for all natural language requests
- **Enhanced Context** - AI understands previous interactions and scene state
- **Simplified Architecture** - Cleaner separation between NLP processing and command execution

## Updated Architecture

```
Natural Language Input: "Make it stormy like yesterday"
        ↓
process_natural_language() with session_id
        ↓
AI Processing with Session Context (build_system_prompt_with_session)
        ↓
Command Handler: Validates and executes with context awareness
        ↓
Session Update: Stores interaction for future context
        ↓
Unreal Engine: Receives command and responds
```

**Key Files:**
```
Python/
├── tools/ai/
│   ├── nlp.py                           # Main NLP processing (REFACTORED)
│   ├── session_management/              # Session context system
│   └── actor_command_handlers/
│       ├── __init__.py                  # Handler registry
│       ├── main.py                      # Base handler class
│       └── your_handler.py              # Your new handler
```

## Key Changes in Refactored System

### 1. New Main Function Signature
```python
# NEW: Session-aware processing
def process_natural_language(
    user_input: str, 
    context: str = None, 
    session_id: str = None
) -> Dict[str, Any]:

# OLD: Simple processing
def _process_natural_language_impl(
    user_input: str, 
    context: str = None
) -> Dict[str, Any]:
```

### 2. Session Context Integration
```python
# Automatic session management
if session_id:
    session_manager = get_session_manager()
    session_context = session_manager.get_or_create_session(session_id)
    # AI gets conversation history and scene state
```

### 3. Enhanced System Prompt
```python
# Context-aware prompt building
system_prompt = build_system_prompt_with_session(context, session_context)
# Includes conversation history and current scene state
```

## Step 1: Create Your Command Handler (Same as Before)

Create `tools/ai/actor_command_handlers/your_category.py`:

```python
"""
Your Category Command Handler for NLP system with session support.
"""

import logging
from typing import Dict, Any, List
from .main import BaseCommandHandler

logger = logging.getLogger("UnrealMCP")

class ValidatedCommand:
    """Result of command validation."""
    def __init__(self, command_type: str, params: Dict[str, Any], is_valid: bool, errors: List[str] = None):
        self.type = command_type
        self.params = params
        self.is_valid = is_valid
        self.validation_errors = errors or []

class YourCategoryHandler(BaseCommandHandler):
    """Handler for your category with session context awareness."""
    
    def get_supported_commands(self) -> List[str]:
        return ["your_command_1", "your_command_2", "your_command_3"]
    
    def validate_command(self, command_type: str, params: Dict[str, Any]):
        """Validate with enhanced context awareness."""
        errors = []
        validated_params = params.copy()
        
        if command_type == "your_command_1":
            # Standard validation
            if "required_param" not in params:
                errors.append("required_param is required")
            
            # Context-aware validation
            # Handler can access session context through the registry system
            
        return ValidatedCommand(
            command_type=command_type,
            params=validated_params,
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced preprocessing with session awareness."""
        processed = params.copy()
        
        # Add session-aware intelligent defaults
        if command_type == "your_command_1":
            # Access session context if available
            try:
                from tools.ai.session_management import get_session_manager
                session_manager = get_session_manager()
                # Use context for smarter defaults
            except:
                # Fallback to standard defaults
                pass
                
        return processed
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute with session context logging."""
        logger.info(f"Executing {command_type} with session-aware params: {params}")
        
        try:
            response = connection.send_command(command_type, params)
            
            if not response:
                raise Exception("No response from Unreal Engine")
            
            if response.get("status") == "error":
                error_msg = response.get("error", "Unknown Unreal error")
                raise Exception(f"Unreal Engine error: {error_msg}")
            
            # Add contextual feedback
            if response.get("success"):
                response["session_aware"] = True
                response["context_description"] = self._generate_context_feedback(command_type, params)
            
            return response
            
        except Exception as e:
            logger.error(f"Session-aware command {command_type} failed: {e}")
            raise
    
    def _generate_context_feedback(self, command_type: str, params: Dict[str, Any]) -> str:
        """Generate context-aware feedback for users."""
        # Create natural language descriptions based on command and session context
        return f"Executed {command_type} - effects should be visible in your scene"
```

## Step 2: Register Your Handler (Same Process)

Update both registration files:

### `__init__.py`
```python
from .your_category import YourCategoryHandler

__all__ = [
    # ... existing handlers ...
    'YourCategoryHandler'
]
```

### `main.py` 
```python
def _initialize_default_handlers(self):
    from .your_category import YourCategoryHandler
    
    handlers = [
        # ... existing handlers ...
        YourCategoryHandler()
    ]
```

## Step 3: Update System Prompt (Enhanced)

The system prompt now automatically includes session context, but you still need to document your commands:

```python
# In build_system_prompt_with_session() function in nlp.py
base_prompt = f"""You are a creative cinematic director's AI assistant with session memory.

## SUPPORTED COMMANDS
**Ultra Dynamic Sky:** get_ultra_dynamic_sky, set_time_of_day, set_color_temperature
**Your Category:** your_command_1, your_command_2, your_command_3  # Add here
**Generic Actors:** get_actors_in_level, create_actor, delete_actor

## PARAMETER VALIDATION RULES
**Your Category Commands:**
- required_param: Non-empty string (default context-aware)
- intensity: Range 0.0-1.0 or descriptive words (session-aware defaults)

## SESSION AWARENESS
- Reference previous commands: "make it brighter like before"
- Use scene context: "adjust that red light we created"
- Remember user preferences: "use my usual settings"

## CONVERSIONS
**Your Category:** "intense like last time"→check session history for previous intensity values
"""
```

## Step 4: Test with Session Support

### Enhanced Test Script
```python
# scripts/test_session_nlp.py
#!/usr/bin/env python3
"""Test your commands with session context."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tools.ai.nlp import process_natural_language
import uuid

def test_session_aware_commands():
    # Create a test session
    session_id = str(uuid.uuid4())
    
    # Test conversation with context building
    commands_sequence = [
        "Create a bright red light",
        "Make it dimmer", 
        "Create another light like the first one",
        "Make the scene more atmospheric"
    ]
    
    print(f"Testing session: {session_id}")
    
    for i, command in enumerate(commands_sequence):
        print(f"\n--- Step {i+1}: '{command}' ---")
        
        # Process with session context
        result = process_natural_language(
            user_input=command,
            context="Test session-aware commands",
            session_id=session_id
        )
        
        print(f"Commands: {result.get('commands')}")
        print(f"Explanation: {result.get('explanation')}")
        print(f"Results: {result.get('executionResults')}")
        
        # Check session context usage
        for cmd in result.get('commands', []):
            if cmd.get('type') in ['your_command_1', 'your_command_2']:
                print(f"✅ Your handler used with session context!")

def test_context_memory():
    """Test that the system remembers previous interactions."""
    session_id = str(uuid.uuid4())
    
    # First interaction
    result1 = process_natural_language(
        "Set weather to heavy rain",
        session_id=session_id
    )
    print(f"First: {result1.get('explanation')}")
    
    # Second interaction referring to first
    result2 = process_natural_language(
        "Make it lighter than before",
        session_id=session_id
    )
    print(f"Second: {result2.get('explanation')}")
    print(f"Context aware: {'previous' in result2.get('explanation', '').lower()}")

if __name__ == "__main__":
    test_session_aware_commands()
    print("\n" + "="*50)
    test_context_memory()
```

## Step 5: Advanced Session Features

### Context-Aware Parameter Defaults
```python
def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    processed = params.copy()
    
    if command_type == "your_command_1":
        # Check if user said "like before" or "same as last time"
        if "like_previous" in params or "intensity" not in params:
            try:
                # Get session context
                from tools.ai.session_management import get_session_manager
                session_manager = get_session_manager()
                
                # Find previous similar command
                # Use that command's intensity as default
                previous_intensity = self._get_previous_intensity(session_manager)
                if previous_intensity:
                    processed["intensity"] = previous_intensity
                    
            except Exception as e:
                logger.debug(f"Could not access session context: {e}")
                # Fall back to standard defaults
                processed.setdefault("intensity", 0.5)
    
    return processed

def _get_previous_intensity(self, session_manager) -> float:
    """Extract intensity from previous similar commands."""
    # Implementation to search session history
    # Return intensity value from previous commands
    pass
```

### Scene State Awareness
```python
def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
    response = connection.send_command(command_type, params)
    
    if response.get("success"):
        # Update session with scene state changes
        scene_change = {
            "command_type": command_type,
            "params": params,
            "timestamp": time.time(),
            "description": f"Applied {command_type} with {params}"
        }
        
        try:
            from tools.ai.session_management import get_session_manager
            session_manager = get_session_manager()
            session_manager.add_scene_state_change(scene_change)
        except:
            pass  # Session management is optional
    
    return response
```

## Step 6: New Testing Patterns

### Session Continuity Test
```python
def test_session_continuity():
    session_id = str(uuid.uuid4())
    
    # Simulate conversation over time
    conversations = [
        ("Create a moody scene", "Initial setup"),
        ("Add some fog", "Building atmosphere"),  
        ("Make it more like the beginning", "Reference to first command"),
        ("Adjust the fog intensity like before", "Reference to specific previous action")
    ]
    
    for user_input, expected_context in conversations:
        result = process_natural_language(user_input, session_id=session_id)
        
        # Verify session awareness
        explanation = result.get('explanation', '').lower()
        context_indicators = ['previous', 'before', 'earlier', 'last time', 'similar']
        
        has_context = any(indicator in explanation for indicator in context_indicators)
        print(f"Input: {user_input}")
        print(f"Context aware: {has_context}")
        print(f"Explanation: {result.get('explanation')}")
        print()
```

## Benefits of Refactored System

✅ **Session Memory** - Commands remember what happened before
✅ **Context Awareness** - "Make it brighter like last time" works automatically  
✅ **Scene State Tracking** - System knows current scene configuration
✅ **Conversation Flow** - Natural dialogue over multiple interactions
✅ **Intelligent Defaults** - Parameters based on conversation history
✅ **Enhanced UX** - Users can reference previous actions naturally

## Key Differences from Previous Guide

| Feature | Old System | New Refactored System |
|---------|------------|----------------------|
| Session Support | No | Yes, with full context |
| Main Function | `_process_natural_language_impl` | `process_natural_language` |
| Context Awareness | Limited | Full conversation & scene history |
| Parameter Defaults | Static | Context-aware and intelligent |
| User References | Not supported | "like before", "same as last time" |
| Scene Memory | No | Tracks all scene changes |

## Migration Notes

If you have existing handlers:
1. **No changes required** - handlers work with new system
2. **Optional enhancements** - add session context awareness
3. **Test with session_id** - verify context features work
4. **Update prompts** - take advantage of session context in system prompt

## Next Steps

1. **Create your handler** using the enhanced template
2. **Test session features** with conversation sequences  
3. **Add context intelligence** to your parameter processing
4. **Document session patterns** in system prompt
5. **Leverage conversation memory** for better user experience

The refactored system makes your commands much more powerful and natural to use, while maintaining backward compatibility with existing handlers.