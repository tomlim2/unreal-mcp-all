#include "MegaMelangeBridge.h"
#include "MCPServerRunnable.h"
#include "Sockets.h"
#include "SocketSubsystem.h"
#include "HAL/RunnableThread.h"
#include "Interfaces/IPv4/IPv4Address.h"
#include "Interfaces/IPv4/IPv4Endpoint.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonWriter.h"
#include "Async/Async.h"
#include "Commands/MegaMelangeActorCommands.h"
#include "Commands/MegaMelangeEditorCommands.h"
#include "Commands/MegaMelangeBlueprintCommands.h"
#include "Commands/MegaMelangeBlueprintNodeCommands.h"
#include "Commands/MegaMelangeRenderingCommands.h"
#include "Commands/MegaMelangeObject3DCommands.h"
#include "Commands/MegaMelangeCommonUtils.h"

// Default settings
#define MCP_SERVER_HOST "127.0.0.1"
#define MCP_SERVER_PORT 55557

// Initialize subsystem
void UMegaMelangeBridge::Initialize(FSubsystemCollectionBase& Collection)
{
	UE_LOG(LogTemp, Display, TEXT("MegaMelangeBridge: Initializing"));

	bIsRunning = false;
	ListenerSocket = nullptr;
	ConnectionSocket = nullptr;
	ServerThread = nullptr;
	Port = MCP_SERVER_PORT;
	FIPv4Address::Parse(MCP_SERVER_HOST, ServerAddress);

	// Create command handlers
	ActorCommands = MakeShared<FMegaMelangeActorCommands>();
	EditorCommands = MakeShared<FMegaMelangeEditorCommands>();
	BlueprintCommands = MakeShared<FMegaMelangeBlueprintCommands>();
	BlueprintNodeCommands = MakeShared<FMegaMelangeBlueprintNodeCommands>();
	RenderingCommands = MakeShared<FMegaMelangeRenderingCommands>();
	Object3DCommands = MakeShared<FMegaMelangeObject3DCommands>();

	// Start the server automatically
	StartServer();
}

// Clean up resources when subsystem is destroyed
void UMegaMelangeBridge::Deinitialize()
{
	UE_LOG(LogTemp, Display, TEXT("MegaMelangeBridge: Shutting down"));
	StopServer();
}

// Start the MCP server
void UMegaMelangeBridge::StartServer()
{
	if (bIsRunning)
	{
		UE_LOG(LogTemp, Warning, TEXT("MegaMelangeBridge: Server is already running"));
		return;
	}

	// Create socket subsystem
	ISocketSubsystem* SocketSubsystem = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
	if (!SocketSubsystem)
	{
		UE_LOG(LogTemp, Error, TEXT("MegaMelangeBridge: Failed to get socket subsystem"));
		return;
	}

	// Create listener socket
	TSharedPtr<FSocket> NewListenerSocket = MakeShareable(SocketSubsystem->CreateSocket(NAME_Stream, TEXT("MegaMelangeListener"), false));
	if (!NewListenerSocket.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("MegaMelangeBridge: Failed to create listener socket"));
		return;
	}

	// Allow address reuse for quick restarts
	NewListenerSocket->SetReuseAddr(true);
	NewListenerSocket->SetNonBlocking(true);

	// Bind to address
	FIPv4Endpoint Endpoint(ServerAddress, Port);
	if (!NewListenerSocket->Bind(*Endpoint.ToInternetAddr()))
	{
		UE_LOG(LogTemp, Error, TEXT("MegaMelangeBridge: Failed to bind listener socket to %s:%d"), *ServerAddress.ToString(), Port);
		return;
	}

	// Start listening
	if (!NewListenerSocket->Listen(5))
	{
		UE_LOG(LogTemp, Error, TEXT("MegaMelangeBridge: Failed to start listening"));
		return;
	}

	ListenerSocket = NewListenerSocket;
	bIsRunning = true;
	UE_LOG(LogTemp, Display, TEXT("MegaMelangeBridge: Server started on %s:%d"), *ServerAddress.ToString(), Port);

	// Start server thread
	ServerThread = FRunnableThread::Create(
		new FMCPServerRunnable(this, ListenerSocket),
		TEXT("MegaMelangeServerThread"),
		0, TPri_Normal
	);

	if (!ServerThread)
	{
		UE_LOG(LogTemp, Error, TEXT("MegaMelangeBridge: Failed to create server thread"));
		StopServer();
		return;
	}
}

// Stop the MCP server
void UMegaMelangeBridge::StopServer()
{
	if (!bIsRunning)
	{
		return;
	}

	bIsRunning = false;

	// Clean up thread
	if (ServerThread)
	{
		ServerThread->Kill(true);
		delete ServerThread;
		ServerThread = nullptr;
	}

	// Close sockets
	if (ConnectionSocket.IsValid())
	{
		ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->DestroySocket(ConnectionSocket.Get());
		ConnectionSocket.Reset();
	}

	if (ListenerSocket.IsValid())
	{
		ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->DestroySocket(ListenerSocket.Get());
		ListenerSocket.Reset();
	}

	UE_LOG(LogTemp, Display, TEXT("MegaMelangeBridge: Server stopped"));
}

// Execute a command received from a client
FString UMegaMelangeBridge::ExecuteCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params)
{
	// Create a promise to wait for the result
	TPromise<FString> Promise;
	TFuture<FString> Future = Promise.GetFuture();

	// Queue execution on Game Thread
	AsyncTask(ENamedThreads::GameThread, [this, CommandType, Params, Promise = MoveTemp(Promise)]() mutable
	{
		TSharedPtr<FJsonObject> ResponseJson = MakeShareable(new FJsonObject);

		try
		{
			TSharedPtr<FJsonObject> ResultJson;

			if (CommandType == TEXT("ping"))
			{
				ResultJson = MakeShareable(new FJsonObject);
				ResultJson->SetStringField(TEXT("message"), TEXT("pong"));
			}
			// Actor Commands
			else if (CommandType == TEXT("get_actors_in_level") ||
					 CommandType == TEXT("find_actors_by_name") ||
					 CommandType == TEXT("create_actor") ||
					 CommandType == TEXT("delete_actor") ||
					 CommandType == TEXT("set_actor_transform") ||
					 CommandType == TEXT("get_actor_properties") ||
					 CommandType == TEXT("get_time_of_day") ||
					 CommandType == TEXT("set_time_of_day") ||
					 CommandType == TEXT("get_ultra_dynamic_sky") ||
					 CommandType == TEXT("get_ultra_dynamic_weather") ||
					 CommandType == TEXT("set_color_temperature") ||
					 CommandType == TEXT("set_current_weather_to_rain") ||
					 CommandType == TEXT("set_cesium_latitude_longitude") ||
					 CommandType == TEXT("get_cesium_properties") ||
					 CommandType == TEXT("create_mm_control_light") ||
					 CommandType == TEXT("get_mm_control_lights") ||
					 CommandType == TEXT("update_mm_control_light") ||
					 CommandType == TEXT("delete_mm_control_light") ||
					 CommandType == TEXT("get_character_actors") ||
					 CommandType == TEXT("select_visible_actors"))
			{
				ResultJson = ActorCommands->HandleCommand(CommandType, Params);
			}
			// 3D Object Commands
			else if (CommandType == TEXT("import_object3d_by_uid"))
			{
				ResultJson = Object3DCommands->HandleCommand(CommandType, Params);
			}
			// Editor Commands
			else if (CommandType == TEXT("focus_viewport"))
			{
				ResultJson = EditorCommands->HandleCommand(CommandType, Params);
			}
			// Blueprint Commands
			else if (CommandType == TEXT("create_blueprint") ||
					 CommandType == TEXT("add_component_to_blueprint") ||
					 CommandType == TEXT("set_component_property") ||
					 CommandType == TEXT("set_physics_properties") ||
					 CommandType == TEXT("compile_blueprint") ||
					 CommandType == TEXT("spawn_blueprint_actor") ||
					 CommandType == TEXT("set_blueprint_property") ||
					 CommandType == TEXT("set_static_mesh_properties") ||
					 CommandType == TEXT("set_pawn_properties"))
			{
				ResultJson = BlueprintCommands->HandleCommand(CommandType, Params);
			}
			// Blueprint Node Commands
			else if (CommandType == TEXT("connect_blueprint_nodes") ||
					 CommandType == TEXT("create_input_mapping") ||
					 CommandType == TEXT("add_blueprint_get_self_component_reference") ||
					 CommandType == TEXT("add_blueprint_self_reference") ||
					 CommandType == TEXT("find_blueprint_nodes") ||
					 CommandType == TEXT("add_blueprint_event_node") ||
					 CommandType == TEXT("add_blueprint_input_action_node") ||
					 CommandType == TEXT("add_blueprint_function_node") ||
					 CommandType == TEXT("add_blueprint_get_component_node") ||
					 CommandType == TEXT("add_blueprint_variable"))
			{
				ResultJson = BlueprintNodeCommands->HandleCommand(CommandType, Params);
			}
			else if (CommandType == TEXT("take_screenshot"))
			{
				ResultJson = RenderingCommands->HandleCommand(CommandType, Params);
			}
			else
			{
				ResponseJson->SetStringField(TEXT("status"), TEXT("error"));
				ResponseJson->SetStringField(TEXT("error"), FString::Printf(TEXT("Unknown command: %s"), *CommandType));

				FString ResultString;
				TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&ResultString);
				FJsonSerializer::Serialize(ResponseJson.ToSharedRef(), Writer);
				Promise.SetValue(ResultString);
				return;
			}

			// Check if the result contains an error
			bool bSuccess = true;
			FString ErrorMessage;

			if (ResultJson->HasField(TEXT("success")))
			{
				bSuccess = ResultJson->GetBoolField(TEXT("success"));
				if (!bSuccess && ResultJson->HasField(TEXT("error")))
				{
					ErrorMessage = ResultJson->GetStringField(TEXT("error"));
				}
			}

			if (bSuccess)
			{
				// Set success status and include the result
				ResponseJson->SetStringField(TEXT("status"), TEXT("success"));
				ResponseJson->SetObjectField(TEXT("result"), ResultJson);
			}
			else
			{
				// Set error status and include the error message
				ResponseJson->SetStringField(TEXT("status"), TEXT("error"));
				ResponseJson->SetStringField(TEXT("error"), ErrorMessage);
			}
		}
		catch (const std::exception& e)
		{
			ResponseJson->SetStringField(TEXT("status"), TEXT("error"));
			ResponseJson->SetStringField(TEXT("error"), UTF8_TO_TCHAR(e.what()));
		}

		FString ResultString;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&ResultString);
		FJsonSerializer::Serialize(ResponseJson.ToSharedRef(), Writer);
		Promise.SetValue(ResultString);
	});

	return Future.Get();
}
