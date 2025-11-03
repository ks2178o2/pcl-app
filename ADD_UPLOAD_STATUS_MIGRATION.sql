-- Add upload_status column to call_records table for failed upload tracking
-- This migration is optional - the code has fallback logic if this column doesn't exist

ALTER TABLE public.call_records 
ADD COLUMN IF NOT EXISTS upload_status TEXT DEFAULT 'pending' 
CHECK (upload_status IN ('pending', 'uploading', 'completed', 'failed'));

-- Add indexes for querying failed uploads efficiently
CREATE INDEX IF NOT EXISTS idx_call_records_upload_status 
ON public.call_records(upload_status);

CREATE INDEX IF NOT EXISTS idx_call_records_user_upload_status 
ON public.call_records(user_id, upload_status);

-- Update existing records to have 'completed' status if they have audio files
UPDATE public.call_records 
SET upload_status = 'completed' 
WHERE audio_file_url IS NOT NULL 
  AND upload_status IS NULL;

