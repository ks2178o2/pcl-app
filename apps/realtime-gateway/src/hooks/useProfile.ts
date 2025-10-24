import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

interface Profile {
  id: string;
  user_id: string;
  salesperson_name: string;
  organization_id?: string;
  created_at: string;
  updated_at: string;
}

export const useProfile = () => {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchProfile();
    } else {
      setProfile(null);
      setLoading(false);
    }
  }, [user]);

  const fetchProfile = async () => {
    if (!user) return;

    setLoading(true);
    console.log('Fetching profile for user:', user.id, user.email);
    try {
      // Try to get profile data from user metadata first
      const userMetadata = user.user_metadata;
      console.log('User metadata:', userMetadata);
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
        console.log('Created profile from metadata:', profileData);
        setProfile(profileData);
        setLoading(false);
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
        console.log('Created fallback profile:', profileData);
        setProfile(profileData);
      } else {
        console.log('Profile fetched from database:', data);
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
      console.log('Created fallback profile from catch block:', profileData);
      setProfile(profileData);
    } finally {
      setLoading(false);
    }
  };

  return {
    profile,
    loading,
    refetch: fetchProfile
  };
};