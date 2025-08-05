#pragma once

#include "CoreMinimal.h"
#include "Json.h"
#include "Engine/World.h"
#include "EngineUtils.h"

/**
 * Handler class for Actor-related MCP commands
 */
class UNREALMCP_API FUnrealMCPActorCommands
{
public:
    FUnrealMCPActorCommands();

    // Handle actor commands
    TSharedPtr<FJsonObject> HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params);

private:
    // Specific actor command handlers
    TSharedPtr<FJsonObject> HandleGetActorsInLevel(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleFindActorsByName(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleCreateActor(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleDeleteActor(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleSetActorTransform(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleGetActorProperties(const TSharedPtr<FJsonObject>& Params);
    
    // Ultra Dynamic Sky specific commands
    TSharedPtr<FJsonObject> HandleGetTimeOfDay(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleSetTimeOfDay(const TSharedPtr<FJsonObject>& Params);
}; 