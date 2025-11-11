-- Migration: Add call_type field for granular call classification
-- Adds call_type field alongside call_category to support more granular categorization
-- call_category: consult_scheduled, consult_not_scheduled (success/failure)
-- call_type: scheduling, pricing, directions, billing, complaint, transfer_to_office, general_question, reschedule, confirming_existing_appointment, cancellation (granular category)

-- Add call_type column to call_records table
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

-- Create index for call_type for better query performance
CREATE INDEX IF NOT EXISTS idx_call_records_call_type ON call_records(call_type);

-- Add comment to clarify the difference between call_category and call_type
COMMENT ON COLUMN call_records.call_category IS 'High-level categorization: consult_scheduled (appointment was scheduled), consult_not_scheduled (no appointment scheduled), or other_question';
COMMENT ON COLUMN call_records.call_type IS 'Granular call type: scheduling, pricing, directions, billing, complaint, transfer_to_office, general_question, reschedule, confirming_existing_appointment, or cancellation';

