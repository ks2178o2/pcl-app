import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

export interface TwoFactorSetup {
  qr_code: string;
  secret: string;
  backup_codes: string[];
}

export interface Device {
  id: string;
  user_id: string;
  device_name: string;
  device_id: string;
  verified_at: string;
  last_used_at: string;
  is_primary: boolean;
  trust_score: number;
  ip_address?: string;
  user_agent?: string;
}

export const use2FA = () => {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ enabled: boolean; setup_required: boolean } | null>(null);
  const { user } = useAuth();

  const fetchStatus = async () => {
    if (!user) return;

    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No session');

      const response = await fetch('/api/auth/2fa/status', {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch 2FA status: ${response.statusText}`);
      }

      const result = await response.json();
      setStatus(result);
    } catch (error) {
      console.error('Error fetching 2FA status:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const setup2FA = async (): Promise<TwoFactorSetup> => {
    if (!user) throw new Error('User not authenticated');

    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No session');

      const response = await fetch('/api/auth/2fa/setup', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to setup 2FA');
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error setting up 2FA:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const verifyCode = async (code: string): Promise<boolean> => {
    if (!user) throw new Error('User not authenticated');

    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No session');

      const response = await fetch('/api/auth/2fa/verify', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }),
      });

      if (!response.ok) {
        return false;
      }

      return true;
    } catch (error) {
      console.error('Error verifying 2FA code:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const enable2FA = async (code: string): Promise<void> => {
    if (!user) throw new Error('User not authenticated');

    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No session');

      const response = await fetch('/api/auth/2fa/enable', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to enable 2FA');
      }

      await fetchStatus();
    } catch (error) {
      console.error('Error enabling 2FA:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const disable2FA = async (code?: string): Promise<void> => {
    if (!user) throw new Error('User not authenticated');

    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No session');

      const response = await fetch('/api/auth/2fa/disable', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to disable 2FA');
      }

      await fetchStatus();
    } catch (error) {
      console.error('Error disabling 2FA:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const listDevices = async (): Promise<Device[]> => {
    if (!user) throw new Error('User not authenticated');

    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No session');

      const response = await fetch('/api/auth/2fa/devices', {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to list devices: ${response.statusText}`);
      }

      const result = await response.json();
      return result.devices;
    } catch (error) {
      console.error('Error listing devices:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const removeDevice = async (deviceId: string): Promise<void> => {
    if (!user) throw new Error('User not authenticated');

    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No session');

      const response = await fetch(`/api/auth/2fa/devices/${deviceId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to remove device');
      }
    } catch (error) {
      console.error('Error removing device:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchStatus();
    }
  }, [user]);

  return {
    loading,
    status,
    fetchStatus,
    setup2FA,
    verifyCode,
    enable2FA,
    disable2FA,
    listDevices,
    removeDevice,
  };
};

