#include "MCPServerRunnable.h"
#include "MegaMelangeBridge.h"
#include "Sockets.h"
#include "SocketSubsystem.h"
#include "Interfaces/IPv4/IPv4Address.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonReader.h"
#include "JsonObjectConverter.h"
#include "HAL/PlatformTime.h"

const int32 BufferSize = 8192;

FMCPServerRunnable::FMCPServerRunnable(UMegaMelangeBridge* InBridge, TSharedPtr<FSocket> InListenerSocket)
	: Bridge(InBridge)
	, ListenerSocket(InListenerSocket)
	, bRunning(true)
{
	UE_LOG(LogTemp, Display, TEXT("MCPServerRunnable: Server runnable created"));
}

FMCPServerRunnable::~FMCPServerRunnable()
{
}

bool FMCPServerRunnable::Init()
{
	return true;
}

uint32 FMCPServerRunnable::Run()
{
	UE_LOG(LogTemp, Display, TEXT("MCPServerRunnable: Server thread starting"));

	while (bRunning)
	{
		bool bPending = false;
		if (ListenerSocket->HasPendingConnection(bPending) && bPending)
		{
			UE_LOG(LogTemp, Display, TEXT("MCPServerRunnable: Accepting client connection"));

			ClientSocket = MakeShareable(ListenerSocket->Accept(TEXT("MCPClient")));
			if (ClientSocket.IsValid())
			{
				UE_LOG(LogTemp, Display, TEXT("MCPServerRunnable: Client connected"));

				// Set socket options for better stability
				ClientSocket->SetNoDelay(true);
				int32 SocketBufferSize = 65536;
				ClientSocket->SetSendBufferSize(SocketBufferSize, SocketBufferSize);
				ClientSocket->SetReceiveBufferSize(SocketBufferSize, SocketBufferSize);

				uint8 Buffer[8192];
				while (bRunning)
				{
					int32 BytesRead = 0;
					if (ClientSocket->Recv(Buffer, sizeof(Buffer), BytesRead))
					{
						if (BytesRead == 0)
						{
							UE_LOG(LogTemp, Display, TEXT("MCPServerRunnable: Client disconnected"));
							break;
						}

						Buffer[BytesRead] = '\0';
						FString ReceivedText = UTF8_TO_TCHAR(Buffer);

						// Parse JSON
						TSharedPtr<FJsonObject> JsonObject;
						TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ReceivedText);

						if (FJsonSerializer::Deserialize(Reader, JsonObject))
						{
							FString CommandType;
							if (JsonObject->TryGetStringField(TEXT("type"), CommandType))
							{
								// Execute command
								FString Response = Bridge->ExecuteCommand(CommandType, JsonObject->GetObjectField(TEXT("params")));

								// Send response
								int32 BytesSent = 0;
								if (!ClientSocket->Send((uint8*)TCHAR_TO_UTF8(*Response), Response.Len(), BytesSent))
								{
									UE_LOG(LogTemp, Warning, TEXT("MCPServerRunnable: Failed to send response"));
								}
							}
							else
							{
								UE_LOG(LogTemp, Warning, TEXT("MCPServerRunnable: Missing 'type' field in command"));
							}
						}
						else
						{
							UE_LOG(LogTemp, Warning, TEXT("MCPServerRunnable: Failed to parse JSON"));
						}
					}
					else
					{
						int32 LastError = (int32)ISocketSubsystem::Get()->GetLastErrorCode();
						bool bShouldBreak = true;

						if (LastError == SE_EWOULDBLOCK)
						{
							bShouldBreak = false;
							FPlatformProcess::Sleep(0.01f);
						}
						else if (LastError == SE_EINTR)
						{
							bShouldBreak = false;
						}
						else
						{
							UE_LOG(LogTemp, Warning, TEXT("MCPServerRunnable: Socket error %d"), LastError);
						}

						if (bShouldBreak)
						{
							break;
						}
					}
				}
			}
			else
			{
				UE_LOG(LogTemp, Warning, TEXT("MCPServerRunnable: Failed to accept client connection"));
			}
		}

		FPlatformProcess::Sleep(0.1f);
	}

	UE_LOG(LogTemp, Display, TEXT("MCPServerRunnable: Server thread stopping"));
	return 0;
}

void FMCPServerRunnable::Stop()
{
	bRunning = false;
}

void FMCPServerRunnable::Exit()
{
}

void FMCPServerRunnable::ProcessMessage(TSharedPtr<FSocket> Client, const FString& Message)
{
	TSharedPtr<FJsonObject> JsonMessage;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Message);

	if (!FJsonSerializer::Deserialize(Reader, JsonMessage) || !JsonMessage.IsValid())
	{
		UE_LOG(LogTemp, Warning, TEXT("MCPServerRunnable: Failed to parse message"));
		return;
	}

	FString CommandType;
	TSharedPtr<FJsonObject> Params = MakeShareable(new FJsonObject());

	if (!JsonMessage->TryGetStringField(TEXT("command"), CommandType))
	{
		UE_LOG(LogTemp, Warning, TEXT("MCPServerRunnable: Message missing 'command' field"));
		return;
	}

	if (JsonMessage->HasField(TEXT("params")))
	{
		TSharedPtr<FJsonValue> ParamsValue = JsonMessage->TryGetField(TEXT("params"));
		if (ParamsValue.IsValid() && ParamsValue->Type == EJson::Object)
		{
			Params = ParamsValue->AsObject();
		}
	}

	// Execute command
	FString Response = Bridge->ExecuteCommand(CommandType, Params);

	// Send response with newline terminator
	Response += TEXT("\n");
	int32 BytesSent = 0;

	if (!Client->Send((uint8*)TCHAR_TO_UTF8(*Response), Response.Len(), BytesSent))
	{
		UE_LOG(LogTemp, Error, TEXT("MCPServerRunnable: Failed to send response"));
	}
}
