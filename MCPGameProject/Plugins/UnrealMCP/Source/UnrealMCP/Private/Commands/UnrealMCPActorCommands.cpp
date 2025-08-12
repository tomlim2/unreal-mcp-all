#include "Commands/UnrealMCPActorCommands.h"
#include "Commands/UnrealMCPCommonUtils.h"
#include "GameFramework/Actor.h"

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
	else if (CommandType == TEXT("get_time_of_day"))
	{
		return HandleGetTimeOfDay(Params);
	}
	else if (CommandType == TEXT("set_time_of_day"))
	{
		return HandleSetTimeOfDay(Params);
	}
	else if (CommandType == TEXT("get_ultra_dynamic_sky"))
	{
		return HandleGetUltraDynamicSky(Params);
	}
	
	return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown actor command: %s"), *CommandType));
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleGetActorsInLevel(const TSharedPtr<FJsonObject>& Params)
{
	// Get the world - runtime compatible way
	UWorld* World = nullptr;
	
	// Try to get world from GEngine if available
	if (GEngine && GEngine->GetWorldContexts().Num() > 0)
	{
		World = GEngine->GetWorldContexts()[1].World();
	}
	
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

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleGetTimeOfDay(const TSharedPtr<FJsonObject>& Params)
{
	// Get sky actor name (default to Ultra_Dynamic_Sky_C_0)
	FString SkyName = TEXT("Ultra_Dynamic_Sky_C_0");
	Params->TryGetStringField(TEXT("sky_name"), SkyName);

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

	// Find the sky actor using runtime-compatible iteration
	AActor* SkyActor = nullptr;
	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		AActor* Actor = *ActorItr;
		if (Actor && Actor->GetName() == SkyName)
		{
			SkyActor = Actor;
			break;
		}
	}

	if (!SkyActor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Ultra Dynamic Sky actor not found: %s"), *SkyName));
	}

	// Get the Time of Day property - try multiple possible property names and types
	UClass* ActorClass = SkyActor->GetClass();
	FProperty* TimeOfDayProperty = nullptr;
	
	// Try different possible property names
	TArray<FString> PossibleNames = {
		TEXT("Time of Day"),
		TEXT("TimeOfDay"), 
		TEXT("Time_of_Day"),
		TEXT("CurrentTime"),
		TEXT("SunAngle"),
		TEXT("Hour")
	};
	
	for (const FString& PropertyName : PossibleNames)
	{
		TimeOfDayProperty = ActorClass->FindPropertyByName(*PropertyName);
		if (TimeOfDayProperty)
		{
			break;
		}
	}
	
	if (!TimeOfDayProperty)
	{
		// List all properties for debugging
		FString PropertyList;
		for (TFieldIterator<FProperty> PropIt(ActorClass); PropIt; ++PropIt)
		{
			FProperty* Property = *PropIt;
			PropertyList += FString::Printf(TEXT("%s (%s), "), *Property->GetName(), *Property->GetClass()->GetName());
		}
		
		return FUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Time of Day property not found. Available properties: %s"), *PropertyList)
		);
	}

	// Get the property value - try different property types
	float TimeOfDayValue = 0.0f;
	bool bFoundValue = false;
	
	if (FFloatProperty* FloatProp = CastField<FFloatProperty>(TimeOfDayProperty))
	{
		TimeOfDayValue = FloatProp->GetPropertyValue_InContainer(SkyActor);
		bFoundValue = true;
	}
	else if (FDoubleProperty* DoubleProp = CastField<FDoubleProperty>(TimeOfDayProperty))
	{
		TimeOfDayValue = static_cast<float>(DoubleProp->GetPropertyValue_InContainer(SkyActor));
		bFoundValue = true;
	}
	else if (FIntProperty* IntProp = CastField<FIntProperty>(TimeOfDayProperty))
	{
		TimeOfDayValue = static_cast<float>(IntProp->GetPropertyValue_InContainer(SkyActor));
		bFoundValue = true;
	}
	else if (FByteProperty* ByteProp = CastField<FByteProperty>(TimeOfDayProperty))
	{
		TimeOfDayValue = static_cast<float>(ByteProp->GetPropertyValue_InContainer(SkyActor));
		bFoundValue = true;
	}
	
	if (!bFoundValue)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Time of Day property '%s' is of unsupported type: %s"), 
				*TimeOfDayProperty->GetName(), *TimeOfDayProperty->GetClass()->GetName())
		);
	}

	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetNumberField(TEXT("time_of_day"), TimeOfDayValue);
	ResultObj->SetStringField(TEXT("sky_name"), SkyName);
	ResultObj->SetStringField(TEXT("property_name"), TimeOfDayProperty->GetName());
	ResultObj->SetStringField(TEXT("property_type"), TimeOfDayProperty->GetClass()->GetName());
	
	return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleSetTimeOfDay(const TSharedPtr<FJsonObject>& Params)
{
	// Get sky actor name (default to Ultra_Dynamic_Sky_C_0)
	FString SkyName = TEXT("Ultra_Dynamic_Sky_C_0");
	Params->TryGetStringField(TEXT("sky_name"), SkyName);

	// Get time of day value
	double TimeOfDayValue;
	if (!Params->TryGetNumberField(TEXT("time_of_day"), TimeOfDayValue))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'time_of_day' parameter"));
	}

	// Validate time range (0-24)
	if (TimeOfDayValue < 0.0 || TimeOfDayValue > 2400.0)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Time of day must be between 0 and 2400"));
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

	// Find the sky actor using runtime-compatible iteration
	AActor* SkyActor = nullptr;
	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		AActor* Actor = *ActorItr;
		if (Actor && Actor->GetName() == SkyName)
		{
			SkyActor = Actor;
			break;
		}
	}

	if (!SkyActor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Ultra Dynamic Sky actor not found: %s"), *SkyName));
	}

	// Get the Time of Day property - try multiple possible property names and types
	UClass* ActorClass = SkyActor->GetClass();
	FProperty* TimeOfDayProperty = nullptr;
	
	// Try different possible property names
	TArray<FString> PossibleNames = {
		TEXT("Time of Day"),
		TEXT("TimeOfDay"), 
		TEXT("Time_of_Day"),
		TEXT("CurrentTime"),
		TEXT("SunAngle"),
		TEXT("Hour")
	};
	
	for (const FString& PropertyName : PossibleNames)
	{
		TimeOfDayProperty = ActorClass->FindPropertyByName(*PropertyName);
		if (TimeOfDayProperty)
		{
			break;
		}
	}
	
	if (!TimeOfDayProperty)
	{
		// List all properties for debugging
		FString PropertyList;
		for (TFieldIterator<FProperty> PropIt(ActorClass); PropIt; ++PropIt)
		{
			FProperty* Property = *PropIt;
			PropertyList += FString::Printf(TEXT("%s (%s), "), *Property->GetName(), *Property->GetClass()->GetName());
		}
		
		return FUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Time of Day property not found. Available properties: %s"), *PropertyList)
		);
	}

	// Set the property value - try different property types
	bool bValueSet = false;
	
	if (FFloatProperty* FloatProp = CastField<FFloatProperty>(TimeOfDayProperty))
	{
		FloatProp->SetPropertyValue_InContainer(SkyActor, static_cast<float>(TimeOfDayValue));
		bValueSet = true;
	}
	else if (FDoubleProperty* DoubleProp = CastField<FDoubleProperty>(TimeOfDayProperty))
	{
		DoubleProp->SetPropertyValue_InContainer(SkyActor, static_cast<double>(TimeOfDayValue));
		bValueSet = true;
	}
	else if (FIntProperty* IntProp = CastField<FIntProperty>(TimeOfDayProperty))
	{
		IntProp->SetPropertyValue_InContainer(SkyActor, static_cast<int32>(TimeOfDayValue));
		bValueSet = true;
	}
	else if (FByteProperty* ByteProp = CastField<FByteProperty>(TimeOfDayProperty))
	{
		ByteProp->SetPropertyValue_InContainer(SkyActor, static_cast<uint8>(TimeOfDayValue));
		bValueSet = true;
	}
	
	if (!bValueSet)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Time of Day property '%s' is of unsupported type: %s"), 
				*TimeOfDayProperty->GetName(), *TimeOfDayProperty->GetClass()->GetName())
		);
	}

	// Call Blueprint's update functions to refresh the sky
	// Ultra Dynamic Sky typically has these functions: UpdateSunAndMoon, RecalculateVariables, etc.
	UFunction* UpdateFunction = nullptr;
	// Try to find common Ultra Dynamic Sky update functions
	TArray<FString> UpdateFunctionNames = {
		TEXT("Update Sun and Moon"),
		TEXT("UpdateSunAndMoon"),
		TEXT("Update Sky"),
		TEXT("UpdateSky"),
		TEXT("Recalculate Variables"),
		TEXT("RecalculateVariables"),
		TEXT("Construction Script"),
		TEXT("ConstructionScript"),
		TEXT("Update Sun Angle"),
		TEXT("UpdateSunAngle")
	};
	
	for (const FString& FunctionName : UpdateFunctionNames)
	{
		UpdateFunction = SkyActor->FindFunction(*FunctionName);
		if (UpdateFunction)
		{
			// Call the update function
			SkyActor->ProcessEvent(UpdateFunction, nullptr);
			UE_LOG(LogTemp, Log, TEXT("Called update function: %s"), *FunctionName);
			break;
		}
	}
	
	// If no specific update function found, try to call ReceiveBeginPlay or similar
	if (!UpdateFunction)
	{
		UpdateFunction = SkyActor->FindFunction(TEXT("ReceiveBeginPlay"));
		if (UpdateFunction)
		{
			SkyActor->ProcessEvent(UpdateFunction, nullptr);
			UE_LOG(LogTemp, Log, TEXT("Called ReceiveBeginPlay to refresh sky"));
		}
	}
	
	// Also try to mark the actor for reconstruction/update
	if (SkyActor->IsA<AActor>())
	{
		SkyActor->RerunConstructionScripts();
		UE_LOG(LogTemp, Log, TEXT("Reran construction scripts for sky actor"));
	}
	
	// Force update all components
	TArray<UActorComponent*> Components;
	SkyActor->GetComponents<UActorComponent>(Components);
	for (UActorComponent* Component : Components)
	{
		if (Component)
		{
			Component->MarkRenderStateDirty();
			if (USceneComponent* SceneComp = Cast<USceneComponent>(Component))
			{
				SceneComp->MarkRenderTransformDirty();
			}
		}
	}
	
	// Try to call Tick function to force immediate update
	UFunction* TickFunction = SkyActor->FindFunction(TEXT("ReceiveTick"));
	if (TickFunction)
	{
		// Create tick parameters
		struct FTickParams
		{
			float DeltaSeconds;
		};
		FTickParams TickParams;
		TickParams.DeltaSeconds = 0.0f;
		
		SkyActor->ProcessEvent(TickFunction, &TickParams);
		UE_LOG(LogTemp, Log, TEXT("Called ReceiveTick to force sky update"));
	}
	
	// Mark the world as needing lighting rebuild
	if (UWorld* SkyWorld = SkyActor->GetWorld())
	{
		SkyWorld->MarkPackageDirty();
	}

	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetNumberField(TEXT("time_of_day"), TimeOfDayValue);
	ResultObj->SetStringField(TEXT("sky_name"), SkyName);
	ResultObj->SetStringField(TEXT("property_name"), TimeOfDayProperty->GetName());
	ResultObj->SetStringField(TEXT("property_type"), TimeOfDayProperty->GetClass()->GetName());
	ResultObj->SetBoolField(TEXT("success"), true);
	ResultObj->SetBoolField(TEXT("update_functions_called"), UpdateFunction != nullptr);
	ResultObj->SetStringField(TEXT("message"), TEXT("Time of day set and sky update functions called"));
	
	return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPActorCommands::HandleGetUltraDynamicSky(const TSharedPtr<FJsonObject> &Params)
{
	UWorld* World = nullptr;
	if (GEngine && GEngine->GetWorldContexts().Num() > 0)
	{
		World = GEngine->GetWorldContexts()[1].World();
	}
	if (!IsValid(World))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get valid world"));
	}

	AActor* SkyActor = nullptr;
	FString SkyClassName = TEXT("Ultra_Dynamic_Sky_C");
	for (TActorIterator<AActor> ActorItr(World); ActorItr; ++ActorItr)
	{
		AActor* Actor = *ActorItr;
		if (Actor && Actor->GetClass()->GetName() == SkyClassName)
		{
			SkyActor = Actor;
			break;
		}
	}

	if (!SkyActor)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Ultra Dynamic Sky actor not found: %s"), *SkyClassName));
	}

	UClass* ActorClass = SkyActor->GetClass();
	FProperty* TimeOfDayProperty = nullptr;
	const FString PropertyName = TEXT("Time of Day");
	TimeOfDayProperty = ActorClass->FindPropertyByName(*PropertyName);
	if (!TimeOfDayProperty)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Time of Day property not found in %s"), *SkyActor->GetName()));
	}
	float TimeOfDayValue = 0.0f;
	if (FDoubleProperty* DoubleProp = CastField<FDoubleProperty>(TimeOfDayProperty))
	{
		TimeOfDayValue = DoubleProp->GetPropertyValue_InContainer(SkyActor);
	}
	else
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Time of Day property '%s' is not a float"), *TimeOfDayProperty->GetName()));
	}
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetNumberField(TEXT("time_of_day"), TimeOfDayValue);
	ResultObj->SetStringField(TEXT("sky_name"), SkyActor->GetName());
	return ResultObj;
}
