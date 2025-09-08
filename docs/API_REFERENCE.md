# Unreal MCP API Reference

Complete API reference for all functions, classes, and interfaces in the Unreal MCP system.

## Table of Contents

1. [Session Management API](#session-management-api)
2. [NLP Processing API](#nlp-processing-api)  
3. [Command Handler API](#command-handler-api)
4. [Storage Backend API](#storage-backend-api)
5. [Utility Functions](#utility-functions)
6. [Type Definitions](#type-definitions)

---

## Session Management API

### SessionManager

**Main session management class with database-only storage.**

```python
class SessionManager:
    def __init__(self, storage_type: str = 'supabase', auto_cleanup: bool = True, 
                 cleanup_interval_hours: int = 6, session_max_age_days: int = 30)
```

#### Parameters
- `storage_type` (str): Storage backend type (default: 'supabase')
- `auto_cleanup` (bool): Whether to start automatic cleanup (default: True)
- `cleanup_interval_hours` (int): How often to run cleanup (default: 6)
- `session_max_age_days` (int): Maximum session age before deletion (default: 30)

#### Methods

##### `create_session(session_id: str = None) -> Optional[SessionContext]`
Create a new session.

**Parameters:**
- `session_id` (str, optional): Session ID. If None, generates a new one.

**Returns:** `SessionContext` if successful, `None` otherwise

**Example:**
```python
session_manager = SessionManager()
session = session_manager.create_session("user_123_session")
```

##### `get_session(session_id: str) -> Optional[SessionContext]`
Retrieve a session by ID.

**Parameters:**
- `session_id` (str): The session ID to retrieve

**Returns:** `SessionContext` if found, `None` otherwise

##### `update_session(session_context: SessionContext) -> bool`
Update an existing session.

**Parameters:**
- `session_context` (SessionContext): The updated session context

**Returns:** `True` if successful, `False` otherwise

##### `delete_session(session_id: str) -> bool`
Delete a session by ID.

**Parameters:**
- `session_id` (str): The session ID to delete

**Returns:** `True` if successful, `False` otherwise

##### `add_interaction(session_id: str, user_input: str, ai_response: Dict[str, Any]) -> bool`
Add a complete user-AI interaction to a session.

**Parameters:**
- `session_id` (str): The session ID
- `user_input` (str): The user's input
- `ai_response` (Dict[str, Any]): The AI's response from NLP processing

**Returns:** `True` if successful, `False` otherwise

**Example:**
```python
session_manager.add_interaction(
    "user_123_session",
    "Make it rain",
    {
        "explanation": "Setting weather to rain",
        "commands": [{"type": "set_weather", "params": {"weather_type": "rain"}}],
        "executionResults": [{"command": "set_weather", "success": True, "result": {...}}]
    }
)
```

##### `get_or_create_session(session_id: str = None) -> Optional[SessionContext]`
Get an existing session or create a new one.

##### `list_sessions(limit: int = 50, offset: int = 0) -> List[SessionContext]`
List sessions with pagination.

##### `cleanup_expired_sessions(max_age: timedelta = timedelta(days=30)) -> int`
Manually trigger cleanup of expired sessions.

##### `get_session_count() -> int`
Get total number of sessions.

##### `get_health_status() -> Dict[str, Any]`
Get health status of storage backend.

---

### SessionContext

**Complete session context including conversation and scene state.**

```python
@dataclass
class SessionContext:
    session_id: str
    created_at: datetime
    last_accessed: datetime
    conversation_history: List[ChatMessage] = field(default_factory=list)
    scene_state: SceneState = field(default_factory=SceneState)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

#### Methods

##### `add_message(role: str, content: str, commands: List[Dict[str, Any]] = None, execution_results: List[Dict[str, Any]] = None)`
Add a new message to the conversation history.

**Parameters:**
- `role` (str): Message sender: "user", "assistant", "system"
- `content` (str): The message content
- `commands` (List[Dict], optional): Commands in this message
- `execution_results` (List[Dict], optional): Command execution results

##### `add_interaction(user_input: str, ai_response: Dict[str, Any])`
Add a complete user-AI interaction.

**Parameters:**
- `user_input` (str): User's message
- `ai_response` (Dict): Complete AI response with commands and results

##### `get_conversation_summary(max_messages: int = 10) -> str`
Get a summary of recent conversation for AI context.

##### `get_scene_summary() -> str`  
Get a summary of current scene state for AI context.

##### `to_dict() -> Dict[str, Any]`
Convert to dictionary for JSON serialization.

##### `from_dict(data: Dict[str, Any]) -> 'SessionContext'`
Create from dictionary (JSON deserialization).

---

## NLP Processing API

### Main Functions

##### `process_natural_language(user_input: str, context: str = None, session_id: str = None) -> Dict[str, Any]`
Process natural language input and return structured commands with optional session support.

**Parameters:**
- `user_input` (str): Natural language input from user
- `context` (str, optional): Additional context for AI processing
- `session_id` (str, optional): Session ID for context awareness

**Returns:** Dict with structure:
```python
{
    "explanation": "Brief description of what will happen",
    "commands": [{"type": "command_name", "params": {...}}],
    "expectedResult": "What the user should expect",
    "executionResults": [
        {
            "command": "command_name",
            "success": bool,
            "result": {...},  # Full Unreal Engine response
            "validation": "passed|failed"
        }
    ]
}
```

**Example:**
```python
result = process_natural_language(
    "Create a bright red light", 
    context="cinematic scene setup",
    session_id="user_123_session"
)
```

##### `build_system_prompt_with_session(context: str, session_context: SessionContext = None) -> str`
Build system prompt with session context information.

##### `execute_command_direct(command: Dict[str, Any]) -> Any`
Execute a command directly using Unreal connection with handler system.

**Parameters:**
- `command` (Dict): Command with "type" and "params" keys

**Returns:** Raw response from Unreal Engine

---

## Command Handler API

### BaseCommandHandler

**Abstract base class for all command handlers.**

```python
class BaseCommandHandler(ABC):
    @abstractmethod
    def get_supported_commands(self) -> List[str]:
        """Return list of command types this handler supports."""
        pass
    
    @abstractmethod
    def validate_command(self, command_type: str, params: Dict[str, Any]):
        """Validate command parameters using schema validation."""
        pass
    
    @abstractmethod
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute the validated command using the Unreal connection."""
        pass
    
    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Override to add command-specific parameter preprocessing."""
        return params.copy()
```

### CommandRegistry

**Registry for managing command handlers with unified execution interface.**

##### `register_handler(command_type: str, handler: BaseCommandHandler)`
Register a custom handler for a command type.

##### `get_handler(command_type: str) -> Optional[BaseCommandHandler]`
Get handler for a specific command type.

##### `get_supported_commands() -> List[str]`
Get list of all supported command types.

##### `execute_command(command: Dict[str, Any], connection) -> Any`
Execute command using appropriate handler with full validation pipeline.

### Built-in Handlers

#### UDSCommandHandler
Handles Ultra Dynamic Sky commands:
- `get_ultra_dynamic_sky`
- `set_time_of_day`
- `set_color_temperature`

#### LightCommandHandler
Handles MM Control Light commands:
- `create_mm_control_light`
- `get_mm_control_lights`
- `update_mm_control_light`
- `delete_mm_control_light`

#### ActorCommandHandler
Handles generic actor commands:
- `get_actors_in_level`
- `create_actor`
- `delete_actor`
- `set_actor_transform`
- `get_actor_properties`
- `find_actors_by_name`

#### CesiumCommandHandler
Handles Cesium geospatial commands:
- `set_cesium_latitude_longitude`
- `get_cesium_properties`

---

## Storage Backend API

### BaseStorage

**Abstract base class for all storage backends.**

```python
class BaseStorage(ABC):
    @abstractmethod
    def create_session(self, session_context: SessionContext) -> bool:
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        pass
    
    @abstractmethod
    def update_session(self, session_context: SessionContext) -> bool:
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        pass
    
    @abstractmethod
    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[SessionContext]:
        pass
    
    @abstractmethod
    def cleanup_expired_sessions(self, max_age: timedelta) -> int:
        pass
    
    @abstractmethod
    def get_session_count(self) -> int:
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        pass
```

### SupabaseStorage

**Supabase implementation of session storage.**

##### `__init__()`
Initialize Supabase client using environment variables:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

##### `create_table_if_not_exists() -> bool`
Reference for creating the sessions table manually in Supabase dashboard.

### StorageFactory

**Factory for creating session storage backends.**

##### `create(storage_type: str = 'supabase', **kwargs) -> BaseStorage`
Create a storage backend instance.

##### `get_available_backends() -> List[str]`
Get list of available storage backends.

##### `test_backend(storage_type: str, **kwargs) -> bool`
Test if a storage backend is working.

---

## Utility Functions

### Session Helpers

##### `generate_session_id() -> str`
Generate a unique session ID.

##### `validate_session_id(session_id: str) -> bool`
Validate session ID format.

### Global Functions

##### `get_session_manager(storage_type: str = 'supabase') -> SessionManager`
Get or create the global session manager instance.

##### `get_command_registry() -> CommandRegistry`
Get the global command registry instance.

---

## Type Definitions

### Core Types

```python
# Session data structures
SessionContext = TypedDict('SessionContext', {
    'session_id': str,
    'created_at': datetime,
    'last_accessed': datetime,
    'conversation_history': List[ChatMessage],
    'scene_state': SceneState,
    'user_preferences': Dict[str, Any],
    'metadata': Dict[str, Any]
})

ChatMessage = TypedDict('ChatMessage', {
    'timestamp': datetime,
    'role': str,  # 'user', 'assistant', 'system'
    'content': str,
    'commands': List[Dict[str, Any]],
    'execution_results': List[Dict[str, Any]]
})

SceneState = TypedDict('SceneState', {
    'actors': List[ActorInfo],
    'lights': List[LightInfo], 
    'sky_settings': Dict[str, Any],
    'cesium_location': Optional[Dict[str, float]],
    'last_commands': List[Dict[str, Any]],
    'last_updated': datetime
})

ActorInfo = TypedDict('ActorInfo', {
    'name': str,
    'actor_class': str,
    'location': Optional[Dict[str, float]],
    'rotation': Optional[Dict[str, float]],
    'scale': Optional[Dict[str, float]],
    'properties': Dict[str, Any]
})

LightInfo = TypedDict('LightInfo', {
    'name': str,
    'light_type': str,
    'intensity': float,
    'color': Dict[str, int],  # RGB values
    'location': Optional[Dict[str, float]],
    'properties': Dict[str, Any]
})
```

### Command Types

```python
# Command structure
Command = TypedDict('Command', {
    'type': str,
    'params': Dict[str, Any]
})

# Command execution result
ExecutionResult = TypedDict('ExecutionResult', {
    'command': str,
    'success': bool,
    'result': Any,  # Full Unreal Engine response
    'validation': str,  # 'passed', 'failed'
    'error': Optional[str]
})

# Validated command
ValidatedCommand = TypedDict('ValidatedCommand', {
    'type': str,
    'params': Dict[str, Any],
    'is_valid': bool,
    'validation_errors': List[str]
})
```

### Unreal Engine Response Types

```python
# Success response format
UnrealSuccessResponse = TypedDict('UnrealSuccessResponse', {
    'status': str,  # 'success'
    'message': str,
    'data': Optional[Dict[str, Any]]
})

# Alternative success format
UnrealSuccessResponseAlt = TypedDict('UnrealSuccessResponseAlt', {
    'success': bool,  # True
    'message': str,
    'result': Optional[Dict[str, Any]]
})

# Error response format  
UnrealErrorResponse = TypedDict('UnrealErrorResponse', {
    'status': str,  # 'error'
    'error': str,
    'details': Optional[Dict[str, Any]]
})

# Alternative error format
UnrealErrorResponseAlt = TypedDict('UnrealErrorResponseAlt', {
    'success': bool,  # False
    'message': str,
    'error': Optional[str]
})
```

---

## Usage Examples

### Basic Session Management

```python
from tools.ai.session_management import get_session_manager

# Get session manager
session_manager = get_session_manager()

# Create new session
session = session_manager.create_session("user_123_session")

# Add interaction
session_manager.add_interaction(
    "user_123_session",
    "Create a red light",
    {
        "explanation": "Creating a red point light",
        "commands": [{"type": "create_mm_control_light", "params": {...}}],
        "executionResults": [{"command": "create_mm_control_light", "success": True, ...}]
    }
)

# Retrieve session
session = session_manager.get_session("user_123_session")
print(session.get_conversation_summary())
```

### NLP Processing with Session

```python
from tools.ai.nlp import process_natural_language

# Process with session context
result = process_natural_language(
    "Make the light brighter like last time",
    context="Adjusting scene lighting",
    session_id="user_123_session"
)

print(result["explanation"])
for cmd_result in result["executionResults"]:
    if cmd_result["success"]:
        print(f"✅ {cmd_result['command']} succeeded")
    else:
        print(f"❌ {cmd_result['command']} failed: {cmd_result['error']}")
```

### Custom Command Handler

```python
from tools.ai.actor_command_handlers.main import BaseCommandHandler, get_command_registry

class WeatherCommandHandler(BaseCommandHandler):
    def get_supported_commands(self) -> List[str]:
        return ["set_weather", "get_weather"]
    
    def validate_command(self, command_type: str, params: Dict[str, Any]):
        # Implementation here
        pass
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        # Implementation here
        pass

# Register custom handler
registry = get_command_registry()
registry.register_handler("set_weather", WeatherCommandHandler())
```

This API reference covers all major functions and classes in the Unreal MCP system. For detailed implementation examples, see the session context schema and response format documentation.