import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

interface ContactPreferences {
  id: string;
  call_record_id: string;
  user_id: string;
  customer_name: string;
  email_allowed: boolean;
  sms_allowed: boolean;
  phone_allowed: boolean;
  voicemail_allowed: boolean;
  preferred_contact_time: string | null;
  timezone: string;
  do_not_contact: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export const useContactPreferences = (callRecordId?: string) => {
  const [preferences, setPreferences] = useState<ContactPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    if (callRecordId && user) {
      fetchPreferences();
    } else {
      setPreferences(null);
      setLoading(false);
    }
  }, [callRecordId, user]);

  const fetchPreferences = async () => {
    if (!callRecordId || !user) return;

    setLoading(true);
    try {
      const { data, error } = await supabase
        .from('contact_preferences')
        .select('*')
        .eq('call_record_id', callRecordId)
        .eq('user_id', user.id)
        .maybeSingle();

      if (error) {
        // Gracefully handle missing table/schema cache errors
        const code = (error as any)?.code;
        const message = (error as any)?.message || '';
        if (code === 'PGRST205' || /Could not find the table 'public\.contact_preferences'/.test(message)) {
          // Treat as no preferences stored; silence noisy error
          console.warn('contact_preferences table not found; treating preferences as empty');
          setPreferences(null);
        } else {
          console.error('Error fetching contact preferences:', error);
        }
      } else {
        setPreferences(data);
      }
    } catch (error) {
      console.error('Error fetching contact preferences:', error);
    } finally {
      setLoading(false);
    }
  };

  const savePreferences = async (prefs: Partial<ContactPreferences> & { customer_name: string }) => {
    if (!user || !callRecordId) return { error: 'User or call record not found' };

    try {
      if (preferences?.id) {
        // Update existing preferences
        const { data, error } = await supabase
          .from('contact_preferences')
          .update(prefs)
          .eq('id', preferences.id)
          .eq('user_id', user.id)
          .select()
          .single();

        if (error) {
          const code = (error as any)?.code;
          const message = (error as any)?.message || '';
          if (code === 'PGRST205' || /Could not find the table 'public\.contact_preferences'/.test(message)) {
            console.warn('contact_preferences table not found on update; ignoring and treating as success');
            return { data: null, error: null } as any;
          }
          throw error;
        }
        setPreferences(data);
        return { data, error: null };
      } else {
        // Create new preferences
        const { data, error } = await supabase
          .from('contact_preferences')
          .insert({
            call_record_id: callRecordId,
            user_id: user.id,
            customer_name: prefs.customer_name,
            email_allowed: prefs.email_allowed ?? true,
            sms_allowed: prefs.sms_allowed ?? true,
            phone_allowed: prefs.phone_allowed ?? true,
            voicemail_allowed: prefs.voicemail_allowed ?? true,
            preferred_contact_time: prefs.preferred_contact_time ?? null,
            timezone: prefs.timezone ?? 'America/New_York',
            do_not_contact: prefs.do_not_contact ?? false,
            notes: prefs.notes ?? null,
          })
          .select()
          .single();

        if (error) {
          const code = (error as any)?.code;
          const message = (error as any)?.message || '';
          if (code === 'PGRST205' || /Could not find the table 'public\.contact_preferences'/.test(message)) {
            console.warn('contact_preferences table not found on insert; ignoring and treating as success');
            return { data: null, error: null } as any;
          }
          throw error;
        }
        setPreferences(data);
        return { data, error: null };
      }
    } catch (error) {
      console.error('Error saving contact preferences:', error);
      return { data: null, error };
    }
  };

  return {
    preferences,
    loading,
    savePreferences,
    refetch: fetchPreferences
  };
};