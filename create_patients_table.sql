-- Create patients table for Sales Angel Buddy
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS patients (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  full_name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  friendly_id TEXT,
  organization_id UUID REFERENCES organizations(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create user_roles table (also missing)
CREATE TABLE IF NOT EXISTS user_roles (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL,
  organization_id UUID REFERENCES organizations(id),
  role TEXT NOT NULL DEFAULT 'salesperson',
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add RLS policies for patients table
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see patients from their organization
CREATE POLICY "Users can view patients from their organization" ON patients
  FOR SELECT USING (
    organization_id IN (
      SELECT organization_id FROM profiles WHERE user_id = auth.uid()
    )
  );

-- Policy: Users can insert patients for their organization
CREATE POLICY "Users can insert patients for their organization" ON patients
  FOR INSERT WITH CHECK (
    organization_id IN (
      SELECT organization_id FROM profiles WHERE user_id = auth.uid()
    )
  );

-- Policy: Users can update patients from their organization
CREATE POLICY "Users can update patients from their organization" ON patients
  FOR UPDATE USING (
    organization_id IN (
      SELECT organization_id FROM profiles WHERE user_id = auth.uid()
    )
  );

-- Policy: Users can delete patients from their organization
CREATE POLICY "Users can delete patients from their organization" ON patients
  FOR DELETE USING (
    organization_id IN (
      SELECT organization_id FROM profiles WHERE user_id = auth.uid()
    )
  );

-- Add RLS policies for user_roles table
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own roles
CREATE POLICY "Users can view their own roles" ON user_roles
  FOR SELECT USING (user_id = auth.uid());

-- Policy: Users can view roles in their organization
CREATE POLICY "Users can view roles in their organization" ON user_roles
  FOR SELECT USING (
    organization_id IN (
      SELECT organization_id FROM profiles WHERE user_id = auth.uid()
    )
  );

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_patients_organization_id ON patients(organization_id);
CREATE INDEX IF NOT EXISTS idx_patients_full_name ON patients(full_name);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_organization_id ON user_roles(organization_id);

-- Add some sample patients for testing
INSERT INTO patients (full_name, email, phone, friendly_id, organization_id) VALUES
  ('John Doe', 'john.doe@example.com', '+1-555-0123', 'P001', (SELECT id FROM organizations LIMIT 1)),
  ('Jane Smith', 'jane.smith@example.com', '+1-555-0124', 'P002', (SELECT id FROM organizations LIMIT 1)),
  ('Bob Johnson', 'bob.johnson@example.com', '+1-555-0125', 'P003', (SELECT id FROM organizations LIMIT 1))
ON CONFLICT DO NOTHING;
