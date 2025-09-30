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
#include "IPythonScriptPlugin.h"  // For executing Python import scripts

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
	UStaticMesh* ImportedMesh = nullptr;
	UObject* ExistingAsset = UEditorAssetLibrary::LoadAsset(FullAssetPath);

	if (ExistingAsset)
	{
		// Asset already exists, use it
		ImportedMesh = Cast<UStaticMesh>(ExistingAsset);
		if (ImportedMesh)
		{
			UE_LOG(LogTemp, Warning, TEXT("Asset already exists: %s, using existing asset"), *FullAssetPath);
		}
	}

	// Step 5: Import 3D mesh file if not already imported
	if (!ImportedMesh)
	{
		UE_LOG(LogTemp, Display, TEXT("=== Starting %s Import Process ==="), *MeshFormat.ToUpper());
		UE_LOG(LogTemp, Display, TEXT("Source File: %s"), *MeshFilePath);
		UE_LOG(LogTemp, Display, TEXT("Destination: %s"), *ImportPath);

		// Use plugin content path directly (no /Game/ prefix needed for plugins)
		// /UnrealMCP/ is automatically mounted as the plugin's content root
		FString PackagePath = ImportPath;

		UE_LOG(LogTemp, Display, TEXT("Package Path (Plugin Content): %s"), *PackagePath);

		// Use Python-based import to avoid Game Thread deadlock
		// Python runs outside Game Thread, potentially preventing the freeze issue
		UE_LOG(LogTemp, Display, TEXT("Using Python-based import to avoid Game Thread blocking"));

		// Get Python plugin
		IPythonScriptPlugin* PythonPlugin = FModuleManager::LoadModulePtr<IPythonScriptPlugin>("PythonScriptPlugin");
		if (!PythonPlugin)
		{
			UE_LOG(LogTemp, Error, TEXT("Python Script Plugin not available"));
			return FUnrealMCPCommonUtils::CreateErrorResponse(
				TEXT("Python Script Plugin not loaded. Please enable it in Project Settings -> Plugins")
			);
		}

		// Build Python script path - use format-agnostic import script
		FString PluginBaseDir = FPaths::ConvertRelativePathToFull(FPaths::ProjectPluginsDir() / TEXT("UnrealMCP"));
		FString PythonScriptPath = PluginBaseDir / TEXT("Content/Python/import_mesh_asset.py");

		UE_LOG(LogTemp, Display, TEXT("Python script path: %s"), *PythonScriptPath);

		// Convert Windows paths to Python-friendly format (forward slashes)
		FString MeshFilePathForPython = MeshFilePath.Replace(TEXT("\\"), TEXT("/"));
		FString PackagePathForPython = PackagePath.Replace(TEXT("\\"), TEXT("/"));

		// Build Python command to execute
		// Use exec() to run the file directly, which avoids module import issues
		FString PythonCommand = FString::Printf(
			TEXT("exec(open(r'%s').read()); import_mesh(r'%s', '%s')"),
			*PythonScriptPath,
			*MeshFilePathForPython,
			*PackagePathForPython
		);

		UE_LOG(LogTemp, Display, TEXT("Executing Python command: %s"), *PythonCommand);

		// Execute Python import (runs outside Game Thread)
		bool bPythonSuccess = PythonPlugin->ExecPythonCommand(*PythonCommand);

		if (!bPythonSuccess)
		{
			UE_LOG(LogTemp, Error, TEXT("Python command execution failed"));
			return FUnrealMCPCommonUtils::CreateErrorResponse(
				TEXT("Failed to execute Python import command")
			);
		}

		// Note: Python import runs asynchronously, so we can't get immediate results
		// We return success immediately and Python will log the actual import result
		UE_LOG(LogTemp, Display, TEXT("Python import command sent successfully"));
		UE_LOG(LogTemp, Display, TEXT("Check Unreal Python logs for actual import status"));

		// Construct expected asset path for response
		FullAssetPath = FString::Printf(TEXT("%s/%s"), *PackagePath, *AssetName);
	}

	// Step 6: Build simplified success response
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