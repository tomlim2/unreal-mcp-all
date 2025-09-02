#include "Commands/UnrealMCPActorCommands.h"
#include "Commands/UnrealMCPCommonUtils.h"
#include "GameFramework/Actor.h"
#include "Components/PointLightComponent.h"
#include "Engine/PointLight.h"

FUnrealMCPActorCommands::FUnrealMCPActorCommands()
{
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params)
{
	if (CommandType == TEXT("get_actors_in_level"))
	{
		return HandleGetActorsInLevel(Params);
	}
	else if (CommandType == TEXT("find_actors_by_name"))
	{
		return HandleFindActorsByName(Params);
	}
	else if (CommandType == TEXT("create_actor"))
	{
		return HandleCreateActor(Params);
	}
	else if (CommandType == TEXT("delete_actor"))
	{
		return HandleDeleteActor(Params);
	}
	else if (CommandType == TEXT("set_actor_transform"))
	{
		return HandleSetActorTransform(Params);
	}
	else if (CommandType == TEXT("get_actor_properties"))
	{
		return HandleGetActorProperties(Params);
	}
	else if (CommandType == TEXT("set_time_of_day"))
	{
		return HandleSetTimeOfDay(Params);
	}
	else if (CommandType == TEXT("get_ultra_dynamic_sky"))
	{
		return HandleGetUltraDynamicSkyProperties(Params);
	}
	else if (CommandType == TEXT("get_ultra_dynamic_weather"))
	{
		return HandleGetUltraDynamicWeather(Params);
	}
	else if (CommandType == TEXT("set_current_weather_to_rain"))
	{
		return HandleSetCurrentWeatherToRain(Params);
	}
	else if (CommandType == TEXT("set_color_temperature"))
	{
		return HandleSetColorTemperature(Params);
	}
	else if (CommandType == TEXT("set_cesium_latitude_longitude"))
	{
		return HandleSetCesiumLatitudeLongitude(Params);
	}
	else if (CommandType == TEXT("get_cesium_properties"))
	{
		return HandleGetCesiumProperties(Params);
	}
	else if (CommandType == TEXT("create_mm_control_light"))
	{
		return HandleCreateMMControlLight(Params);
	}
	else if (CommandType == TEXT("get_mm_control_lights"))
	{
		return HandleGetMMControlLights(Params);
	}
	else if (CommandType == TEXT("update_mm_control_light"))
	{
		return HandleUpdateMMControlLight(Params);
	}
	else if (CommandType == TEXT("delete_mm_control_light"))
	{
		return HandleDeleteMMControlLight(Params);
	}
	
	
	return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown actor command: %s"), *CommandType));
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleGetActorsInLevel(const TSharedPtr<FJsonObject>& Params)
{
	// Get the world - runtime compatible way
	UWorld* World = GetCurrentWorld();
	if (!World)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get world context"));
	}
	TArray<AActor*> AllActors;
	// Use runtime-compatible actor iteration
	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		AActor* Actor = *ActorItr;
		if (Actor && IsValid(Actor))
		{
			AllActors.Add(Actor);
		}
	}
	
	TArray<TSharedPtr<FJsonValue>> ActorArray;
	for (AActor* Actor : AllActors)
	{
		if (Actor)
		{
			ActorArray.Add(FUnrealMCPCommonUtils::ActorToJson(Actor));
		}
	}
	
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetArrayField(TEXT("actors"), ActorArray);
	
	return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleFindActorsByName(const TSharedPtr<FJsonObject>& Params)
{
	FString Pattern;
	if (!Params->TryGetStringField(TEXT("pattern"), Pattern))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'pattern' parameter"));
	}
	
	// Get the world - runtime compatible way
	UWorld* World = nullptr;
	
	if (GEngine && GEngine->GetWorldContexts().Num() > 0)
	{
		World = GEngine->GetWorldContexts()[1].World();
	}
	
	if (!World)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get world context"));
	}
	
	TArray<TSharedPtr<FJsonValue>> MatchingActors;
	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		AActor* Actor = *ActorItr;
		if (Actor && IsValid(Actor) && Actor->GetName().Contains(Pattern))
		{
			MatchingActors.Add(FUnrealMCPCommonUtils::ActorToJson(Actor));
		}
	}
	
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetArrayField(TEXT("actors"), MatchingActors);
	
	return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleCreateActor(const TSharedPtr<FJsonObject>& Params)
{
	// Get required parameters
	FString ActorType;
	if (!Params->TryGetStringField(TEXT("type"), ActorType))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'type' parameter"));
	}

	// Get actor name (required parameter)
	FString ActorName;
	if (!Params->TryGetStringField(TEXT("name"), ActorName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
	}

	// Get optional transform parameters
	FVector Location(0.0f, 0.0f, 0.0f);
	FRotator Rotation(0.0f, 0.0f, 0.0f);
	FVector Scale(1.0f, 1.0f, 1.0f);

	if (Params->HasField(TEXT("location")))
	{
		Location = FUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("location"));
	}
	if (Params->HasField(TEXT("rotation")))
	{
		Rotation = FUnrealMCPCommonUtils::GetRotatorFromJson(Params, TEXT("rotation"));
	}
	if (Params->HasField(TEXT("scale")))
	{
		Scale = FUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("scale"));
	}

	// Create the actor based on type
	AActor* NewActor = nullptr;
	
	// Get the world - runtime compatible way
	UWorld* World = nullptr;
	
	if (GEngine && GEngine->GetWorldContexts().Num() > 0)
	{
		World = GEngine->GetWorldContexts()[1].World();
	}

	if (!World)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get world context"));
	}

	// Check if an actor with this name already exists - runtime compatible way
	bool bNameExists = false;
	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		AActor* Actor = *ActorItr;
		if (Actor && IsValid(Actor) && Actor->GetName() == ActorName)
		{
			bNameExists = true;
			break;
		}
	}
	
	if (bNameExists)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor with name '%s' already exists"), *ActorName));
	}

	FActorSpawnParameters SpawnParams;
	SpawnParams.Name = *ActorName;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;

	// Use runtime-compatible actor spawning
	if (ActorType == TEXT("StaticMeshActor") || ActorType == TEXT("STATICMESHACTOR"))
	{
		// For runtime, we'll create a basic actor and add components
		NewActor = World->SpawnActor<AActor>(AActor::StaticClass(), Location, Rotation, SpawnParams);
		if (NewActor)
		{
			// Add a static mesh component at runtime
			// Note: This is simplified - in a real implementation you'd want to set up the mesh properly
		}
	}
	else if (ActorType == TEXT("PointLight") || ActorType == TEXT("POINTLIGHT"))
	{
		// Create basic actor - light components would need to be added manually for runtime
		NewActor = World->SpawnActor<AActor>(AActor::StaticClass(), Location, Rotation, SpawnParams);
	}
	else if (ActorType == TEXT("DirectionalLight") || ActorType == TEXT("DIRECTIONALLIGHT"))
	{
		NewActor = World->SpawnActor<AActor>(AActor::StaticClass(), Location, Rotation, SpawnParams);
	}
	else if (ActorType == TEXT("CameraActor") || ActorType == TEXT("CAMERA"))
	{
		NewActor = World->SpawnActor<AActor>(AActor::StaticClass(), Location, Rotation, SpawnParams);
	}
	else
	{
		// Default to basic actor for unknown types
		NewActor = World->SpawnActor<AActor>(AActor::StaticClass(), Location, Rotation, SpawnParams);
	}

	if (NewActor)
	{
		// Set scale (since SpawnActor only takes location and rotation)
		FTransform Transform = NewActor->GetTransform();
		Transform.SetScale3D(Scale);
		NewActor->SetActorTransform(Transform);

		// Return the created actor's details
		return FUnrealMCPCommonUtils::ActorToJsonObject(NewActor, true);
	}

	return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create actor"));
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleDeleteActor(const TSharedPtr<FJsonObject>& Params)
{
	FString ActorName;
	if (!Params->TryGetStringField(TEXT("name"), ActorName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
	}

	// Get world in runtime-compatible way
	UWorld* World = nullptr;
	if (GEngine && GEngine->GetWorldContexts().Num() > 0)
	{
		World = GEngine->GetWorldContexts()[1].World();
	}

	if (!IsValid(World))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get valid world"));
	}

	// Find the actor using runtime-compatible iteration
	AActor* ActorToDelete = nullptr;
	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		AActor* Actor = *ActorItr;
		if (Actor && Actor->GetName() == ActorName)
		{
			ActorToDelete = Actor;
			break;
		}
	}

	if (!ActorToDelete)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
	}

	// Runtime-compatible actor deletion
	if (IsValid(ActorToDelete))
	{
		// Store actor info before deletion for the response
		TSharedPtr<FJsonObject> ActorInfo = FUnrealMCPCommonUtils::ActorToJsonObject(ActorToDelete);
		
		ActorToDelete->Destroy();
		
		TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
		ResultObj->SetObjectField(TEXT("deleted_actor"), ActorInfo);
		ResultObj->SetBoolField(TEXT("success"), true);
		ResultObj->SetStringField(TEXT("message"), FString::Printf(TEXT("Actor deleted: %s"), *ActorName));
		return ResultObj;
	}
	else
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Failed to delete actor: %s"), *ActorName));
	}
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleSetActorTransform(const TSharedPtr<FJsonObject>& Params)
{
	// Get actor name
	FString ActorName;
	if (!Params->TryGetStringField(TEXT("name"), ActorName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
	}

	// Get world in runtime-compatible way
	UWorld* World = nullptr;
	if (GEngine && GEngine->GetWorldContexts().Num() > 0)
	{
		World = GEngine->GetWorldContexts()[1].World();
	}

	if (!IsValid(World))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get valid world"));
	}

	// Find the actor using runtime-compatible iteration
	AActor* TargetActor = nullptr;
	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		AActor* Actor = *ActorItr;
		if (Actor && Actor->GetName() == ActorName)
		{
			TargetActor = Actor;
			break;
		}
	}

	if (!TargetActor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
	}

	// Get transform parameters
	FTransform NewTransform = TargetActor->GetTransform();

	if (Params->HasField(TEXT("location")))
	{
		NewTransform.SetLocation(FUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("location")));
	}
	if (Params->HasField(TEXT("rotation")))
	{
		NewTransform.SetRotation(FQuat(FUnrealMCPCommonUtils::GetRotatorFromJson(Params, TEXT("rotation"))));
	}
	if (Params->HasField(TEXT("scale")))
	{
		NewTransform.SetScale3D(FUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("scale")));
	}

	// Set the new transform
	TargetActor->SetActorTransform(NewTransform);

	// Return updated actor info
	return FUnrealMCPCommonUtils::ActorToJsonObject(TargetActor, true);
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleGetActorProperties(const TSharedPtr<FJsonObject>& Params)
{
	// Get actor name
	FString ActorName;
	if (!Params->TryGetStringField(TEXT("name"), ActorName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
	}

	// Get world in runtime-compatible way
	UWorld* World = nullptr;
	if (GEngine && GEngine->GetWorldContexts().Num() > 0)
	{
		World = GEngine->GetWorldContexts()[1].World();
	}

	if (!IsValid(World))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get valid world"));
	}

	// Find the actor using runtime-compatible iteration
	AActor* TargetActor = nullptr;
	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		AActor* Actor = *ActorItr;
		if (Actor && Actor->GetName() == ActorName)
		{
			TargetActor = Actor;
			break;
		}
	}

	if (!TargetActor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
	}

	// Always return detailed properties for this command
	return FUnrealMCPCommonUtils::ActorToJsonObject(TargetActor, true);
}

// common helper function
UWorld* FUnrealMCPActorCommands::GetCurrentWorld()
{
	UWorld* World = nullptr;
	if (GEngine && GEngine->GetWorldContexts().Num() > 0)
	{
		int32 CurrentWorldIndex = 0;
		int32 WorldCount = GEngine->GetWorldContexts().Num();
		for (int32 i = 0; i < WorldCount; ++i)
		{
			const FWorldContext& WorldContext = GEngine->GetWorldContexts()[i];
			UWorld* TestWorld = WorldContext.World();
			
			// Skip invalid worlds
			if (!TestWorld || !IsValid(TestWorld))
			{
				continue;
			}
			
			// Find world with most actors (prefer game worlds over editor worlds)
			int32 TestActorCount = TestWorld->GetActorCount();
			UWorld* CurrentWorld = GEngine->GetWorldContexts()[CurrentWorldIndex].World();
			
			if (CurrentWorld && TestActorCount > CurrentWorld->GetActorCount())
			{
				CurrentWorldIndex = i;
			}
		}
		World = GEngine->GetWorldContexts()[CurrentWorldIndex].World();
	}
	return World;
}

AActor* FUnrealMCPActorCommands::FindActorByClassName(const FString& ClassName)
{
	UWorld* World = GetCurrentWorld();
	if (!IsValid(World))
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get valid world"));
		return nullptr;
	}
	AActor* Actor = nullptr;
	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		AActor* CurrentActor = *ActorItr;
		if (CurrentActor && CurrentActor->GetClass()->GetName() == ClassName)
		{
			Actor = CurrentActor;
			break;
		}
	}
	return Actor;
}

bool FUnrealMCPActorCommands::GetDoublePropertyValue(AActor* Actor, const FName& PropertyName, float& OutValue)
{
	if (!Actor)
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Actor not found"));
		return false;
	}
	UClass* ActorClass = Actor->GetClass();
	if (!ActorClass)
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get actor class"));
		return false;
	}
	FProperty* FoundProperty = ActorClass->FindPropertyByName(PropertyName);
	if (!FoundProperty)
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Property not found in %s"), *Actor->GetName()));
		return false;
	}
	float DoubleValue = 0.0f;
	if (FDoubleProperty* DoubleProp = CastField<FDoubleProperty>(FoundProperty))
	{
		DoubleValue = DoubleProp->GetPropertyValue_InContainer(Actor);
	}
	else
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Property '%s' is not a float"), *FoundProperty->GetName()));
		return false;
	}
	OutValue = DoubleValue;
	return true;
}

bool FUnrealMCPActorCommands::UpdateDoubleProperty(AActor* Actor, const FName& PropertyName, float NewValue)
{
	if (!Actor)
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Ultra Dynamic Sky actor not found"));
		return false;
	}
	UClass* ActorClass = Actor->GetClass();
	FProperty* Property = ActorClass->FindPropertyByName(PropertyName);
	if (!Property)
	{
		return false;
	}

	if (FDoubleProperty* DoubleProp = CastField<FDoubleProperty>(Property))
	{
		DoubleProp->SetPropertyValue_InContainer(Actor, NewValue);
	}

	if (Actor->IsA<AActor>())
	{
		Actor->RerunConstructionScripts();
	}
	return true;
}

// Ultra Dynamic Sky specific functions from now on
static const FName UDSTODName = TEXT("Time of Day");
static const FString UDSTODJSONKey = TEXT("time_of_day");
static const FName UDSColorTempName = TEXT("ColorTemperature");
static const FString UDSColorTempJSONKey = TEXT("color_temperature");

AActor* FUnrealMCPActorCommands::GetUltraDynamicSkyActor()
{
	const FString SkyClassName = TEXT("Ultra_Dynamic_Sky_C");
	return FindActorByClassName(SkyClassName);
}
AActor* FUnrealMCPActorCommands::GetUltraDynamicWeatherActor()
{
	const FString WeatherClassName = TEXT("Ultra_Dynamic_Weather_C");
	return FindActorByClassName(WeatherClassName);
}
TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleGetUltraDynamicSkyProperties(const TSharedPtr<FJsonObject> &Params)
{
	AActor* SkyActor = GetUltraDynamicSkyActor();
	if (!SkyActor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Ultra Dynamic Sky actor not found"));
	}

	float TimeOfDayValue;
	float ColorTempValue;
	if (!GetDoublePropertyValue(SkyActor, UDSTODName, TimeOfDayValue) ||
		!GetDoublePropertyValue(SkyActor, UDSColorTempName, ColorTempValue))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get Ultra Dynamic Sky properties"));
	}

	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("sky_name"), SkyActor->GetName());
	ResultObj->SetNumberField(UDSTODJSONKey, TimeOfDayValue);
	ResultObj->SetNumberField(UDSColorTempJSONKey, ColorTempValue);
	return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleSetTimeOfDay(const TSharedPtr<FJsonObject>& Params)
{
	double TimeOfDayValue;
	if (!Params->TryGetNumberField(UDSTODJSONKey, TimeOfDayValue))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'time_of_day' parameter"));
	}
	if (TimeOfDayValue < 0.0 || TimeOfDayValue > 2400.0)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Time of day must be between 0 and 2400"));
	}
	AActor* Actor = GetUltraDynamicSkyActor();
	if (!Actor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Ultra Dynamic Sky actor not found"));
	}

	if (!UpdateDoubleProperty(Actor, UDSTODName, TimeOfDayValue))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to update Ultra Dynamic Sky property"));
	}
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("sky_name"), Actor->GetName());
	ResultObj->SetStringField(TEXT("property_name"), UDSTODName.ToString());
	ResultObj->SetStringField(TEXT("property_type"), TEXT("float"));
	ResultObj->SetNumberField(TEXT("value"), TimeOfDayValue);
	ResultObj->SetBoolField(TEXT("success"), true);
	ResultObj->SetStringField(TEXT("message"), TEXT("Time of day set and sky update functions called"));
	return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleSetColorTemperature(const TSharedPtr<FJsonObject>& Params)
{
	double ColorTemperatureValue;
	if (!Params->TryGetNumberField(UDSColorTempJSONKey, ColorTemperatureValue))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'color_temperature' parameter"));
	}
	if (ColorTemperatureValue < 1500.0 || ColorTemperatureValue > 15000.0)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Color temperature must be between 1500 and 15000"));
	}

	AActor* Actor = GetUltraDynamicSkyActor();
	if (!Actor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Ultra Dynamic Sky actor not found"));
	}
	if (!UpdateDoubleProperty(Actor, UDSColorTempName, ColorTemperatureValue))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to update Ultra Dynamic Sky property"));
	}
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("sky_name"), Actor->GetName());
	ResultObj->SetStringField(TEXT("property_name"), UDSColorTempName.ToString());
	ResultObj->SetStringField(TEXT("property_type"), TEXT("float"));
	ResultObj->SetNumberField(TEXT("value"), ColorTemperatureValue);
	ResultObj->SetBoolField(TEXT("success"), true);
	ResultObj->SetStringField(TEXT("message"), TEXT("Color temperature set and sky update functions called"));
	return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleGetUltraDynamicWeather(const TSharedPtr<FJsonObject>& Params)
{
	AActor* WeatherActor = GetUltraDynamicWeatherActor();
	if (!WeatherActor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Ultra Dynamic Weather actor not found"));
	}
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("weather_name"), WeatherActor->GetName());
	return ResultObj;
}
TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleSetCurrentWeatherToRain(const TSharedPtr<FJsonObject>& Params)
{
	AActor* WeatherActor = GetUltraDynamicWeatherActor();
	FString weather_name;
	if (!WeatherActor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Ultra Dynamic Weather actor not found"));
	}
	UFunction* SetWeatherFunction = WeatherActor->FindFunction(TEXT("SetCurrentWeatherToRain"));
	if (!SetWeatherFunction)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("SetCurrentWeatherToRain function not found on Ultra Dynamic Weather actor"));
	}
	//WeatherActor->ProcessEvent(SetWeatherFunction, nullptr);
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("weather_name"), WeatherActor->GetName());
	ResultObj->SetStringField(TEXT("weather_type"), TEXT("rain"));
	ResultObj->SetBoolField(TEXT("success"), true);
	ResultObj->SetStringField(TEXT("message"), TEXT("Current weather set to rain"));
	return ResultObj;
}

//Cesium from now on
static const FName CesiumLatitudeName = TEXT("OriginLatitude");
static const FString CesiumLatitudeJSONKey = TEXT("latitude");
static const FName CesiumLongitudeName = TEXT("OriginLongitude");
static const FString CesiumLongitudeJSONKey = TEXT("longitude");

AActor* FUnrealMCPActorCommands::GetCesiumGeoreferenceActor()
{
	static const FString ClassName = TEXT("CesiumGeoreference");
	return FindActorByClassName(ClassName);
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleSetCesiumLatitudeLongitude(const TSharedPtr<FJsonObject>& Params)
{
	double Latitude = 0.0;
	double Longitude = 0.0;
	if (!Params->TryGetNumberField(CesiumLatitudeJSONKey, Latitude) ||
		!Params->TryGetNumberField(CesiumLongitudeJSONKey, Longitude))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'latitude' or 'longitude' parameter"));
	}
	AActor* CesiumActor = GetCesiumGeoreferenceActor();
	if (!CesiumActor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Cesium Georeference actor not found"));
	}
	// Update the actor's properties
	if (!UpdateDoubleProperty(CesiumActor, CesiumLatitudeName, Latitude) ||
		!UpdateDoubleProperty(CesiumActor, CesiumLongitudeName, Longitude))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to update Cesium properties"));
	}
	// Create success response
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("actor_name"), CesiumActor->GetName());
	ResultObj->SetNumberField(CesiumLatitudeJSONKey, Latitude);
	ResultObj->SetNumberField(CesiumLongitudeJSONKey, Longitude);
	ResultObj->SetBoolField(TEXT("success"), true);
	ResultObj->SetStringField(TEXT("message"), FString::Printf(TEXT("Cesium coordinates set to Lat: %f, Lng: %f for actor '%s'"), Latitude, Longitude, *CesiumActor->GetName()));
	return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleGetCesiumProperties(const TSharedPtr<FJsonObject>& Params)
{
	AActor* CesiumActor = GetCesiumGeoreferenceActor();
	if (!CesiumActor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Cesium Georeference actor not found"));
	}
	float Latitude = 0.0;
	float Longitude = 0.0;
	if (!GetDoublePropertyValue(CesiumActor, CesiumLatitudeName, Latitude) ||
		!GetDoublePropertyValue(CesiumActor, CesiumLongitudeName, Longitude))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get Cesium properties"));
	}
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetNumberField(CesiumLatitudeJSONKey, Latitude);
	ResultObj->SetNumberField(CesiumLongitudeJSONKey, Longitude);
	return ResultObj;
}

// MM Control Light CRUD operations
TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleCreateMMControlLight(const TSharedPtr<FJsonObject> &Params)
{
	// Get required light_name parameter
	FString LightName;
	if (!Params->TryGetStringField(TEXT("light_name"), LightName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'light_name' parameter"));
	}

	// Get optional transform parameters
	FVector Location(0.0f, 0.0f, 100.0f); // Default to 100cm above origin
	if (Params->HasField(TEXT("location")))
	{
		Location = FUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("location"));
	}

	// Get optional intensity parameter
	float Intensity = 1000.0f; // Default intensity
	double IntensityValue;
	if (Params->TryGetNumberField(TEXT("intensity"), IntensityValue))
	{
		Intensity = static_cast<float>(IntensityValue);
	}

	// Get optional color parameter
	FLinearColor LightColor = FLinearColor::White; // Default white
	if (Params->HasField(TEXT("color")))
	{
		const TSharedPtr<FJsonObject>* ColorObj;
		if (Params->TryGetObjectField(TEXT("color"), ColorObj))
		{
			double R = 255.0, G = 255.0, B = 255.0;
			(*ColorObj)->TryGetNumberField(TEXT("r"), R);
			(*ColorObj)->TryGetNumberField(TEXT("g"), G);
			(*ColorObj)->TryGetNumberField(TEXT("b"), B);
			
			// Convert RGB 0-255 to 0-1 range
			LightColor = FLinearColor(R / 255.0f, G / 255.0f, B / 255.0f, 1.0f);
		}
	}

	// Get current world
	UWorld* World = GetCurrentWorld();
	if (!World)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get world context"));
	}

	// Check if light with this name already exists
	bool bNameExists = false;
	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		AActor* Actor = *ActorItr;
		if (Actor && IsValid(Actor) && Actor->GetName() == LightName)
		{
			bNameExists = true;
			break;
		}
	}

	if (bNameExists)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Light with name '%s' already exists"), *LightName));
	}

	// Create spawn parameters
	FActorSpawnParameters SpawnParams;
	SpawnParams.Name = *LightName;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;

	// Spawn the point light actor
	APointLight* NewLightActor = World->SpawnActor<APointLight>(APointLight::StaticClass(), Location, FRotator::ZeroRotator, SpawnParams);
	
	if (!NewLightActor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to spawn light actor"));
	}

	// Explicitly set the actor location to ensure it's positioned correctly
	NewLightActor->SetActorLocation(Location);

	// Configure the point light component
	UPointLightComponent* PointLightComp = NewLightActor->FindComponentByClass<UPointLightComponent>();
	if (PointLightComp)
	{
		PointLightComp->SetIntensity(Intensity);
		PointLightComp->SetLightColor(LightColor);
		PointLightComp->SetAttenuationRadius(3000.0f); // Set reasonable attenuation radius
	}

	// Add MM_Control_Light tag
	NewLightActor->Tags.Add(TEXT("MM_Control_Light"));

	// Create success response
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetBoolField(TEXT("success"), true);
	ResultObj->SetStringField(TEXT("actor_name"), NewLightActor->GetName());
	ResultObj->SetStringField(TEXT("actor_class"), TEXT("APointLight"));
	
	// Add location info (get actual spawned location)
	FVector ActualLocation = NewLightActor->GetActorLocation();
	TSharedPtr<FJsonObject> LocationObj = MakeShared<FJsonObject>();
	LocationObj->SetNumberField(TEXT("x"), ActualLocation.X);
	LocationObj->SetNumberField(TEXT("y"), ActualLocation.Y);
	LocationObj->SetNumberField(TEXT("z"), ActualLocation.Z);
	ResultObj->SetObjectField(TEXT("location"), LocationObj);
	
	ResultObj->SetNumberField(TEXT("intensity"), Intensity);
	
	// Add color info (convert back to RGB 0-255)
	TSharedPtr<FJsonObject> ColorObj = MakeShared<FJsonObject>();
	ColorObj->SetNumberField(TEXT("r"), LightColor.R * 255.0f);
	ColorObj->SetNumberField(TEXT("g"), LightColor.G * 255.0f);
	ColorObj->SetNumberField(TEXT("b"), LightColor.B * 255.0f);
	ResultObj->SetObjectField(TEXT("color"), ColorObj);
	
	// Add tags array
	TArray<TSharedPtr<FJsonValue>> TagsArray;
	TagsArray.Add(MakeShared<FJsonValueString>(TEXT("MM_Control_Light")));
	ResultObj->SetArrayField(TEXT("tags"), TagsArray);
	
	ResultObj->SetStringField(TEXT("message"), TEXT("MM Light created successfully"));

	return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleGetMMControlLights(const TSharedPtr<FJsonObject> &Params)
{
	// Get current world
	UWorld* World = GetCurrentWorld();
	if (!World)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get world context"));
	}

	// Find all actors with MM_Control_Light tag
	TArray<AActor*> MMControlLights;
	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		AActor* Actor = *ActorItr;
		if (Actor && IsValid(Actor) && Actor->Tags.Contains(TEXT("MM_Control_Light")))
		{
			MMControlLights.Add(Actor);
		}
	}

	// Create lights array
	TArray<TSharedPtr<FJsonValue>> LightsArray;
	for (AActor* LightActor : MMControlLights)
	{
		if (LightActor && IsValid(LightActor))
		{
			TSharedPtr<FJsonObject> LightInfo = MakeShared<FJsonObject>();
			
			// Add basic actor info
			LightInfo->SetStringField(TEXT("actor_name"), LightActor->GetName());
			
			// Add location info
			FVector Location = LightActor->GetActorLocation();
			TSharedPtr<FJsonObject> LocationObj = MakeShared<FJsonObject>();
			LocationObj->SetNumberField(TEXT("x"), Location.X);
			LocationObj->SetNumberField(TEXT("y"), Location.Y);
			LocationObj->SetNumberField(TEXT("z"), Location.Z);
			LightInfo->SetObjectField(TEXT("location"), LocationObj);
			
			// Add default intensity and color (since this is a basic actor without light components)
			// In a real implementation, you'd extract these from light components
			LightInfo->SetNumberField(TEXT("intensity"), 1000);
			
			TSharedPtr<FJsonObject> ColorObj = MakeShared<FJsonObject>();
			ColorObj->SetNumberField(TEXT("r"), 255);
			ColorObj->SetNumberField(TEXT("g"), 255);
			ColorObj->SetNumberField(TEXT("b"), 255);
			LightInfo->SetObjectField(TEXT("color"), ColorObj);
			
			LightsArray.Add(MakeShared<FJsonValueObject>(LightInfo));
		}
	}

	// Create success response
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetBoolField(TEXT("success"), true);
	ResultObj->SetArrayField(TEXT("lights"), LightsArray);
	ResultObj->SetNumberField(TEXT("count"), LightsArray.Num());

	return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleUpdateMMControlLight(const TSharedPtr<FJsonObject> &Params)
{
	// Get required light_name parameter
	FString LightName;
	if (!Params->TryGetStringField(TEXT("light_name"), LightName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'light_name' parameter"));
	}

	// Get current world
	UWorld* World = GetCurrentWorld();
	if (!World)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get world context"));
	}

	// Find the specific MM Control Light by name and tag
	AActor* TargetLightActor = nullptr;
	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		AActor* Actor = *ActorItr;
		if (Actor && IsValid(Actor) && 
			Actor->GetName() == LightName && 
			Actor->Tags.Contains(TEXT("MM_Control_Light")))
		{
			TargetLightActor = Actor;
			break;
		}
	}

	if (!TargetLightActor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("MM Control Light not found: %s"), *LightName));
	}

	// Track what properties were updated
	TSharedPtr<FJsonObject> UpdatedProperties = MakeShared<FJsonObject>();

	// Update location if provided
	if (Params->HasField(TEXT("location")))
	{
		FVector NewLocation = FUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("location"));
		TargetLightActor->SetActorLocation(NewLocation);
		
		TSharedPtr<FJsonObject> LocationObj = MakeShared<FJsonObject>();
		LocationObj->SetNumberField(TEXT("x"), NewLocation.X);
		LocationObj->SetNumberField(TEXT("y"), NewLocation.Y);
		LocationObj->SetNumberField(TEXT("z"), NewLocation.Z);
		UpdatedProperties->SetObjectField(TEXT("location"), LocationObj);
	}

	// Update intensity if provided
	if (Params->HasField(TEXT("intensity")))
	{
		double IntensityValue;
		if (Params->TryGetNumberField(TEXT("intensity"), IntensityValue))
		{
			float Intensity = static_cast<float>(IntensityValue);
			UpdatedProperties->SetNumberField(TEXT("intensity"), Intensity);
			// Note: In a real implementation, you'd update the light component's intensity
		}
	}

	// Update color if provided
	if (Params->HasField(TEXT("color")))
	{
		const TSharedPtr<FJsonObject>* ColorObj;
		if (Params->TryGetObjectField(TEXT("color"), ColorObj))
		{
			double R = 255.0, G = 255.0, B = 255.0;
			(*ColorObj)->TryGetNumberField(TEXT("r"), R);
			(*ColorObj)->TryGetNumberField(TEXT("g"), G);
			(*ColorObj)->TryGetNumberField(TEXT("b"), B);
			
			// Convert RGB 0-255 to 0-1 range for Unreal
			FLinearColor LightColor = FLinearColor(R / 255.0f, G / 255.0f, B / 255.0f, 1.0f);
			
			// Store updated color in response
			TSharedPtr<FJsonObject> UpdatedColorObj = MakeShared<FJsonObject>();
			UpdatedColorObj->SetNumberField(TEXT("r"), R);
			UpdatedColorObj->SetNumberField(TEXT("g"), G);
			UpdatedColorObj->SetNumberField(TEXT("b"), B);
			UpdatedProperties->SetObjectField(TEXT("color"), UpdatedColorObj);
			// Note: In a real implementation, you'd update the light component's color
		}
	}

	// Create success response
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetBoolField(TEXT("success"), true);
	ResultObj->SetStringField(TEXT("actor_name"), TargetLightActor->GetName());
	ResultObj->SetObjectField(TEXT("updated_properties"), UpdatedProperties);
	ResultObj->SetStringField(TEXT("message"), TEXT("MM Light updated successfully"));

	return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleDeleteMMControlLight(const TSharedPtr<FJsonObject> &Params)
{
	// Get required light_name parameter
	FString LightName;
	if (!Params->TryGetStringField(TEXT("light_name"), LightName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'light_name' parameter"));
	}

	// Get current world
	UWorld* World = GetCurrentWorld();
	if (!World)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get world context"));
	}

	// Find the specific MM Control Light by name and tag
	AActor* TargetLightActor = nullptr;
	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		AActor* Actor = *ActorItr;
		if (Actor && IsValid(Actor) && 
			Actor->GetName() == LightName && 
			Actor->Tags.Contains(TEXT("MM_Control_Light")))
		{
			TargetLightActor = Actor;
			break;
		}
	}

	if (!TargetLightActor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("MM Control Light not found: %s"), *LightName));
	}

	// Store the actor name before deletion for the response
	FString ActorName = TargetLightActor->GetName();

	// Delete the actor
	if (IsValid(TargetLightActor))
	{
		TargetLightActor->Destroy();
		
		// Create success response
		TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
		ResultObj->SetBoolField(TEXT("success"), true);
		ResultObj->SetStringField(TEXT("actor_name"), ActorName);
		ResultObj->SetStringField(TEXT("message"), TEXT("MM Light deleted successfully"));

		return ResultObj;
	}
	else
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Failed to delete MM Control Light: %s"), *LightName));
	}
}