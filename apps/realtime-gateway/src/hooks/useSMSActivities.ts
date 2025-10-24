import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

export interface SMSActivity {
  id: string;
  user_id: string;
  call_record_id?: string;
  recipient_phone: string;
  recipient_name?: string;
  message_content: string;
  message_type: string;
  delivery_status: string;
  twilio_message_sid?: string;
  sent_at: string;
  delivered_at?: string;
  created_at: string;
  updated_at: string;
}

export const useSMSActivities = (callRecordId?: string) => {
  const [activities, setActivities] = useState<SMSActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  const fetchActivities = async () => {
    if (!user) return;

    try {
      setLoading(true);
      let query = supabase
        .from('sms_activities')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (callRecordId) {
        query = query.eq('call_record_id', callRecordId);
      }

      const { data, error } = await query;

      if (error) {
        console.error('Error fetching SMS activities:', error);
        return;
      }

      setActivities(data || []);
    } catch (error) {
      console.error('Error in fetchActivities:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActivities();
  }, [user, callRecordId]);

  return {
    activities,
    loading,
    refetch: fetchActivities
  };
};