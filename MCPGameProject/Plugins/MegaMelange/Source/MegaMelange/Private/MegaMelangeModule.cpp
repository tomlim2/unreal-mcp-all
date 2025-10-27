#include "MegaMelangeModule.h"
#include "Modules/ModuleManager.h"

#define LOCTEXT_NAMESPACE "FMegaMelangeModule"

void FMegaMelangeModule::StartupModule()
{
	UE_LOG(LogTemp, Display, TEXT("MegaMelange Module has started"));
}

void FMegaMelangeModule::ShutdownModule()
{
	UE_LOG(LogTemp, Display, TEXT("MegaMelange Module has shut down"));
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FMegaMelangeModule, MegaMelange)
