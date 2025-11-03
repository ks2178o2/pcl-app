import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

export interface FailedUpload {
  id: string;
  customer_name: string;
  start_time: string;
  duration_seconds: number | null;
  created_at: string;
}

export const useFailedUploads = () => {
  const [failedUploads, setFailedUploads] = useState<FailedUpload[]>([]);
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();

  const loadFailedUploads = async () => {
    if (!user) return;

    setLoading(true);
    try {
      // Query for failed uploads - check upload_status column if it exists
      // Fallback to checking for recordings with no audio_file_url and recent timestamp
      const { data, error } = await supabase
        .from('call_records')
        .select('id, customer_name, start_time, duration_seconds, created_at')
        .eq('user_id', user.id)
        .eq('is_active', true)
        .or('upload_status.eq.failed,audio_file_url.is.null')
        .order('created_at', { ascending: false })
        .limit(50);

      if (error) {
        // If upload_status column doesn't exist, try without it
        const { data: fallbackData, error: fallbackError } = await supabase
          .from('call_records')
          .select('id, customer_name, start_time, duration_seconds, created_at')
          .eq('user_id', user.id)
          .eq('is_active', true)
          .is('audio_file_url', null)
          .order('created_at', { ascending: false })
          .limit(50);
        
        if (fallbackError) throw fallbackError;
        setFailedUploads((fallbackData || []) as FailedUpload[]);
      } else {
        setFailedUploads((data || []) as FailedUpload[]);
      }
    } catch (error) {
      console.error('Failed to load failed uploads:', error);
      setFailedUploads([]);
    } finally {
      setLoading(false);
    }
  };

  const retryUpload = async (callRecordId: string) => {
    console.log('Retrying upload for:', callRecordId);
    
    try {
      // Call edge function to trigger retry if it exists
      const { error } = await supabase.functions.invoke('retry-recording-upload', {
        body: { callRecordId }
      });

      if (error) {
        // If edge function doesn't exist, update status manually
        console.warn('Retry edge function not available, updating status manually');
        await supabase
          .from('call_records')
          .update({ upload_status: 'pending' } as any)
          .eq('id', callRecordId);
      }
      
      // Reload failed uploads
      await loadFailedUploads();
    } catch (error) {
      console.error('Failed to retry upload:', error);
      throw error;
    }
  };

  const deleteFailedUpload = async (callRecordId: string) => {
    try {
      await supabase
        .from('call_records')
        .update({ is_active: false } as any)
        .eq('id', callRecordId);

      await loadFailedUploads();
    } catch (error) {
      console.error('Failed to delete upload:', error);
      throw error;
    }
  };

  useEffect(() => {
    if (user) {
      loadFailedUploads();

      // Subscribe to real-time changes
      const channel = supabase
        .channel('failed-uploads-changes')
        .on(
          'postgres_changes',
          {
            event: '*',
            schema: 'public',
            table: 'call_records',
            filter: `user_id=eq.${user.id}`
          },
          () => {
            loadFailedUploads();
          }
        )
        .subscribe();

      return () => {
        supabase.removeChannel(channel);
      };
    }
  }, [user?.id]);

  return {
    failedUploads,
    loading,
    retryUpload,
    deleteFailedUpload,
    refresh: loadFailedUploads,
  };
};

