#pragma once

#include "CoreMinimal.h"
#include "EditorSubsystem.h"
#include "Sockets.h"
#include "SocketSubsystem.h"
#include "Http.h"
#include "Json.h"
#include "Interfaces/IPv4/IPv4Address.h"
#include "Interfaces/IPv4/IPv4Endpoint.h"
#include "MegaMelangeBridge.generated.h"

class FMCPServerRunnable;
class FMegaMelangeActorCommands;
class FMegaMelangeEditorCommands;
class FMegaMelangeBlueprintCommands;
class FMegaMelangeBlueprintNodeCommands;
class FMegaMelangeRenderingCommands;
class FMegaMelangeObject3DCommands;
class FMegaMelangeAssetCommands;

/**
 * Editor subsystem for MCP Bridge
 */
UCLASS()
class MEGAMELANGE_API UMegaMelangeBridge : public UEditorSubsystem
{
	GENERATED_BODY()

public:
	// UEditorSubsystem implementation
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	// Server functions
	void StartServer();
	void StopServer();
	bool IsRunning() const { return bIsRunning; }

	// Command execution
	FString ExecuteCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params);

private:
	// Server state
	bool bIsRunning;
	TSharedPtr<FSocket> ListenerSocket;
	TSharedPtr<FSocket> ConnectionSocket;
	FRunnableThread* ServerThread;

	// Server configuration
	FIPv4Address ServerAddress;
	uint16 Port;

	// Command handler instances
	TSharedPtr<FMegaMelangeActorCommands> ActorCommands;
	TSharedPtr<FMegaMelangeEditorCommands> EditorCommands;
	TSharedPtr<FMegaMelangeBlueprintCommands> BlueprintCommands;
	TSharedPtr<FMegaMelangeBlueprintNodeCommands> BlueprintNodeCommands;
	TSharedPtr<FMegaMelangeRenderingCommands> RenderingCommands;
	TSharedPtr<FMegaMelangeObject3DCommands> Object3DCommands;
	TSharedPtr<FMegaMelangeAssetCommands> AssetCommands;
};
