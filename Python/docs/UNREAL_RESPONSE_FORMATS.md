# Unreal Engine Response Formats

This document details all response formats returned by the Unreal Engine MCP plugin, including success and error cases.

## Table of Contents

1. [Response Structure Overview](#response-structure-overview)
2. [Success Response Formats](#success-response-formats)
3. [Error Response Formats](#error-response-formats)
4. [Command-Specific Responses](#command-specific-responses)
5. [Status Code Reference](#status-code-reference)
6. [Example Responses](#example-responses)

---

## Response Structure Overview

All Unreal Engine responses follow one of these formats:

### Standard Success Format
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": {
    // Command-specific result data
  }
}
```

### Alternative Success Format  
```json
{
  "success": true,
  "message": "Operation completed",
  "result": {
    // Command-specific result data
  }
}
```

### Standard Error Format
```json
{
  "status": "error", 
  "error": "Error description",
  "details": {
    // Optional error details
  }
}
```

### Alternative Error Format
```json
{
  "success": false,
  "message": "Error description",
  "error": "Detailed error message"
}
```

---

## Success Response Formats

### Actor Commands

#### `create_actor`
```json
{
  "status": "success",
  "message": "Actor created successfully", 
  "data": {
    "actor_name": "TestCube_001",
    "actor_class": "StaticMeshActor",
    "location": {"x": 0.0, "y": 0.0, "z": 0.0},
    "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
    "scale": {"x": 1.0, "y": 1.0, "z": 1.0},
    "unique_id": "actor_12345"
  }
}
```

#### `delete_actor`
```json
{
  "status": "success",
  "message": "Actor deleted successfully",
  "data": {
    "deleted_actor": "TestCube_001", 
    "actor_count": 15
  }
}
```

#### `set_actor_transform`
```json
{
  "status": "success",
  "message": "Actor transform updated",
  "data": {
    "actor_name": "TestCube_001",
    "previous_location": {"x": 0.0, "y": 0.0, "z": 0.0},
    "new_location": {"x": 100.0, "y": 200.0, "z": 50.0},
    "transform_updated": true
  }
}
```

#### `get_actors_in_level`
```json
{
  "status": "success",
  "message": "Retrieved 3 actors",
  "result": {
    "actors": [
      {
        "name": "TestCube_001",
        "class": "StaticMeshActor",
        "location": {"x": 0.0, "y": 0.0, "z": 0.0}
      },
      {
        "name": "MainLight",
        "class": "PointLight", 
        "location": {"x": 0.0, "y": 0.0, "z": 200.0}
      }
    ]
  }
}
```

### Sky Commands

#### `set_time_of_day`
```json
{
  "status": "success",
  "message": "Time of day updated to 1600",
  "data": {
    "sky_name": "Ultra_Dynamic_Sky",
    "previous_time": 1200,
    "new_time": 1600,
    "sun_angle": 45.5,
    "lighting_changed": true
  }
}
```

#### `set_color_temperature`
```json
{
  "status": "success",
  "message": "Color temperature updated",
  "data": {
    "sky_name": "Ultra_Dynamic_Sky", 
    "previous_temperature": 6500,
    "new_temperature": 3200,
    "temperature_kelvin": 3200
  }
}
```

#### `get_ultra_dynamic_sky`
```json
{
  "status": "success",
  "message": "Sky properties retrieved",
  "result": {
    "sky_name": "Ultra_Dynamic_Sky",
    "time_of_day": 1200,
    "color_temperature": 6500,
    "sun_intensity": 10.0,
    "sky_intensity": 1.0,
    "cloud_coverage": 0.5,
    "weather_settings": {
      "precipitation": 0.0,
      "wind_strength": 1.0
    }
  }
}
```

### Light Commands

#### `create_mm_control_light`
```json
{
  "status": "success",
  "message": "MM Control Light created successfully",
  "data": {
    "actor_name": "MMLight_001",
    "light_type": "PointLight",
    "intensity": 5000.0,
    "color": {"r": 255, "g": 128, "b": 64},
    "location": {"x": 0.0, "y": 0.0, "z": 200.0},
    "light_id": "light_67890"
  }
}
```

#### `update_mm_control_light`
```json
{
  "status": "success",
  "message": "Light updated successfully",
  "data": {
    "light_name": "MMLight_001",
    "updated_properties": {
      "intensity": {"old": 5000.0, "new": 7500.0},
      "color": {"old": {"r": 255, "g": 128, "b": 64}, "new": {"r": 255, "g": 255, "b": 255}}
    },
    "changes_applied": 2
  }
}
```

### Blueprint Commands

#### `create_blueprint_class`
```json
{
  "status": "success",
  "message": "Blueprint class created",
  "result": {
    "blueprint_name": "BP_CustomActor",
    "blueprint_path": "/Game/Blueprints/BP_CustomActor",
    "parent_class": "Actor",
    "success": true
  }
}
```

#### `add_component_to_blueprint`
```json
{
  "status": "success",
  "message": "Component added to blueprint",
  "data": {
    "blueprint_name": "BP_CustomActor",
    "component_name": "MeshComponent",
    "component_type": "StaticMeshComponent",
    "component_id": "comp_12345"
  }
}
```

### Cesium Commands

#### `set_cesium_latitude_longitude`
```json
{
  "status": "success",
  "message": "Cesium location updated",
  "data": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "altitude": 100.0,
    "previous_location": {
      "latitude": 40.7128,
      "longitude": -74.0060
    },
    "coordinate_system": "WGS84"
  }
}
```

---

## Error Response Formats

### Validation Errors

#### Invalid Parameters
```json
{
  "status": "error",
  "error": "Invalid parameters provided",
  "details": {
    "field_errors": {
      "intensity": "Must be a positive number",
      "color": "RGB values must be between 0-255"
    },
    "error_code": "VALIDATION_ERROR"
  }
}
```

#### Missing Required Fields
```json
{
  "status": "error",
  "error": "Required parameter missing: actor_name",
  "details": {
    "required_fields": ["actor_name", "actor_type"],
    "provided_fields": ["actor_type"],
    "error_code": "MISSING_PARAMETER"
  }
}
```

### Runtime Errors

#### Actor Not Found
```json
{
  "status": "error",
  "error": "Actor 'NonExistentActor' not found in level",
  "details": {
    "searched_name": "NonExistentActor",
    "available_actors": ["TestCube_001", "MainLight", "PlayerStart"],
    "error_code": "ACTOR_NOT_FOUND"
  }
}
```

#### Command Execution Failed
```json
{
  "status": "error", 
  "error": "Failed to create actor: Mesh asset not found",
  "details": {
    "command": "create_actor",
    "attempted_mesh": "/Game/Meshes/NonExistentMesh",
    "error_code": "ASSET_NOT_FOUND"
  }
}
```

### Connection Errors

#### Engine Not Ready
```json
{
  "success": false,
  "message": "Unreal Engine is not ready to accept commands",
  "error": "Engine state: Loading"
}
```

#### Plugin Not Loaded
```json
{
  "status": "error",
  "error": "UnrealMCP plugin not loaded or not responding",
  "details": {
    "expected_plugin": "UnrealMCP",
    "plugin_status": "not_loaded",
    "error_code": "PLUGIN_ERROR"
  }
}
```

---

## Command-Specific Responses

### Test/Debug Commands

#### `ping`
```json
{
  "status": "success",
  "message": "pong",
  "data": {
    "server_time": "2024-01-01T12:00:00Z",
    "uptime_seconds": 3600,
    "version": "1.0.0"
  }
}
```

#### `get_engine_info`
```json
{
  "status": "success", 
  "message": "Engine information retrieved",
  "result": {
    "engine_version": "5.3.2",
    "project_name": "MCPGameProject", 
    "build_configuration": "Development",
    "platform": "Win64",
    "plugin_version": "1.0.0"
  }
}
```

### Complex Operations

#### Batch Operations
```json
{
  "status": "success",
  "message": "Batch operation completed",
  "data": {
    "total_operations": 5,
    "successful_operations": 4,
    "failed_operations": 1,
    "results": [
      {"operation": "create_actor", "success": true, "actor_name": "Cube1"},
      {"operation": "create_actor", "success": true, "actor_name": "Cube2"},
      {"operation": "create_actor", "success": false, "error": "Name already exists"},
      {"operation": "set_lighting", "success": true, "intensity": 5000},
      {"operation": "set_time", "success": true, "time": 1600}
    ]
  }
}
```

---

## Status Code Reference

### Success Statuses
- `"success"` - Operation completed successfully
- `true` (success field) - Alternative success indicator

### Error Codes
- `"VALIDATION_ERROR"` - Parameter validation failed
- `"MISSING_PARAMETER"` - Required parameter not provided
- `"ACTOR_NOT_FOUND"` - Referenced actor doesn't exist
- `"ASSET_NOT_FOUND"` - Required asset/resource not found
- `"PLUGIN_ERROR"` - UnrealMCP plugin issue
- `"ENGINE_ERROR"` - General Unreal Engine error
- `"PERMISSION_DENIED"` - Operation not allowed
- `"TIMEOUT"` - Operation timed out
- `"UNKNOWN_COMMAND"` - Command not recognized

---

## Example Responses

### Complete Success Flow

**Request:**
```json
{
  "type": "create_actor",
  "params": {
    "name": "MyTestCube",
    "type": "CUBE", 
    "location": [100.0, 200.0, 50.0]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Actor created successfully",
  "data": {
    "actor_name": "MyTestCube",
    "actor_class": "StaticMeshActor", 
    "location": {"x": 100.0, "y": 200.0, "z": 50.0},
    "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
    "scale": {"x": 1.0, "y": 1.0, "z": 1.0},
    "mesh_path": "/Engine/BasicShapes/Cube",
    "unique_id": "actor_98765"
  }
}
```

### Complete Error Flow

**Request:**
```json
{
  "type": "set_actor_transform", 
  "params": {
    "name": "NonExistentActor",
    "location": [0.0, 0.0, 100.0]
  }
}
```

**Response:**
```json
{
  "status": "error",
  "error": "Actor 'NonExistentActor' not found in level",
  "details": {
    "searched_name": "NonExistentActor",
    "available_actors": ["MyTestCube", "PlayerStart", "DefaultPawn"],
    "suggestion": "Use get_actors_in_level to see available actors",
    "error_code": "ACTOR_NOT_FOUND"
  }
}
```

### Mixed Results (Batch Operation)

**Request:**
```json
{
  "type": "batch_create_actors",
  "params": {
    "actors": [
      {"name": "Cube1", "type": "CUBE"},
      {"name": "Cube1", "type": "SPHERE"},  // Duplicate name
      {"name": "Light1", "type": "LIGHT"}
    ]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Batch operation completed with some failures",
  "data": {
    "total_requested": 3,
    "successful": 2,
    "failed": 1,
    "results": [
      {
        "index": 0,
        "success": true,
        "actor_name": "Cube1",
        "message": "Actor created successfully"
      },
      {
        "index": 1, 
        "success": false,
        "error": "Actor name 'Cube1' already exists",
        "error_code": "NAME_CONFLICT"
      },
      {
        "index": 2,
        "success": true,
        "actor_name": "Light1",
        "message": "Light actor created successfully"
      }
    ]
  }
}
```

---

## Response Handling Best Practices

1. **Always check status first**: Look for `status: "error"` or `success: false`
2. **Handle both formats**: Code should handle both `{status: "success"}` and `{success: true}` formats
3. **Extract error details**: Error responses may have additional context in `details` field
4. **Use error codes**: `error_code` field provides programmatic error handling
5. **Log full responses**: For debugging, log the complete response structure
6. **Validate data fields**: Success responses may have varying data structures
7. **Handle missing fields**: Not all responses include all optional fields
8. **Check nested success**: Some commands have nested success indicators

This documentation covers all response formats you'll encounter when working with the Unreal Engine MCP system.