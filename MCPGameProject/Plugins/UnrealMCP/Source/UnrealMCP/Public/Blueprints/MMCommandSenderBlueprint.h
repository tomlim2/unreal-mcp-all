#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/MMCesiumEventComponent.h"
#include "MMCommandSenderBlueprint.generated.h"

UCLASS(Blueprintable, BlueprintType, Category = "MegaMelange")
class UNREALMCP_API AMMCommandSenderBlueprint : public AActor
{
	GENERATED_BODY()
	
public:	
	AMMCommandSenderBlueprint();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "MegaMelange", meta = (AllowPrivateAccess = "true"))
	class UMMCesiumEventComponent* CesiumEventComponent;

protected:
	virtual void BeginPlay() override;

public:	
	virtual void Tick(float DeltaTime) override;
};