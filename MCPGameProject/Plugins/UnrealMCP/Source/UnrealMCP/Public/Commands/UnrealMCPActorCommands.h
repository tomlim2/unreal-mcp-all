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

	// to do : how to get REAL current world in cinev from source code
	UWorld* GetCurrentWorld();
	AActor* FindActorByClassName(const FString& ClassName);
	bool GetDoublePropertyValue(AActor* Actor, const FName& PropertyName, float& OutValue);
	bool UpdateDoubleProperty(AActor* SkyActor, const FName& PropertyName, float NewValue);

    // Ultra Dynamic Sky specific commands
	AActor* GetUltraDynamicSkyActor();
    TSharedPtr<FJsonObject> HandleSetTimeOfDay(const TSharedPtr<FJsonObject>& Params);
	TSharedPtr<FJsonObject> HandleSetColorTemperature(const TSharedPtr<FJsonObject>& Params);
	TSharedPtr<FJsonObject> HandleGetUltraDynamicSkyProperties(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleGetUltraDynamicWeather(const TSharedPtr<FJsonObject>& Params);
    // Ultra Dynamic Weather specific commands
    AActor* GetUltraDynamicWeatherActor();
    TSharedPtr<FJsonObject> HandleSetCurrentWeatherToRain(const TSharedPtr<FJsonObject>& Params);
    // Cesium specific commands
	AActor* GetCesiumGeoreferenceActor();
    TSharedPtr<FJsonObject> HandleGetCesiumProperties(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleSetCesiumLatitudeLongitude(const TSharedPtr<FJsonObject>& Params);

	// Add Light Commands Create Read Update Delete
	TSharedPtr<FJsonObject> HandleCreateMMControlLight(const TSharedPtr<FJsonObject>& Params);
	TSharedPtr<FJsonObject> HandleGetMMControlLights(const TSharedPtr<FJsonObject>& Params);
	TSharedPtr<FJsonObject> HandleUpdateMMControlLight(const TSharedPtr<FJsonObject>& Params);
	TSharedPtr<FJsonObject> HandleDeleteMMControlLight(const TSharedPtr<FJsonObject>& Params);
};
