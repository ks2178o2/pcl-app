-- ============================================================================
-- Migration: Add call_type field for granular call classification
-- ============================================================================
-- This migration adds the call_type field to the call_records table to support
-- more granular call categorization alongside the existing call_category field.
--
-- call_category (existing): High-level success/failure status
--   - consult_scheduled: Appointment was successfully scheduled
--   - consult_not_scheduled: Call ended without scheduling
--   - other_question: General question or inquiry
--
-- call_type (new): Granular category describing what the call was about
--   - scheduling: Call about scheduling a new appointment
--   - pricing: Call about pricing, costs, or payment options
--   - directions: Call asking for directions or location information
--   - billing: Call about billing issues, invoices, or payment problems
--   - complaint: Call expressing a complaint or dissatisfaction
--   - transfer_to_office: Call requesting to be transferred to an office/department
--   - general_question: General inquiry or question
--   - reschedule: Call to reschedule an existing appointment
--   - confirming_existing_appointment: Call to confirm an existing appointment
--   - cancellation: Call to cancel an appointment or service
--
-- ============================================================================

-- Step 1: Add call_type column to call_records table
-- This column is nullable to allow existing records to remain valid
ALTER TABLE call_records 
ADD COLUMN IF NOT EXISTS call_type TEXT CHECK (call_type IN (
    'scheduling',
    'pricing',
    'directions',
    'billing',
    'complaint',
    'transfer_to_office',
    'general_question',
    'reschedule',
    'confirming_existing_appointment',
    'cancellation'
));

-- Step 2: Create index for call_type for better query performance
-- This index is essential for filtering and aggregation queries
CREATE INDEX IF NOT EXISTS idx_call_records_call_type ON call_records(call_type);

-- Step 3: Create composite index for common query patterns
-- This index optimizes queries that filter by both category and type
CREATE INDEX IF NOT EXISTS idx_call_records_category_type 
ON call_records(call_category, call_type);

-- Step 4: Create index for time-based analytics with call_type
-- This index optimizes queries that analyze call_type trends over time
CREATE INDEX IF NOT EXISTS idx_call_records_type_created 
ON call_records(call_type, created_at) 
WHERE call_type IS NOT NULL;

-- Step 5: Add comments to clarify the difference between call_category and call_type
COMMENT ON COLUMN call_records.call_category IS 
'High-level categorization indicating success/failure status: consult_scheduled (appointment was scheduled), consult_not_scheduled (no appointment scheduled), or other_question (general inquiry)';

COMMENT ON COLUMN call_records.call_type IS 
'Granular call type describing what the call was about: scheduling, pricing, directions, billing, complaint, transfer_to_office, general_question, reschedule, confirming_existing_appointment, or cancellation';

-- Step 6: Verify the migration
-- This query should return 0 rows if the migration is successful
DO $$
BEGIN
    -- Check if column exists
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'call_records' 
        AND column_name = 'call_type'
    ) THEN
        RAISE EXCEPTION 'call_type column was not created successfully';
    END IF;
    
    -- Check if indexes exist
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_indexes 
        WHERE tablename = 'call_records' 
        AND indexname = 'idx_call_records_call_type'
    ) THEN
        RAISE EXCEPTION 'idx_call_records_call_type index was not created successfully';
    END IF;
    
    RAISE NOTICE 'Migration completed successfully: call_type column and indexes created';
END $$;

