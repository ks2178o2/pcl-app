import { useState, useEffect, useRef, useMemo } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

interface Profile {
  id: string;
  user_id: string;
  salesperson_name: string;
  organization_id?: string;
  timezone?: string;
  created_at: string;
  updated_at: string;
}

export const useProfile = () => {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const lastUserIdRef = useRef<string | null>(null);
  const fetchingRef = useRef(false);

  useEffect(() => {
    // Skip if no user or if we've already fetched for this user
    if (!user) {
      if (profile !== null || loading) {
        setProfile(null);
        setLoading(false);
      }
      lastUserIdRef.current = null;
      fetchingRef.current = false;
      return;
    }

    // Skip if already fetching
    if (fetchingRef.current) {
      return;
    }

    // Skip if we've already loaded profile for this user ID
    if (lastUserIdRef.current === user.id && profile !== null) {
      return;
    }

    // Only fetch if user ID changed
    if (lastUserIdRef.current === user.id) {
      return;
    }

    const fetchProfile = async () => {
      fetchingRef.current = true;
      lastUserIdRef.current = user.id;
      
      setLoading(true);
      try {
        // Try to get profile data from user metadata first
        const userMetadata = user.user_metadata;
        if (userMetadata?.salesperson_name) {
          // Create a profile object from user metadata
          const profileData = {
            id: user.id,
            user_id: user.id,
            salesperson_name: userMetadata.salesperson_name,
            organization_id: userMetadata.organization_id || null,
            created_at: user.created_at,
            updated_at: user.updated_at
          };
          setProfile(profileData);
          setLoading(false);
          fetchingRef.current = false;
          return;
        }

        // Fallback to database query
        const { data, error } = await supabase
          .from('profiles')
          .select('*')
          .eq('user_id', user.id)
          .single();

        if (error) {
          console.error('Error fetching profile from database:', error);
          // If database query fails, try to create a basic profile from user data
          const profileData = {
            id: user.id,
            user_id: user.id,
            salesperson_name: user.email?.split('@')[0] || 'User',
            organization_id: null,
            created_at: user.created_at,
            updated_at: user.updated_at
          };
          setProfile(profileData);
        } else {
          setProfile(data);
        }
      } catch (error) {
        console.error('Error fetching profile:', error);
        // Create a basic profile from user data as fallback
        const profileData = {
          id: user.id,
          user_id: user.id,
          salesperson_name: user.email?.split('@')[0] || 'User',
          organization_id: null,
          created_at: user.created_at,
          updated_at: user.updated_at
        };
        setProfile(profileData);
      } finally {
        setLoading(false);
        fetchingRef.current = false;
      }
    };

    fetchProfile();
    // Only depend on user.id to prevent refetching when user object reference changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  const refetch = () => {
    // This will trigger the useEffect to re-run
    console.warn('refetch() called but not implemented in new structure');
  };

  return {
    profile,
    loading,
    refetch
  };
};