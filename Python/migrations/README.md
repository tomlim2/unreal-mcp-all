# Database Migrations

This directory contains SQL migration files for the image datatable system.

## Migration Files

### 001_create_images_table.sql
- Creates the `images` table for centralized image management
- Adds indexes for performance (session_id, created_at, is_styled)
- Sets up JSONB meta field for flexible metadata storage

### 002_enhance_sessions_table.sql
- Enhances existing `user_sessions` table with new columns
- Adds foreign key constraint between images and sessions
- Creates triggers for automatic image_count updates
- Adds performance indexes

## Running Migrations

### Manual Execution (Supabase Dashboard)
1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy and paste each migration file in order
4. Execute the SQL

### Programmatic Execution
```python
from tools.ai.image_management import run_migrations
run_migrations()  # Runs all pending migrations
```

## Schema Overview

### images table
```sql
- image_id (TEXT PRIMARY KEY)     -- "img_20250911_215503"
- image_url (TEXT NOT NULL)       -- "/screenshots/img_20250911_215503.png"
- is_styled (BOOLEAN)             -- false for screenshots, true for styled
- session_id (TEXT)               -- FK to user_sessions
- meta (JSONB)                    -- {parent_id, style_info, dimensions, etc.}
- created_at (TIMESTAMP)          -- Auto-set creation time
```

### Enhanced user_sessions table
```sql
- session_id (TEXT PRIMARY KEY)   -- Existing
- context (JSONB)                 -- Existing conversation/scene data
- created_at (TIMESTAMP)          -- Existing
- updated_at (TIMESTAMP)          -- Existing
- session_name (TEXT)             -- NEW: Human-readable name
- llm_model (TEXT)                -- NEW: Preferred model (default: gemini-2)
- last_activity (TIMESTAMP)       -- NEW: Last activity timestamp
- image_count (INTEGER)           -- NEW: Auto-updated image count
- message_count (INTEGER)         -- NEW: Message count for analytics
```

## Features

- **Automatic Image Counting**: Triggers keep image_count in sync
- **Cascade Deletion**: Deleting a session removes all its images
- **Performance Indexes**: Optimized for gallery queries
- **Flexible Metadata**: JSONB field supports any image-related data
- **Foreign Key Integrity**: Ensures data consistency