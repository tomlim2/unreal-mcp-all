-- Add llm_model column to chat_context table with gemini-2 as default
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'chat_context' 
        AND column_name = 'llm_model'
    ) THEN
        ALTER TABLE chat_context ADD COLUMN llm_model TEXT DEFAULT 'gemini-2';
        
        -- Update existing rows to have the default value
        UPDATE chat_context SET llm_model = 'gemini-2' WHERE llm_model IS NULL;
        
        -- Add index for llm_model queries
        CREATE INDEX IF NOT EXISTS idx_chat_context_llm_model 
        ON chat_context(llm_model);
        
        -- Add comment
        COMMENT ON COLUMN chat_context.llm_model IS 'LLM model preference (gemini, gemini-2, claude)';
        
        RAISE NOTICE 'Added llm_model column to chat_context table with default gemini-2';
    ELSE
        RAISE NOTICE 'llm_model column already exists in chat_context table';
    END IF;
END $$;

-- Query to check if the column was added successfully
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'chat_context' 
AND column_name IN ('session_name', 'llm_model');

-- Query to see current llm_model values
SELECT session_id, llm_model, created_at 
FROM chat_context 
ORDER BY created_at DESC 
LIMIT 10;