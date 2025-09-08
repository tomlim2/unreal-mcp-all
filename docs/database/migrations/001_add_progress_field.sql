-- Migration: Add progress field to screenshot_jobs table
-- Date: 2025-01-04
-- Description: Add progress tracking for job execution

-- Add progress column if it doesn't exist
ALTER TABLE screenshot_jobs 
ADD COLUMN IF NOT EXISTS progress REAL DEFAULT 0.0 
CHECK (progress >= 0.0 AND progress <= 100.0);

-- Update existing jobs to have 0.0 progress if they don't have it
UPDATE screenshot_jobs 
SET progress = 0.0 
WHERE progress IS NULL;

-- Completed jobs should have 100% progress
UPDATE screenshot_jobs 
SET progress = 100.0 
WHERE status = 'completed' AND progress = 0.0;