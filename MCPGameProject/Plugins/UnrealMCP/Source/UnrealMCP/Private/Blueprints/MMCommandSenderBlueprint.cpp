#include "Blueprints/MMCommandSenderBlueprint.h"

AMMCommandSenderBlueprint::AMMCommandSenderBlueprint()
{
	PrimaryActorTick.bCanEverTick = true;

	// Create and set up the Cesium Event Component
	CesiumEventComponent = CreateDefaultSubobject<UMMCesiumEventComponent>(TEXT("CesiumEventComponent"));
}

void AMMCommandSenderBlueprint::BeginPlay()
{
	Super::BeginPlay();
	
}

void AMMCommandSenderBlueprint::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
}