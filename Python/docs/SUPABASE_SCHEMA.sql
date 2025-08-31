-- Unreal MCP Supabase Database Schema
-- Complete database schema for session management and context storage

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===============================================
-- MAIN CHAT CONTEXT TABLE
-- ===============================================

CREATE TABLE IF NOT EXISTS chat_context (
    -- Primary key
    id SERIAL PRIMARY KEY,
    
    -- Session identification
    session_id TEXT UNIQUE NOT NULL,
    
    -- Complete session context as JSON
    -- Contains: conversation_history, scene_state, user_preferences, metadata
    context JSONB NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    
    -- Metadata
    user_id TEXT,                    -- Optional user identifier
    client_version TEXT,             -- Client app version
    session_type TEXT DEFAULT 'interactive',  -- 'interactive', 'batch', 'api'
    
    -- Constraints
    CONSTRAINT valid_session_id CHECK (LENGTH(session_id) > 0),
    CONSTRAINT valid_context CHECK (jsonb_typeof(context) = 'object')
);

-- ===============================================
-- INDEXES FOR PERFORMANCE
-- ===============================================

-- Primary lookup index
CREATE INDEX IF NOT EXISTS idx_chat_context_session_id 
ON chat_context(session_id);

-- Session name index for searching
CREATE INDEX IF NOT EXISTS idx_chat_context_session_name 
ON chat_context(session_name);

-- Cleanup and maintenance indexes
CREATE INDEX IF NOT EXISTS idx_chat_context_last_accessed 
ON chat_context(last_accessed);

CREATE INDEX IF NOT EXISTS idx_chat_context_created_at 
ON chat_context(created_at);

-- User-based queries (if using user_id)
CREATE INDEX IF NOT EXISTS idx_chat_context_user_id 
ON chat_context(user_id) WHERE user_id IS NOT NULL;

-- Session type filtering
CREATE INDEX IF NOT EXISTS idx_chat_context_type 
ON chat_context(session_type);

-- ===============================================
-- JSONB INDEXES FOR CONTEXT QUERIES
-- ===============================================

-- Index for conversation history queries
CREATE INDEX IF NOT EXISTS idx_chat_context_conversation_history 
ON chat_context USING GIN ((context->'conversation_history'));

-- Index for scene state queries
CREATE INDEX IF NOT EXISTS idx_chat_context_scene_state 
ON chat_context USING GIN ((context->'scene_state'));

-- Index for user preferences
CREATE INDEX IF NOT EXISTS idx_chat_context_user_preferences 
ON chat_context USING GIN ((context->'user_preferences'));

-- ===============================================
-- HELPER FUNCTIONS
-- ===============================================

-- Function to update last_accessed timestamp automatically
CREATE OR REPLACE FUNCTION update_last_accessed()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update last_accessed on any update
CREATE TRIGGER trigger_update_last_accessed
    BEFORE UPDATE ON chat_context
    FOR EACH ROW
    EXECUTE FUNCTION update_last_accessed();

-- ===============================================
-- DATA VALIDATION FUNCTIONS
-- ===============================================

-- Validate session context structure
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
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Add validation constraint to table
ALTER TABLE chat_context 
ADD CONSTRAINT valid_session_context 
CHECK (validate_session_context(context));

-- ===============================================
-- CLEANUP FUNCTIONS
-- ===============================================

-- Function to cleanup expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions(
    max_age_days INTEGER DEFAULT 30
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
    cutoff_date TIMESTAMPTZ;
BEGIN
    cutoff_date := NOW() - (max_age_days || ' days')::INTERVAL;
    
    -- Delete expired sessions
    DELETE FROM chat_context 
    WHERE last_accessed < cutoff_date;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log the cleanup
    RAISE NOTICE 'Cleaned up % expired sessions older than % days', deleted_count, max_age_days;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup sessions by size (keep only N most recent per user)
CREATE OR REPLACE FUNCTION cleanup_sessions_by_count(
    max_sessions_per_user INTEGER DEFAULT 100
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Delete old sessions, keeping only the most recent N per user
    WITH sessions_to_delete AS (
        SELECT id
        FROM (
            SELECT id, user_id,
                   ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY last_accessed DESC) as rn
            FROM chat_context
            WHERE user_id IS NOT NULL
        ) ranked
        WHERE rn > max_sessions_per_user
    )
    DELETE FROM chat_context 
    WHERE id IN (SELECT id FROM sessions_to_delete);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RAISE NOTICE 'Cleaned up % sessions exceeding limit of % per user', deleted_count, max_sessions_per_user;
    
    return deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ===============================================
-- USEFUL QUERIES FOR ANALYSIS
-- ===============================================

-- View for session summary statistics
CREATE OR REPLACE VIEW session_stats AS
SELECT 
    COUNT(*) as total_sessions,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(EXTRACT(EPOCH FROM (last_accessed - created_at))/3600) as avg_session_duration_hours,
    MIN(created_at) as oldest_session,
    MAX(last_accessed) as most_recent_activity,
    AVG(jsonb_array_length(context->'conversation_history')) as avg_conversation_length
FROM chat_context;

-- View for recent activity
CREATE OR REPLACE VIEW recent_sessions AS
SELECT 
    session_id,
    user_id,
    session_type,
    jsonb_array_length(context->'conversation_history') as message_count,
    (context->'scene_state'->>'last_updated')::TIMESTAMPTZ as last_scene_update,
    created_at,
    last_accessed,
    EXTRACT(EPOCH FROM (last_accessed - created_at))/60 as duration_minutes
FROM chat_context
WHERE last_accessed > NOW() - INTERVAL '24 hours'
ORDER BY last_accessed DESC;

-- ===============================================
-- EXAMPLE QUERIES
-- ===============================================

-- Find all sessions with recent Unreal Engine commands
/*
SELECT 
    session_id,
    jsonb_path_query_array(
        context, 
        '$.conversation_history[*].execution_results[*] ? (@.success == true)'
    ) as successful_commands
FROM chat_context
WHERE context @@ '$.conversation_history[*].execution_results[*].success ? (@ == true)';
*/

-- Find sessions with specific actor types
/*
SELECT 
    session_id,
    context->'scene_state'->'actors' as scene_actors
FROM chat_context
WHERE context->'scene_state'->'actors' @> '[{"actor_class": "PointLight"}]';
*/

-- Find sessions with failed commands
/*
SELECT 
    session_id,
    jsonb_path_query_array(
        context,
        '$.conversation_history[*].execution_results[*] ? (@.success == false)'
    ) as failed_commands
FROM chat_context
WHERE context @@ '$.conversation_history[*].execution_results[*].success ? (@ == false)';
*/

-- ===============================================
-- ROW LEVEL SECURITY (RLS) SETUP
-- ===============================================

-- Enable RLS
ALTER TABLE chat_context ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own sessions
CREATE POLICY chat_context_policy ON chat_context
    FOR ALL USING (auth.uid()::TEXT = user_id);

-- Policy: Service role can access all sessions (for cleanup, etc.)
CREATE POLICY service_role_chat_context_policy ON chat_context
    FOR ALL USING (auth.role() = 'service_role');

-- ===============================================
-- TRIGGERS FOR AUTOMATIC MAINTENANCE
-- ===============================================

-- Trigger function to validate context on insert/update
CREATE OR REPLACE FUNCTION validate_context_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure session_id in context matches table session_id
    IF (NEW.context->>'session_id') != NEW.session_id THEN
        RAISE EXCEPTION 'Context session_id must match table session_id';
    END IF;
    
    -- Update context timestamps
    NEW.context = jsonb_set(
        NEW.context, 
        '{last_accessed}', 
        to_jsonb(NEW.last_accessed::TEXT)
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validate_context_before_write
    BEFORE INSERT OR UPDATE ON chat_context
    FOR EACH ROW
    EXECUTE FUNCTION validate_context_trigger();

-- ===============================================
-- SAMPLE DATA (for testing)
-- ===============================================

-- Insert sample session (uncomment to use)
/*
INSERT INTO chat_context (session_id, context, user_id, session_type) VALUES (
    'sample_session_001',
    '{
        "session_id": "sample_session_001",
        "conversation_history": [
            {
                "timestamp": "2024-01-01T10:00:00Z",
                "role": "user",
                "content": "Create a red light",
                "commands": [{"type": "create_mm_control_light", "params": {"light_name": "RedLight"}}],
                "execution_results": [{"command": "create_mm_control_light", "success": true, "result": {"status": "success"}}]
            }
        ],
        "scene_state": {
            "actors": [{"name": "RedLight", "actor_class": "PointLight"}],
            "lights": [{"name": "RedLight", "light_type": "PointLight", "intensity": 1000, "color": {"r": 255, "g": 0, "b": 0}}],
            "sky_settings": {},
            "last_commands": [],
            "last_updated": "2024-01-01T10:00:30Z"
        },
        "user_preferences": {},
        "metadata": {}
    }'::jsonb,
    'user_123',
    'interactive'
);
*/

-- ===============================================
-- MAINTENANCE PROCEDURES
-- ===============================================

-- Stored procedure for regular maintenance
CREATE OR REPLACE FUNCTION perform_session_maintenance()
RETURNS TEXT AS $$
DECLARE
    expired_count INTEGER;
    oversized_count INTEGER;
    result_text TEXT;
BEGIN
    -- Clean up expired sessions (older than 30 days)
    SELECT cleanup_expired_sessions(30) INTO expired_count;
    
    -- Clean up excess sessions (keep only 50 most recent per user)
    SELECT cleanup_sessions_by_count(50) INTO oversized_count;
    
    -- Analyze table for performance
    ANALYZE chat_context;
    
    result_text := format(
        'Maintenance completed: %s expired sessions deleted, %s excess sessions deleted',
        expired_count,
        oversized_count
    );
    
    RETURN result_text;
END;
$$ LANGUAGE plpgsql;

-- ===============================================
-- COMMENTS FOR DOCUMENTATION
-- ===============================================

COMMENT ON TABLE chat_context IS 'Stores complete chat session contexts for Unreal MCP conversations including chat history and scene state';
COMMENT ON COLUMN chat_context.session_id IS 'Unique session identifier, URL-safe string';
COMMENT ON COLUMN chat_context.session_name IS 'Human-readable name for the chat session';
COMMENT ON COLUMN chat_context.context IS 'Complete session data as JSON including conversation_history, scene_state, preferences';
COMMENT ON COLUMN chat_context.last_accessed IS 'Automatically updated timestamp for cleanup purposes';

-- ===============================================
-- GRANTS (adjust based on your security model)
-- ===============================================

-- Grant necessary permissions to application user
-- GRANT SELECT, INSERT, UPDATE, DELETE ON chat_context TO your_app_user;
-- GRANT USAGE ON SEQUENCE chat_context_id_seq TO your_app_user;