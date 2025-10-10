#include "Commands/UnrealMCPObject3DCommands.h"
#include "Commands/UnrealMCPCommonUtils.h"
#include "EditorAssetLibrary.h"
#include "Misc/Paths.h"
#include "AssetToolsModule.h"
#include "IAssetTools.h"
#include "AssetImportTask.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Misc/PackageName.h"
#include "FileHelpers.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/SkinnedAssetCommon.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceConstant.h"
#include "Materials/Material.h"
#include "Engine/Texture2D.h"

FUnrealMCPObject3DCommands::FUnrealMCPObject3DCommands()
{
}

TSharedPtr<FJsonObject> FUnrealMCPObject3DCommands::HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params)
{
	if (CommandType == TEXT("import_object3d_by_uid"))
	{
		return HandleImportObject3DByUID(Params);
	}

	return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown 3D object command: %s"), *CommandType));
}

TSharedPtr<FJsonObject> FUnrealMCPObject3DCommands::HandleImportObject3DByUID(const TSharedPtr<FJsonObject>& Params)
{
	// Step 1: Extract parameters from JSON
	FString UID, MeshFilePath, MeshFormat, Username;
	int32 UserId = 0;

	if (!Params->TryGetStringField(TEXT("uid"), UID))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'uid' parameter"));
	}

	if (!Params->TryGetStringField(TEXT("mesh_file_path"), MeshFilePath))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'mesh_file_path' parameter"));
	}

	if (!Params->TryGetStringField(TEXT("mesh_format"), MeshFormat))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'mesh_format' parameter"));
	}

	if (!Params->TryGetStringField(TEXT("username"), Username))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'username' parameter"));
	}

	if (!Params->TryGetNumberField(TEXT("user_id"), UserId))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'user_id' parameter"));
	}

	// Validate username and user_id
	if (Username.IsEmpty() || UserId <= 0)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Invalid username or user_id: %s, %d"), *Username, UserId)
		);
	}

	// Normalize format to lowercase
	MeshFormat = MeshFormat.ToLower();

	UE_LOG(LogTemp, Display, TEXT("Importing 3D object: UID=%s, Format=%s, User=%s_%d, File=%s"),
		*UID, *MeshFormat, *Username, UserId, *MeshFilePath);

	// Step 2: Validate mesh file exists
	if (!FPaths::FileExists(MeshFilePath))
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Mesh file not found: %s"), *MeshFilePath)
		);
	}

	// Step 3: Construct import path in plugin Content directory
	// Format: /UnrealMCP/Roblox/[Username_UserId]/
	// This maps to: Plugins/UnrealMCP/Content/Roblox/[Username_UserId]/
	FString UserDirectory = FString::Printf(TEXT("%s_%d"), *Username, UserId);
	FString ImportPath = FString::Printf(TEXT("/UnrealMCP/Roblox/%s"), *UserDirectory);

	// Asset name from filename (without extension)
	FString AssetName = FPaths::GetBaseFilename(MeshFilePath);
	FString FullAssetPath = FString::Printf(TEXT("%s/%s"), *ImportPath, *AssetName);

	UE_LOG(LogTemp, Display, TEXT("Import destination: %s"), *FullAssetPath);
	UE_LOG(LogTemp, Display, TEXT("Physical path: Plugins/UnrealMCP/Content/Roblox/%s/"), *UserDirectory);

	// Step 4: Check if asset already exists
	UObject* ImportedAsset = nullptr;
	UObject* ExistingAsset = UEditorAssetLibrary::LoadAsset(FullAssetPath);

	if (ExistingAsset)
	{
		// Asset already exists, use it
		ImportedAsset = ExistingAsset;
		UE_LOG(LogTemp, Warning, TEXT("Asset already exists: %s, using existing asset"), *FullAssetPath);
	}

	// Step 5: Import 3D mesh file if not already imported
	if (!ImportedAsset)
	{
		UE_LOG(LogTemp, Display, TEXT("=== Starting %s Import Process ==="), *MeshFormat.ToUpper());
		UE_LOG(LogTemp, Display, TEXT("Source File: %s"), *MeshFilePath);
		UE_LOG(LogTemp, Display, TEXT("Destination: %s"), *ImportPath);

		// Use plugin content path directly (no /Game/ prefix needed for plugins)
		// /UnrealMCP/ is automatically mounted as the plugin's content root
		FString PackagePath = ImportPath;

		UE_LOG(LogTemp, Display, TEXT("Package Path (Plugin Content): %s"), *PackagePath);

		// Use native C++ AssetImportTask for direct import (FBX works without freezing!)
		UE_LOG(LogTemp, Display, TEXT("Using native C++ AssetImportTask for %s import"), *MeshFormat.ToUpper());

		// Get AssetTools module
		FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools");
		IAssetTools& AssetTools = AssetToolsModule.Get();

		// Create import task
		UAssetImportTask* ImportTask = NewObject<UAssetImportTask>();
		ImportTask->Filename = MeshFilePath;
		ImportTask->DestinationPath = PackagePath;
		ImportTask->bSave = true;
		ImportTask->bAutomated = true;
		ImportTask->bReplaceExisting = false;
		ImportTask->bReplaceExistingSettings = false;

		UE_LOG(LogTemp, Display, TEXT("Import Task Configuration:"));
		UE_LOG(LogTemp, Display, TEXT("  - Filename: %s"), *ImportTask->Filename);
		UE_LOG(LogTemp, Display, TEXT("  - Destination: %s"), *ImportTask->DestinationPath);
		UE_LOG(LogTemp, Display, TEXT("  - Automated: %s"), ImportTask->bAutomated ? TEXT("true") : TEXT("false"));

		// Execute import
		UE_LOG(LogTemp, Display, TEXT("Executing AssetTools.ImportAssetTasks()..."));
		AssetTools.ImportAssetTasks({ ImportTask });
		UE_LOG(LogTemp, Display, TEXT("Import task completed!"));

		// Check import results
		if (ImportTask->ImportedObjectPaths.Num() > 0)
		{
			FullAssetPath = ImportTask->ImportedObjectPaths[0];
			UE_LOG(LogTemp, Display, TEXT("✅ Import successful: %s"), *FullAssetPath);

			// Try to load the imported asset
			ImportedAsset = UEditorAssetLibrary::LoadAsset(FullAssetPath);
			if (ImportedAsset)
			{
				UE_LOG(LogTemp, Display, TEXT("✅ Asset loaded successfully: %s"), *ImportedAsset->GetClass()->GetName());
			}
			else
			{
				UE_LOG(LogTemp, Warning, TEXT("⚠️ Asset imported but could not be loaded"));
			}
		}
		else
		{
			UE_LOG(LogTemp, Error, TEXT("❌ Import failed: No objects were imported"));
			return FUnrealMCPCommonUtils::CreateErrorResponse(
				FString::Printf(TEXT("Failed to import %s file: %s"), *MeshFormat.ToUpper(), *MeshFilePath)
			);
		}
	}

	// Step 6: Roblox Material Instance Setup (if SkeletalMesh)
	USkeletalMesh* SkeletalMesh = Cast<USkeletalMesh>(ImportedAsset);
	if (SkeletalMesh)
	{
		// Access materials through the Materials property
		const TArray<FSkeletalMaterial>& Materials = SkeletalMesh->GetMaterials();
		if (Materials.Num() > 0)
		{
			UE_LOG(LogTemp, Display, TEXT("=== Starting Roblox Material Setup ==="));

			// 1. Find texture from base material
			UTexture2D* RobloxTexture = nullptr;
			UMaterialInterface* BaseMat = Materials[0].MaterialInterface;

			if (BaseMat)
			{
				UE_LOG(LogTemp, Display, TEXT("Base Material: %s"), *BaseMat->GetName());

				// Try to get texture from BaseColor parameter
				UTexture* BaseColorTexture = nullptr;
				if (BaseMat->GetTextureParameterValue(FMaterialParameterInfo(TEXT("BaseColor")), BaseColorTexture))
				{
					RobloxTexture = Cast<UTexture2D>(BaseColorTexture);
					if (RobloxTexture)
					{
						UE_LOG(LogTemp, Display, TEXT("✅ Found texture from BaseColor parameter: %s"), *RobloxTexture->GetName());
					}
				}

				// If not found in BaseColor parameter, try to get from material's textures
				if (!RobloxTexture)
				{
					TArray<UTexture*> UsedTextures;
					BaseMat->GetUsedTextures(UsedTextures, EMaterialQualityLevel::High, true, ERHIFeatureLevel::SM5, true);

					if (UsedTextures.Num() > 0)
					{
						RobloxTexture = Cast<UTexture2D>(UsedTextures[0]);
						if (RobloxTexture)
						{
							UE_LOG(LogTemp, Display, TEXT("✅ Found texture from material textures: %s"), *RobloxTexture->GetName());
						}
					}
				}

				if (!RobloxTexture)
				{
					UE_LOG(LogTemp, Warning, TEXT("⚠️ No texture found in base material, will keep base material as-is"));
				}
			}

			// 2. Duplicate MI_Roblox to user folder
			FString SourceMIPath = TEXT("/UnrealMCP/Roblox/Materials/MI_Roblox");
			FString NewMIName = FString::Printf(TEXT("MI_Roblox_%s_%d"), *Username, UserId);
			FString NewMIPath = FString::Printf(TEXT("%s/%s"), *ImportPath, *NewMIName);

			UE_LOG(LogTemp, Display, TEXT("Duplicating material instance:"));
			UE_LOG(LogTemp, Display, TEXT("  Source: %s"), *SourceMIPath);
			UE_LOG(LogTemp, Display, TEXT("  Destination: %s"), *NewMIPath);

			UMaterialInstanceConstant* NewMI = Cast<UMaterialInstanceConstant>(
				UEditorAssetLibrary::DuplicateAsset(SourceMIPath, NewMIPath)
			);

			if (NewMI)
			{
				UE_LOG(LogTemp, Display, TEXT("✅ Material instance duplicated successfully"));

				// 3. If texture found, apply to BaseColor parameter
				if (RobloxTexture)
				{
					UE_LOG(LogTemp, Display, TEXT("Applying texture to BaseColor parameter..."));

					NewMI->SetTextureParameterValueEditorOnly(
						FMaterialParameterInfo(TEXT("BaseColor")),
						RobloxTexture
					);

					// Save the modified material instance
					if (UEditorAssetLibrary::SaveAsset(NewMIPath, false))
					{
						UE_LOG(LogTemp, Display, TEXT("✅ Texture applied and material instance saved"));
					}
					else
					{
						UE_LOG(LogTemp, Warning, TEXT("⚠️ Material instance modified but save failed"));
					}
				}
				else
				{
					UE_LOG(LogTemp, Display, TEXT("Material instance duplicated without texture (keeping base material)"));
				}
			}
			else
			{
				UE_LOG(LogTemp, Error, TEXT("❌ Failed to duplicate material instance from %s"), *SourceMIPath);
			}

			UE_LOG(LogTemp, Display, TEXT("=== Material Setup Complete ==="));
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("SkeletalMesh has no materials, skipping material setup"));
		}
	}

	// Step 7: Build simplified success response
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("message"), TEXT("Avatar imported to Plugin Content Browser"));
	ResultObj->SetStringField(TEXT("uid"), UID);
	ResultObj->SetStringField(TEXT("username"), Username);
	ResultObj->SetNumberField(TEXT("user_id"), UserId);
	ResultObj->SetStringField(TEXT("asset_path"), FullAssetPath);
	ResultObj->SetStringField(TEXT("format"), MeshFormat);

	UE_LOG(LogTemp, Display, TEXT("Import completed successfully: %s"), *FullAssetPath);
	UE_LOG(LogTemp, Display, TEXT("Browse in Content Browser: /UnrealMCP/Roblox/%s/"), *UserDirectory);

	return ResultObj;
}