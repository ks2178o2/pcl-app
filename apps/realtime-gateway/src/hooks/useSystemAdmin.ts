import { useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { UserRole } from './useUserRoles';

interface CreateUserData {
  email: string;
  password: string;
  name: string;
  roles: Array<'doctor' | 'salesperson' | 'coach' | 'leader' | 'org_admin' | 'system_admin'>;
  center_id?: string;
  region_id?: string;
  organization_id?: string;
}

interface OrganizationData {
  name: string;
  businessType?: string;
  transcriptionProvider?: 'deepgram' | 'assemblyai';
  transcriptionFallbackProvider?: 'deepgram' | 'assemblyai';
  transcriptionAllowFallback?: boolean;
  transcriptionBakeoff?: boolean;
}

interface RegionData {
  name: string;
  organization_id: string;
}

interface CenterData {
  name: string;
  address?: string;
  regionId: string;
}

export const useSystemAdmin = () => {
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const createOrganization = async (data: OrganizationData) => {
    setLoading(true);
    try {
      const insertData: any = {
        name: data.name,
        business_type: data.businessType
      };
      
      // Add transcription settings if provided
      if (data.transcriptionProvider) {
        insertData.transcription_provider = data.transcriptionProvider;
      }
      if (data.transcriptionFallbackProvider) {
        insertData.transcription_fallback_provider = data.transcriptionFallbackProvider;
      }
      if (data.transcriptionAllowFallback !== undefined) {
        insertData.transcription_allow_fallback = data.transcriptionAllowFallback;
      }
      if (data.transcriptionBakeoff !== undefined) {
        insertData.transcription_bakeoff = data.transcriptionBakeoff;
      }
      
      const { data: result, error } = await supabase
        .from('organizations')
        .insert([insertData])
        .select()
        .single();

      if (error) throw error;
      
      toast({
        title: "Success",
        description: "Organization created successfully"
      });
      
      return { data: result, error: null };
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
      return { data: null, error };
    } finally {
      setLoading(false);
    }
  };


  const createRegion = async (data: RegionData) => {
    setLoading(true);
    try {
      // Check if organization_id column exists by trying to insert with it
      // If it fails, we know migration hasn't been applied yet
      let insertData: any = { name: data.name };
      
      // Try with organization_id first (post-migration)
      try {
        insertData.organization_id = data.organization_id;
        const { data: result, error } = await supabase
          .from('regions')
          .insert([insertData])
          .select()
          .single();

        if (error) {
          // If it fails due to column not existing, fall back to pre-migration approach
          if (error.message.includes('organization_id') && error.message.includes('does not exist')) {
            toast({
              title: "Database Migration Required",
              description: "Please apply the database migration first to enable region creation",
              variant: "destructive"
            });
            return { data: null, error: new Error('Database migration required') };
          }
          throw error;
        }
        
        toast({
          title: "Success",
          description: "Region created successfully"
        });
        
        return { data: result, error: null };
      } catch (innerError: any) {
        throw innerError;
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
      return { data: null, error };
    } finally {
      setLoading(false);
    }
  };

  const createCenter = async (data: CenterData) => {
    setLoading(true);
    try {
      const { data: result, error } = await supabase
        .from('centers')
        .insert([{
          name: data.name,
          address: data.address,
          region_id: data.regionId
        }])
        .select()
        .single();

      if (error) throw error;
      
      toast({
        title: "Success",
        description: "Center created successfully"
      });
      
      return { data: result, error: null };
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
      return { data: null, error };
    } finally {
      setLoading(false);
    }
  };

  const createUserWithRoles = async (userData: CreateUserData) => {
    setLoading(true);
    try {
      // Create user account
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email: userData.email,
        password: userData.password,
        options: {
          emailRedirectTo: `${window.location.origin}/`,
          data: {
            name: userData.name
          }
        }
      });

      if (authError) throw authError;
      if (!authData.user) throw new Error('Failed to create user');

      // Wait a bit for the trigger to create the profile
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Assign roles - filter out org_admin for now since database schema doesn't support it yet
      const validRoles = userData.roles.filter(role => role !== 'org_admin');
      const roleInserts = validRoles.map(role => ({
        user_id: authData.user!.id,
        role: role as 'doctor' | 'salesperson' | 'coach' | 'leader' | 'system_admin'
      }));

      if (roleInserts.length > 0) {
        const { error: rolesError } = await supabase
          .from('user_roles')
          .insert(roleInserts);

        if (rolesError) throw rolesError;
      }


      // Create user assignments
      if (userData.center_id || userData.region_id || userData.organization_id) {
        const assignmentData: any = { user_id: authData.user.id };
        if (userData.center_id) assignmentData.center_id = userData.center_id;
        if (userData.region_id) assignmentData.region_id = userData.region_id;
        if (userData.organization_id) assignmentData.organization_id = userData.organization_id;

        const { error: assignmentError } = await supabase
          .from('user_assignments')
          .insert([assignmentData]);

        if (assignmentError) throw assignmentError;
      }

      toast({
        title: "Success",
        description: "User created and roles assigned successfully"
      });
      
      return { data: authData.user, error: null };
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
      return { data: null, error };
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    createOrganization,
    createRegion,
    createCenter,
    createUserWithRoles
  };
};