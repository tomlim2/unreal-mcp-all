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
	
	OnSetLatitudeAndLongitude.AddDynamic(this, &UMMCesiumEventComponent::HandleSetLatitudeAndLongitude);
}

void UMMCesiumEventComponent::TriggerSetLatitudeAndLongitude(double Latitude, double Longitude)
{
	UE_LOG(LogTemp, Display, TEXT("MMCesiumEventComponent: Triggering SetLatitudeAndLongitude event - Lat: %f, Long: %f"), Latitude, Longitude);
	OnSetLatitudeAndLongitude.Broadcast(Latitude, Longitude);
}

void UMMCesiumEventComponent::TriggerCustomEvent(const FString& EventName, const FString& JsonParams)
{
	UE_LOG(LogTemp, Display, TEXT("MMCesiumEventComponent: Triggering custom event '%s' with params: %s"), *EventName, *JsonParams);
	
	if (EventName == TEXT("EventSetLatitudeAndLogitude"))
	{
		// Parse JSON parameters to extract latitude and longitude
		TSharedPtr<FJsonObject> JsonObject;
		TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonParams);
		
		if (FJsonSerializer::Deserialize(Reader, JsonObject))
		{
			double Latitude = 0.0;
			double Longitude = 0.0;
			
			if (JsonObject->TryGetNumberField(TEXT("latitude"), Latitude) && 
				JsonObject->TryGetNumberField(TEXT("longitude"), Longitude))
			{
				TriggerSetLatitudeAndLongitude(Latitude, Longitude);
			}
			else
			{
				UE_LOG(LogTemp, Warning, TEXT("MMCesiumEventComponent: Failed to parse latitude/longitude from JSON params"));
			}
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("MMCesiumEventComponent: Failed to deserialize JSON params"));
		}
	}
}

void UMMCesiumEventComponent::HandleSetLatitudeAndLongitude(double Latitude, double Longitude)
{
	UE_LOG(LogTemp, Display, TEXT("MMCesiumEventComponent: Handling SetLatitudeAndLongitude - Lat: %f, Long: %f"), Latitude, Longitude);
}