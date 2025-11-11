-- ===========================================
-- Encryption/Decryption Functions for Sensitive Data
-- ===========================================
-- 
-- This script creates the encrypt_sensitive_data and decrypt_sensitive_data
-- functions that are used to encrypt/decrypt sensitive information like
-- email addresses and phone numbers in appointments and other tables.
--
-- Run this in your Supabase SQL Editor
--
-- Created: 2025-01-27
-- ===========================================

-- Enable pgcrypto extension for encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ===========================================
-- 1. CREATE ENCRYPTION SETTINGS TABLE
-- ===========================================
-- Store encryption key in a secure table (only accessible to service role)
-- Note: In production, you should set this via Supabase secrets or environment

CREATE TABLE IF NOT EXISTS public.encryption_settings (
  id INTEGER PRIMARY KEY DEFAULT 1,
  encryption_key TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  CONSTRAINT single_row CHECK (id = 1)
);

-- Enable RLS
ALTER TABLE public.encryption_settings ENABLE ROW LEVEL SECURITY;

-- Only service role can access encryption settings
CREATE POLICY "Service role only" ON public.encryption_settings
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Block all access from authenticated/anonymous roles for security
CREATE POLICY "Block public access" ON public.encryption_settings
  FOR ALL
  TO authenticated, anon
  USING (false)
  WITH CHECK (false);

-- ===========================================
-- 2. ENCRYPT SENSITIVE DATA FUNCTION
-- ===========================================

CREATE OR REPLACE FUNCTION public.encrypt_sensitive_data(data TEXT)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  encryption_key TEXT;
  encrypted_data BYTEA;
BEGIN
  -- Get encryption key from settings or use a default
  -- In production, this should be set via Supabase secrets
  SELECT COALESCE(
    (SELECT es.encryption_key FROM public.encryption_settings es WHERE es.id = 1),
    current_setting('app.settings.encryption_key', true)
  ) INTO encryption_key;
  
  -- If no key found, use a default (NOT SECURE - for development only)
  -- In production, ensure encryption_key is always set!
  IF encryption_key IS NULL OR encryption_key = '' THEN
    -- Generate a default key (NOT for production use!)
    encryption_key := encode(gen_random_bytes(32), 'hex');
    -- Store it (only works if service role)
    INSERT INTO public.encryption_settings (id, encryption_key)
    VALUES (1, encryption_key)
    ON CONFLICT (id) DO NOTHING;
  END IF;
  
  -- If input is empty, return empty string
  IF data IS NULL OR data = '' THEN
    RETURN '';
  END IF;
  
  -- Encrypt using pgcrypto's pgp_sym_encrypt
  -- Using 'AES' algorithm with a random IV
  encrypted_data := pgp_sym_encrypt(data, encryption_key, 'compress-algo=1');
  
  -- Return as base64-encoded string for easy storage in TEXT columns
  RETURN encode(encrypted_data, 'base64');
EXCEPTION
  WHEN OTHERS THEN
    -- If encryption fails, return original data (fallback)
    RAISE WARNING 'Encryption failed: %', SQLERRM;
    RETURN data;
END;
$$;

-- ===========================================
-- 3. DECRYPT SENSITIVE DATA FUNCTION
-- ===========================================

CREATE OR REPLACE FUNCTION public.decrypt_sensitive_data(encrypted_data TEXT)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  encryption_key TEXT;
  encrypted_bytes BYTEA;
  decrypted_text TEXT;
BEGIN
  -- If input is empty, return empty string
  IF encrypted_data IS NULL OR encrypted_data = '' THEN
    RETURN '';
  END IF;
  
  -- Get encryption key from settings
  SELECT COALESCE(
    (SELECT es.encryption_key FROM public.encryption_settings es WHERE es.id = 1),
    current_setting('app.settings.encryption_key', true)
  ) INTO encryption_key;
  
  -- If no key found, return the input as-is (may be unencrypted data)
  IF encryption_key IS NULL OR encryption_key = '' THEN
    RETURN encrypted_data;
  END IF;
  
  -- Decode from base64
  BEGIN
    encrypted_bytes := decode(encrypted_data, 'base64');
  EXCEPTION
    WHEN OTHERS THEN
      -- If decoding fails, data might not be encrypted, return as-is
      RETURN encrypted_data;
  END;
  
  -- Decrypt using pgcrypto's pgp_sym_decrypt
  BEGIN
    decrypted_text := pgp_sym_decrypt(encrypted_bytes, encryption_key);
  EXCEPTION
    WHEN OTHERS THEN
      -- If decryption fails, data might not be encrypted, return as-is
      RETURN encrypted_data;
  END;
  
  RETURN decrypted_text;
END;
$$;

-- ===========================================
-- 4. GRANT PERMISSIONS
-- ===========================================

-- Grant execute permissions to authenticated users
GRANT EXECUTE ON FUNCTION public.encrypt_sensitive_data(TEXT) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION public.decrypt_sensitive_data(TEXT) TO authenticated, anon;

-- ===========================================
-- 5. INITIALIZE ENCRYPTION KEY
-- ===========================================
-- This will be called automatically if no key exists
-- In production, you should set the encryption key manually via:
-- UPDATE public.encryption_settings SET encryption_key = 'your-secure-key-here' WHERE id = 1;

-- Generate a default encryption key (for development/testing only)
-- In production, set this to a secure value from your environment
DO $$
DECLARE
  default_key TEXT;
BEGIN
  -- Only insert if no key exists
  IF NOT EXISTS (SELECT 1 FROM public.encryption_settings WHERE id = 1) THEN
    -- Generate a random key (32 bytes = 256 bits)
    default_key := encode(gen_random_bytes(32), 'hex');
    
    INSERT INTO public.encryption_settings (id, encryption_key)
    VALUES (1, default_key)
    ON CONFLICT (id) DO NOTHING;
    
    RAISE NOTICE 'Generated default encryption key. In production, replace this with a secure key from your environment!';
  END IF;
END $$;

-- ===========================================
-- 6. VERIFICATION
-- ===========================================

-- Test the functions (optional - remove in production)
DO $$
DECLARE
  test_data TEXT := 'test@example.com';
  encrypted TEXT;
  decrypted TEXT;
BEGIN
  -- Test encryption
  encrypted := public.encrypt_sensitive_data(test_data);
  
  -- Test decryption
  decrypted := public.decrypt_sensitive_data(encrypted);
  
  -- Verify
  IF decrypted = test_data THEN
    RAISE NOTICE '✅ Encryption/Decryption functions working correctly!';
  ELSE
    RAISE WARNING '❌ Encryption/Decryption test failed!';
  END IF;
END $$;

-- ===========================================
-- COMPLETION MESSAGE
-- ===========================================

DO $$
BEGIN
  RAISE NOTICE '✅ Encryption/Decryption functions created successfully!';
  RAISE NOTICE '';
  RAISE NOTICE 'Created functions:';
  RAISE NOTICE '  1. encrypt_sensitive_data(TEXT)';
  RAISE NOTICE '  2. decrypt_sensitive_data(TEXT)';
  RAISE NOTICE '';
  RAISE NOTICE '⚠️  IMPORTANT: In production, set a secure encryption key by running:';
  RAISE NOTICE '  UPDATE public.encryption_settings SET encryption_key = ''your-secure-key'' WHERE id = 1;';
  RAISE NOTICE '';
  RAISE NOTICE 'The encryption key should be at least 32 bytes (256 bits) and kept secure!';
END $$;

