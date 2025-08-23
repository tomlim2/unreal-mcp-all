#include "MMCesiumEventComponent.h"
#include "Engine/Engine.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonReader.h"

UMMCesiumEventComponent::UMMCesiumEventComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UMMCesiumEventComponent::BeginPlay()
{
	Super::BeginPlay();
	
	// Check if delegate is already bound to avoid duplicate bindings
	if (!OnSetLatitudeAndLongitude.IsAlreadyBound(this, FName("HandleSetLatitudeAndLongitude")))
	{
		OnSetLatitudeAndLongitude.AddDynamic(this, &UMMCesiumEventComponent::HandleSetLatitudeAndLongitude);
		UE_LOG(LogTemp, Display, TEXT("MMCesiumEventComponent: Bound HandleSetLatitudeAndLongitude delegate"));
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("MMCesiumEventComponent: HandleSetLatitudeAndLongitude delegate already bound"));
	}
}

void UMMCesiumEventComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	// Clean up delegate bindings to prevent issues
	if (OnSetLatitudeAndLongitude.IsAlreadyBound(this, FName("HandleSetLatitudeAndLongitude")))
	{
		OnSetLatitudeAndLongitude.RemoveDynamic(this, &UMMCesiumEventComponent::HandleSetLatitudeAndLongitude);
		UE_LOG(LogTemp, Display, TEXT("MMCesiumEventComponent: Unbound HandleSetLatitudeAndLongitude delegate"));
	}
	
	Super::EndPlay(EndPlayReason);
}

void UMMCesiumEventComponent::TriggerSetLatitudeAndLongitude(double Latitude, double Longitude)
{
	UE_LOG(LogTemp, Display, TEXT("MMCesiumEventComponent: Triggering SetLatitudeAndLongitude event - Lat: %f, Long: %f"), Latitude, Longitude);
	
	// Check if delegate has any bindings
	bool bIsBound = OnSetLatitudeAndLongitude.IsBound();
	UE_LOG(LogTemp, Display, TEXT("MMCesiumEventComponent: Delegate IsBound: %s"), bIsBound ? TEXT("true") : TEXT("false"));
	
	if (bIsBound)
	{
		UE_LOG(LogTemp, Display, TEXT("MMCesiumEventComponent: Broadcasting event..."));
		OnSetLatitudeAndLongitude.Broadcast(Latitude, Longitude);
		UE_LOG(LogTemp, Display, TEXT("MMCesiumEventComponent: Event broadcast completed"));
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("MMCesiumEventComponent: No delegates bound to OnSetLatitudeAndLongitude"));
	}
}

void UMMCesiumEventComponent::HandleSetLatitudeAndLongitude(double Latitude, double Longitude)
{
	UE_LOG(LogTemp, Display, TEXT("MMCesiumEventComponent: HandleSetLatitudeAndLongitude CALLED - Lat: %f, Long: %f"), Latitude, Longitude);
	
	// Add owner actor information for debugging
	AActor* OwnerActor = GetOwner();
	if (OwnerActor)
	{
		UE_LOG(LogTemp, Display, TEXT("MMCesiumEventComponent: Owner Actor: %s (%s)"), *OwnerActor->GetName(), *OwnerActor->GetClass()->GetName());
	}
	
	UE_LOG(LogTemp, Display, TEXT("MMCesiumEventComponent: Event handled successfully - coordinates received"));
}