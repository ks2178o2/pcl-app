// Mock useAuth hook for testing
import { useState } from 'react';

export const useAuth = () => {
  const [user, setUser] = useState({
    id: 'test-user-123',
    email: 'test@example.com',
    organization_id: 'org-123',
    role: 'admin'
  });

  const [isAuthenticated, setIsAuthenticated] = useState(true);

  const login = async (email: string, password: string) => {
    setIsAuthenticated(true);
    return { success: true, user };
  };

  const logout = async () => {
    setIsAuthenticated(false);
    setUser(null);
  };

  return {
    user,
    isAuthenticated,
    login,
    logout,
    isLoading: false
  };
};
