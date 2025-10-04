# NLP Module Refactoring Plan

**Status**: 📋 Planned (Not Started)
**Priority**: Medium
**Estimated Effort**: 4-6 hours
**Risk Level**: Medium (requires careful testing)

---

## Current State Analysis

### File: `tools/ai/nlp.py`
- **Total Lines**: 995
- **Functions**: 10
- **Main Issues**:
  - ❌ Monolithic structure (single responsibility principle violated)
  - ❌ 300-line system prompt hardcoded in function
  - ❌ Mixed concerns (JSON parsing, session management, prompt building, image processing)
  - ❌ Difficult to test individual components
  - ❌ Hard to maintain prompt documentation

### Function Breakdown

| Function | Lines | Responsibility | Target Module |
|----------|-------|----------------|---------------|
| `_attempt_json_completion` | 57 | Fix incomplete JSON responses | `json_utils.py` |
| `_resolve_image_path` | 39 | Resolve screenshot paths | `image_processor.py` |
| `_extract_from_partial_response` | 117 | Parse partial AI responses | `json_utils.py` |
| `_auto_assign_latest_image_if_needed` | 48 | Session image fallback | `session_handler.py` |
| `_extract_style_essence` | 46 | Token optimization for styles | `session_handler.py` |
| `_process_images_for_commands` | 43 | Inject images into commands | `image_processor.py` |
| `_process_natural_language_impl` | 246 | Main NLP processing logic | `processor.py` |
| `process_natural_language` | 14 | Public API wrapper | `processor.py` |
| `build_system_prompt_with_session` | 295 | System prompt construction | `prompt_builder.py` |
| `execute_command_direct` | 32 | Direct command execution | `processor.py` |

---

## Proposed Architecture

### New Structure: Convert to Package

```
tools/ai/nlp/
├── __init__.py                    # Public API exports
├── processor.py                   # Main NLP processing (150 lines)
├── prompt_builder.py              # System prompt construction (350 lines)
├── json_utils.py                  # JSON parsing utilities (100 lines)
├── image_processor.py             # Image handling (80 lines)
├── session_handler.py             # Session management (60 lines)
└── model_config.py                # Model selection (40 lines)
```

### Module Specifications

#### 1. `__init__.py` (~20 lines)
**Purpose**: Public API surface

```python
"""
NLP Package for MegaMelange.

Provides natural language processing for Unreal Engine command generation.
"""

from .processor import process_natural_language, execute_command_direct

__all__ = [
    'process_natural_language',
    'execute_command_direct'
]
```

**Exports**:
- `process_natural_language()` - Main entry point (backward compatible)
- `execute_command_direct()` - Direct command execution

---

#### 2. `processor.py` (~150 lines)
**Purpose**: Core NLP processing orchestration

**Functions**:
- `process_natural_language()` - Public wrapper (error handling)
- `_process_natural_language_impl()` - Main processing logic
- `execute_command_direct()` - Execute single command

**Dependencies**:
```python
from .prompt_builder import build_system_prompt
from .json_utils import attempt_json_completion, extract_from_partial_response
from .image_processor import process_images_for_commands
from .session_handler import get_or_create_session, extract_style_essence
from .model_config import get_default_model, get_model_provider
from ..command_handlers import get_command_registry
```

**Responsibilities**:
- Orchestrate the NLP pipeline
- Manage conversation flow
- Execute commands via registry
- Return structured responses

---

#### 3. `prompt_builder.py` (~350 lines)
**Purpose**: System prompt construction and management

**Functions**:
- `build_system_prompt(context, session_context, is_style_request)` - Main builder
- `_build_minimal_prompt()` - Optimized for style requests
- `_build_full_prompt()` - Complete command documentation
- `_get_command_examples()` - Korean/English examples
- `_get_decision_flowchart()` - Command selection logic

**Constants**:
```python
MINIMAL_STYLE_PROMPT = """..."""
COMMAND_CATEGORIES = {...}
PARAMETER_RULES = {...}
DECISION_EXAMPLES = {...}
```

**Responsibilities**:
- Generate appropriate prompts based on request type
- Minimize token usage for style requests (75% reduction)
- Maintain command documentation
- Provide decision flowcharts

**Why Separate**:
- Prompts change frequently during development
- Easy to A/B test different prompt structures
- Command documentation can be auto-generated from registry
- Enables prompt versioning

---

#### 4. `json_utils.py` (~100 lines)
**Purpose**: JSON parsing and completion utilities

**Functions**:
- `attempt_json_completion(incomplete_json)` - Fix truncated JSON
- `extract_from_partial_response(partial_response)` - Parse partial AI output
- `_find_last_complete_structure(content)` - Helper for completion
- `_complete_missing_braces(content)` - Helper for completion

**Responsibilities**:
- Handle incomplete AI responses gracefully
- Fix common JSON formatting issues
- Extract valid structures from partial responses

**Why Separate**:
- Pure utility functions (no dependencies)
- Easy to unit test with test cases
- Reusable across different AI integrations

---

#### 5. `image_processor.py` (~80 lines)
**Purpose**: Image path resolution and command injection

**Functions**:
- `resolve_image_path(filename)` - Find screenshot in Unreal project
- `process_images_for_commands(commands, target_uid, main_data, refs)` - Inject images
- `_get_supported_image_commands()` - List of image-compatible commands

**Dependencies**:
```python
from core.utils.path_manager import get_path_manager
```

**Responsibilities**:
- Resolve screenshot paths from Unreal project
- Inject image data into appropriate commands
- Support both UID and user-uploaded images

**Why Separate**:
- Image handling is a distinct concern
- Path resolution logic can be reused
- Easier to add new image sources

---

#### 6. `session_handler.py` (~60 lines)
**Purpose**: Session context and optimization

**Functions**:
- `get_or_create_session(session_id)` - Session management
- `extract_style_essence(user_input, provider)` - Token optimization
- `auto_assign_latest_image(command, session_context)` - Image fallback

**Dependencies**:
```python
from core.session import get_session_manager
```

**Responsibilities**:
- Manage session lifecycle
- Optimize prompts for token usage
- Auto-assign latest images from session history

**Why Separate**:
- Session logic is independent of NLP processing
- Easy to swap session storage implementations
- Clear separation of concerns

---

#### 7. `model_config.py` (~40 lines)
**Purpose**: Model provider selection and configuration

**Functions**:
- `get_default_model()` - Determine default model
- `get_model_provider(model_name)` - Instantiate provider
- `is_model_available(model_name)` - Check availability

**Dependencies**:
```python
from ..model_providers import ClaudeProvider, GeminiProvider
```

**Constants**:
```python
MODEL_PRIORITY = ['gemini-2', 'claude-3-5-sonnet-20241022']
MODEL_PROVIDERS = {
    'gemini-2': GeminiProvider,
    'claude-3-5-sonnet-20241022': ClaudeProvider
}
```

**Responsibilities**:
- Select appropriate model provider
- Check API key availability
- Handle model fallbacks

**Why Separate**:
- Model configuration changes frequently
- Easy to add new providers
- Clear model selection logic

---

## Migration Strategy

### Phase 1: Preparation (30 min)
1. ✅ Create `/tools/ai/nlp/` directory
2. ✅ Backup current `nlp.py` → `nlp_legacy.py`
3. ✅ Create empty module files with docstrings

### Phase 2: Extract Utilities (1 hour)
1. ✅ Implement `json_utils.py`
   - Copy `_attempt_json_completion`
   - Copy `_extract_from_partial_response`
   - Remove `_` prefix (now public in module)
   - Add unit tests

2. ✅ Implement `model_config.py`
   - Extract model selection logic
   - Create provider factory
   - Add model availability checks

### Phase 3: Extract Image Handling (45 min)
1. ✅ Implement `image_processor.py`
   - Copy `_resolve_image_path`
   - Copy `_process_images_for_commands`
   - Update imports to use `core.utils.path_manager`

### Phase 4: Extract Session Logic (45 min)
1. ✅ Implement `session_handler.py`
   - Copy `_extract_style_essence`
   - Copy `_auto_assign_latest_image_if_needed`
   - Extract session retrieval logic

### Phase 5: Extract Prompt Building (1.5 hours)
1. ✅ Implement `prompt_builder.py`
   - Copy entire `build_system_prompt_with_session` function
   - Split into minimal/full prompt builders
   - Organize constants and templates
   - **This is the largest and most critical module**

### Phase 6: Main Processor (1 hour)
1. ✅ Implement `processor.py`
   - Copy `process_natural_language`
   - Copy `_process_natural_language_impl`
   - Copy `execute_command_direct`
   - Update imports to use new modules

### Phase 7: Public API (15 min)
1. ✅ Implement `__init__.py`
   - Export public functions
   - Add backward compatibility notes

### Phase 8: Update Imports (30 min)
1. ✅ Find all files importing from `tools.ai.nlp`
2. ✅ Update imports (should be minimal due to `__init__.py`)
3. ✅ Verify no breaking changes

### Phase 9: Testing (1 hour)
1. ✅ Unit test each module
2. ✅ Integration test full NLP pipeline
3. ✅ Test with both Gemini and Claude
4. ✅ Test with/without session context
5. ✅ Test with/without images
6. ✅ Test error handling

### Phase 10: Cleanup (15 min)
1. ✅ Remove `nlp.py` (keep `nlp_legacy.py` for reference)
2. ✅ Update documentation
3. ✅ Commit changes

---

## Files That Import from nlp.py

**Current Import Pattern**:
```python
from tools.ai.nlp import process_natural_language
```

**Files to Update** (minimal changes due to `__init__.py`):
- `api/http/handlers/nlp_handler.py`
- Any MCP tools using NLP

**Backward Compatibility**: ✅
The new `__init__.py` exports the same `process_natural_language()` function, so existing code continues to work.

---

## Testing Checklist

### Unit Tests (Per Module)

**json_utils.py**:
- [ ] Test complete JSON completion
- [ ] Test partial response extraction
- [ ] Test malformed JSON handling
- [ ] Test edge cases (empty strings, very long strings)

**model_config.py**:
- [ ] Test default model selection
- [ ] Test provider instantiation
- [ ] Test model availability checks
- [ ] Test fallback logic

**image_processor.py**:
- [ ] Test path resolution (Unreal screenshots)
- [ ] Test image injection into commands
- [ ] Test UID vs user-uploaded images
- [ ] Test missing image handling

**session_handler.py**:
- [ ] Test session creation/retrieval
- [ ] Test style essence extraction
- [ ] Test auto-assign latest image
- [ ] Test session without images

**prompt_builder.py**:
- [ ] Test minimal prompt generation
- [ ] Test full prompt generation
- [ ] Test with/without session context
- [ ] Test Korean/English examples
- [ ] Test command documentation

**processor.py**:
- [ ] Test full NLP pipeline
- [ ] Test error handling
- [ ] Test command execution
- [ ] Test response formatting

### Integration Tests

- [ ] Process simple style request ("cyberpunk style")
- [ ] Process Unreal command ("set time to 1800")
- [ ] Process with reference images
- [ ] Process with session context
- [ ] Process with invalid input
- [ ] Process with unavailable model
- [ ] Process with partial AI response

---

## Benefits of Refactoring

### Code Quality
✅ **Single Responsibility** - Each module has one clear purpose
✅ **DRY Principle** - Reusable components across codebase
✅ **Testability** - Easy to unit test individual functions
✅ **Readability** - 150-line files vs 995-line monolith

### Maintainability
✅ **Prompt Updates** - Change only `prompt_builder.py`
✅ **Model Changes** - Change only `model_config.py`
✅ **Image Handling** - Change only `image_processor.py`
✅ **Clear Dependencies** - Easy to see what depends on what

### Extensibility
✅ **New Models** - Add to `model_config.py` only
✅ **New Commands** - Registry auto-updates prompt
✅ **New Image Sources** - Extend `image_processor.py`
✅ **Prompt Versioning** - A/B test different prompts

### Performance
✅ **Token Optimization** - Isolated in `session_handler.py`
✅ **Minimal Imports** - Only load what's needed
✅ **Caching Opportunities** - Session/model caching clearer

---

## Risks and Mitigation

### Risk 1: Breaking Changes
**Mitigation**:
- Keep `nlp_legacy.py` as backup
- Maintain same public API via `__init__.py`
- Comprehensive integration tests

### Risk 2: Import Cycles
**Mitigation**:
- Clear dependency hierarchy (no circular imports)
- Use dependency injection where needed
- Import only what's necessary

### Risk 3: Subtle Behavior Changes
**Mitigation**:
- Copy functions exactly (don't refactor logic yet)
- Test with real API calls (Gemini + Claude)
- Compare outputs before/after

### Risk 4: Increased Complexity
**Mitigation**:
- Clear module documentation
- Keep public API simple (`__init__.py`)
- Good naming conventions

---

## Success Criteria

✅ All existing NLP tests pass
✅ No breaking changes to public API
✅ Each module has unit tests
✅ Code coverage maintained or improved
✅ Prompt updates take <5 minutes
✅ Adding new models takes <10 minutes
✅ File count: 7 modules vs 1 monolith
✅ Average file size: <200 lines

---

## Future Enhancements (Post-Refactoring)

1. **Prompt Templates** - Move prompts to YAML/JSON files
2. **Prompt Versioning** - A/B test different prompt structures
3. **Command Auto-Documentation** - Generate from registry
4. **Streaming Responses** - Add streaming support to processor
5. **Caching** - Cache prompts and model responses
6. **Metrics** - Add token usage tracking per module

---

## Notes

- This refactoring does NOT change functionality
- Same inputs → same outputs
- Focus on structure, not behavior
- Test extensively before removing legacy code
- Keep migration atomic (all-or-nothing)

---

**Last Updated**: 2025-10-05
**Status**: Ready for Implementation
**Assigned To**: TBD
