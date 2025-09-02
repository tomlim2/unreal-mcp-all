#pragma once

#include "CoreMinimal.h"
#include "Json.h"

/**
 * Handler class for Actor-related MCP commands
 */
class UNREALMCP_API FUnrealMCPRenderingCommands
{
public:
    FUnrealMCPRenderingCommands();
    TSharedPtr<FJsonObject> HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params);

private:
    // Specific actor command handlers
    TSharedPtr<FJsonObject> HandleTakeHighResShot(const TSharedPtr<FJsonObject>& Params);
};
