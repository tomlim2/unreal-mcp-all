#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class FMegaMelangeModule : public IModuleInterface
{
public:
	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

	static inline FMegaMelangeModule& Get()
	{
		return FModuleManager::LoadModuleChecked<FMegaMelangeModule>("MegaMelange");
	}

	static inline bool IsAvailable()
	{
		return FModuleManager::Get().IsModuleLoaded("MegaMelange");
	}
};
