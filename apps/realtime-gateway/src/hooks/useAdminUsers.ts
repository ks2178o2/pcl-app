import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { useOrganizationSecurity } from './useOrganizationSecurity';

interface AdminUser {
  id: string;
  email: string;
  name?: string;
  roles: string[];
  created_at: string;
  updated_at: string;
  is_active: boolean;
  organization_id?: string;
  region_id?: string;
  center_id?: string;
  organization?: {
    id: string;
    name: string;
  };
  region?: {
    id: string;
    name: string;
  };
  center?: {
    id: string;
    name: string;
  };
}

export const useAdminUsers = () => {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();
  const { filterByOrganization, getOrganizationFilter, canAccessAllOrganizations, userOrganizationId } = useOrganizationSecurity();

  console.log('=== useAdminUsers hook initialized ===');

  useEffect(() => {
    console.log('=== useEffect triggered, calling fetchUsers ===', { canAccessAllOrganizations, userOrganizationId });
    fetchUsers();
  }, [canAccessAllOrganizations, userOrganizationId]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      console.log('=== Starting user fetch process with organization security ===');
      
      // Get organization filter for security
      const orgFilter = getOrganizationFilter();
      
      // Build query with organization filter if needed
      let query = supabase
        .from('profiles')
        .select(`
          *,
          organizations(id, name)
        `)
        .order('created_at', { ascending: false });

      // Apply organization filter for non-system admins
      if (orgFilter) {
        query = query.eq('organization_id', orgFilter);
      }

      const { data: profiles, error: profilesError } = await query;

      if (profilesError) {
        console.error('Error fetching profiles:', profilesError);
        setUsers([]);
        return;
      }

      console.log('Profiles fetched:', profiles?.length);
      console.log('Sample profile structure:', profiles?.[0]);

      // Let's check what email fields are available in profiles
      profiles?.forEach((profile: any, index: number) => {
        console.log(`Profile ${index + 1}:`, {
          id: profile.id,
          user_id: profile.user_id,
          email: profile.email,
          salesperson_name: profile.salesperson_name,
          all_keys: Object.keys(profile)
        });
      });

      // Instead of trying auth admin API, let's use what we have
      const profilesWithAuth = (profiles || []).map((profile: any) => {
        // Use the email from profile if it exists, otherwise show clear message
        const emailToUse = profile.email || 'No email in profile';
        console.log(`Using email for ${profile.salesperson_name}: ${emailToUse}`);
        
        return {
          ...profile,
          auth_email: emailToUse
        };
      });

      console.log('Final profiles with auth emails:', profilesWithAuth.map(p => ({ id: p.id, name: p.salesperson_name, email: p.auth_email })));

      // Get regions and centers separately
      const { data: regions } = await supabase
        .from('regions')
        .select('id, name');

      const { data: centers } = await supabase
        .from('centers')
        .select('id, name');

      // Get all user roles
      const { data: userRoles, error: rolesError } = await supabase
        .from('user_roles')
        .select('user_id, role');

      if (rolesError) {
        console.error('Error fetching user roles:', rolesError);
      }

      // Get user assignments to get region/center mappings
      const { data: userAssignments, error: assignmentsError } = await supabase
        .from('user_assignments')
        .select('user_id, region_id, center_id');

      if (assignmentsError) {
        console.error('Error fetching user assignments:', assignmentsError);
      }

      // Transform profiles to our user format
      const transformedUsers = profilesWithAuth.map((profile: any) => {        
        // Find roles for this user
        const roles = (userRoles || [])
          .filter(ur => ur.user_id === profile.user_id)
          .map(ur => ur.role);

        // Find user assignments to get region/center
        const assignment = userAssignments?.find(ua => ua.user_id === profile.user_id);
        const region = assignment ? regions?.find(r => r.id === assignment.region_id) : null;
        const center = assignment ? centers?.find(c => c.id === assignment.center_id) : null;

        return {
          id: profile.id,
          email: profile.auth_email || profile.email || 'No email available',
          name: profile.salesperson_name || 'No name set',
          roles: roles,
          created_at: profile.created_at,
          updated_at: profile.updated_at,
          is_active: profile.is_active ?? true,
          organization_id: profile.organization_id,
          region_id: assignment?.region_id || null,
          center_id: assignment?.center_id || null,
          organization: profile.organizations,
          region: region,
          center: center
        };
      });

      // Apply additional organization filtering on the frontend as a safety measure
      const secureUsers = filterByOrganization(transformedUsers);
      setUsers(secureUsers);
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleUserStatus = async (userId: string, isActive: boolean) => {
    try {
      const { error } = await supabase
        .from('profiles')
        .update({ is_active: isActive } as any)
        .eq('id', userId);

      if (error) throw error;

      toast({
        title: "Success",
        description: `User ${isActive ? 'activated' : 'deactivated'} successfully`
      });

      fetchUsers(); // Refresh the list
      return { error: null };
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
      return { error };
    }
  };

  return {
    users,
    loading,
    refetch: fetchUsers,
    toggleUserStatus
  };
};