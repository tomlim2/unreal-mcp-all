"""
Schema validation utilities for Unreal MCP commands
Based on the defined JSON schemas and TypeScript interfaces
"""

import json
from typing import Dict, Any, Union, Optional, List
from dataclasses import dataclass

# ============================
# VALIDATION CONSTANTS
# ============================

SKY_CONSTRAINTS = {
    "TIME_RANGE": {"min": 0, "max": 2400},
    "COLOR_TEMP_RANGE": {"min": 1500, "max": 15000},
    "DEFAULT_SKY_NAME": "Ultra_Dynamic_Sky_C_0",
}

LIGHT_CONSTRAINTS = {
    "DEFAULT_INTENSITY": 1000.0,
    "DEFAULT_LOCATION": {"x": 0.0, "y": 0.0, "z": 100.0},
    "DEFAULT_COLOR": {"r": 255, "g": 255, "b": 255},
    "COLOR_RANGE": {"min": 0, "max": 255},
}

# Valid command types
SKY_COMMANDS = ["get_ultra_dynamic_sky", "set_time_of_day", "set_color_temperature"]
LIGHT_COMMANDS = ["create_mm_control_light", "get_mm_control_lights", "update_mm_control_light", "delete_mm_control_light"]
ACTOR_COMMANDS = ["get_actors_in_level", "create_actor", "delete_actor", "set_actor_transform", "get_actor_properties"]
CESIUM_COMMANDS = ["set_cesium_latitude_longitude", "get_cesium_properties"]

ALL_COMMANDS = SKY_COMMANDS + LIGHT_COMMANDS + ACTOR_COMMANDS + CESIUM_COMMANDS

# ============================
# TYPED DATA CLASSES
# ============================

@dataclass
class Vector3:
    x: float
    y: float
    z: float
    
    def to_dict(self) -> Dict[str, float]:
        return {"x": self.x, "y": self.y, "z": self.z}
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'Vector3':
        return cls(x=data["x"], y=data["y"], z=data["z"])

@dataclass 
class RGBColor:
    r: int
    g: int
    b: int
    
    def to_dict(self) -> Dict[str, int]:
        return {"r": self.r, "g": self.g, "b": self.b}
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'RGBColor':
        return cls(r=data["r"], g=data["g"], b=data["b"])
    
    def to_linear(self) -> Dict[str, float]:
        """Convert RGB 0-255 to Linear 0-1 (matches Unreal's internal conversion)"""
        return {"r": self.r / 255.0, "g": self.g / 255.0, "b": self.b / 255.0}

@dataclass
class ValidatedCommand:
    """A validated command with typed parameters"""
    type: str
    params: Dict[str, Any]
    is_valid: bool
    validation_errors: List[str]

# ============================
# VALIDATION FUNCTIONS
# ============================

def validate_time_of_day(time: Union[int, float, str]) -> List[str]:
    """Validate time of day parameter (accepts number or HHMM string format)"""
    errors = []
    
    # Convert string HHMM format to number
    if isinstance(time, str):
        try:
            # Convert string like "0200" to number 200
            time_num = int(time)
        except ValueError:
            errors.append("time_of_day string must be a valid HHMM format (e.g., '0600', '1800')")
            return errors
    elif isinstance(time, (int, float)):
        time_num = int(time)
    else:
        errors.append("time_of_day must be a number or HHMM string format")
        return errors
    
    # Validate range
    if time_num < SKY_CONSTRAINTS["TIME_RANGE"]["min"] or time_num > SKY_CONSTRAINTS["TIME_RANGE"]["max"]:
        errors.append(f"time_of_day must be between {SKY_CONSTRAINTS['TIME_RANGE']['min']} and {SKY_CONSTRAINTS['TIME_RANGE']['max']}")
    
    return errors

def validate_color_temperature(temp: Union[int, float]) -> List[str]:
    """Validate color temperature parameter"""
    errors = []
    if not isinstance(temp, (int, float)):
        errors.append("color_temperature must be a number")
    elif temp < SKY_CONSTRAINTS["COLOR_TEMP_RANGE"]["min"] or temp > SKY_CONSTRAINTS["COLOR_TEMP_RANGE"]["max"]:
        errors.append(f"color_temperature must be between {SKY_CONSTRAINTS['COLOR_TEMP_RANGE']['min']} and {SKY_CONSTRAINTS['COLOR_TEMP_RANGE']['max']} Kelvin")
    return errors

def validate_vector3(vec: Dict[str, Any]) -> List[str]:
    """Validate Vector3 parameter"""
    errors = []
    if not isinstance(vec, dict):
        errors.append("location must be an object with x, y, z properties")
        return errors
    
    for coord in ["x", "y", "z"]:
        if coord not in vec:
            errors.append(f"location missing required property: {coord}")
        elif not isinstance(vec[coord], (int, float)):
            errors.append(f"location.{coord} must be a number")
    
    return errors

def validate_rgb_color(color: Dict[str, Any]) -> List[str]:
    """Validate RGB color parameter"""
    errors = []
    if not isinstance(color, dict):
        errors.append("color must be an object with r, g, b properties")
        return errors
    
    for component in ["r", "g", "b"]:
        if component not in color:
            errors.append(f"color missing required property: {component}")
        elif not isinstance(color[component], int):
            errors.append(f"color.{component} must be an integer")
        elif color[component] < LIGHT_CONSTRAINTS["COLOR_RANGE"]["min"] or color[component] > LIGHT_CONSTRAINTS["COLOR_RANGE"]["max"]:
            errors.append(f"color.{component} must be between {LIGHT_CONSTRAINTS['COLOR_RANGE']['min']} and {LIGHT_CONSTRAINTS['COLOR_RANGE']['max']}")
    
    return errors

def validate_light_intensity(intensity: Union[int, float]) -> List[str]:
    """Validate light intensity parameter"""
    errors = []
    if not isinstance(intensity, (int, float)):
        errors.append("intensity must be a number")
    elif intensity < 0:
        errors.append("intensity must be non-negative")
    return errors

# ============================
# COMMAND VALIDATION
# ============================

def validate_sky_command(command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
    """Validate Ultra Dynamic Sky commands"""
    errors = []
    
    if command_type == "set_time_of_day":
        if "time_of_day" in params:
            errors.extend(validate_time_of_day(params["time_of_day"]))
            # Convert string HHMM to number for consistency
            if isinstance(params["time_of_day"], str):
                try:
                    params["time_of_day"] = int(params["time_of_day"])
                except ValueError:
                    pass  # Error already captured by validate_time_of_day
        elif "time" in params:
            # Support legacy parameter name
            errors.extend(validate_time_of_day(params["time"]))
            # Convert string HHMM to number and normalize parameter name
            time_value = params.pop("time")
            if isinstance(time_value, str):
                try:
                    params["time_of_day"] = int(time_value)
                except ValueError:
                    params["time_of_day"] = time_value  # Keep original for error reporting
            else:
                params["time_of_day"] = time_value
        else:
            errors.append("set_time_of_day requires time_of_day parameter")
        
        # Validate optional sky_name
        if "sky_name" in params and not isinstance(params["sky_name"], str):
            errors.append("sky_name must be a string")
    
    elif command_type == "set_color_temperature":
        if "color_temperature" in params:
            if isinstance(params["color_temperature"], (int, float)):
                errors.extend(validate_color_temperature(params["color_temperature"]))
            elif isinstance(params["color_temperature"], str):
                # String description is valid, will be processed by temperature mapping
                pass
            else:
                errors.append("color_temperature must be a number or string description")
        elif "temperature" in params:
            # Support legacy parameter name
            if isinstance(params["temperature"], (int, float)):
                errors.extend(validate_color_temperature(params["temperature"]))
            params["color_temperature"] = params.pop("temperature")
        else:
            errors.append("set_color_temperature requires color_temperature parameter")
    
    elif command_type == "get_ultra_dynamic_sky":
        # No required parameters for get command
        pass
    elif command_type == "get_ultra_dynamic_weather":
        # No required parameters for get command
        pass
    return ValidatedCommand(
        type=command_type,
        params=params,
        is_valid=len(errors) == 0,
        validation_errors=errors
    )

def validate_light_command(command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
    """Validate MM Control Light commands"""
    errors = []
    
    if command_type in ["create_mm_control_light", "update_mm_control_light", "delete_mm_control_light"]:
        if "light_name" not in params:
            errors.append(f"{command_type} requires light_name parameter")
        elif not isinstance(params["light_name"], str) or not params["light_name"].strip():
            errors.append("light_name must be a non-empty string")
    
    if command_type in ["create_mm_control_light", "update_mm_control_light"]:
        # Validate optional location
        if "location" in params:
            errors.extend(validate_vector3(params["location"]))
        
        # Validate optional intensity  
        if "intensity" in params:
            errors.extend(validate_light_intensity(params["intensity"]))
        
        # Validate optional color
        if "color" in params:
            errors.extend(validate_rgb_color(params["color"]))
    
    elif command_type == "get_mm_control_lights":
        # No required parameters for get command
        pass
    
    return ValidatedCommand(
        type=command_type,
        params=params,
        is_valid=len(errors) == 0,
        validation_errors=errors
    )

def validate_command(command: Dict[str, Any]) -> ValidatedCommand:
    """Validate any command using schema-based validation"""
    if not isinstance(command, dict):
        return ValidatedCommand(
            type="unknown",
            params={},
            is_valid=False,
            validation_errors=["Command must be an object"]
        )
    
    command_type = command.get("type")
    if not command_type:
        return ValidatedCommand(
            type="unknown",
            params={},
            is_valid=False,
            validation_errors=["Command must have a 'type' property"]
        )
    
    if command_type not in ALL_COMMANDS:
        return ValidatedCommand(
            type=command_type,
            params={},
            is_valid=False,
            validation_errors=[f"Unknown command type: {command_type}"]
        )
    
    params = command.get("params", {})
    if not isinstance(params, dict):
        return ValidatedCommand(
            type=command_type,
            params={},
            is_valid=False,
            validation_errors=["Command params must be an object"]
        )
    
    # Route to appropriate validator
    if command_type in SKY_COMMANDS:
        return validate_sky_command(command_type, params)
    elif command_type in LIGHT_COMMANDS:
        return validate_light_command(command_type, params)
    else:
        # For other commands, do basic validation
        return ValidatedCommand(
            type=command_type,
            params=params,
            is_valid=True,
            validation_errors=[]
        )

# ============================
# UTILITY FUNCTIONS
# ============================

def normalize_light_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize light parameters with schema defaults"""
    normalized = params.copy()
    
    # Apply defaults if not provided
    if "location" not in normalized:
        normalized["location"] = LIGHT_CONSTRAINTS["DEFAULT_LOCATION"].copy()
    
    if "intensity" not in normalized:
        normalized["intensity"] = LIGHT_CONSTRAINTS["DEFAULT_INTENSITY"]
    
    if "color" not in normalized:
        normalized["color"] = LIGHT_CONSTRAINTS["DEFAULT_COLOR"].copy()
    
    return normalized

def normalize_sky_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize sky parameters with schema defaults"""
    normalized = params.copy()
    
    # Apply default sky name if not provided
    if "sky_name" not in normalized and "sky_name" not in params:
        normalized["sky_name"] = SKY_CONSTRAINTS["DEFAULT_SKY_NAME"]
    
    return normalized

def convert_hhmm_to_decimal(hhmm: Union[int, float]) -> float:
    """Convert HHMM format to decimal hours"""
    hours = int(hhmm) // 100
    minutes = int(hhmm) % 100
    return hours + (minutes / 60.0)

def convert_decimal_to_hhmm(decimal: float) -> int:
    """Convert decimal hours to HHMM format"""
    hours = int(decimal)
    minutes = round((decimal - hours) * 60)
    return (hours * 100) + minutes