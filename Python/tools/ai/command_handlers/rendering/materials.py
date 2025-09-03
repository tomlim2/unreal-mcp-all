"""
Material and texture rendering command handler.

Handles Unreal Engine material operations including material parameter control,
texture assignments, and material instance creation for rendering customization.
"""

import logging
from typing import Dict, Any, List
from ..main import BaseCommandHandler
from ...nlp_schema_validator import ValidatedCommand

logger = logging.getLogger("UnrealMCP")


class MaterialCommandHandler(BaseCommandHandler):
    """Handler for material and texture rendering commands.
    
    Purpose: Material parameter control and texture management for rendering
    
    Supported Commands:
    - set_material_parameter: Modify material scalar, vector, or texture parameters
    - get_material_parameters: Retrieve current material parameter values
    - apply_material_to_actor: Assign material to specific actor mesh
    - create_material_instance: Create dynamic material instance from base material
    
    Input Constraints:
    - actor_name: Required string (target actor for material operations)
    - material_name: Required string (material asset name or path)
    - parameter_name: Required string (material parameter identifier)
    - parameter_value: Value type depends on parameter (float, Vector3, texture path)
    - material_slot: Optional integer (mesh material slot index, defaults to 0)
    
    Parameter Types:
    - Scalar: Float value (0.0-1.0 typical range for most parameters)
    - Vector: {"r": float, "g": float, "b": float} for color parameters
    - Texture: String path to texture asset
    """
    
    def get_supported_commands(self) -> List[str]:
        return [
            "set_material_parameter",
            "get_material_parameters", 
            "apply_material_to_actor",
            "create_material_instance"
        ]
    
    def validate_command(self, command_type: str, params: Dict[str, Any]) -> ValidatedCommand:
        """Validate material commands with parameter checks."""
        errors = []
        
        # Common validations for all material commands
        if command_type in ["set_material_parameter", "apply_material_to_actor", "create_material_instance"]:
            if "actor_name" not in params:
                errors.append("Missing required parameter: actor_name")
            elif not isinstance(params["actor_name"], str) or not params["actor_name"].strip():
                errors.append("actor_name must be a non-empty string")
        
        if command_type == "set_material_parameter":
            if "parameter_name" not in params:
                errors.append("Missing required parameter: parameter_name")
            elif not isinstance(params["parameter_name"], str) or not params["parameter_name"].strip():
                errors.append("parameter_name must be a non-empty string")
            
            if "parameter_value" not in params:
                errors.append("Missing required parameter: parameter_value")
            
            # Validate material_slot if provided
            if "material_slot" in params:
                slot = params["material_slot"]
                if not isinstance(slot, int) or slot < 0:
                    errors.append("material_slot must be a non-negative integer")
        
        elif command_type in ["apply_material_to_actor", "create_material_instance"]:
            if "material_name" not in params:
                errors.append("Missing required parameter: material_name")
            elif not isinstance(params["material_name"], str) or not params["material_name"].strip():
                errors.append("material_name must be a non-empty string")
        
        elif command_type == "get_material_parameters":
            if "actor_name" not in params:
                errors.append("Missing required parameter: actor_name")
            elif not isinstance(params["actor_name"], str) or not params["actor_name"].strip():
                errors.append("actor_name must be a non-empty string")
        
        return ValidatedCommand(
            type=command_type,
            params=params,
            is_valid=len(errors) == 0,
            validation_errors=errors
        )
    
    def preprocess_params(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values and normalize material parameters."""
        processed = params.copy()
        
        # Apply default material slot
        if command_type in ["set_material_parameter", "apply_material_to_actor"]:
            processed.setdefault("material_slot", 0)
        
        # Normalize vector parameters
        if command_type == "set_material_parameter" and "parameter_value" in processed:
            value = processed["parameter_value"]
            if isinstance(value, dict) and all(k in value for k in ["r", "g", "b"]):
                # Ensure RGB values are floats
                processed["parameter_value"] = {
                    "r": float(value["r"]),
                    "g": float(value["g"]), 
                    "b": float(value["b"])
                }
        
        return processed
    
    def execute_command(self, connection, command_type: str, params: Dict[str, Any]) -> Any:
        """Execute material commands."""
        logger.info(f"Material Handler: Executing {command_type} with params: {params}")
        
        response = connection.send_command(command_type, params)
        
        if response and response.get("status") == "error":
            raise Exception(response.get("error", "Unknown material operation error"))
        
        return response