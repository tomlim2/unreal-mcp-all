#pragma once

#include "CoreMinimal.h"
#include "Json.h"

/**
 * Handler class for 3D Object MCP commands
 *
 * Specialized handler for 3D object operations including:
 * - Import from various formats (OBJ, FBX, glTF, etc.)
 * - Spawn imported objects as actors
 * - Transform and manipulate 3D geometry
 * - Material assignment to 3D objects
 *
 * Separates 3D object concerns from generic asset management,
 * allowing focused extension of 3D-specific functionality.
 */
class UNREALMCP_API FUnrealMCPObject3DCommands
{
public:
    FUnrealMCPObject3DCommands();
    TSharedPtr<FJsonObject> HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params);

private:
    // 3D Object Import Commands
    TSharedPtr<FJsonObject> HandleImportObject3DByUID(const TSharedPtr<FJsonObject>& Params);

    // Future: Additional 3D object handlers
    // TSharedPtr<FJsonObject> HandleSpawnImportedObject(const TSharedPtr<FJsonObject>& Params);
    // TSharedPtr<FJsonObject> HandleApplyMaterialToObject3D(const TSharedPtr<FJsonObject>& Params);
    // TSharedPtr<FJsonObject> HandleTransformObject3D(const TSharedPtr<FJsonObject>& Params);
};