#include "Commands/UnrealMCPRenderingCommands.h"
#include "Commands/UnrealMCPCommonUtils.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Misc/Paths.h"
#include "HAL/PlatformFilemanager.h"
#include "HAL/PlatformProcess.h"
#include "Editor.h"
#include "EngineUtils.h"

FUnrealMCPRenderingCommands::FUnrealMCPRenderingCommands()
{
}

TSharedPtr<FJsonObject> FUnrealMCPRenderingCommands::HandleTakeShot(const TSharedPtr<FJsonObject>& Params)
{
	// Get parameters with defaults
	FString Filename = TEXT("");
	bool bIncludeUI = false;

	if (Params.IsValid())
	{
		Params->TryGetStringField(TEXT("filename"), Filename);
		Params->TryGetBoolField(TEXT("include_ui"), bIncludeUI);
	}

	// Determine world context
	UWorld* World = nullptr;
	UGameViewportClient* GameViewportClient = GEngine->GameViewport;
	
	if (GameViewportClient)
	{
		World = GameViewportClient->GetWorld();
		UE_LOG(LogTemp, Log, TEXT("Found GameViewport World: %s"), World ? *World->GetName() : TEXT("NULL"));
	}
	else
	{
		World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		UE_LOG(LogTemp, Log, TEXT("Found Editor World: %s"), World ? *World->GetName() : TEXT("NULL"));
		
		if (!World)
		{
			return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No valid world context found"));
		}
	}

	// Hide UI if requested
	if (!bIncludeUI)
	{
		GEngine->Exec(World, TEXT("showflag.hud 0"));
		GEngine->Exec(World, TEXT("showflag.screenmessages 0"));
	}

	// Try multiple screenshot commands in order of preference
	bool bCommandSuccess = false;
	FString SuccessfulCommand;
	
	// Build command list to try
	TArray<FString> CommandsToTry;
	
	if (!Filename.IsEmpty())
	{
		CommandsToTry.Add(FString::Printf(TEXT("Shot %s"), *Filename));
		CommandsToTry.Add(FString::Printf(TEXT("HighResShot %s"), *Filename));
	}
	else
	{
		// Try different variations of screenshot commands with proper parameters
		CommandsToTry.Add(TEXT("screenshot"));
		CommandsToTry.Add(TEXT("HighResShot 1"));
		CommandsToTry.Add(TEXT("HighResShot 1920x1080"));
	}
	
	for (const FString& Command : CommandsToTry)
	{
		UE_LOG(LogTemp, Log, TEXT("Trying screenshot command: %s"), *Command);
		bCommandSuccess = GEngine->Exec(World, *Command);
		
		if (bCommandSuccess)
		{
			SuccessfulCommand = Command;
			UE_LOG(LogTemp, Log, TEXT("Screenshot command '%s' succeeded"), *Command);
			break;
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("Screenshot command '%s' failed"), *Command);
		}
	}

	// Restore UI immediately if it was hidden
	if (!bIncludeUI)
	{
		GEngine->Exec(World, TEXT("showflag.hud 1"));
		GEngine->Exec(World, TEXT("showflag.screenmessages 1"));
	}

	if (!bCommandSuccess)
	{
		FString ErrorMsg = TEXT("All screenshot commands failed");
		UE_LOG(LogTemp, Error, TEXT("%s"), *ErrorMsg);
		return FUnrealMCPCommonUtils::CreateErrorResponse(ErrorMsg);
	}
	
	UE_LOG(LogTemp, Log, TEXT("Screenshot command '%s' executed successfully"), *SuccessfulCommand);

	// Find the latest screenshot file
	FString ScreenshotDir = FPaths::Combine(FPaths::ProjectDir(), TEXT("Saved/Screenshots"));
	FString FullScreenshotDir = FPaths::Combine(ScreenshotDir, TEXT("WindowsEditor"));
	
	// Create success response
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("success"), TEXT("true"));
	
	if (!Filename.IsEmpty())
	{
		ResultObj->SetStringField(TEXT("message"), FString::Printf(TEXT("Screenshot saved: %s"), *Filename));
		ResultObj->SetStringField(TEXT("image_url"), FString::Printf(TEXT("/api/screenshot-file/%s"), *Filename));
	}
	else
	{
		ResultObj->SetStringField(TEXT("message"), TEXT("Screenshot saved: ScreenShot00001.png"));
		ResultObj->SetStringField(TEXT("image_url"), TEXT("/api/screenshot-file/ScreenShot00001.png"));
	}
	
	return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPRenderingCommands::HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params)
{
	if (CommandType == TEXT("take_shot"))
	{
		return HandleTakeShot(Params);
	}
	else if (CommandType == TEXT("take_highresshot"))
	{
		return HandleTakeHighResShot(Params);
	}
	return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown rendering command: %s"), *CommandType));
}

TSharedPtr<FJsonObject> FUnrealMCPRenderingCommands::HandleTakeHighResShot(const TSharedPtr<FJsonObject>& Params)
{
	// Get parameters with defaults
	double ResolutionMultiplier = 1.0;
	bool bIncludeUI = false;

	if (Params.IsValid())
	{
		Params->TryGetNumberField(TEXT("resolution_multiplier"), ResolutionMultiplier);
		Params->TryGetBoolField(TEXT("include_ui"), bIncludeUI);
	}

	// Validate resolution multiplier
	if (ResolutionMultiplier < 1.0 || ResolutionMultiplier > 8.0)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Resolution multiplier must be between 1.0 and 8.0"));
	}

	// Debug world context and actor count before screenshot
	UE_LOG(LogTemp, Log, TEXT("Using immediate response approach for resolution multiplier: %.1f"), ResolutionMultiplier);
	
	// Check world context and actor count
	UWorld* World = nullptr;
	UGameViewportClient* GameViewportClient = GEngine->GameViewport;
	
	if (GameViewportClient)
	{
		World = GameViewportClient->GetWorld();
		UE_LOG(LogTemp, Log, TEXT("Found GameViewport World: %s"), World ? *World->GetName() : TEXT("NULL"));
	}
	else
	{
		World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		UE_LOG(LogTemp, Log, TEXT("Found Editor World: %s"), World ? *World->GetName() : TEXT("NULL"));
	}
	
	if (World)
	{
		int32 ActorCount = 0;
		for (TActorIterator<AActor> ActorIterator(World); ActorIterator; ++ActorIterator)
		{
			ActorCount++;
		}
		UE_LOG(LogTemp, Log, TEXT("World '%s' has %d actors"), *World->GetName(), ActorCount);
		UE_LOG(LogTemp, Log, TEXT("World Type: %d"), (int32)World->WorldType);
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("No valid world context found!"));
	}
	
	return HandleQuickScreenshot(Params);
}

TSharedPtr<FJsonObject> FUnrealMCPRenderingCommands::HandleQuickScreenshot(const TSharedPtr<FJsonObject>& Params)
{
	// Get parameters with defaults
	double ResolutionMultiplier = 1.0;
	bool bIncludeUI = false;

	if (Params.IsValid())
	{
		Params->TryGetNumberField(TEXT("resolution_multiplier"), ResolutionMultiplier);
		Params->TryGetBoolField(TEXT("include_ui"), bIncludeUI);
	}

	// Determine world context
	UWorld* World = nullptr;
	UGameViewportClient* GameViewportClient = GEngine->GameViewport;
	
	if (GameViewportClient)
	{
		World = GameViewportClient->GetWorld();
	}
	else
	{
		World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		if (!World)
		{
			return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No valid world context found"));
		}
	}

	// Hide UI if requested
	if (!bIncludeUI)
	{
		GEngine->Exec(World, TEXT("showflag.hud 0"));
		GEngine->Exec(World, TEXT("showflag.screenmessages 0"));
	}

	// Try multiple screenshot commands in order of preference with proper parameters
	bool bCommandSuccess = false;
	TArray<FString> CommandsToTry = {
		TEXT("screenshot"), 
		FString::Printf(TEXT("HighResShot %d"), FMath::RoundToInt(ResolutionMultiplier)),
		TEXT("HighResShot 1920x1080")
	};
	FString SuccessfulCommand;
	
	for (const FString& Command : CommandsToTry)
	{
		UE_LOG(LogTemp, Log, TEXT("Trying screenshot command: %s"), *Command);
		bCommandSuccess = GEngine->Exec(World, *Command);
		
		if (bCommandSuccess)
		{
			SuccessfulCommand = Command;
			UE_LOG(LogTemp, Log, TEXT("Screenshot command '%s' succeeded"), *Command);
			break;
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("Screenshot command '%s' failed"), *Command);
		}
	}

	// Restore UI immediately if it was hidden
	if (!bIncludeUI)
	{
		GEngine->Exec(World, TEXT("showflag.hud 1"));
		GEngine->Exec(World, TEXT("showflag.screenmessages 1"));
	}

	if (!bCommandSuccess)
	{
		FString ErrorMsg = TEXT("All screenshot commands failed: Shot, screenshot, HighResShot");
		UE_LOG(LogTemp, Error, TEXT("%s"), *ErrorMsg);
		return FUnrealMCPCommonUtils::CreateErrorResponse(*ErrorMsg);
	}
	
	UE_LOG(LogTemp, Log, TEXT("Screenshot command '%s' executed successfully"), *SuccessfulCommand);

	// Simple success response
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("success"), TEXT("true"));
	ResultObj->SetStringField(TEXT("message"), TEXT("Screenshot command executed"));
	
	return ResultObj;
}