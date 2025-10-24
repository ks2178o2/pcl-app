import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

export type UserRole = 'doctor' | 'salesperson' | 'coach' | 'leader' | 'org_admin' | 'system_admin';

interface UserRoleData {
  id: string;
  user_id: string;
  role: UserRole;
  created_at: string;
  updated_at: string;
}

export const useUserRoles = () => {
  const [roles, setRoles] = useState<UserRole[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchUserRoles();
    } else {
      setRoles([]);
      setLoading(false);
    }
  }, [user]);

  const fetchUserRoles = async () => {
    if (!user) return;

    setLoading(true);
    try {
      const { data, error } = await supabase
        .from('user_roles')
        .select('*')
        .eq('user_id', user.id);

      if (error) {
        console.error('Error fetching user roles:', error);
      } else {
        setRoles(data?.map(r => r.role) || []);
      }
    } catch (error) {
      console.error('Error fetching user roles:', error);
    } finally {
      setLoading(false);
    }
  };

  const hasRole = (role: UserRole): boolean => {
    return roles.includes(role);
  };

  const isLeader = (): boolean => hasRole('leader');
  const isCoach = (): boolean => hasRole('coach');
  const isSalesperson = (): boolean => hasRole('salesperson');
  const isDoctor = (): boolean => hasRole('doctor');
  const isOrgAdmin = (): boolean => hasRole('org_admin');
  const isSystemAdmin = (): boolean => hasRole('system_admin');

  // Organization-scoped admin check (org_admin or system_admin)
  const isAdmin = (): boolean => hasRole('org_admin') || hasRole('system_admin');
  
  // Check if user can access cross-organization data
  const canAccessAllOrganizations = (): boolean => hasRole('system_admin');

  return {
    roles,
    loading,
    hasRole,
    isLeader,
    isCoach,
    isSalesperson,
    isDoctor,
    isOrgAdmin,
    isSystemAdmin,
    isAdmin,
    canAccessAllOrganizations,
    refetch: fetchUserRoles
  };
};