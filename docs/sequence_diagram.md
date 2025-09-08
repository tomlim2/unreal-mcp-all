# MegaMelange System Flow - Sequence Diagram

```mermaid
sequenceDiagram
    participant Frontend as Frontend (Next.js)
    participant Bridge as HTTP Bridge (Python)
    participant Supabase as Supabase Database
    participant LLM as LLM (Claude API)
    participant NLP as NLP Processor
    participant UE as Unreal Engine

    Note over Frontend, UE: User Natural Language Request Flow

    Frontend->>+Bridge: POST /api/mcp<br/>{"prompt": "create red light", "session_id": "123"}
    
    Bridge->>+Supabase: Get session context
    Supabase-->>-Bridge: Session history & scene state
    
    Bridge->>+NLP: process_natural_language(prompt, context, session_id)
    
    NLP->>+LLM: Send system prompt + conversation history<br/>Model: claude-3-haiku-20240307
    LLM-->>-NLP: JSON response with commands<br/>{"commands": [{"type": "create_mm_control_light", "params": {...}}]}
    
    loop For each command in response
        NLP->>+UE: TCP connection (port 55557)<br/>execute_command_direct(command)
        UE-->>-NLP: JSON result from Unreal
    end
    
    NLP->>+Supabase: Store interaction<br/>(user input + AI response + execution results)
    Supabase-->>-NLP: Confirmation
    
    NLP-->>-Bridge: Complete response with execution results
    Bridge-->>-Frontend: JSON response for UI display

    Note over Frontend, UE: Session Management Flow
    
    Frontend->>+Bridge: GET /api/sessions
    Bridge->>+Supabase: Query chat_context table
    Supabase-->>-Bridge: List of sessions
    Bridge-->>-Frontend: Session list for UI

    Note over Frontend, UE: Session Creation Flow
    
    Frontend->>+Bridge: POST /api/sessions<br/>{"session_name": "My Project"}
    Bridge->>+Supabase: Insert new session record
    Supabase-->>-Bridge: New session_id generated
    Bridge-->>-Frontend: Session created confirmation
```

## Component Responsibilities

### Frontend (Next.js)
- User interface for natural language input
- Session management UI
- API route forwarding to Python bridge

### HTTP Bridge (Python)
- Routes requests between Frontend and other components
- Handles session creation/management logic
- Forwards NLP requests to processing layer

### Supabase Database
- Stores session data in `chat_context` table
- Maintains conversation history and scene state
- Provides session persistence across requests

### LLM (Claude API)
- Processes natural language with system prompts
- Returns structured JSON commands
- Uses conversation history for context

### NLP Processor
- Orchestrates LLM interaction
- Validates and executes commands
- Manages session context updates

### Unreal Engine
- Executes commands via TCP server (port 55557)
- Returns execution results as JSON
- Maintains actual 3D scene state