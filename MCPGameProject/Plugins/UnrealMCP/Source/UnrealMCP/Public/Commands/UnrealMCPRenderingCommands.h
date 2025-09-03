#pragma once

#include "CoreMinimal.h"
#include "Json.h"
#include "Engine/EngineTypes.h"

/**
 * Data structure for screenshot completion tracking
 */
struct FScreenshotCompletionData
{
    FString FilePath;
    FString Filename;
    FString Format;
    FString ScreenshotDir;
    double ResolutionMultiplier;
    bool bIncludeUI;
    bool bUIWasHidden;
};

/**
 * Handler class for Rendering-related MCP commands
 */
class UNREALMCP_API FUnrealMCPRenderingCommands
{
public:
    FUnrealMCPRenderingCommands();
    TSharedPtr<FJsonObject> HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params);

private:
    // Screenshot command handlers
    TSharedPtr<FJsonObject> HandleTakeHighResShot(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleSynchronousScreenshot(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleAsynchronousHighResScreenshot(const TSharedPtr<FJsonObject>& Params);
    
    // Utility methods for file detection
    bool IsFileReady(const FString& FilePath);
    FString FindLatestScreenshotFile(const FString& ScreenshotDir);
};
