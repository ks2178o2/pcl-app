-- Fix follow_up_messages table schema to support JSONB storage
-- Run this in your Supabase SQL Editor

-- 1. Add message_data JSONB column (for storing full message data)
ALTER TABLE follow_up_messages
  ADD COLUMN IF NOT EXISTS message_data JSONB;

-- 2. Add message_type column (required, used by our code)
ALTER TABLE follow_up_messages
  ADD COLUMN IF NOT EXISTS message_type TEXT;

-- Make message_type required if it's new, or ensure it has a default
DO $$
BEGIN
  -- If message_type was just added, set a default for existing rows
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'follow_up_messages'
      AND column_name = 'message_type'
      AND column_default IS NULL
  ) THEN
    -- Set default for existing rows (use 'email' as default)
    UPDATE follow_up_messages
    SET message_type = 'email'
    WHERE message_type IS NULL;
    
    -- Make it NOT NULL with default
    ALTER TABLE follow_up_messages
      ALTER COLUMN message_type SET NOT NULL,
      ALTER COLUMN message_type SET DEFAULT 'email';
  END IF;
END$$;

-- 3. Make 'content' column nullable (if it exists and is required)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'follow_up_messages'
      AND column_name = 'content'
      AND is_nullable = 'NO'
  ) THEN
    ALTER TABLE follow_up_messages ALTER COLUMN content DROP NOT NULL;
  END IF;
END$$;

-- 4. Make optional columns nullable (they're stored in message_data JSONB anyway)
DO $$
DECLARE
  col_name TEXT;
BEGIN
  FOR col_name IN 
    SELECT column_name FROM information_schema.columns
    WHERE table_name = 'follow_up_messages'
      AND column_name IN (
        'message_content', 'channel_type', 'subject_line', 
        'call_to_action', 'personalization_notes', 'tone',
        'estimated_send_time'
      )
      AND is_nullable = 'NO'
      AND column_name NOT IN ('id', 'follow_up_plan_id', 'user_id', 'message_type', 'status', 'created_at', 'updated_at')
  LOOP
    EXECUTE format('ALTER TABLE follow_up_messages ALTER COLUMN %I DROP NOT NULL', col_name);
  END LOOP;
END$$;

-- 5. Add missing optional columns if they don't exist (for backward compatibility)
ALTER TABLE follow_up_messages
  ADD COLUMN IF NOT EXISTS message_content TEXT,
  ADD COLUMN IF NOT EXISTS channel_type TEXT,
  ADD COLUMN IF NOT EXISTS subject_line TEXT,
  ADD COLUMN IF NOT EXISTS call_to_action TEXT,
  ADD COLUMN IF NOT EXISTS personalization_notes TEXT,
  ADD COLUMN IF NOT EXISTS tone TEXT,
  ADD COLUMN IF NOT EXISTS estimated_send_time TIMESTAMP WITH TIME ZONE;

-- 6. Reload PostgREST schema cache (critical!)
SELECT pg_notify('pgrst', 'reload schema');

-- 7. Verify the schema
SELECT 
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_name = 'follow_up_messages'
  AND column_name IN (
    'id', 'follow_up_plan_id', 'user_id', 'message_type', 'message_data',
    'message_content', 'channel_type', 'subject_line', 'call_to_action',
    'personalization_notes', 'tone', 'estimated_send_time', 'status',
    'created_at', 'updated_at', 'content'
  )
ORDER BY column_name;

