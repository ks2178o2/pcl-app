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

export const useAllContactPreferences = () => {
  const [preferences, setPreferences] = useState<ContactPreferences[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchAllPreferences();
    } else {
      setPreferences([]);
      setLoading(false);
    }
  }, [user]);

  const fetchAllPreferences = async () => {
    if (!user) return;

    setLoading(true);
    try {
      const { data, error } = await supabase
        .from('contact_preferences')
        .select('*')
        .eq('user_id', user.id)
        .order('updated_at', { ascending: false });

      if (error) {
        console.error('Error fetching contact preferences:', error);
      } else {
        setPreferences(data || []);
      }
    } catch (error) {
      console.error('Error fetching contact preferences:', error);
    } finally {
      setLoading(false);
    }
  };

  const updatePreferences = async (id: string, updates: Partial<ContactPreferences>) => {
    if (!user) return { error: 'User not found' };

    try {
      const { data, error } = await supabase
        .from('contact_preferences')
        .update(updates)
        .eq('id', id)
        .eq('user_id', user.id)
        .select()
        .single();

      if (error) throw error;

      // Update local state
      setPreferences(prev => 
        prev.map(pref => pref.id === id ? data : pref)
      );

      return { data, error: null };
    } catch (error) {
      console.error('Error updating contact preferences:', error);
      return { data: null, error };
    }
  };

  const deletePreferences = async (id: string) => {
    if (!user) return { error: 'User not found' };

    try {
      const { error } = await supabase
        .from('contact_preferences')
        .delete()
        .eq('id', id)
        .eq('user_id', user.id);

      if (error) throw error;

      // Update local state
      setPreferences(prev => prev.filter(pref => pref.id !== id));

      return { error: null };
    } catch (error) {
      console.error('Error deleting contact preferences:', error);
      return { error };
    }
  };

  return {
    preferences,
    loading,
    updatePreferences,
    deletePreferences,
    refetch: fetchAllPreferences
  };
};