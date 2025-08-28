# Session Context Data Structures

This document provides comprehensive documentation for all session context data structures used in the Unreal MCP system.

## Table of Contents

1. [SessionContext](#sessioncontext) - Main session container
2. [ChatMessage](#chatmessage) - Individual conversation messages
3. [SceneState](#scenestate) - Current Unreal Engine scene state
4. [ActorInfo](#actorinfo) - Information about Unreal actors
5. [LightInfo](#lightinfo) - Light-specific actor information
6. [Supabase Storage Schema](#supabase-storage-schema)
7. [Example Data](#example-data)

---

## SessionContext

**Main session container that holds all conversation and scene data.**

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | `string` | ✅ | Unique identifier for this session |
| `created_at` | `datetime` | ✅ | When the session was created |
| `last_accessed` | `datetime` | ✅ | Last time session was accessed/updated |
| `conversation_history` | `List[ChatMessage]` | ✅ | Complete conversation history |
| `scene_state` | `SceneState` | ✅ | Current state of Unreal Engine scene |
| `user_preferences` | `Dict[str, Any]` | ✅ | User-specific preferences and settings |
| `metadata` | `Dict[str, Any]` | ✅ | Additional session metadata |

### Methods

- `add_message(role, content, commands?, execution_results?)` - Add single message
- `add_interaction(user_input, ai_response)` - Add complete user-AI interaction
- `get_conversation_summary(max_messages=10)` - Get recent conversation summary
- `get_scene_summary()` - Get current scene state summary
- `to_dict()` / `from_dict()` - JSON serialization

---

## ChatMessage

**Represents a single message in the conversation.**

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | `datetime` | ✅ | When the message was created |
| `role` | `string` | ✅ | Message sender: `"user"`, `"assistant"`, `"system"` |
| `content` | `string` | ✅ | The actual message content |
| `commands` | `List[Dict[str, Any]]` | ❌ | Commands extracted from this message |
| `execution_results` | `List[Dict[str, Any]]` | ❌ | Results from executing commands |

### Command Structure

Commands in the `commands` array follow this format:

```json
{
  "type": "string",           // Command name (e.g., "set_weather", "create_actor")
  "params": {                 // Command parameters
    "param1": "value1",
    "param2": 123
  }
}
```

### Execution Results Structure

Results in the `execution_results` array follow this format:

```json
{
  "command": "string",        // Command name that was executed
  "success": boolean,         // Whether command succeeded
  "result": {                 // Full Unreal Engine response
    "status": "success|error",
    "message": "string",
    "data": {...}
  },
  "validation": "string",     // Validation status: "passed", "failed"
  "error": "string"          // Error message if success=false
}
```

---

## SceneState

**Current state of the Unreal Engine scene.**

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `actors` | `List[ActorInfo]` | ✅ | All actors currently in scene |
| `lights` | `List[LightInfo]` | ✅ | All light actors in scene |
| `sky_settings` | `Dict[str, Any]` | ✅ | Ultra Dynamic Sky settings |
| `cesium_location` | `Dict[str, float]` | ❌ | Cesium geospatial location |
| `last_commands` | `List[Dict[str, Any]]` | ✅ | Last 10 commands executed |
| `last_updated` | `datetime` | ✅ | When scene was last modified |

### Sky Settings Structure

```json
{
  "time_of_day": 1200,        // HHMM format (0000-2400)
  "color_temperature": 6500,  // Kelvin or string description
  "sky_name": "string"        // Name of sky actor
}
```

### Cesium Location Structure

```json
{
  "latitude": 37.7749,        // Degrees (-90 to 90)
  "longitude": -122.4194,     // Degrees (-180 to 180)
  "altitude": 0.0            // Meters above sea level
}
```

### Last Commands Structure

```json
{
  "command": "string",        // Command name
  "params": {...},           // Command parameters
  "result": {...},           // Unreal Engine response
  "timestamp": "ISO8601"     // When command was executed
}
```

---

## ActorInfo

**Information about an Unreal Engine actor.**

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | ✅ | Unique actor name in the scene |
| `actor_class` | `string` | ✅ | Unreal class type (e.g., "StaticMeshActor") |
| `location` | `Dict[str, float]` | ❌ | 3D world position |
| `rotation` | `Dict[str, float]` | ❌ | 3D rotation in degrees |
| `scale` | `Dict[str, float]` | ❌ | 3D scale factors |
| `properties` | `Dict[str, Any]` | ✅ | Additional actor properties |

### Transform Structures

```json
{
  "location": {"x": 0.0, "y": 0.0, "z": 0.0},
  "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
  "scale": {"x": 1.0, "y": 1.0, "z": 1.0}
}
```

### Common Actor Classes

- `"StaticMeshActor"` - Static mesh objects (cubes, spheres, etc.)
- `"PointLight"` - Point light sources
- `"DirectionalLight"` - Directional lights (sun)
- `"SpotLight"` - Spot lights with cones
- `"CameraActor"` - Camera objects
- `"Pawn"` - Controllable characters

---

## LightInfo

**Light-specific actor information.**

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | ✅ | Unique light name |
| `light_type` | `string` | ✅ | Type of light |
| `intensity` | `float` | ✅ | Light intensity (lumens) |
| `color` | `Dict[str, int]` | ✅ | RGB color values |
| `location` | `Dict[str, float]` | ❌ | 3D world position |
| `properties` | `Dict[str, Any]` | ✅ | Additional light properties |

### Light Types

- `"PointLight"` - Omnidirectional point light
- `"DirectionalLight"` - Parallel rays (sun-like)
- `"SpotLight"` - Cone-shaped light beam
- `"RectLight"` - Rectangular area light

### Color Structure

```json
{
  "r": 255,    // Red (0-255)
  "g": 255,    // Green (0-255) 
  "b": 255     // Blue (0-255)
}
```

### Intensity Guidelines

- `500-2000` - Indoor lighting
- `2000-10000` - Bright indoor/outdoor
- `10000-100000` - Very bright/sunlight
- `100000+` - Extreme lighting effects

---

## Supabase Storage Schema

### Table: `user_sessions`

```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    context JSONB NOT NULL,           -- Complete SessionContext as JSON
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_sessions_session_id ON user_sessions(session_id);
CREATE INDEX idx_sessions_last_accessed ON user_sessions(last_accessed);
```

### Context JSON Structure

The `context` field contains the complete `SessionContext.to_dict()` output:

```json
{
  "session_id": "session_123",
  "created_at": "2024-01-01T10:00:00",
  "last_accessed": "2024-01-01T12:30:00",
  "conversation_history": [
    {
      "timestamp": "2024-01-01T10:05:00",
      "role": "user",
      "content": "Make it rain heavily",
      "commands": [...],
      "execution_results": [...]
    }
  ],
  "scene_state": {
    "actors": [...],
    "lights": [...],
    "sky_settings": {...},
    "last_commands": [...],
    "last_updated": "2024-01-01T10:05:30"
  },
  "user_preferences": {},
  "metadata": {}
}
```

---

## Example Data

### Complete Session Example

```json
{
  "session_id": "user_123_20240101",
  "created_at": "2024-01-01T10:00:00.000Z",
  "last_accessed": "2024-01-01T10:15:30.000Z",
  "conversation_history": [
    {
      "timestamp": "2024-01-01T10:05:00.000Z",
      "role": "user",
      "content": "Create a bright red light in the scene",
      "commands": [
        {
          "type": "create_mm_control_light",
          "params": {
            "light_name": "RedLight_001",
            "intensity": 5000,
            "color": {"r": 255, "g": 0, "b": 0},
            "location": {"x": 0, "y": 0, "z": 200}
          }
        }
      ],
      "execution_results": [
        {
          "command": "create_mm_control_light",
          "success": true,
          "result": {
            "status": "success",
            "message": "Light created successfully",
            "actor_name": "RedLight_001",
            "intensity": 5000,
            "location": {"x": 0, "y": 0, "z": 200}
          },
          "validation": "passed"
        }
      ]
    },
    {
      "timestamp": "2024-01-01T10:06:00.000Z",
      "role": "assistant", 
      "content": "I've created a bright red light at height 200. The light has an intensity of 5000 lumens and should provide good illumination for your scene.",
      "commands": [],
      "execution_results": []
    },
    {
      "timestamp": "2024-01-01T10:10:00.000Z",
      "role": "user",
      "content": "Make it darker like evening time",
      "commands": [
        {
          "type": "set_time_of_day",
          "params": {
            "time_of_day": 1900,
            "sky_name": "Ultra_Dynamic_Sky"
          }
        }
      ],
      "execution_results": [
        {
          "command": "set_time_of_day", 
          "success": true,
          "result": {
            "status": "success",
            "message": "Time set to 1900",
            "previous_time": 1200,
            "new_time": 1900
          },
          "validation": "passed"
        }
      ]
    }
  ],
  "scene_state": {
    "actors": [
      {
        "name": "RedLight_001",
        "actor_class": "PointLight",
        "location": {"x": 0, "y": 0, "z": 200},
        "rotation": {"pitch": 0, "yaw": 0, "roll": 0},
        "scale": {"x": 1, "y": 1, "z": 1},
        "properties": {
          "intensity": 5000,
          "light_color": {"r": 255, "g": 0, "b": 0}
        }
      }
    ],
    "lights": [
      {
        "name": "RedLight_001",
        "light_type": "PointLight",
        "intensity": 5000,
        "color": {"r": 255, "g": 0, "b": 0},
        "location": {"x": 0, "y": 0, "z": 200},
        "properties": {}
      }
    ],
    "sky_settings": {
      "time_of_day": 1900,
      "color_temperature": "warm",
      "sky_name": "Ultra_Dynamic_Sky"
    },
    "cesium_location": null,
    "last_commands": [
      {
        "command": "create_mm_control_light",
        "params": {
          "light_name": "RedLight_001",
          "intensity": 5000,
          "color": {"r": 255, "g": 0, "b": 0}
        },
        "result": {"status": "success", "message": "Light created successfully"},
        "timestamp": "2024-01-01T10:05:30.000Z"
      },
      {
        "command": "set_time_of_day",
        "params": {
          "time_of_day": 1900,
          "sky_name": "Ultra_Dynamic_Sky"
        },
        "result": {"status": "success", "message": "Time set to 1900"},
        "timestamp": "2024-01-01T10:10:30.000Z"
      }
    ],
    "last_updated": "2024-01-01T10:10:30.000Z"
  },
  "user_preferences": {
    "preferred_light_intensity": 5000,
    "favorite_time_of_day": 1900
  },
  "metadata": {
    "client_version": "1.0.0",
    "session_type": "interactive"
  }
}
```

### Failed Command Example

```json
{
  "timestamp": "2024-01-01T10:20:00.000Z",
  "role": "user",
  "content": "Create a light with invalid parameters",
  "commands": [
    {
      "type": "create_mm_control_light",
      "params": {
        "light_name": "",  // Invalid: empty name
        "intensity": -500  // Invalid: negative intensity
      }
    }
  ],
  "execution_results": [
    {
      "command": "create_mm_control_light",
      "success": false,
      "error": "Validation failed: light_name cannot be empty; intensity must be non-negative",
      "validation": "failed"
    }
  ]
}
```

---

## Usage Notes

1. **Timestamps**: All timestamps use ISO 8601 format with timezone
2. **Coordinates**: Unreal uses centimeters, +X=forward, +Y=right, +Z=up
3. **Colors**: RGB values 0-255, some systems may use 0.0-1.0 floats
4. **Time Format**: Ultra Dynamic Sky uses HHMM (0000-2400)
5. **Session IDs**: Should be unique and URL-safe
6. **Validation**: Commands are validated before execution
7. **Error Handling**: Both success flags and detailed error messages
8. **Scene Tracking**: Automatic updates when commands modify the scene

This documentation covers all major data structures used in the Unreal MCP session management system.