-- Migration: Bulk Import Module Schema
-- Creates tables for bulk audio import, call categorization, and objection tracking

-- Table for tracking bulk import jobs
CREATE TABLE IF NOT EXISTS bulk_import_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    customer_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    storage_bucket_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'discovering', 'converting', 'uploading', 'analyzing', 'completed', 'failed')),
    total_files INTEGER DEFAULT 0,
    processed_files INTEGER DEFAULT 0,
    failed_files INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Table for tracking individual files in bulk import
CREATE TABLE IF NOT EXISTS bulk_import_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES bulk_import_jobs(id) ON DELETE CASCADE,
    call_record_id UUID REFERENCES call_records(id) ON DELETE SET NULL,
    file_name TEXT NOT NULL,
    original_url TEXT NOT NULL,
    storage_path TEXT,
    file_size BIGINT,
    file_format TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'downloading', 'converting', 'uploading', 'transcribing', 'analyzing', 'categorized', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Extend call_records table with bulk import and categorization fields
ALTER TABLE call_records 
ADD COLUMN IF NOT EXISTS bulk_import_job_id UUID REFERENCES bulk_import_jobs(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS call_category TEXT CHECK (call_category IN ('consult_not_scheduled', 'consult_scheduled', 'other_question')),
ADD COLUMN IF NOT EXISTS categorization_confidence DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS categorization_notes TEXT;

-- Table for storing call objections
CREATE TABLE IF NOT EXISTS call_objections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_record_id UUID NOT NULL REFERENCES call_records(id) ON DELETE CASCADE,
    objection_type TEXT NOT NULL CHECK (objection_type IN ('safety-risk', 'cost-value', 'timing', 'social-concerns', 'provider-trust', 'results-skepticism', 'other')),
    objection_text TEXT NOT NULL,
    speaker TEXT,
    confidence DECIMAL(3,2),
    transcript_segment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing objection overcome details (only for scheduled consult calls)
CREATE TABLE IF NOT EXISTS objection_overcome_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_record_id UUID NOT NULL REFERENCES call_records(id) ON DELETE CASCADE,
    objection_id UUID REFERENCES call_objections(id) ON DELETE CASCADE,
    overcome_method TEXT NOT NULL,
    transcript_quote TEXT NOT NULL,
    speaker TEXT,
    confidence DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_bulk_import_jobs_user_id ON bulk_import_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_bulk_import_jobs_status ON bulk_import_jobs(status);
CREATE INDEX IF NOT EXISTS idx_bulk_import_jobs_customer_name ON bulk_import_jobs(customer_name);
CREATE INDEX IF NOT EXISTS idx_bulk_import_files_job_id ON bulk_import_files(job_id);
CREATE INDEX IF NOT EXISTS idx_bulk_import_files_call_record_id ON bulk_import_files(call_record_id);
CREATE INDEX IF NOT EXISTS idx_bulk_import_files_status ON bulk_import_files(status);
CREATE INDEX IF NOT EXISTS idx_call_records_bulk_import_job_id ON call_records(bulk_import_job_id);
CREATE INDEX IF NOT EXISTS idx_call_records_call_category ON call_records(call_category);
CREATE INDEX IF NOT EXISTS idx_call_objections_call_record_id ON call_objections(call_record_id);
CREATE INDEX IF NOT EXISTS idx_objection_overcome_details_call_record_id ON objection_overcome_details(call_record_id);
CREATE INDEX IF NOT EXISTS idx_objection_overcome_details_objection_id ON objection_overcome_details(objection_id);

-- RLS Policies
ALTER TABLE bulk_import_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE bulk_import_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_objections ENABLE ROW LEVEL SECURITY;
ALTER TABLE objection_overcome_details ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own bulk import jobs
CREATE POLICY "Users can view their own bulk import jobs"
    ON bulk_import_jobs FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can create bulk import jobs
CREATE POLICY "Users can create bulk import jobs"
    ON bulk_import_jobs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own bulk import jobs
CREATE POLICY "Users can update their own bulk import jobs"
    ON bulk_import_jobs FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy: Users can view files from their own jobs
CREATE POLICY "Users can view files from their own jobs"
    ON bulk_import_files FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM bulk_import_jobs
            WHERE bulk_import_jobs.id = bulk_import_files.job_id
            AND bulk_import_jobs.user_id = auth.uid()
        )
    );

-- Policy: Users can insert files for their own jobs
CREATE POLICY "Users can insert files for their own jobs"
    ON bulk_import_files FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM bulk_import_jobs
            WHERE bulk_import_jobs.id = bulk_import_files.job_id
            AND bulk_import_jobs.user_id = auth.uid()
        )
    );

-- Policy: Users can update files from their own jobs
CREATE POLICY "Users can update files from their own jobs"
    ON bulk_import_files FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM bulk_import_jobs
            WHERE bulk_import_jobs.id = bulk_import_files.job_id
            AND bulk_import_jobs.user_id = auth.uid()
        )
    );

-- Policy: Users can view objections for their own call records
CREATE POLICY "Users can view objections for their own calls"
    ON call_objections FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM call_records
            WHERE call_records.id = call_objections.call_record_id
            AND call_records.user_id = auth.uid()
        )
    );

-- Policy: Users can insert objections for their own call records
CREATE POLICY "Users can insert objections for their own calls"
    ON call_objections FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM call_records
            WHERE call_records.id = call_objections.call_record_id
            AND call_records.user_id = auth.uid()
        )
    );

-- Policy: Users can view objection overcome details for their own call records
CREATE POLICY "Users can view objection overcome details for their own calls"
    ON objection_overcome_details FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM call_records
            WHERE call_records.id = objection_overcome_details.call_record_id
            AND call_records.user_id = auth.uid()
        )
    );

-- Policy: Users can insert objection overcome details for their own call records
CREATE POLICY "Users can insert objection overcome details for their own calls"
    ON objection_overcome_details FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM call_records
            WHERE call_records.id = objection_overcome_details.call_record_id
            AND call_records.user_id = auth.uid()
        )
    );

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_bulk_import_jobs_updated_at BEFORE UPDATE ON bulk_import_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bulk_import_files_updated_at BEFORE UPDATE ON bulk_import_files
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

