#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Engine/Engine.h"

#include "MMCesiumEventComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnSetLatitudeAndLongitude, double, Latitude, double, Longitude);

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class UNREALMCP_API UMMCesiumEventComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMMCesiumEventComponent();

	UPROPERTY(BlueprintAssignable, Category = "MegaMelange Events")
	FOnSetLatitudeAndLongitude OnSetLatitudeAndLongitude;

	UFUNCTION(BlueprintCallable, Category = "MegaMelange")
	void TriggerSetLatitudeAndLongitude(double Latitude, double Longitude);

	UFUNCTION(BlueprintCallable, Category = "MegaMelange")
	void TriggerCustomEvent(const FString& EventName, const FString& JsonParams);

protected:
	virtual void BeginPlay() override;

private:
	UFUNCTION()
	void HandleSetLatitudeAndLongitude(double Latitude, double Longitude);
};