import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

export interface Invitation {
  id: string;
  email: string;
  organization_id: string;
  role: string;
  center_ids?: string[];
  region_id?: string;
  status: 'pending' | 'accepted' | 'expired' | 'cancelled';
  expires_at: string;
  invited_by: string;
  created_at: string;
  updated_at?: string;
}

export interface CreateInvitationData {
  email: string;
  organization_id: string;
  role: string;
  center_ids?: string[];
  region_id?: string;
  expires_in_days?: number;
}

export interface InvitationResponse {
  invitation_id: string;
  email: string;
  token: string;
  expires_at: string;
  status: string;
  created_at: string;
}

export const useInvitations = () => {
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();

  const fetchInvitations = async (statusFilter?: string) => {
    if (!user) return;

    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No session');

      let url = '/api/invitations?';
      if (statusFilter) {
        url += `status_filter=${statusFilter}`;
      }

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch invitations: ${response.statusText}`);
      }

      const result = await response.json();
      setInvitations(result.invitations);
    } catch (error) {
      console.error('Error fetching invitations:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const createInvitation = async (invitationData: CreateInvitationData): Promise<InvitationResponse> => {
    if (!user) throw new Error('User not authenticated');

    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No session');

      const response = await fetch('/api/invitations/', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(invitationData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create invitation');
      }

      const result = await response.json();
      
      // Refresh invitations list
      await fetchInvitations();
      
      return result;
    } catch (error) {
      console.error('Error creating invitation:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const cancelInvitation = async (invitationId: string): Promise<void> => {
    if (!user) throw new Error('User not authenticated');

    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No session');

      const response = await fetch(`/api/invitations/${invitationId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to cancel invitation');
      }

      // Refresh invitations list
      await fetchInvitations();
    } catch (error) {
      console.error('Error cancelling invitation:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const validateInvitationToken = async (token: string): Promise<any> => {
    try {
      const response = await fetch('/api/invitations/validate-token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Invalid invitation token');
      }

      return await response.json();
    } catch (error) {
      console.error('Error validating invitation token:', error);
      throw error;
    }
  };

  const acceptInvitation = async (token: string, password: string, name?: string): Promise<any> => {
    try {
      const response = await fetch('/api/invitations/accept', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token, password, name }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to accept invitation');
      }

      return await response.json();
    } catch (error) {
      console.error('Error accepting invitation:', error);
      throw error;
    }
  };

  return {
    invitations,
    loading,
    fetchInvitations,
    createInvitation,
    cancelInvitation,
    validateInvitationToken,
    acceptInvitation,
  };
};

