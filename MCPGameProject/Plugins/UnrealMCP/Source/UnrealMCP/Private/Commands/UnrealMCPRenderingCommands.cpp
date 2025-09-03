#include "Commands/UnrealMCPRenderingCommands.h"
#include "Commands/UnrealMCPCommonUtils.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Misc/Paths.h"
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

	// Use immediate response approach - return quickly without waiting for file detection
	UE_LOG(LogTemp, Log, TEXT("Using immediate response approach for resolution multiplier: %.1f"), ResolutionMultiplier);
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

	// Execute HighResShot command
	FString ScreenshotCommand = FString::Printf(TEXT("HighResShot %d"), FMath::RoundToInt(ResolutionMultiplier));
	bool bCommandSuccess = GEngine->Exec(World, *ScreenshotCommand);

	// Restore UI immediately if it was hidden
	if (!bIncludeUI)
	{
		GEngine->Exec(World, TEXT("showflag.hud 1"));
		GEngine->Exec(World, TEXT("showflag.screenmessages 1"));
	}

	if (!bCommandSuccess)
	{
		return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to execute HighResShot command"));
	}

	// Simple success response
	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetStringField(TEXT("success"), TEXT("true"));
	ResultObj->SetStringField(TEXT("message"), TEXT("Screenshot command executed"));
	
	return ResultObj;
}