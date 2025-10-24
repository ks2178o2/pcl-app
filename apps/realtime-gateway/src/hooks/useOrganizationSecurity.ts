import { useUserRoles } from './useUserRoles';
import { useProfile } from './useProfile';

export const useOrganizationSecurity = () => {
  const { canAccessAllOrganizations, isSystemAdmin, isOrgAdmin, isAdmin } = useUserRoles();
  const { profile } = useProfile();

  /**
   * Check if user can access data from a specific organization
   */
  const canAccessOrganization = (organizationId?: string): boolean => {
    // System admins can access everything
    if (canAccessAllOrganizations()) {
      return true;
    }

    // If no organization specified, only system admins can access
    if (!organizationId) {
      return canAccessAllOrganizations();
    }

    // Org admins and other roles can only access their own organization
    return profile?.organization_id === organizationId;
  };

  /**
   * Filter data array to only include items user can access based on organization
   */
  const filterByOrganization = <T extends { organization_id?: string }>(
    data: T[]
  ): T[] => {
    if (canAccessAllOrganizations()) {
      return data;
    }

    return data.filter(item => canAccessOrganization(item.organization_id));
  };

  /**
   * Get organization filter for database queries
   * Returns null if user can access all organizations, otherwise returns user's org ID
   */
  const getOrganizationFilter = (): string | null => {
    return canAccessAllOrganizations() ? null : profile?.organization_id || null;
  };

  /**
   * Check if user has admin access within their organization scope
   */
  const hasAdminAccess = (): boolean => {
    return isAdmin();
  };

  /**
   * Check if user can perform system-wide administrative actions
   */
  const hasSystemAdminAccess = (): boolean => {
    return isSystemAdmin();
  };

  return {
    canAccessOrganization,
    filterByOrganization,
    getOrganizationFilter,
    hasAdminAccess,
    hasSystemAdminAccess,
    userOrganizationId: profile?.organization_id,
    canAccessAllOrganizations: canAccessAllOrganizations()
  };
};