# Unreal MCP Documentation Index

This directory contains comprehensive documentation for all data structures, APIs, and schemas used in the Unreal MCP system.

## 📖 Documentation Files

### Core Documentation

| File | Description | Use Case |
|------|-------------|----------|
| [SESSION_CONTEXT_SCHEMA.md](SESSION_CONTEXT_SCHEMA.md) | Complete data structure schemas | Understanding session data format |
| [UNREAL_RESPONSE_FORMATS.md](UNREAL_RESPONSE_FORMATS.md) | All Unreal Engine response formats | Handling responses and errors |
| [API_REFERENCE.md](API_REFERENCE.md) | Complete API documentation | Using functions and classes |
| [JSON_SCHEMAS.json](JSON_SCHEMAS.json) | JSON Schema definitions | Validation and IDE support |
| [SUPABASE_SCHEMA.sql](SUPABASE_SCHEMA.sql) | Database schema and setup | Database management |

### Existing Documentation

| File | Description |
|------|-------------|
| [unreal_mcp_best_practices.md](unreal_mcp_best_practices.md) | Best practices and guidelines |

## 🚀 Quick Start Guide

### For Developers
1. Start with [API_REFERENCE.md](API_REFERENCE.md) for function signatures
2. Check [SESSION_CONTEXT_SCHEMA.md](SESSION_CONTEXT_SCHEMA.md) for data structures
3. Use [UNREAL_RESPONSE_FORMATS.md](UNREAL_RESPONSE_FORMATS.md) for response handling

### For Database Administrators
1. Use [SUPABASE_SCHEMA.sql](SUPABASE_SCHEMA.sql) to set up the database
2. Review [SESSION_CONTEXT_SCHEMA.md](SESSION_CONTEXT_SCHEMA.md) for stored data format

### For Frontend Developers
1. Check [JSON_SCHEMAS.json](JSON_SCHEMAS.json) for type definitions
2. Review [UNREAL_RESPONSE_FORMATS.md](UNREAL_RESPONSE_FORMATS.md) for API responses

### For Students Adding Commands
1. Follow the [STUDENT_COMMAND_GUIDE_UPDATED.md](../STUDENT_COMMAND_GUIDE_UPDATED.md)
2. Use [API_REFERENCE.md](API_REFERENCE.md) for command handler interfaces

## 📋 Documentation Summary

### Session Management
- **SessionContext**: Complete session with conversation and scene state
- **ChatMessage**: Individual messages with commands and results
- **SceneState**: Current Unreal Engine scene information
- **ActorInfo/LightInfo**: Actor and light data structures

### NLP Processing
- **Natural Language → Commands**: Input processing pipeline
- **Execution Results**: Command execution with success/failure tracking
- **Session Awareness**: Context-aware command processing

### Storage
- **Supabase Integration**: Database schema and queries
- **JSON Storage**: Complete session context in JSONB format
- **Cleanup**: Automated maintenance and cleanup procedures

### Command System
- **Command Handlers**: Modular command processing
- **Validation Pipeline**: Parameter validation and preprocessing
- **Registry System**: Command routing and execution

## 🔧 Key Features Documented

### ✅ Session Context Storage
- Complete conversation history with Unreal Engine responses
- Scene state tracking (actors, lights, sky settings)
- User preferences and metadata
- Automatic timestamp management

### ✅ Error Handling  
- Standard and alternative Unreal Engine response formats
- Detailed error codes and messages
- Validation failure handling
- Connection and timeout errors

### ✅ Natural Language Processing
- User input → structured commands
- Session-aware processing with conversation memory
- Command validation and execution
- Success/failure tracking with detailed results

### ✅ Database Schema
- Optimized indexes for performance
- Automatic cleanup procedures
- Row-level security setup
- Maintenance functions and views

## 🎯 Use Cases

### Building Frontend Applications
```javascript
// Use JSON schemas for TypeScript types
import { SessionContext, NLPResponse } from './schemas';

// Handle API responses
if (response.status === 'success') {
  // Process successful response
} else {
  // Handle error with detailed error codes
}
```

### Database Operations
```sql
-- Query recent conversations
SELECT session_id, context->'conversation_history' 
FROM user_sessions 
WHERE last_accessed > NOW() - INTERVAL '1 day';

-- Find sessions with failed commands
SELECT session_id 
FROM user_sessions 
WHERE context @@ '$.conversation_history[*].execution_results[*].success ? (@ == false)';
```

### Python Development
```python
from tools.ai.session_management import get_session_manager
from tools.ai.nlp import process_natural_language

# Session-aware NLP processing
result = process_natural_language(
    "Make it brighter", 
    session_id="user_123"
)

# Access complete conversation history
session = session_manager.get_session("user_123")
summary = session.get_conversation_summary()
```

## 🏗️ Architecture Overview

```
User Input → NLP Processing → Command Validation → Unreal Engine → Response Storage
     ↓              ↓               ↓                    ↓              ↓
Natural Language   AI Analysis    Schema Check      TCP Command    Supabase DB
     ↓              ↓               ↓                    ↓              ↓
"Make it rain"   →  Commands   →   Validation   →    Execution   →   Session Update
```

### Data Flow
1. **User Input**: Natural language or direct API calls
2. **NLP Processing**: Convert to structured commands (optional)
3. **Validation**: Parameter validation and preprocessing
4. **Execution**: Send to Unreal Engine via TCP
5. **Storage**: Store complete interaction in database
6. **Context**: Available for future interactions

## 📊 Response Format Examples

### Successful Command
```json
{
  "status": "success",
  "message": "Actor created successfully",
  "data": {
    "actor_name": "TestCube_001",
    "location": {"x": 0, "y": 0, "z": 0}
  }
}
```

### Failed Command
```json
{
  "status": "error", 
  "error": "Actor not found",
  "details": {
    "error_code": "ACTOR_NOT_FOUND",
    "searched_name": "NonExistent"
  }
}
```

### NLP Response
```json
{
  "explanation": "Creating a red light in the scene",
  "commands": [{"type": "create_light", "params": {...}}],
  "executionResults": [
    {
      "command": "create_light",
      "success": true,
      "result": {...}
    }
  ]
}
```

## 🛠️ Development Tools

### JSON Schema Validation
Use the provided JSON schemas with your IDE for:
- ✅ Auto-completion
- ✅ Type checking  
- ✅ Validation
- ✅ Documentation tooltips

### Database Tools
The SQL schema includes:
- ✅ Performance indexes
- ✅ Cleanup functions
- ✅ Analysis views
- ✅ Security policies

### Testing Utilities
Example queries and test data for:
- ✅ Session management
- ✅ Command execution
- ✅ Error handling
- ✅ Performance testing

## 📚 Related Documentation

- **Project Root**: [CLAUDE.md](../../CLAUDE.md) - Project overview and setup
- **Student Guide**: [STUDENT_COMMAND_GUIDE_UPDATED.md](../STUDENT_COMMAND_GUIDE_UPDATED.md) - Adding new commands
- **Best Practices**: [unreal_mcp_best_practices.md](unreal_mcp_best_practices.md) - Development guidelines

## 🤝 Contributing

When adding new features:
1. Update relevant schema documentation
2. Add examples to the documentation
3. Update JSON schemas if data structures change
4. Test with provided validation tools

This comprehensive documentation ensures consistent development and integration across the Unreal MCP system.