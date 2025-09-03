#pragma once

#include "CoreMinimal.h"
#include "Json.h"

/**
 * Handler class for Rendering-related MCP commands
 */
class UNREALMCP_API FUnrealMCPRenderingCommands
{
public:
    FUnrealMCPRenderingCommands();
    TSharedPtr<FJsonObject> HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params);

private:
    // Screenshot command handlers
    TSharedPtr<FJsonObject> HandleTakeHighResShot(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleQuickScreenshot(const TSharedPtr<FJsonObject>& Params);
};