import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

export interface EmailActivity {
  id: string;
  user_id: string;
  call_record_id: string;
  recipient_email: string;
  recipient_name: string;
  subject: string;
  email_content: string;
  email_type: string;
  sent_at: string;
  opened_at?: string;
  first_open_at?: string;
  total_opens: number;
  total_read_time_seconds: number;
  last_engagement_at?: string;
  delivery_status: string;
  tracking_pixel_id: string;
  created_at: string;
  updated_at: string;
}

export const useEmailActivities = (callRecordId?: string) => {
  const [activities, setActivities] = useState<EmailActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  const fetchActivities = async () => {
    if (!user) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      let query = supabase
        .from('email_activities')
        .select('*')
        .eq('user_id', user.id)
        .order('sent_at', { ascending: false });

      if (callRecordId) {
        query = query.eq('call_record_id', callRecordId);
      }

      const { data, error: fetchError } = await query;

      if (fetchError) {
        throw fetchError;
      }

      setActivities(data || []);
    } catch (err: any) {
      console.error('Error fetching email activities:', err);
      setError(err.message || 'Failed to fetch email activities');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActivities();
  }, [user, callRecordId]);

  // Set up real-time subscription for activity updates
  useEffect(() => {
    if (!user) return;

    const channel = supabase
      .channel('email_activities_changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'email_activities',
          filter: `user_id=eq.${user.id}${callRecordId ? ` and call_record_id=eq.${callRecordId}` : ''}`
        },
        (payload) => {
          console.log('Email activity updated:', payload);
          fetchActivities(); // Refetch to get updated data
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [user, callRecordId]);

  const getEngagementStats = () => {
    const totalSent = activities.length;
    const totalOpened = activities.filter(a => a.total_opens > 0).length;
    const totalReadTime = activities.reduce((sum, a) => sum + a.total_read_time_seconds, 0);
    const averageReadTime = totalSent > 0 ? totalReadTime / totalSent : 0;
    const openRate = totalSent > 0 ? (totalOpened / totalSent) * 100 : 0;

    return {
      totalSent,
      totalOpened,
      totalReadTime,
      averageReadTime,
      openRate
    };
  };

  return {
    activities,
    loading,
    error,
    refetch: fetchActivities,
    stats: getEngagementStats()
  };
};