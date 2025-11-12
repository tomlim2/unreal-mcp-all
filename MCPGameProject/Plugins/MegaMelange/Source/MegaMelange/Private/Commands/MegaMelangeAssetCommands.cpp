#include "Commands/MegaMelangeAssetCommands.h"
#include "Commands/MegaMelangeCommonUtils.h"
#include "Editor.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/AssetData.h"
#include "EditorAssetLibrary.h"
#include "UObject/UObjectGlobals.h"
#include "UObject/UObjectHash.h"
#include "Selection.h"
#include "IContentBrowserSingleton.h"
#include "ContentBrowserModule.h"

FMegaMelangeAssetCommands::FMegaMelangeAssetCommands()
{
}

TSharedPtr<FJsonObject> FMegaMelangeAssetCommands::HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params)
{
	if (CommandType == TEXT("get_selected_assets"))
	{
		return HandleGetSelectedAssets(Params);
	}
	else if (CommandType == TEXT("rename_assets_batch"))
	{
		return HandleRenameAssetsBatch(Params);
	}

	return FMegaMelangeCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown asset command: %s"), *CommandType));
}

TSharedPtr<FJsonObject> FMegaMelangeAssetCommands::HandleGetSelectedAssets(const TSharedPtr<FJsonObject>& Params)
{
	if (!GEditor)
	{
		return FMegaMelangeCommonUtils::CreateErrorResponse(TEXT("Editor not available"));
	}

	// Get selected assets from Content Browser using the more reliable Content Browser module API
	TArray<FAssetData> SelectedAssets;

	// First try the Content Browser module API (more reliable)
	FContentBrowserModule& ContentBrowserModule = FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser");
	IContentBrowserSingleton& ContentBrowser = ContentBrowserModule.Get();
	ContentBrowser.GetSelectedAssets(SelectedAssets);

	// Fallback to GEditor method if Content Browser API didn't return anything
	if (SelectedAssets.Num() == 0)
	{
		UE_LOG(LogTemp, Warning, TEXT("Content Browser API returned no selections, trying GEditor fallback"));
		GEditor->GetContentBrowserSelections(SelectedAssets);
	}

	if (SelectedAssets.Num() == 0)
	{
		return FMegaMelangeCommonUtils::CreateErrorResponse(TEXT("No assets selected in Content Browser"));
	}

	// Build JSON array of asset information
	TArray<TSharedPtr<FJsonValue>> AssetsArray;

	for (const FAssetData& AssetData : SelectedAssets)
	{
		TSharedPtr<FJsonObject> AssetObj = MakeShared<FJsonObject>();

		// Get asset path (ObjectPath format: /Game/Path/AssetName.AssetName)
		FString AssetPath = AssetData.ObjectPath.ToString();
		AssetObj->SetStringField(TEXT("path"), AssetPath);

		// Get asset type (class name)
		FString AssetType = AssetData.AssetClassPath.GetAssetName().ToString();
		AssetObj->SetStringField(TEXT("type"), AssetType);

		// Get display name (asset name without path)
		FString DisplayName = AssetData.AssetName.ToString();
		AssetObj->SetStringField(TEXT("name"), DisplayName);

		// Add package path for context
		FString PackagePath = AssetData.PackagePath.ToString();
		AssetObj->SetStringField(TEXT("package_path"), PackagePath);

		UE_LOG(LogTemp, Display, TEXT("get_selected_assets returning asset:"));
		UE_LOG(LogTemp, Display, TEXT("  - name: %s"), *DisplayName);
		UE_LOG(LogTemp, Display, TEXT("  - type: %s"), *AssetType);
		UE_LOG(LogTemp, Display, TEXT("  - path (ObjectPath): %s"), *AssetPath);
		UE_LOG(LogTemp, Display, TEXT("  - package_path: %s"), *PackagePath);

		AssetsArray.Add(MakeShared<FJsonValueObject>(AssetObj));
	}

	// Create success response with assets array
	TSharedPtr<FJsonObject> ResultData = MakeShared<FJsonObject>();
	ResultData->SetArrayField(TEXT("assets"), AssetsArray);
	ResultData->SetNumberField(TEXT("count"), SelectedAssets.Num());

	UE_LOG(LogTemp, Display, TEXT("Successfully retrieved %d selected asset(s)"), SelectedAssets.Num());

	return FMegaMelangeCommonUtils::CreateSuccessResponse(ResultData);
}

TSharedPtr<FJsonObject> FMegaMelangeAssetCommands::HandleRenameAssetsBatch(const TSharedPtr<FJsonObject>& Params)
{
	if (!GEditor)
	{
		return FMegaMelangeCommonUtils::CreateErrorResponse(TEXT("Editor not available"));
	}

	// Get the rename operations array from params
	const TArray<TSharedPtr<FJsonValue>>* RenameOpsArray;
	if (!Params->TryGetArrayField(TEXT("operations"), RenameOpsArray))
	{
		return FMegaMelangeCommonUtils::CreateErrorResponse(TEXT("Missing 'operations' array parameter"));
	}

	// Track results
	TArray<TSharedPtr<FJsonValue>> SuccessArray;
	TArray<TSharedPtr<FJsonValue>> FailedArray;
	int32 TotalProcessed = 0;

	// Process each rename operation
	for (const TSharedPtr<FJsonValue>& OpValue : *RenameOpsArray)
	{
		const TSharedPtr<FJsonObject>& OpObj = OpValue->AsObject();
		if (!OpObj.IsValid())
		{
			continue;
		}

		FString OldPath;
		FString NewName;

		if (!OpObj->TryGetStringField(TEXT("old_path"), OldPath) ||
			!OpObj->TryGetStringField(TEXT("new_name"), NewName))
		{
			// Create failed entry
			TSharedPtr<FJsonObject> FailedObj = MakeShared<FJsonObject>();
			FailedObj->SetStringField(TEXT("path"), OldPath.IsEmpty() ? TEXT("unknown") : OldPath);
			FailedObj->SetStringField(TEXT("error"), TEXT("Missing old_path or new_name"));
			FailedArray.Add(MakeShared<FJsonValueObject>(FailedObj));
			continue;
		}

		TotalProcessed++;

		// Perform the rename
		FString NewPath;
		FString Error;
		bool bSuccess = RenameAsset(OldPath, NewName, NewPath, Error);

		if (bSuccess)
		{
			// Create success entry
			TSharedPtr<FJsonObject> SuccessObj = MakeShared<FJsonObject>();
			SuccessObj->SetStringField(TEXT("old_path"), OldPath);
			SuccessObj->SetStringField(TEXT("new_name"), NewName);
			SuccessObj->SetStringField(TEXT("new_path"), NewPath);
			SuccessArray.Add(MakeShared<FJsonValueObject>(SuccessObj));
		}
		else
		{
			// Create failed entry
			TSharedPtr<FJsonObject> FailedObj = MakeShared<FJsonObject>();
			FailedObj->SetStringField(TEXT("path"), OldPath);
			FailedObj->SetStringField(TEXT("new_name"), NewName);
			FailedObj->SetStringField(TEXT("error"), Error);
			FailedArray.Add(MakeShared<FJsonValueObject>(FailedObj));
		}
	}

	// Build response
	TSharedPtr<FJsonObject> ResultData = MakeShared<FJsonObject>();
	ResultData->SetArrayField(TEXT("success"), SuccessArray);
	ResultData->SetArrayField(TEXT("failed"), FailedArray);
	ResultData->SetNumberField(TEXT("total"), TotalProcessed);
	ResultData->SetNumberField(TEXT("success_count"), SuccessArray.Num());
	ResultData->SetNumberField(TEXT("failed_count"), FailedArray.Num());

	return FMegaMelangeCommonUtils::CreateSuccessResponse(ResultData);
}

FString FMegaMelangeAssetCommands::GetAssetTypeName(UObject* Asset)
{
	if (!Asset)
	{
		return TEXT("Unknown");
	}

	return Asset->GetClass()->GetName();
}

FString FMegaMelangeAssetCommands::GetAssetDisplayName(const FString& AssetPath)
{
	// Extract the asset name from the full path
	// Format: /Game/Path/To/AssetName.AssetName
	FString Left, Right;
	if (AssetPath.Split(TEXT("."), &Left, &Right, ESearchCase::IgnoreCase, ESearchDir::FromEnd))
	{
		return Right;
	}

	// If no dot, try to get the last part after /
	if (AssetPath.Split(TEXT("/"), &Left, &Right, ESearchCase::IgnoreCase, ESearchDir::FromEnd))
	{
		return Right;
	}

	return AssetPath;
}

bool FMegaMelangeAssetCommands::RenameAsset(const FString& OldPath, const FString& NewName, FString& OutNewPath, FString& OutError)
{
	// Validate asset exists (DoesAssetExist works with ObjectPath)
	if (!UEditorAssetLibrary::DoesAssetExist(OldPath))
	{
		OutError = FString::Printf(TEXT("Asset does not exist: %s"), *OldPath);
		return false;
	}

	// Convert ObjectPath to PackagePath by removing the .AssetName suffix
	// ObjectPath format: /Game/Path/AssetName.AssetName
	// PackagePath format: /Game/Path/AssetName
	FString OldPackagePath = OldPath;
	if (OldPath.Contains(TEXT(".")))
	{
		int32 DotIndex;
		if (OldPath.FindLastChar('.', DotIndex))
		{
			OldPackagePath = OldPath.Left(DotIndex);
		}
	}

	// Extract the directory path from package path
	FString Directory, OldName;
	if (!OldPackagePath.Split(TEXT("/"), &Directory, &OldName, ESearchCase::IgnoreCase, ESearchDir::FromEnd))
	{
		OutError = TEXT("Invalid asset path format");
		return false;
	}

	// Build new package path (RenameAsset expects package paths, not object paths)
	FString NewPackagePath = Directory + TEXT("/") + NewName;

	// Build the ObjectPath for checking existence
	OutNewPath = NewPackagePath + TEXT(".") + NewName;

	UE_LOG(LogTemp, Display, TEXT("Attempting rename: %s -> %s (package path: %s -> %s)"),
		*OldPath, *OutNewPath, *OldPackagePath, *NewPackagePath);

	// Check if target already exists
	if (UEditorAssetLibrary::DoesAssetExist(OutNewPath))
	{
		OutError = FString::Printf(TEXT("Asset already exists at: %s"), *OutNewPath);
		return false;
	}

	// Perform the rename using package paths
	bool bSuccess = UEditorAssetLibrary::RenameAsset(OldPackagePath, NewPackagePath);

	if (!bSuccess)
	{
		OutError = FString::Printf(TEXT("Failed to rename asset from %s to %s"), *OldPackagePath, *NewPackagePath);
		UE_LOG(LogTemp, Error, TEXT("RenameAsset failed: %s -> %s"), *OldPackagePath, *NewPackagePath);
		return false;
	}

	UE_LOG(LogTemp, Display, TEXT("Successfully renamed asset to: %s"), *OutNewPath);
	return true;
}
