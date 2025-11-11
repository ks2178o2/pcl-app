import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

export interface LoginHistoryEntry {
  id: string;
  user_id: string;
  organization_id?: string;
  ip_address?: string;
  user_agent?: string;
  device_fingerprint?: string;
  device_name?: string;
  login_method: 'password' | 'oauth_google' | 'oauth_apple' | 'magic_link' | '2fa_code';
  status: 'success' | 'failed' | 'blocked';
  failure_reason?: string;
  location_data?: any;
  session_id?: string;
  login_at: string;
  logout_at?: string;
  created_at: string;
}

export const useLoginHistory = () => {
  const [history, setHistory] = useState<LoginHistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const { user } = useAuth();

  const fetchHistory = async (limit: number = 50, offset: number = 0) => {
    if (!user) return;

    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No session');

      const response = await fetch(`/api/auth/login-history?limit=${limit}&offset=${offset}`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch login history: ${response.statusText}`);
      }

      const result = await response.json();
      setHistory(result.logins);
      setTotal(result.total);
    } catch (error) {
      console.error('Error fetching login history:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const refreshToken = async () => {
    if (!user) throw new Error('User not authenticated');

    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No session');

      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: session.refresh_token
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to refresh token');
      }

      const result = await response.json();
      
      // Update session with new tokens
      await supabase.auth.setSession({
        access_token: result.access_token,
        refresh_token: result.refresh_token
      });

      return result;
    } catch (error) {
      console.error('Error refreshing token:', error);
      throw error;
    }
  };

  const revokeToken = async () => {
    if (!user) throw new Error('User not authenticated');

    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No session');

      const response = await fetch('/api/auth/revoke', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: session.access_token
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to revoke token');
      }

      // Sign out after revoking
      await supabase.auth.signOut();
      
      return { success: true };
    } catch (error) {
      console.error('Error revoking token:', error);
      throw error;
    }
  };

  useEffect(() => {
    if (user) {
      fetchHistory();
    }
  }, [user]);

  return {
    history,
    loading,
    total,
    fetchHistory,
    refreshToken,
    revokeToken,
  };
};

