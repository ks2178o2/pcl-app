// Mock useUserRoles hook for testing
import { useState } from 'react';

export const useUserRoles = () => {
  const [roles, setRoles] = useState(['admin', 'user']);

  const hasRole = (role: string) => {
    return roles.includes(role);
  };

  const hasPermission = (permission: string) => {
    // Mock permission logic
    return roles.includes('admin') || permission === 'read';
  };

  return {
    roles,
    hasRole,
    hasPermission,
    isLoading: false
  };
};
