-- Supabase schema for MegaMelange worker infrastructure
-- Execute this in your Supabase SQL editor to create the required tables

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Screenshot jobs table for worker pattern
CREATE TABLE IF NOT EXISTS screenshot_jobs (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT,
    job_type TEXT NOT NULL CHECK (job_type IN ('screenshot', 'rendering', 'batch_screenshot')),
    status TEXT NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')),
    params JSONB DEFAULT '{}',
    result JSONB DEFAULT NULL,
    error TEXT DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_screenshot_jobs_session_id ON screenshot_jobs(session_id);
CREATE INDEX IF NOT EXISTS idx_screenshot_jobs_status ON screenshot_jobs(status);
CREATE INDEX IF NOT EXISTS idx_screenshot_jobs_job_type ON screenshot_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_screenshot_jobs_created_at ON screenshot_jobs(created_at);

-- Create a function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_screenshot_jobs_updated_at ON screenshot_jobs;
CREATE TRIGGER update_screenshot_jobs_updated_at
    BEFORE UPDATE ON screenshot_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) - Optional but recommended
-- ALTER TABLE screenshot_jobs ENABLE ROW LEVEL SECURITY;

-- Create policies if you want to restrict access by session_id or other criteria
-- Example policy (uncomment and modify as needed):
-- CREATE POLICY "Users can view their own jobs" ON screenshot_jobs
--     FOR SELECT USING (session_id = current_user_id());

-- Example queries to test the schema:
-- 
-- Insert a test job:
-- INSERT INTO screenshot_jobs (job_type, session_id, status, params) 
-- VALUES ('screenshot', 'test-session-123', 'pending', '{"resolution_multiplier": 2.0}');
-- 
-- Query active jobs:
-- SELECT * FROM screenshot_jobs WHERE status IN ('pending', 'in_progress');
-- 
-- Update job status:
-- UPDATE screenshot_jobs SET status = 'completed', result = '{"filename": "test.png"}' WHERE job_id = 'your-job-id';

-- Cleanup function to remove old completed jobs (optional)
CREATE OR REPLACE FUNCTION cleanup_old_jobs(max_age_days INTEGER DEFAULT 7)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM screenshot_jobs 
    WHERE status IN ('completed', 'failed', 'cancelled')
    AND updated_at < NOW() - INTERVAL '1 day' * max_age_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Example: Run cleanup for jobs older than 7 days
-- SELECT cleanup_old_jobs(7);