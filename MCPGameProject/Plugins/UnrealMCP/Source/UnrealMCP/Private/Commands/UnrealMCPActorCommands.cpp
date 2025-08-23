#include "Commands/UnrealMCPActorCommands.h"
#include "Commands/UnrealMCPCommonUtils.h"
#include "GameFramework/Actor.h"
#include "Components/MMCesiumEventComponent.h"
#include "Blueprints/MMCommandSenderBlueprint.h"

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
	else if (CommandType == TEXT("set_color_temperature"))
	{
		return HandleSetColorTemperature(Params);
	}
	else if (CommandType == TEXT("trigger_custom_event"))
	{
		return HandleTriggerCustomEvent(Params);
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

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleGetUltraDynamicSkyProperties(const TSharedPtr<FJsonObject> &Params)
{
	AActor* SkyActor = GetUltraDynamicSkyActor();
	if (!SkyActor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Ultra Dynamic Sky actor not found"));
	}
	const FName TODName = TEXT("Time of Day");
	const FName ColorTempName = TEXT("ColorTemperature");

	float TimeOfDayValue = GetUdsDoublePropertyValue(SkyActor, TODName);
	float ColorTempValue = GetUdsDoublePropertyValue(SkyActor, ColorTempName);

	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("sky_name"), SkyActor->GetName());
	ResultObj->SetNumberField(TEXT("time_of_day"), TimeOfDayValue);
	ResultObj->SetNumberField(TEXT("color_temperature"), ColorTempValue);
	return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleSetTimeOfDay(const TSharedPtr<FJsonObject>& Params)
{
	static const FName PropertyName = TEXT("Time of Day");
	double TimeOfDayValue;
	if (!Params->TryGetNumberField(TEXT("time_of_day"), TimeOfDayValue))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'time_of_day' parameter"));
	}
	if (TimeOfDayValue < 0.0 || TimeOfDayValue > 2400.0)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Time of day must be between 0 and 2400"));
	}
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	UpdateUdsDoubleProperty(PropertyName, TimeOfDayValue, ResultObj);
	return ResultObj;
}

AActor *FUnrealMCPActorCommands::GetUltraDynamicSkyActor()
{
	UWorld* World = GetCurrentWorld();
	if (!IsValid(World))
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get valid world"));
		return nullptr;
	}
	const FString SkyClassName = TEXT("Ultra_Dynamic_Sky_C");
	AActor* SkyActor = nullptr;
	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		AActor* Actor = *ActorItr;
		if (Actor && Actor->GetClass()->GetName() == SkyClassName)
		{
			SkyActor = Actor;
			break;
		}
	}
	return SkyActor;
}

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

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleSetColorTemperature(const TSharedPtr<FJsonObject>& Params)
{
	FName PropertyName = TEXT("ColorTemperature");
	double ColorTemperatureValue;
	if (!Params->TryGetNumberField(TEXT("color_temperature"), ColorTemperatureValue))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'color_temperature' parameter"));
	}
	if (ColorTemperatureValue < 1500.0 || ColorTemperatureValue > 15000.0)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Color temperature must be between 1500 and 15000"));
	}
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	UpdateUdsDoubleProperty(PropertyName, ColorTemperatureValue, ResultObj);
	return ResultObj;
}

void FUnrealMCPActorCommands::UpdateUdsDoubleProperty(const FName& PropertyName, float NewValue, TSharedPtr<FJsonObject>& ResultObj)
{
	AActor* Actor = GetUltraDynamicSkyActor();
	if (!Actor)
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Ultra Dynamic Sky actor not found"));
		return;
	}
	UClass* ActorClass = Actor->GetClass();
	FProperty* Property = ActorClass->FindPropertyByName(PropertyName);
	if (!Property)
	{
		return;
	}

	if (FDoubleProperty* DoubleProp = CastField<FDoubleProperty>(Property))
	{
		DoubleProp->SetPropertyValue_InContainer(Actor, NewValue);
	}

	if (Actor->IsA<AActor>())
	{
		Actor->RerunConstructionScripts();
	}

	ResultObj->SetStringField(TEXT("sky_name"), Actor->GetName());
	ResultObj->SetStringField(TEXT("property_name"), Property->GetName());
	ResultObj->SetStringField(TEXT("property_type"), Property->GetClass()->GetName());
	ResultObj->SetNumberField(TEXT("value"), NewValue);
	ResultObj->SetBoolField(TEXT("success"), true);
	ResultObj->SetStringField(TEXT("message"), TEXT("Time of day set and sky update functions called"));
}

void FUnrealMCPActorCommands::GetUdsDoubleProperty(const FName& PropertyName, TSharedPtr<FJsonObject>& ResultObj)
{
	AActor* SkyActor = GetUltraDynamicSkyActor();
	if (!SkyActor)
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Ultra Dynamic Sky actor not found"));
		return;
	}
	UClass* ActorClass = SkyActor->GetClass();
	if (!ActorClass)
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get actor class"));
		return;
	}
	FProperty* UdsProperty = ActorClass->FindPropertyByName(PropertyName);
	if (!UdsProperty)
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Property not found in %s"), *SkyActor->GetName()));
		return;
	}
	float DoubleValue = 0.0f;
	if (FDoubleProperty* DoubleProp = CastField<FDoubleProperty>(UdsProperty))
	{
		DoubleValue = DoubleProp->GetPropertyValue_InContainer(SkyActor);
	}
	else
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Property '%s' is not a float"), *UdsProperty->GetName()));
		return;
	}
	ResultObj->SetStringField(TEXT("sky_name"), SkyActor->GetName());
	ResultObj->SetStringField(TEXT("property_name"), PropertyName.ToString());
	ResultObj->SetStringField(TEXT("property_type"), UdsProperty->GetClass()->GetName());
	ResultObj->SetNumberField(TEXT("value"), DoubleValue);
	ResultObj->SetBoolField(TEXT("success"), true);
	ResultObj->SetStringField(TEXT("message"), TEXT("Retrieved property value successfully"));
}

float FUnrealMCPActorCommands::GetUdsDoublePropertyValue(AActor* SkyActor,const FName& PropertyName)
{
	if (!SkyActor)
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Ultra Dynamic Sky actor not found"));
		return 0.0f;
	}
	UClass* ActorClass = SkyActor->GetClass();
	if (!ActorClass)
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get actor class"));
		return 0.0f;
	}
	FProperty* UdsProperty = ActorClass->FindPropertyByName(PropertyName);
	if (!UdsProperty)
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Property not found in %s"), *SkyActor->GetName()));
		return 0.0f;
	}
	float DoubleValue = 0.0f;
	if (FDoubleProperty* DoubleProp = CastField<FDoubleProperty>(UdsProperty))
	{
		DoubleValue = DoubleProp->GetPropertyValue_InContainer(SkyActor);
	}
	else
	{
		FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Property '%s' is not a float"), *UdsProperty->GetName()));
		return 0.0f;
	}
	return DoubleValue;
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleTriggerCustomEvent(const TSharedPtr<FJsonObject>& Params)
{
	// Get required parameters
	FString ActorName;
	if (!Params->TryGetStringField(TEXT("actor_name"), ActorName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'actor_name' parameter"));
	}

	FString EventName;
	if (!Params->TryGetStringField(TEXT("event_name"), EventName))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'event_name' parameter"));
	}

	// Get optional event parameters
	FString EventParams = TEXT("{}");
	if (Params->HasField(TEXT("event_params")))
	{
		const TSharedPtr<FJsonObject>* EventParamsObj;
		if (Params->TryGetObjectField(TEXT("event_params"), EventParamsObj))
		{
			// Convert JSON object to string
			FString EventParamsString;
			TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&EventParamsString);
			FJsonSerializer::Serialize(EventParamsObj->ToSharedRef(), Writer);
			EventParams = EventParamsString;
		}
		else
		{
			// Try to get as string directly
			Params->TryGetStringField(TEXT("event_params"), EventParams);
		}
	}

	// Get the world
	UWorld* World = GetCurrentWorld();
	if (!World)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get world context"));
	}

	// Find actors with MMCesiumEventComponent by name - prioritize MMCommandSenderBlueprint
	UMMCesiumEventComponent* TargetComponent = nullptr;
	AActor* TargetActor = nullptr;
	AMMCommandSenderBlueprint* BlueprintActor = nullptr;
	bool bFoundBlueprintActor = false;
	
	// First pass: Look for MMCommandSenderBlueprint actors
	for (TActorIterator<AMMCommandSenderBlueprint> BlueprintItr(World); BlueprintItr; ++BlueprintItr)
	{
		AMMCommandSenderBlueprint* Actor = *BlueprintItr;
		if (Actor && IsValid(Actor) && Actor->GetName() == ActorName)
		{
			// Check if it has the CesiumEventComponent
			if (Actor->CesiumEventComponent && IsValid(Actor->CesiumEventComponent))
			{
				TargetComponent = Actor->CesiumEventComponent;
				TargetActor = Actor;
				BlueprintActor = Actor;
				bFoundBlueprintActor = true;
				UE_LOG(LogTemp, Display, TEXT("Found MMCommandSenderBlueprint actor: %s"), *ActorName);
				break;
			}
		}
	}
	
	// Second pass: Fallback to generic actors with MMCesiumEventComponent if Blueprint not found
	if (!TargetComponent)
	{
		UE_LOG(LogTemp, Display, TEXT("MMCommandSenderBlueprint not found, searching generic actors for: %s"), *ActorName);
		
		for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
		{
			AActor* Actor = *ActorItr;
			if (Actor && IsValid(Actor) && Actor->GetName() == ActorName)
			{
				// Look for MMCesiumEventComponent on this actor
				TargetComponent = Actor->FindComponentByClass<UMMCesiumEventComponent>();
				if (TargetComponent)
				{
					TargetActor = Actor;
					UE_LOG(LogTemp, Display, TEXT("Found generic actor with MMCesiumEventComponent: %s"), *ActorName);
					break;
				}
			}
		}
	}

	if (!TargetComponent || !TargetActor)
	{
		FString ErrorMsg = FString::Printf(TEXT("Actor with MMCesiumEventComponent not found: %s. Searched %s actors."), 
			*ActorName, 
			bFoundBlueprintActor ? TEXT("MMCommandSenderBlueprint and generic") : TEXT("generic"));
		return FUnrealMCPCommonUtils::CreateErrorResponse(ErrorMsg);
	}

	// Trigger the custom event on the component
	TargetComponent->TriggerCustomEvent(EventName, EventParams);

	// Create success response with enhanced information
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("actor_name"), ActorName);
	ResultObj->SetStringField(TEXT("actor_type"), bFoundBlueprintActor ? TEXT("MMCommandSenderBlueprint") : TEXT("Generic Actor"));
	ResultObj->SetStringField(TEXT("actor_class"), TargetActor->GetClass()->GetName());
	ResultObj->SetStringField(TEXT("event_name"), EventName);
	ResultObj->SetStringField(TEXT("event_params"), EventParams);
	ResultObj->SetBoolField(TEXT("success"), true);
	ResultObj->SetNumberField(TEXT("actors_found"), 1);
	
	FString Message = FString::Printf(TEXT("Custom event '%s' triggered on %s '%s'"), 
		*EventName, 
		bFoundBlueprintActor ? TEXT("MMCommandSenderBlueprint") : TEXT("actor"), 
		*ActorName);
	ResultObj->SetStringField(TEXT("message"), Message);

	return ResultObj;
}