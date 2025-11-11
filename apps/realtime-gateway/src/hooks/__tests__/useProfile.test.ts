import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useProfile } from '../useProfile';

vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          single: vi.fn(() => Promise.resolve({ data: null, error: null })),
        })),
      })),
    })),
  },
}));

vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({
    user: { id: 'user-123', user_metadata: { salesperson_name: 'Test User' } },
  })),
}));

describe('useProfile', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with loading state', () => {
    const { result } = renderHook(() => useProfile());
    
    expect(result.current.loading).toBe(true);
  });

  it('should provide profile state', () => {
    const { result } = renderHook(() => useProfile());
    
    expect(result.current).toHaveProperty('profile');
    expect(result.current).toHaveProperty('loading');
  });

  it('should handle null user', () => {
    const { useAuth } = require('@/hooks/useAuth');
    useAuth.mockReturnValue({ user: null });

    const { result } = renderHook(() => useProfile());
    
    expect(result.current.profile).toBeNull();
  });
});

