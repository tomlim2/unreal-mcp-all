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
    TSharedPtr<FJsonObject> HandleSetTimeOfDay(const TSharedPtr<FJsonObject>& Params);
	TSharedPtr<FJsonObject> HandleSetColorTemperature(const TSharedPtr<FJsonObject>& Params);
	TSharedPtr<FJsonObject> HandleGetUltraDynamicSkyProperties(const TSharedPtr<FJsonObject>& Params);

    // Cesium specific commands
    TSharedPtr<FJsonObject> HandleSetCesiumLatitudeLongitude(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleGetCesiumProperties(const TSharedPtr<FJsonObject>& Params);

	AActor* GetUltraDynamicSkyActor();
	UWorld* GetCurrentWorld();
	void UpdateUdsDoubleProperty(const FName& PropertyName, float NewValue, TSharedPtr<FJsonObject>& ResultObj);
	void GetUdsDoubleProperty(const FName& PropertyName, TSharedPtr<FJsonObject>& ResultObj);
	float GetUdsDoublePropertyValue(AActor* SkyActor, const FName& PropertyName);
};