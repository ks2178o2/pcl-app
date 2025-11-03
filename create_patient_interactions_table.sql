-- Create patient_interactions table to track all patient touchpoints
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS patient_interactions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
  patient_name TEXT NOT NULL, -- Denormalized for easier querying
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  
  -- Interaction details
  interaction_type TEXT NOT NULL CHECK (interaction_type IN (
    'call',
    'email',
    'sms',
    'webform',
    'walk_in',
    'online_inquiry',
    'referral',
    'social_media',
    'appointment',
    'consultation',
    'follow_up'
  )),
  
  -- Optional references to related records
  call_record_id UUID REFERENCES call_records(id) ON DELETE SET NULL,
  appointment_id UUID REFERENCES appointments(id) ON DELETE SET NULL,
  email_activity_id UUID REFERENCES email_activities(id) ON DELETE SET NULL,
  
  -- Interaction metadata
  interaction_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  notes TEXT,
  outcome TEXT, -- e.g., 'scheduled', 'no_show', 'converted', 'pending'
  metadata JSONB, -- Flexible storage for additional data
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_patient_interactions_patient_id ON patient_interactions(patient_id);
CREATE INDEX IF NOT EXISTS idx_patient_interactions_patient_name ON patient_interactions(patient_name);
CREATE INDEX IF NOT EXISTS idx_patient_interactions_user_id ON patient_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_patient_interactions_organization_id ON patient_interactions(organization_id);
CREATE INDEX IF NOT EXISTS idx_patient_interactions_type ON patient_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_patient_interactions_date ON patient_interactions(interaction_date);
CREATE INDEX IF NOT EXISTS idx_patient_interactions_call_record_id ON patient_interactions(call_record_id);
CREATE INDEX IF NOT EXISTS idx_patient_interactions_appointment_id ON patient_interactions(appointment_id);

-- Enable RLS
ALTER TABLE patient_interactions ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Users can view interactions from their organization
CREATE POLICY "Users can view interactions from their organization" ON patient_interactions
  FOR SELECT USING (
    organization_id IN (
      SELECT organization_id FROM profiles WHERE user_id = auth.uid()
    )
  );

-- Users can create interactions for their organization
CREATE POLICY "Users can create interactions for their organization" ON patient_interactions
  FOR INSERT WITH CHECK (
    organization_id IN (
      SELECT organization_id FROM profiles WHERE user_id = auth.uid()
    ) AND user_id = auth.uid()
  );

-- Users can update interactions from their organization
CREATE POLICY "Users can update interactions from their organization" ON patient_interactions
  FOR UPDATE USING (
    organization_id IN (
      SELECT organization_id FROM profiles WHERE user_id = auth.uid()
    ) AND user_id = auth.uid()
  );

-- Users can delete interactions from their organization
CREATE POLICY "Users can delete interactions from their organization" ON patient_interactions
  FOR DELETE USING (
    organization_id IN (
      SELECT organization_id FROM profiles WHERE user_id = auth.uid()
    ) AND user_id = auth.uid()
  );

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_patient_interactions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at on row update
CREATE TRIGGER update_patient_interactions_updated_at
  BEFORE UPDATE ON patient_interactions
  FOR EACH ROW
  EXECUTE FUNCTION update_patient_interactions_updated_at();

-- Function to automatically create interaction records from call_records
CREATE OR REPLACE FUNCTION sync_call_records_to_interactions()
RETURNS TRIGGER AS $$
BEGIN
  -- Only create interaction if recording is complete
  IF NEW.recording_complete = true THEN
    INSERT INTO patient_interactions (
      patient_id,
      patient_name,
      user_id,
      organization_id,
      interaction_type,
      call_record_id,
      interaction_date,
      metadata
    )
    VALUES (
      NEW.patient_id,
      NEW.customer_name,
      NEW.user_id,
      (SELECT organization_id FROM profiles WHERE user_id = NEW.user_id LIMIT 1),
      'call',
      NEW.id,
      NEW.start_time,
      jsonb_build_object(
        'duration_seconds', NEW.duration_seconds,
        'has_transcript', CASE WHEN NEW.transcript IS NOT NULL THEN true ELSE false END
      )
    )
    ON CONFLICT DO NOTHING; -- Prevent duplicates
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to sync call_records to patient_interactions
DROP TRIGGER IF EXISTS trigger_sync_call_records_to_interactions ON call_records;
CREATE TRIGGER trigger_sync_call_records_to_interactions
  AFTER INSERT OR UPDATE ON call_records
  FOR EACH ROW
  WHEN (NEW.recording_complete = true)
  EXECUTE FUNCTION sync_call_records_to_interactions();

-- Function to automatically create interaction records from appointments
CREATE OR REPLACE FUNCTION sync_appointments_to_interactions()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO patient_interactions (
    patient_id,
    patient_name,
    user_id,
    organization_id,
    interaction_type,
    appointment_id,
    interaction_date,
    metadata
  )
  VALUES (
    NEW.patient_id,
    NEW.customer_name,
    NEW.user_id,
    NEW.organization_id,
    CASE 
      WHEN NEW.type ILIKE '%consult%' THEN 'consultation'
      WHEN NEW.type ILIKE '%follow%' THEN 'follow_up'
      ELSE 'appointment'
    END,
    NEW.id,
    COALESCE(NEW.appointment_date, NEW.created_at),
    jsonb_build_object(
      'status', NEW.status,
      'type', NEW.type,
      'duration_minutes', NEW.duration_minutes
    )
  )
  ON CONFLICT DO NOTHING; -- Prevent duplicates
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to sync appointments to patient_interactions
DROP TRIGGER IF EXISTS trigger_sync_appointments_to_interactions ON appointments;
CREATE TRIGGER trigger_sync_appointments_to_interactions
  AFTER INSERT ON appointments
  FOR EACH ROW
  EXECUTE FUNCTION sync_appointments_to_interactions();

COMMENT ON TABLE patient_interactions IS 'Tracks all patient touchpoints and interactions across all channels';
COMMENT ON COLUMN patient_interactions.interaction_type IS 'Type of interaction: call, email, sms, webform, walk_in, online_inquiry, referral, social_media, appointment, consultation, follow_up';
COMMENT ON COLUMN patient_interactions.metadata IS 'Flexible JSONB storage for interaction-specific data';
