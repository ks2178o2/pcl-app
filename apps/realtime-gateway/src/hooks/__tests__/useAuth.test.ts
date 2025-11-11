import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAuth } from '../useAuth';

// Mock Supabase
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      onAuthStateChange: vi.fn((callback) => {
        // Store callback for manual triggering
        (window as any).__authCallback = callback;
        return {
          data: {
            subscription: {
              unsubscribe: vi.fn(),
            },
          },
        };
      }),
      getSession: vi.fn(),
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
      resetPasswordForEmail: vi.fn(),
    },
  },
}));

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (window as any).__authListenerSetup = false;
  });

  it('should initialize with loading state', () => {
    const { result } = renderHook(() => useAuth());
    
    expect(result.current.loading).toBe(true);
    expect(result.current.user).toBeNull();
    expect(result.current.session).toBeNull();
  });

  it('should set up auth state listener on mount', () => {
    const { supabase } = require('@/integrations/supabase/client');
    renderHook(() => useAuth());
    
    expect(supabase.auth.onAuthStateChange).toHaveBeenCalled();
  });

  it('should update user when auth state changes', async () => {
    const mockUser = {
      id: 'user-123',
      email: 'test@example.com',
    };
    const mockSession = {
      user: mockUser,
      access_token: 'token-123',
    };

    const { result } = renderHook(() => useAuth());
    
    // Trigger auth state change
    const callback = (window as any).__authCallback;
    if (callback) {
      callback('SIGNED_IN', mockSession);
    }

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.session).toEqual(mockSession);
  });

  it('should clear user on sign out', async () => {
    const { result } = renderHook(() => useAuth());
    
    // First sign in
    const mockUser = { id: 'user-123', email: 'test@example.com' };
    const mockSession = { user: mockUser, access_token: 'token-123' };
    const callback = (window as any).__authCallback;
    if (callback) {
      callback('SIGNED_IN', mockSession);
    }

    await waitFor(() => {
      expect(result.current.user).not.toBeNull();
    });

    // Then sign out
    if (callback) {
      callback('SIGNED_OUT', null);
    }

    await waitFor(() => {
      expect(result.current.user).toBeNull();
      expect(result.current.session).toBeNull();
    });
  });

  it('should provide signIn function', () => {
    const { result } = renderHook(() => useAuth());
    
    expect(typeof result.current.signIn).toBe('function');
  });

  it('should provide signUp function', () => {
    const { result } = renderHook(() => useAuth());
    
    expect(typeof result.current.signUp).toBe('function');
  });

  it('should provide signOut function', () => {
    const { result } = renderHook(() => useAuth());
    
    expect(typeof result.current.signOut).toBe('function');
  });

  it('should provide resetPassword function', () => {
    const { result } = renderHook(() => useAuth());
    
    expect(typeof result.current.resetPassword).toBe('function');
  });
});

