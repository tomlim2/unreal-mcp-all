# MegaMelange (Creative Hub) - Sequence Diagrams

## 1. End-to-End Natural Language Command Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Web Frontend<br/>(Next.js)
    participant HTTP as HTTP Bridge<br/>(Python FastAPI)
    participant AI as Claude AI<br/>(NLP Processing)
    participant Registry as Command Registry<br/>(Handler System)
    participant Handler as Command Handler<br/>(Category-specific)
    participant TCP as TCP Bridge<br/>(Port 55557)
    participant CPP as C++ Plugin<br/>(Unreal Engine)
    participant UE as Unreal Engine<br/>(Editor API)

    User->>Frontend: "Create a red cube and make lighting warmer"
    Frontend->>HTTP: POST /ai/process-command
    HTTP->>AI: Process natural language input
    AI->>AI: Generate structured commands
    AI-->>HTTP: JSON commands array

    loop For each command
        HTTP->>Registry: Route command by type
        Registry->>Handler: Validate & execute command
        Handler->>Handler: Validate parameters (schema)
        Handler->>TCP: Send JSON command
        TCP->>CPP: TCP socket communication
        CPP->>CPP: Parse JSON command
        CPP->>UE: Execute Unreal API calls
        UE-->>CPP: Execution result
        CPP-->>TCP: JSON response
        TCP-->>Handler: Command result
        Handler-->>Registry: Execution status
        Registry-->>HTTP: Command results
    end

    HTTP-->>Frontend: Aggregated results
    Frontend-->>User: Display success/error messages
```

## 2. Multi-Tool Creative Hub Flow (NEW Architecture)

```mermaid
sequenceDiagram
    participant User
    participant UI as Tool Selector UI<br/>(Frontend)
    participant HTTP as HTTP Bridge<br/>(FastAPI)
    participant Plugin as Plugin System<br/>(tools/plugins/)
    participant NB as Nano Banana Plugin<br/>(Image Generation)
    participant UE as Unreal Engine Plugin<br/>(3D/Rendering)
    participant API as External APIs<br/>(OpenAI, etc.)

    User->>UI: Select tool (Nano Banana / Unreal)
    UI->>HTTP: POST /ai/process-command {tool: "nano_banana"}
    HTTP->>Plugin: Route to plugin system
    Plugin->>Plugin: Load appropriate plugin

    alt Nano Banana Tool
        Plugin->>NB: Execute image command
        NB->>API: Call image generation API
        API-->>NB: Generated image
        NB->>NB: Save with UID (img_XXX)
        NB-->>Plugin: Image result + UID
    else Unreal Engine Tool
        Plugin->>UE: Execute 3D command
        UE->>UE: TCP communication (port 55557)
        UE-->>Plugin: Execution result
    end

    Plugin-->>HTTP: Tool execution result
    HTTP-->>UI: Display result with UID
    UI-->>User: Show generated content
```

## 3. Image Processing Flow (Copyright-Safe)

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(Image Upload)
    participant Validator as Image Validator<br/>(Client-side)
    participant HTTP as HTTP Bridge
    participant Resource as Resource Module<br/>(core/resources/images)
    participant NB as Nano Banana API
    participant UID as UID System<br/>(Storage)

    User->>Frontend: Upload original image
    Frontend->>Validator: Validate file (size, type, dimensions)
    Validator-->>Frontend: Validation OK
    Frontend->>Frontend: Convert to base64 Data URI

    Frontend->>HTTP: POST {mainImageData: base64_string}
    Note over Frontend,HTTP: User upload: in-memory only, NO storage

    HTTP->>Resource: process_main_image(main_image_data)
    Resource->>Resource: Validate & normalize
    Resource-->>HTTP: In-memory image data

    HTTP->>NB: Transform image (styling/editing)
    NB-->>HTTP: Generated result image

    HTTP->>UID: Save generated image
    UID->>UID: Assign new UID (img_XXX)
    Note over UID: Only generated content stored!
    UID-->>HTTP: new_uid

    HTTP-->>Frontend: {result_uid: "img_001", preview_url: "..."}
    Frontend-->>User: Display generated image

    Note over Frontend,UID: Original upload discarded, only result saved
```

## 4. Screenshot Capture & Serving Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant HTTP as HTTP Bridge
    participant Handler as Screenshot Handler<br/>(rendering/screenshot.py)
    participant TCP as TCP Bridge
    participant CPP as C++ Plugin
    participant UE as Unreal Engine
    participant FS as File System<br/>(Saved/Screenshots/)
    participant UID as UID System

    User->>Frontend: "Take a 4K screenshot"
    Frontend->>HTTP: POST /ai/process-command
    HTTP->>Handler: Route "take_highresshot" command
    Handler->>Handler: Validate resolution parameter
    Handler->>TCP: Send take_highresshot command
    TCP->>CPP: JSON command {resolution: 4}
    CPP->>UE: Execute HighResShot command
    UE->>FS: Save screenshot file
    FS-->>UE: File path
    UE-->>CPP: Screenshot saved
    CPP-->>TCP: {filename: "HighresScreenshot00001.png", path: "..."}
    TCP-->>Handler: File details
    Handler->>UID: Register screenshot with UID
    UID->>UID: Assign img_XXX
    Handler->>Handler: Cache file path for serving
    Handler-->>HTTP: {uid: "img_001", url: "/api/screenshots/img_001"}
    HTTP-->>Frontend: Screenshot URL
    Frontend->>HTTP: GET /api/screenshots/img_001
    HTTP->>Handler: Serve cached file
    Handler->>FS: Read screenshot file
    FS-->>Handler: Image data
    Handler-->>HTTP: Image binary
    HTTP-->>Frontend: PNG image
    Frontend-->>User: Display screenshot
```

## 5. MCP Client Integration Flow

```mermaid
sequenceDiagram
    participant User
    participant Client as MCP Client<br/>(Claude Desktop/Cursor)
    participant MCP as MCP Server<br/>(Python)
    participant Handler as Tool Handler
    participant TCP as TCP Bridge
    participant UE as Unreal Engine

    User->>Client: Natural language request
    Client->>MCP: Invoke MCP tool
    MCP->>Handler: Execute tool function
    Handler->>Handler: Validate parameters
    Handler->>TCP: Send command to Unreal
    TCP->>UE: Execute command
    UE-->>TCP: Result
    TCP-->>Handler: Response
    Handler-->>MCP: Tool result
    MCP-->>Client: Formatted response
    Client-->>User: Display result
```

## 6. Command Handler Registration & Routing

```mermaid
sequenceDiagram
    participant Init as System Init
    participant Registry as Command Registry<br/>(main.py)
    participant Actor as Actor Handlers<br/>(actor/*.py)
    participant Render as Rendering Handlers<br/>(rendering/*.py)
    participant Plugin as Plugin Handlers<br/>(plugins/*.py)

    Init->>Registry: Initialize registry
    Registry->>Actor: Import actor handlers
    Actor-->>Registry: Register: UDS, Cesium, Light, Actor
    Registry->>Render: Import rendering handlers
    Render-->>Registry: Register: Screenshot, Materials, Camera
    Registry->>Plugin: Import plugin handlers
    Plugin-->>Registry: Register: Nano Banana, etc.
    Registry->>Registry: Build command map

    Note over Registry: Runtime: Command arrives
    Registry->>Registry: Lookup handler by command type
    Registry->>Actor: Route to appropriate handler
    Actor->>Actor: Validate & execute
    Actor-->>Registry: Execution result
```

## 7. Multi-Developer Environment Setup

```mermaid
sequenceDiagram
    participant Dev1 as Developer 1
    participant Dev2 as Developer 2
    participant Script as Port Assignment<br/>Script
    participant Env as Environment<br/>Variables
    participant UE1 as Unreal Engine<br/>(Dev 1: Port 55557)
    participant UE2 as Unreal Engine<br/>(Dev 2: Port 55558)

    Dev1->>Script: Run script-set-ports.bat
    Script->>Env: Set UNREAL_TCP_PORT=55557
    Script->>Env: Set HTTP_PORT=8080
    Script->>Env: Set FRONTEND_PORT=3000
    Dev1->>UE1: Start project on port 55557

    Dev2->>Script: Run script-set-ports.bat
    Script->>Env: Set UNREAL_TCP_PORT=55558
    Script->>Env: Set HTTP_PORT=8081
    Script->>Env: Set FRONTEND_PORT=3001
    Dev2->>UE2: Start project on port 55558

    Note over Dev1,UE2: No port conflicts - parallel development
```

## Key Interaction Patterns

### 1. Command Validation Pattern
- **Client-side**: File validation (images, uploads)
- **Python Handler**: Schema validation (parameters, types)
- **C++ Plugin**: Unreal API parameter validation

### 2. Error Propagation
```
User Input → Frontend → HTTP Bridge → Handler → TCP → C++ → Unreal
                ↓          ↓           ↓        ↓      ↓       ↓
            UI Error   HTTP Error   Handler   TCP    C++   UE API
                                    Error    Error  Error  Error
                                       ↓
                                All errors bubble up to user
```

### 3. Resource Management
- **User Uploads**: In-memory only, discarded after processing
- **Generated Content**: Saved with UID, tracked in database
- **Screenshots**: Cached file paths, served via HTTP

### 4. Tool Routing Priority
1. Check tool selector (frontend)
2. Analyze command capabilities (NLP)
3. Route to appropriate plugin
4. Execute via plugin-specific handler

## Technology Stack Flow

```mermaid
graph LR
    A[User] --> B[Next.js 15.4+]
    B --> C[FastAPI HTTP Bridge]
    C --> D[Claude AI NLP]
    C --> E[Plugin System]
    E --> F[Nano Banana Plugin]
    E --> G[Unreal Engine Plugin]
    G --> H[TCP Bridge Port 55557]
    H --> I[C++ Plugin UE 5.3+]
    I --> J[Unreal Engine Editor API]

    style D fill:#f9f,stroke:#333
    style E fill:#9ff,stroke:#333
    style I fill:#ff9,stroke:#333
```
