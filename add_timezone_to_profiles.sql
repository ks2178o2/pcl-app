-- Add timezone column to profiles table
-- Run this in Supabase SQL Editor

ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS timezone TEXT DEFAULT 'America/Los_Angeles';

-- Add comment
COMMENT ON COLUMN profiles.timezone IS 'User preferred timezone (IANA timezone name, e.g., America/Los_Angeles)';

-- Create index for faster lookups (optional)
CREATE INDEX IF NOT EXISTS idx_profiles_timezone ON profiles(timezone);

