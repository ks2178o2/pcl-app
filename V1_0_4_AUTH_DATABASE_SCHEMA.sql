-- ===========================================
-- v1.0.4 Authentication Enhancement Schema
-- Complete Database Foundation for Auth Features
-- ===========================================
-- 
-- This script creates all tables, columns, and triggers
-- needed for the v1.0.4 authentication enhancements:
-- 1. User invitations
-- 2. Login audit trail
-- 3. 2FA support
-- 4. Device management
-- 
-- Run this in your Supabase SQL Editor
--
-- Created: 2025-10-31
-- Version: 1.0.4
-- ===========================================

-- ===========================================
-- 1. USER INVITATIONS TABLE
-- ===========================================

CREATE TABLE IF NOT EXISTS public.user_invitations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT NOT NULL,
  organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
  role TEXT NOT NULL DEFAULT 'salesperson',
  center_ids TEXT[] DEFAULT '{}', -- Array of center IDs for multi-center assignment
  region_id UUID REFERENCES public.regions(id),
  invited_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  token TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'expired', 'cancelled')),
  expires_at TIMESTAMPTZ NOT NULL,
  accepted_at TIMESTAMPTZ,
  accepted_by UUID REFERENCES auth.users(id),
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for user_invitations
CREATE INDEX IF NOT EXISTS idx_invitations_email ON public.user_invitations(email);
CREATE INDEX IF NOT EXISTS idx_invitations_token ON public.user_invitations(token);
CREATE INDEX IF NOT EXISTS idx_invitations_org ON public.user_invitations(organization_id);
CREATE INDEX IF NOT EXISTS idx_invitations_status ON public.user_invitations(status);
CREATE INDEX IF NOT EXISTS idx_invitations_expires ON public.user_invitations(expires_at);

-- Enable RLS
ALTER TABLE public.user_invitations ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_invitations
-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view invitations for their organization" ON public.user_invitations;
DROP POLICY IF EXISTS "Admins can create invitations for their organization" ON public.user_invitations;
DROP POLICY IF EXISTS "Users can view their own invitations" ON public.user_invitations;
DROP POLICY IF EXISTS "Users can accept pending invitations" ON public.user_invitations;

CREATE POLICY "Users can view invitations for their organization"
ON public.user_invitations FOR SELECT
TO authenticated
USING (
  organization_id IN (
    SELECT organization_id FROM public.profiles WHERE user_id = auth.uid()
  )
);

CREATE POLICY "Admins can create invitations for their organization"
ON public.user_invitations FOR INSERT
TO authenticated
WITH CHECK (
  organization_id IN (
    SELECT organization_id FROM public.profiles WHERE user_id = auth.uid()
  )
  AND invited_by = auth.uid()
);

CREATE POLICY "Users can view their own invitations"
ON public.user_invitations FOR SELECT
TO authenticated
USING (email = (SELECT email FROM auth.users WHERE id = auth.uid()));

CREATE POLICY "Users can accept pending invitations"
ON public.user_invitations FOR UPDATE
TO authenticated
USING (email = (SELECT email FROM auth.users WHERE id = auth.uid()))
WITH CHECK (status IN ('pending', 'accepted'));

-- ===========================================
-- 2. LOGIN AUDIT TABLE
-- ===========================================

CREATE TABLE IF NOT EXISTS public.login_audit (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  organization_id UUID REFERENCES public.organizations(id),
  ip_address INET,
  user_agent TEXT,
  device_fingerprint TEXT,
  device_name TEXT,
  login_method TEXT NOT NULL CHECK (login_method IN ('password', 'magic_link', '2fa_code')),
  status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'blocked')),
  failure_reason TEXT,
  location_data JSONB DEFAULT '{}'::jsonb,
  session_id TEXT,
  login_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  logout_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for login_audit
CREATE INDEX IF NOT EXISTS idx_login_audit_user ON public.login_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_login_audit_org ON public.login_audit(organization_id);
CREATE INDEX IF NOT EXISTS idx_login_audit_method ON public.login_audit(login_method);
CREATE INDEX IF NOT EXISTS idx_login_audit_status ON public.login_audit(status);
CREATE INDEX IF NOT EXISTS idx_login_audit_date ON public.login_audit(login_at DESC);
CREATE INDEX IF NOT EXISTS idx_login_audit_ip ON public.login_audit(ip_address);

-- Enable RLS
ALTER TABLE public.login_audit ENABLE ROW LEVEL SECURITY;

-- RLS Policies for login_audit
DROP POLICY IF EXISTS "Users can view their own login history" ON public.login_audit;
DROP POLICY IF EXISTS "Service role can insert login audit" ON public.login_audit;
DROP POLICY IF EXISTS "Admins can view their org's login history" ON public.login_audit;

CREATE POLICY "Users can view their own login history"
ON public.login_audit FOR SELECT
TO authenticated
USING (user_id = auth.uid());

CREATE POLICY "Service role can insert login audit"
ON public.login_audit FOR INSERT
TO authenticated
WITH CHECK (true); -- Will be filtered by application logic

CREATE POLICY "Admins can view their org's login history"
ON public.login_audit FOR SELECT
TO authenticated
USING (
  organization_id IN (
    SELECT organization_id FROM public.profiles WHERE user_id = auth.uid()
  )
  AND EXISTS (
    SELECT 1 FROM public.user_roles 
    WHERE user_id = auth.uid() 
    AND role IN ('org_admin', 'system_admin')
  )
);

-- ===========================================
-- 3. USER DEVICES TABLE (for 2FA)
-- ===========================================

CREATE TABLE IF NOT EXISTS public.user_devices (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  device_name TEXT NOT NULL,
  device_id TEXT NOT NULL UNIQUE, -- Unique device fingerprint
  verified_at TIMESTAMPTZ NOT NULL,
  last_used_at TIMESTAMPTZ DEFAULT NOW(),
  is_primary BOOLEAN DEFAULT false,
  trust_score INTEGER DEFAULT 0 CHECK (trust_score >= 0 AND trust_score <= 100),
  ip_address INET,
  user_agent TEXT,
  two_factor_code_hash TEXT, -- Stored for SMS-based 2FA
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for user_devices
CREATE INDEX IF NOT EXISTS idx_user_devices_user ON public.user_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_user_devices_device_id ON public.user_devices(device_id);
CREATE INDEX IF NOT EXISTS idx_user_devices_primary ON public.user_devices(user_id, is_primary) WHERE is_primary = true;

-- Enable RLS
ALTER TABLE public.user_devices ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_devices
DROP POLICY IF EXISTS "Users can view their own devices" ON public.user_devices;
DROP POLICY IF EXISTS "Users can insert their own devices" ON public.user_devices;
DROP POLICY IF EXISTS "Users can update their own devices" ON public.user_devices;
DROP POLICY IF EXISTS "Users can delete their own devices" ON public.user_devices;

CREATE POLICY "Users can view their own devices"
ON public.user_devices FOR SELECT
TO authenticated
USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own devices"
ON public.user_devices FOR INSERT
TO authenticated
WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own devices"
ON public.user_devices FOR UPDATE
TO authenticated
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can delete their own devices"
ON public.user_devices FOR DELETE
TO authenticated
USING (user_id = auth.uid());

-- ===========================================
-- 4. ALTER PROFILES TABLE (add 2FA fields)
-- ===========================================

DO $$ 
BEGIN
  -- Add two_factor_enabled column if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'profiles' 
    AND column_name = 'two_factor_enabled'
  ) THEN
    ALTER TABLE public.profiles ADD COLUMN two_factor_enabled BOOLEAN DEFAULT false;
  END IF;

  -- Add two_factor_secret column if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'profiles' 
    AND column_name = 'two_factor_secret'
  ) THEN
    ALTER TABLE public.profiles ADD COLUMN two_factor_secret TEXT;
  END IF;

  -- Add verified_devices column if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'profiles' 
    AND column_name = 'verified_devices'
  ) THEN
    ALTER TABLE public.profiles ADD COLUMN verified_devices JSONB DEFAULT '[]'::jsonb;
  END IF;

  -- Add last_login_ip column if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'profiles' 
    AND column_name = 'last_login_ip'
  ) THEN
    ALTER TABLE public.profiles ADD COLUMN last_login_ip INET;
  END IF;

  -- Add last_login_at column if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'profiles' 
    AND column_name = 'last_login_at'
  ) THEN
    ALTER TABLE public.profiles ADD COLUMN last_login_at TIMESTAMPTZ;
  END IF;
END $$;

-- ===========================================
-- 5. HELPER FUNCTIONS & TRIGGERS
-- ===========================================

-- Function to clean up expired invitations
CREATE OR REPLACE FUNCTION cleanup_expired_invitations()
RETURNS void AS $$
BEGIN
  UPDATE public.user_invitations
  SET status = 'expired', updated_at = NOW()
  WHERE status = 'pending'
    AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to automatically set updated_at timestamp
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for user_invitations updated_at
DROP TRIGGER IF EXISTS trigger_user_invitations_updated_at ON public.user_invitations;
CREATE TRIGGER trigger_user_invitations_updated_at
  BEFORE UPDATE ON public.user_invitations
  FOR EACH ROW
  EXECUTE FUNCTION set_updated_at();

-- Trigger for user_devices updated_at
DROP TRIGGER IF EXISTS trigger_user_devices_updated_at ON public.user_devices;
CREATE TRIGGER trigger_user_devices_updated_at
  BEFORE UPDATE ON public.user_devices
  FOR EACH ROW
  EXECUTE FUNCTION set_updated_at();

-- Note: OAuth removed from v1.0.4 - profile creation handled via Supabase Auth triggers

-- ===========================================
-- 6. VIEWS FOR EASIER ACCESS
-- ===========================================

-- View for active invitations
CREATE OR REPLACE VIEW public.active_invitations AS
SELECT 
  i.id,
  i.email,
  i.organization_id,
  o.name as organization_name,
  i.role,
  i.center_ids,
  r.name as region_name,
  i.status,
  i.expires_at,
  i.invited_by,
  inviter.email as inviter_email,
  i.created_at
FROM public.user_invitations i
JOIN public.organizations o ON i.organization_id = o.id
LEFT JOIN public.regions r ON i.region_id = r.id
LEFT JOIN auth.users inviter ON i.invited_by = inviter.id
WHERE i.status = 'pending'
  AND i.expires_at > NOW();

-- View for recent login history
CREATE OR REPLACE VIEW public.recent_logins AS
SELECT 
  la.id,
  la.user_id,
  p.salesperson_name,
  la.organization_id,
  o.name as organization_name,
  la.login_method,
  la.status,
  la.ip_address,
  la.device_name,
  la.login_at,
  la.location_data
FROM public.login_audit la
LEFT JOIN public.profiles p ON la.user_id = p.user_id
LEFT JOIN public.organizations o ON la.organization_id = o.id
ORDER BY la.login_at DESC
LIMIT 100;

-- ===========================================
-- 7. GRANT PERMISSIONS
-- ===========================================

GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_invitations TO authenticated;
GRANT SELECT, INSERT ON public.login_audit TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_devices TO authenticated;
GRANT SELECT ON public.active_invitations TO authenticated;
GRANT SELECT ON public.recent_logins TO authenticated;

-- ===========================================
-- COMPLETION MESSAGE
-- ===========================================

DO $$
BEGIN
  RAISE NOTICE '✅ v1.0.4 Authentication schema created successfully!';
  RAISE NOTICE '';
  RAISE NOTICE 'Created tables:';
  RAISE NOTICE '  1. user_invitations';
  RAISE NOTICE '  2. login_audit';
  RAISE NOTICE '  3. user_devices';
  RAISE NOTICE '';
  RAISE NOTICE 'Altered tables:';
  RAISE NOTICE '  4. profiles (added 2FA fields)';
  RAISE NOTICE '';
  RAISE NOTICE 'Created views:';
  RAISE NOTICE '  5. active_invitations';
  RAISE NOTICE '  6. recent_logins';
  RAISE NOTICE '';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '  API integration tests and email notifications';
END $$;

