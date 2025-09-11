-- Migration: Enhance user_sessions table for better performance and image integration
-- Created: 2025-09-11
-- Description: Adds metadata columns and foreign key constraints

-- Add new columns to existing user_sessions table
ALTER TABLE user_sessions 
ADD COLUMN IF NOT EXISTS session_name TEXT,
ADD COLUMN IF NOT EXISTS llm_model TEXT DEFAULT 'gemini-2',
ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS image_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0;

-- Update existing records to have default llm_model if null
UPDATE user_sessions 
SET llm_model = 'gemini-2' 
WHERE llm_model IS NULL;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_sessions_activity ON user_sessions(last_activity);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON user_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_model ON user_sessions(llm_model);

-- Add foreign key constraint from images to user_sessions
ALTER TABLE images 
ADD CONSTRAINT fk_images_session 
FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) 
ON DELETE CASCADE;

-- Add trigger to automatically update image_count in user_sessions
CREATE OR REPLACE FUNCTION update_session_image_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE user_sessions 
        SET image_count = image_count + 1,
            last_activity = NOW()
        WHERE session_id = NEW.session_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE user_sessions 
        SET image_count = GREATEST(0, image_count - 1),
            last_activity = NOW()
        WHERE session_id = OLD.session_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
DROP TRIGGER IF EXISTS trigger_update_image_count ON images;
CREATE TRIGGER trigger_update_image_count
    AFTER INSERT OR DELETE ON images
    FOR EACH ROW
    EXECUTE FUNCTION update_session_image_count();

-- Add comments
COMMENT ON COLUMN user_sessions.session_name IS 'Human-readable session name';
COMMENT ON COLUMN user_sessions.llm_model IS 'Preferred LLM model (gemini, gemini-2, claude)';
COMMENT ON COLUMN user_sessions.last_activity IS 'Timestamp of last session activity';
COMMENT ON COLUMN user_sessions.image_count IS 'Auto-updated count of images in this session';
COMMENT ON COLUMN user_sessions.message_count IS 'Count of messages in conversation';