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

	// Smart routing: Use synchronous method for standard resolution, async for high-res
	if (ResolutionMultiplier <= 1.0)
	{
		UE_LOG(LogTemp, Log, TEXT("Using synchronous screenshot method for resolution multiplier: %.1f"), ResolutionMultiplier);
		return HandleSynchronousScreenshot(Params);
	}
	else
	{
		UE_LOG(LogTemp, Log, TEXT("Using asynchronous high-res screenshot method for resolution multiplier: %.1f"), ResolutionMultiplier);
		return HandleAsynchronousHighResScreenshot(Params);
	}
}

TSharedPtr<FJsonObject> FUnrealMCPRenderingCommands::HandleSynchronousScreenshot(const TSharedPtr<FJsonObject>& Params)
{
	// Get parameters with defaults
	FString Format = TEXT("png");
	bool bIncludeUI = false;
	FString CustomFilename;

	if (Params.IsValid())
	{
		Params->TryGetStringField(TEXT("format"), Format);
		Params->TryGetBoolField(TEXT("include_ui"), bIncludeUI);
		Params->TryGetStringField(TEXT("filename"), CustomFilename);
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

	// Determine viewport context (PIE vs Editor)
	FViewport* Viewport = nullptr;
	UWorld* World = nullptr;
	
	UGameViewportClient* GameViewportClient = GEngine->GameViewport;
	if (GameViewportClient)
	{
		// We're in game/PIE mode
		Viewport = GameViewportClient->Viewport;
		World = GameViewportClient->GetWorld();
		UE_LOG(LogTemp, Log, TEXT("Using game viewport for synchronous screenshot"));
	}
	else if (GEditor && GEditor->GetActiveViewport())
	{
		// We're in editor mode
		Viewport = GEditor->GetActiveViewport();
		World = GEditor->GetEditorWorldContext().World();
		UE_LOG(LogTemp, Log, TEXT("Using editor viewport for synchronous screenshot"));
	}
	else
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No valid viewport found for screenshot"));
	}

	if (!Viewport || !World)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Invalid viewport or world context"));
	}

	// Hide UI if requested
	bool bUIWasHidden = false;
	if (!bIncludeUI)
	{
		GEngine->Exec(World, TEXT("showflag.hud 0"));
		GEngine->Exec(World, TEXT("showflag.screenmessages 0"));
		bUIWasHidden = true;
		UE_LOG(LogTemp, Log, TEXT("UI hidden for screenshot"));
	}

	// Capture viewport pixels synchronously
	TArray<FColor> Bitmap;
	FIntRect ViewportRect(0, 0, Viewport->GetSizeXY().X, Viewport->GetSizeXY().Y);
	bool bCaptureSuccess = Viewport->ReadPixels(Bitmap, FReadSurfaceDataFlags(), ViewportRect);

	// Restore UI if it was hidden
	if (bUIWasHidden)
	{
		GEngine->Exec(World, TEXT("showflag.hud 1"));
		GEngine->Exec(World, TEXT("showflag.screenmessages 1"));
		UE_LOG(LogTemp, Log, TEXT("UI restored after screenshot"));
	}

	if (!bCaptureSuccess || Bitmap.Num() == 0)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to capture viewport pixels"));
	}

	// Generate filename
	FString ActualFilename;
	if (CustomFilename.IsEmpty())
	{
		FDateTime Now = FDateTime::Now();
		ActualFilename = FString::Printf(TEXT("Screenshot_%04d-%02d-%02d_%02d-%02d-%02d.%s"),
			Now.GetYear(), Now.GetMonth(), Now.GetDay(),
			Now.GetHour(), Now.GetMinute(), Now.GetSecond(),
			*Format.ToLower());
	}
	else
	{
		// Ensure proper extension
		FString Extension = FPaths::GetExtension(CustomFilename);
		if (Extension.IsEmpty())
		{
			ActualFilename = CustomFilename + TEXT(".") + Format.ToLower();
		}
		else
		{
			ActualFilename = CustomFilename;
		}
	}

	FString ActualFilePath = FPaths::Combine(ScreenshotDir, ActualFilename);

	// Save bitmap to file
	bool bSaveSuccess = false;
	if (Format.ToLower() == TEXT("png"))
	{
		// Compress and save as PNG
		TArray<uint8> CompressedBitmap;
		FImageUtils::CompressImageArray(Viewport->GetSizeXY().X, Viewport->GetSizeXY().Y, Bitmap, CompressedBitmap);
		bSaveSuccess = FFileHelper::SaveArrayToFile(CompressedBitmap, *ActualFilePath);
	}
	else if (Format.ToLower() == TEXT("jpg") || Format.ToLower() == TEXT("jpeg"))
	{
		// For JPEG, we need to convert FColor to uint8 array
		TArray<uint8> RawData;
		RawData.Reserve(Bitmap.Num() * 3); // RGB format
		
		for (const FColor& Color : Bitmap)
		{
			RawData.Add(Color.R);
			RawData.Add(Color.G);
			RawData.Add(Color.B);
		}
		
		// Use basic file save for now (could be enhanced with proper JPEG compression)
		bSaveSuccess = FFileHelper::SaveArrayToFile(RawData, *ActualFilePath);
	}
	else
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unsupported format: %s"), *Format));
	}

	if (!bSaveSuccess)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to save screenshot file"));
	}

	// Verify file was created successfully
	int64 FileSize = FPlatformFileManager::Get().GetPlatformFile().FileSize(*ActualFilePath);
	if (FileSize <= 0)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Screenshot file was created but appears to be empty"));
	}

	UE_LOG(LogTemp, Log, TEXT("Synchronous screenshot completed successfully: %s (%lld bytes)"), *ActualFilePath, FileSize);

	// Create success response
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("success"), TEXT("true"));
	ResultObj->SetStringField(TEXT("message"), TEXT("Synchronous screenshot captured successfully"));
	ResultObj->SetStringField(TEXT("file_path"), ActualFilePath);
	ResultObj->SetStringField(TEXT("filename"), ActualFilename);
	ResultObj->SetStringField(TEXT("format"), Format);
	ResultObj->SetNumberField(TEXT("resolution_multiplier"), 1.0);
	ResultObj->SetBoolField(TEXT("include_ui"), bIncludeUI);
	ResultObj->SetStringField(TEXT("screenshot_dir"), ScreenshotDir);
	ResultObj->SetNumberField(TEXT("file_size_bytes"), static_cast<double>(FileSize));
	ResultObj->SetNumberField(TEXT("width"), Viewport->GetSizeXY().X);
	ResultObj->SetNumberField(TEXT("height"), Viewport->GetSizeXY().Y);
	
	return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPRenderingCommands::HandleAsynchronousHighResScreenshot(const TSharedPtr<FJsonObject>& Params)
{
	// Get parameters with defaults
	double ResolutionMultiplier = 2.0;
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

	// Determine world context (PIE vs Editor)
	UWorld* World = nullptr;
	UGameViewportClient* GameViewportClient = GEngine->GameViewport;
	
	if (GameViewportClient)
	{
		// We're in game/PIE mode
		World = GameViewportClient->GetWorld();
		UE_LOG(LogTemp, Log, TEXT("Using game viewport for async high-res screenshot"));
	}
	else
	{
		// We're in editor mode
		World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		if (!World)
		{
			return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No valid world context found for high-res screenshot"));
		}
		UE_LOG(LogTemp, Log, TEXT("Using editor world for async high-res screenshot"));
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

	// Hide UI if requested
	bool bUIWasHidden = false;
	if (!bIncludeUI)
	{
		GEngine->Exec(World, TEXT("showflag.hud 0"));
		GEngine->Exec(World, TEXT("showflag.screenmessages 0"));
		bUIWasHidden = true;
		UE_LOG(LogTemp, Log, TEXT("UI hidden for high-res screenshot"));
	}

	// Execute the high-resolution screenshot command
	FString ScreenshotCommand = FString::Printf(TEXT("HighResShot %d"), FMath::RoundToInt(ResolutionMultiplier));
	UE_LOG(LogTemp, Log, TEXT("Executing high-res screenshot command: %s"), *ScreenshotCommand);
	
	bool bCommandSuccess = GEngine->Exec(World, *ScreenshotCommand);

	if (!bCommandSuccess)
	{
		// Restore UI if it was hidden
		if (bUIWasHidden)
		{
			GEngine->Exec(World, TEXT("showflag.hud 1"));
			GEngine->Exec(World, TEXT("showflag.screenmessages 1"));
		}
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to execute high-resolution screenshot command"));
	}

	// Optimized file waiting with intelligent detection (reduced timeout for socket compatibility)
	float TimeoutSeconds = 6.0f;  // Reduced from 15s to 6s for socket compatibility
	float QuickCheckDuration = 2.0f;  // Quick checks for first 2 seconds
	float CheckInterval = 0.1f;
	float ElapsedTime = 0.0f;
	FString ActualFilePath;
	FString ActualFilename;
	
	UE_LOG(LogTemp, Log, TEXT("Starting optimized file detection (%.1fs timeout)..."), TimeoutSeconds);

	// Phase 1: Quick polling for first 2 seconds
	while (ElapsedTime < QuickCheckDuration && ElapsedTime < TimeoutSeconds)
	{
		ActualFilePath = FindLatestScreenshotFile(ScreenshotDir);
		if (!ActualFilePath.IsEmpty() && IsFileReady(ActualFilePath))
		{
			ActualFilename = FPaths::GetCleanFilename(ActualFilePath);
			UE_LOG(LogTemp, Log, TEXT("Screenshot ready in quick check phase: %s (%.2fs)"), *ActualFilename, ElapsedTime);
			break;
		}
		
		FPlatformProcess::Sleep(CheckInterval);
		ElapsedTime += CheckInterval;
	}

	// Phase 2: Continued monitoring if still not found
	while (ActualFilePath.IsEmpty() && ElapsedTime < TimeoutSeconds)
	{
		ActualFilePath = FindLatestScreenshotFile(ScreenshotDir);
		if (!ActualFilePath.IsEmpty() && IsFileReady(ActualFilePath))
		{
			ActualFilename = FPaths::GetCleanFilename(ActualFilePath);
			UE_LOG(LogTemp, Log, TEXT("Screenshot ready in extended check: %s (%.2fs)"), *ActualFilename, ElapsedTime);
			break;
		}
		
		FPlatformProcess::Sleep(CheckInterval * 2); // Slower polling in phase 2
		ElapsedTime += CheckInterval * 2;
	}

	// Restore UI if it was hidden
	if (bUIWasHidden)
	{
		GEngine->Exec(World, TEXT("showflag.hud 1"));
		GEngine->Exec(World, TEXT("showflag.screenmessages 1"));
		UE_LOG(LogTemp, Log, TEXT("UI restored after high-res screenshot"));
	}

	// Check if screenshot was successfully created
	if (ActualFilePath.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("High-res screenshot file not found after %.1fs timeout"), TimeoutSeconds);
		return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(
			TEXT("High-resolution screenshot command executed but file was not created within %.1fs timeout period"), TimeoutSeconds));
	}

	// Final verification
	int64 FileSize = FPlatformFileManager::Get().GetPlatformFile().FileSize(*ActualFilePath);
	if (FileSize <= 0)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("High-res screenshot file was created but appears to be empty"));
	}

	UE_LOG(LogTemp, Log, TEXT("High-res screenshot completed successfully: %s (%lld bytes, %.2fs)"), *ActualFilePath, FileSize, ElapsedTime);

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
	ResultObj->SetNumberField(TEXT("file_size_bytes"), static_cast<double>(FileSize));
	ResultObj->SetNumberField(TEXT("capture_time_seconds"), ElapsedTime);
	
	return ResultObj;
}

bool FUnrealMCPRenderingCommands::IsFileReady(const FString& FilePath)
{
	if (FilePath.IsEmpty())
	{
		return false;
	}

	// Static variables for stability tracking (reset for different files)
	static FString LastCheckedFile;
	static int64 LastKnownSize = -1;
	static int StabilityCount = 0;
	static const int64 MinimumFileSize = 10000; // 10KB minimum for valid screenshots
	static const int RequiredStabilityChecks = 3; // File must be stable for 3 consecutive checks

	// Check if this is a different file (reset tracking)
	if (LastCheckedFile != FilePath)
	{
		LastCheckedFile = FilePath;
		LastKnownSize = -1;
		StabilityCount = 0;
	}

	// Check if file exists and get current size
	int64 CurrentSize = FPlatformFileManager::Get().GetPlatformFile().FileSize(*FilePath);
	
	if (CurrentSize <= 0)
	{
		// File doesn't exist or is empty
		return false;
	}

	if (CurrentSize < MinimumFileSize)
	{
		// File is too small to be a valid screenshot
		UE_LOG(LogTemp, VeryVerbose, TEXT("Screenshot file too small: %lld bytes"), CurrentSize);
		return false;
	}

	// Check size stability
	if (CurrentSize == LastKnownSize)
	{
		// Size hasn't changed - increment stability counter
		StabilityCount++;
		UE_LOG(LogTemp, VeryVerbose, TEXT("Screenshot file stable: %s (%lld bytes, check %d/%d)"), 
			*FPaths::GetCleanFilename(FilePath), CurrentSize, StabilityCount, RequiredStabilityChecks);

		if (StabilityCount >= RequiredStabilityChecks)
		{
			// File has been stable long enough - check if we can access it
			TUniquePtr<FArchive> TestReader(IFileManager::Get().CreateFileReader(*FilePath));
			if (TestReader.IsValid())
			{
				TestReader->Close();
				UE_LOG(LogTemp, Verbose, TEXT("Screenshot file ready: %s (%lld bytes)"), 
					*FPaths::GetCleanFilename(FilePath), CurrentSize);
				return true;
			}
			else
			{
				UE_LOG(LogTemp, VeryVerbose, TEXT("Screenshot file still locked: %s"), *FPaths::GetCleanFilename(FilePath));
				return false;
			}
		}
	}
	else
	{
		// Size changed - reset stability tracking
		LastKnownSize = CurrentSize;
		StabilityCount = 1; // This counts as the first stable check
		UE_LOG(LogTemp, VeryVerbose, TEXT("Screenshot file size changed to %lld bytes, restarting stability check"), CurrentSize);
	}

	return false;
}

FString FUnrealMCPRenderingCommands::FindLatestScreenshotFile(const FString& ScreenshotDir)
{
	TArray<FString> FoundFiles;
	
	// Search for PNG files first (most common)
	IFileManager::Get().FindFiles(FoundFiles, *FPaths::Combine(ScreenshotDir, TEXT("*.png")), true, false);
	
	// Also search for JPG files
	TArray<FString> JpgFiles;
	IFileManager::Get().FindFiles(JpgFiles, *FPaths::Combine(ScreenshotDir, TEXT("*.jpg")), true, false);
	FoundFiles.Append(JpgFiles);

	if (FoundFiles.Num() == 0)
	{
		return FString(); // No files found
	}

	// Find the most recently created screenshot file
	FString LatestFile;
	FDateTime LatestTime = FDateTime::MinValue();
	
	for (const FString& FileName : FoundFiles)
	{
		// Only consider files that look like Unreal screenshots
		if (FileName.Contains(TEXT("HighresScreenshot")) || 
			FileName.Contains(TEXT("Screenshot")) ||
			FileName.Contains(TEXT("screenshot")))
		{
			FString FullPath = FPaths::Combine(ScreenshotDir, FileName);
			FDateTime FileTime = FPlatformFileManager::Get().GetPlatformFile().GetTimeStamp(*FullPath);
			
			if (FileTime > LatestTime)
			{
				LatestTime = FileTime;
				LatestFile = FullPath;
			}
		}
	}

	if (!LatestFile.IsEmpty())
	{
		UE_LOG(LogTemp, VeryVerbose, TEXT("Latest screenshot file candidate: %s"), *FPaths::GetCleanFilename(LatestFile));
	}
	
	return LatestFile;
}
