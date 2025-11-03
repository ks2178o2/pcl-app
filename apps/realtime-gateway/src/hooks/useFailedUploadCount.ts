import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

/**
 * Lightweight hook that only fetches the count of failed uploads
 * This minimizes egress usage compared to fetching full failed upload data
 */
export const useFailedUploadCount = () => {
  const [failedUploadCount, setFailedUploadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();

  const checkFailedUploads = async () => {
    if (!user) return;

    setLoading(true);
    try {
      // Only get the count, not the full data - this is much more efficient
      const { count, error } = await supabase
        .from('call_records')
        .select('*', { count: 'exact', head: true })
        .eq('user_id', user.id)
        .eq('is_active', true)
        .eq('upload_status', 'failed');

      if (error) {
        console.error('Error checking failed uploads count:', error);
        return;
      }

      setFailedUploadCount(count || 0);
    } catch (error) {
      console.error('Error checking failed uploads count:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      checkFailedUploads();
    }
  }, [user]);

  return {
    failedUploadCount,
    loading,
    refresh: checkFailedUploads,
  };
};

