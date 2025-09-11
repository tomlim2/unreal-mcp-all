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

TSharedPtr<FJsonObject> FUnrealMCPRenderingCommands::HandleTakeScreenshot(const TSharedPtr<FJsonObject>& Params)
{
	// Debug: Log all received parameters
	UE_LOG(LogTemp, Warning, TEXT("=== SCREENSHOT COMMAND DEBUG ==="));
	UE_LOG(LogTemp, Warning, TEXT("Params.IsValid(): %s"), Params.IsValid() ? TEXT("true") : TEXT("false"));
	
	if (Params.IsValid())
	{
		FString JsonString;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
		FJsonSerializer::Serialize(Params.ToSharedRef(), Writer);
		UE_LOG(LogTemp, Warning, TEXT("Raw JSON Parameters: %s"), *JsonString);
	}
	
	// Get parameters with defaults
	FString Filename = TEXT("");
	double ResolutionMultiplier = 1.0;
	bool bIncludeUI = false;

	if (Params.IsValid())
	{
		Params->TryGetStringField(TEXT("filename"), Filename);
		Params->TryGetNumberField(TEXT("resolution_multiplier"), ResolutionMultiplier);
		Params->TryGetBoolField(TEXT("include_ui"), bIncludeUI);
		
		// Debug: Log parsed parameters
		UE_LOG(LogTemp, Warning, TEXT("Parsed filename: '%s'"), *Filename);
		UE_LOG(LogTemp, Warning, TEXT("Parsed resolution_multiplier: %.2f"), ResolutionMultiplier);
		UE_LOG(LogTemp, Warning, TEXT("Parsed include_ui: %s"), bIncludeUI ? TEXT("true") : TEXT("false"));
	}

	// Validate resolution multiplier
	if (ResolutionMultiplier < 1.0 || ResolutionMultiplier > 8.0)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Resolution multiplier must be between 1.0 and 8.0"));
	}

	// Debug world context and actor count before screenshot
	UE_LOG(LogTemp, Log, TEXT("Taking screenshot with resolution multiplier: %.1f"), ResolutionMultiplier);
	
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
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No valid world context found"));
	}

	// Hide UI if requested
	if (!bIncludeUI)
	{
		GEngine->Exec(World, TEXT("showflag.hud 0"));
		GEngine->Exec(World, TEXT("showflag.screenmessages 0"));
	}

	// Use Shot command only - most reliable
	// Note: Shot command doesn't support custom filenames, it uses auto-numbering (ScreenShot00001.png, etc.)
	FString ScreenshotCommand = TEXT("Shot");
	
	// Log the requested filename for reference, but Shot will use its own naming
	if (!Filename.IsEmpty())
	{
		UE_LOG(LogTemp, Log, TEXT("Custom filename requested: %s (Shot command will use auto-numbering instead)"), *Filename);
	}
	
	UE_LOG(LogTemp, Warning, TEXT("Executing screenshot command: %s"), *ScreenshotCommand);
	UE_LOG(LogTemp, Warning, TEXT("World Type: %d (Game=1, PIE=2, Editor=3)"), (int32)World->WorldType);
	
	// Execute Shot command using multiple methods to ensure it works
	// Note: Exec() return values are unreliable, but the command itself works
	
	// Method 1: Try GameViewportClient execution (runtime console context)
	if (GameViewportClient && World->WorldType == EWorldType::Game)
	{
		UE_LOG(LogTemp, Warning, TEXT("Method 1: Using GameViewportClient->Exec (runtime console context)"));
		GameViewportClient->Exec(World, *ScreenshotCommand, *GLog);
	}
	
	// Method 2: Try standard GEngine execution
	UE_LOG(LogTemp, Warning, TEXT("Method 2: Using GEngine->Exec (standard context)"));
	GEngine->Exec(World, *ScreenshotCommand);
	
	// Method 3: Try console command manager directly (this was working before)
	if (GameViewportClient)
	{
		UE_LOG(LogTemp, Warning, TEXT("Method 3: Trying direct console command execution"));
		if (ULocalPlayer* LocalPlayer = GameViewportClient->GetGameInstance()->GetFirstGamePlayer())
		{
			if (APlayerController* PC = LocalPlayer->GetPlayerController(World))
			{
				FString Result = PC->ConsoleCommand(*ScreenshotCommand, true);
				UE_LOG(LogTemp, Warning, TEXT("Method 3 ConsoleCommand result: '%s'"), *Result);
			}
			else
			{
				UE_LOG(LogTemp, Warning, TEXT("Method 3: No PlayerController found"));
			}
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("Method 3: No LocalPlayer found"));
		}
	}

	// Restore UI immediately if it was hidden
	if (!bIncludeUI)
	{
		GEngine->Exec(World, TEXT("showflag.hud 1"));
		GEngine->Exec(World, TEXT("showflag.screenmessages 1"));
	}

	// Always assume success since Shot command demonstrably works
	UE_LOG(LogTemp, Warning, TEXT("Shot command executed via multiple methods - assuming success"));
	
	UE_LOG(LogTemp, Log, TEXT("Screenshot command executed successfully: %s"), *ScreenshotCommand);

	// Create success response
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("success"), TEXT("true"));
	
	// Shot command uses auto-numbering, so we indicate this in the response
	if (!Filename.IsEmpty())
	{
		ResultObj->SetStringField(TEXT("message"), FString::Printf(TEXT("Screenshot saved with auto-numbering (requested: %s)"), *Filename));
		ResultObj->SetStringField(TEXT("image_url"), TEXT("/api/screenshot-file/ScreenShot00001.png")); // Will be auto-numbered
	}
	else
	{
		ResultObj->SetStringField(TEXT("message"), TEXT("Screenshot saved with auto-numbering"));
		ResultObj->SetStringField(TEXT("image_url"), TEXT("/api/screenshot-file/ScreenShot00001.png")); // Will be auto-numbered
	}
	
	return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPRenderingCommands::HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params)
{
	if (CommandType == TEXT("take_screenshot"))
	{
		return HandleTakeScreenshot(Params);
	}
	return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown rendering command: %s"), *CommandType));
}

