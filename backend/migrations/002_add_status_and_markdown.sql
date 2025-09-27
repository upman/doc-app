-- Migration 002: Add status and markdown_content fields to extractions table
-- Created: 2025-09-27

-- Add status field to track processing status
ALTER TABLE extractions ADD COLUMN status TEXT DEFAULT 'pending';

-- Add markdown_content field to store the converted markdown
ALTER TABLE extractions ADD COLUMN markdown_content TEXT;

-- Add filename field for better tracking
ALTER TABLE extractions ADD COLUMN filename TEXT;

-- Add file_size field
ALTER TABLE extractions ADD COLUMN file_size INTEGER;

-- Create index on status for filtering
CREATE INDEX IF NOT EXISTS idx_extractions_status ON extractions(status);
CREATE INDEX IF NOT EXISTS idx_extractions_filename ON extractions(filename);