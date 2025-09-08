-- Migration to add session_name column to chat_context table
-- This column is referenced in the code but missing from the original schema

-- Add session_name column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'chat_context' 
        AND column_name = 'session_name'
    ) THEN
        ALTER TABLE chat_context ADD COLUMN session_name TEXT;
        
        -- Add index for session name searches
        CREATE INDEX IF NOT EXISTS idx_chat_context_session_name 
        ON chat_context(session_name);
        
        -- Add comment
        COMMENT ON COLUMN chat_context.session_name IS 'Human-readable name for the chat session';
        
        -- Log the change
        RAISE NOTICE 'Added session_name column to chat_context table';
    ELSE
        RAISE NOTICE 'session_name column already exists in chat_context table';
    END IF;
END $$;

-- Update validation function to handle llm_model in context
CREATE OR REPLACE FUNCTION validate_session_context(ctx JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check required top-level fields
    IF NOT (ctx ? 'session_id' AND ctx ? 'conversation_history' AND ctx ? 'scene_state') THEN
        RETURN FALSE;
    END IF;
    
    -- Validate conversation_history is an array
    IF jsonb_typeof(ctx->'conversation_history') != 'array' THEN
        RETURN FALSE;
    END IF;
    
    -- Validate scene_state is an object
    IF jsonb_typeof(ctx->'scene_state') != 'object' THEN
        RETURN FALSE;
    END IF;
    
    -- Validate llm_model if present (should be text)
    IF ctx ? 'llm_model' AND jsonb_typeof(ctx->'llm_model') != 'string' THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Add GIN index for llm_model queries
CREATE INDEX IF NOT EXISTS idx_chat_context_llm_model 
ON chat_context USING GIN ((context->'llm_model'));

-- Example query to find sessions by preferred model
/*
-- Find all sessions using Claude model:
SELECT session_id, context->>'llm_model' as llm_model
FROM chat_context 
WHERE context->>'llm_model' = 'claude';

-- Find all sessions using Gemini models:
SELECT session_id, context->>'llm_model' as llm_model
FROM chat_context 
WHERE context->>'llm_model' LIKE 'gemini%';

-- Update a session's preferred model:
UPDATE chat_context 
SET context = jsonb_set(context, '{llm_model}', '"gemini-2"')
WHERE session_id = 'your_session_id';
*/