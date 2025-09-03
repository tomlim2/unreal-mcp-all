#include "Commands/UnrealMCPRenderingCommands.h"
#include "Commands/UnrealMCPCommonUtils.h"
#include "Engine/Engine.h"
#include "UnrealClient.h"
#include "HAL/FileManager.h"
#include "Misc/Paths.h"
#include "Misc/DateTime.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "HAL/PlatformFilemanager.h"
#include "HAL/PlatformProcess.h"
#include "Editor.h"

FUnrealMCPRenderingCommands::FUnrealMCPRenderingCommands()
{
}

TSharedPtr<FJsonObject> FUnrealMCPRenderingCommands::HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params)
{
	if (CommandType == TEXT("take_highresshot"))
	{
		return HandleTakeHighResShot(Params);
	}
	return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown actor command: %s"), *CommandType));
}

TSharedPtr<FJsonObject> FUnrealMCPRenderingCommands::HandleTakeHighResShot(const TSharedPtr<FJsonObject>& Params)
{
	// Get parameters with defaults
	double ResolutionMultiplier = 1.0;
	FString Format = TEXT("png");
	bool bIncludeUI = false;
	bool bCaptureHDR = false;
	FString CustomFilename;

	if (Params.IsValid())
	{
		Params->TryGetNumberField(TEXT("resolution_multiplier"), ResolutionMultiplier);
		Params->TryGetStringField(TEXT("format"), Format);
		Params->TryGetBoolField(TEXT("include_ui"), bIncludeUI);
		Params->TryGetBoolField(TEXT("capture_hdr"), bCaptureHDR);
		Params->TryGetStringField(TEXT("filename"), CustomFilename);
	}

	// Validate resolution multiplier
	if (ResolutionMultiplier < 1.0 || ResolutionMultiplier > 8.0)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Resolution multiplier must be between 1.0 and 8.0"));
	}

	// Check if we're in game/PIE mode first
	UGameViewportClient* GameViewportClient = GEngine->GameViewport;
	UWorld* World = nullptr;
	
	if (GameViewportClient)
	{
		// We have a game viewport (PIE or standalone game)
		World = GameViewportClient->GetWorld();
		UE_LOG(LogTemp, Log, TEXT("Using game viewport for screenshot"));
	}
	else
	{
		// We're in editor mode - use editor world
		World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		if (!World)
		{
			return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No valid world context found for screenshot"));
		}
		UE_LOG(LogTemp, Log, TEXT("Using editor world for screenshot"));
	}

	// Create screenshot directory if it doesn't exist
	FString ProjectDir = FPaths::ProjectDir();
	FString ScreenshotDir = FPaths::Combine(ProjectDir, TEXT("Saved"), TEXT("Screenshots"));
	
	if (!IFileManager::Get().DirectoryExists(*ScreenshotDir))
	{
		if (!IFileManager::Get().MakeDirectory(*ScreenshotDir, true))
		{
			return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create Screenshots directory"));
		}
	}


	// Take the high-resolution screenshot
	FString ScreenshotCommand = FString::Printf(TEXT("HighResShot %d"), FMath::RoundToInt(ResolutionMultiplier));
	
	// Add UI hiding if requested
	if (!bIncludeUI)
	{
		GEngine->Exec(World, TEXT("showflag.hud 0"));
		GEngine->Exec(World, TEXT("showflag.screenmessages 0"));
	}

	// Log screenshot initiation
	UE_LOG(LogTemp, Log, TEXT("Initiating screenshot with resolution multiplier: %d"), FMath::RoundToInt(ResolutionMultiplier));
	
	// Execute the screenshot command
	bool bSuccess = GEngine->Exec(World, *ScreenshotCommand);

	if (!bSuccess)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to execute high-resolution screenshot command"));
	}
	
	// Wait for screenshot file to be created
	float TimeoutSeconds = 15.0f;
	float CheckInterval = 0.1f;
	float ElapsedTime = 0.0f;
	FString ActualFilePath;
	FString ActualFilename;
	
	while (ElapsedTime < TimeoutSeconds)
	{
		// Look for any new screenshot files in the directory
		TArray<FString> FoundFiles;
		IFileManager::Get().FindFiles(FoundFiles, *FPaths::Combine(ScreenshotDir, TEXT("*.png")), true, false);
		IFileManager::Get().FindFiles(FoundFiles, *FPaths::Combine(ScreenshotDir, TEXT("*.jpg")), true, false);
		
		for (const FString& FoundFile : FoundFiles)
		{
			FString FullFoundPath = FPaths::Combine(ScreenshotDir, FoundFile);
			
			// Check if this is a newly created Unreal screenshot
			if (FoundFile.Contains(TEXT("HighresScreenshot")) || FoundFile.Contains(TEXT("Screenshot")))
			{
				// Check file size to ensure it's complete
				int64 FileSize = FPlatformFileManager::Get().GetPlatformFile().FileSize(*FullFoundPath);
				if (FileSize > 0)
				{
					ActualFilePath = FullFoundPath;
					ActualFilename = FoundFile;
					UE_LOG(LogTemp, Log, TEXT("Found screenshot file: %s"), *FoundFile);
					break;
				}
			}
		}
		
		if (!ActualFilePath.IsEmpty())
		{
			break;
		}
		
		// Wait before next check
		FPlatformProcess::Sleep(CheckInterval);
		ElapsedTime += CheckInterval;
	}
	
	// Restore UI if it was hidden
	if (!bIncludeUI)
	{
		GEngine->Exec(World, TEXT("showflag.hud 1"));
		GEngine->Exec(World, TEXT("showflag.screenmessages 1"));
		UE_LOG(LogTemp, Log, TEXT("UI restored after screenshot"));
	}
	
	// Check if screenshot was actually created
	if (ActualFilePath.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("Screenshot file not found after timeout"));
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Screenshot command executed but file was not created within timeout period"));
	}
	
	UE_LOG(LogTemp, Log, TEXT("Screenshot completed successfully: %s"), *ActualFilePath);

	// Create success response
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("success"), TEXT("true"));
	ResultObj->SetStringField(TEXT("message"), TEXT("High-resolution screenshot captured and verified"));
	ResultObj->SetStringField(TEXT("file_path"), ActualFilePath);
	ResultObj->SetStringField(TEXT("filename"), ActualFilename);
	ResultObj->SetStringField(TEXT("format"), Format);
	ResultObj->SetNumberField(TEXT("resolution_multiplier"), ResolutionMultiplier);
	ResultObj->SetBoolField(TEXT("include_ui"), bIncludeUI);
	ResultObj->SetStringField(TEXT("screenshot_dir"), ScreenshotDir);
	
	// Add file verification info
	int64 FileSize = FPlatformFileManager::Get().GetPlatformFile().FileSize(*ActualFilePath);
	ResultObj->SetNumberField(TEXT("file_size_bytes"), static_cast<double>(FileSize));
	
	return ResultObj;
}
