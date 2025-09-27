-- Migration 001: Initial schema for extractions and question results
-- Created: 2025-09-27

-- Create extractions table
CREATE TABLE IF NOT EXISTS extractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    questions TEXT, -- JSON array of questions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create question_results table
CREATE TABLE IF NOT EXISTS question_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    extraction_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    confidence REAL, -- Optional confidence score
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (extraction_id) REFERENCES extractions (id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_extractions_file_path ON extractions(file_path);
CREATE INDEX IF NOT EXISTS idx_extractions_created_at ON extractions(created_at);
CREATE INDEX IF NOT EXISTS idx_question_results_extraction_id ON question_results(extraction_id);
CREATE INDEX IF NOT EXISTS idx_question_results_created_at ON question_results(created_at);