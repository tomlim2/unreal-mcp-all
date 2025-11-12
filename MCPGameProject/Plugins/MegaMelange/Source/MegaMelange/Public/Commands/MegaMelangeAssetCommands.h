#pragma once

#include "CoreMinimal.h"
#include "Json.h"

/**
 * Handler class for Asset-related MCP commands
 */
class MEGAMELANGE_API FMegaMelangeAssetCommands
{
public:
	FMegaMelangeAssetCommands();
	TSharedPtr<FJsonObject> HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params);

private:
	// Asset command handlers
	TSharedPtr<FJsonObject> HandleGetSelectedAssets(const TSharedPtr<FJsonObject>& Params);
	TSharedPtr<FJsonObject> HandleRenameAssetsBatch(const TSharedPtr<FJsonObject>& Params);

	// Helper functions
	FString GetAssetTypeName(UObject* Asset);
	FString GetAssetDisplayName(const FString& AssetPath);
	bool RenameAsset(const FString& OldPath, const FString& NewName, FString& OutNewPath, FString& OutError);
};
