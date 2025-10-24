import { useUserRoles } from './useUserRoles';
import { useOrganizationSecurity } from './useOrganizationSecurity';

/**
 * Hook to determine admin access levels and UI visibility
 * This enforces the security model where:
 * - system_admin: Can see and manage everything across all organizations
 * - org_admin: Can only see and manage their own organization's data
 * - Other roles: Limited access based on their specific permissions
 */
export const useSecureAdminAccess = () => {
  const { 
    isSystemAdmin, 
    isOrgAdmin, 
    isAdmin,
    canAccessAllOrganizations 
  } = useUserRoles();
  
  const { 
    hasAdminAccess, 
    hasSystemAdminAccess,
    userOrganizationId 
  } = useOrganizationSecurity();

  /**
   * Determine which admin UI sections should be visible
   */
  const getAdminUIAccess = () => {
    return {
      // System management (users, organizations, global settings)
      canManageSystem: hasSystemAdminAccess(),
      
      // Organization management (within user's org scope)
      canManageOrganization: hasAdminAccess(),
      
      // User management (within user's org scope)
      canManageUsers: hasAdminAccess(),
      
      // Cross-organization data access
      canViewAllOrganizations: canAccessAllOrganizations,
      
      // Specific admin actions
      canCreateOrganizations: hasSystemAdminAccess(),
      canDeleteOrganizations: hasSystemAdminAccess(),
      canManageSystemSettings: hasSystemAdminAccess(),
      
      // Current user's admin level
      adminLevel: isSystemAdmin() ? 'system' : isOrgAdmin() ? 'organization' : 'none',
      
      // Organization scope
      organizationScope: userOrganizationId
    };
  };

  /**
   * Check if user should see admin navigation/menu items
   */
  const shouldShowAdminNavigation = (): boolean => {
    return hasAdminAccess();
  };

  /**
   * Get access control message for restricted areas
   */
  const getAccessDeniedMessage = (requiredLevel: 'system' | 'organization'): string => {
    if (requiredLevel === 'system') {
      return 'This section requires system administrator privileges.';
    }
    return 'This section requires organization administrator privileges.';
  };

  return {
    ...getAdminUIAccess(),
    shouldShowAdminNavigation,
    getAccessDeniedMessage,
    isSystemAdmin: isSystemAdmin(),
    isOrgAdmin: isOrgAdmin(),
    hasAnyAdminAccess: hasAdminAccess()
  };
};