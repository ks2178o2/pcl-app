import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useOrganizationData } from '../useOrganizationData';

vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          then: vi.fn(),
        })),
      })),
    })),
  },
}));

vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({
    user: { id: 'user-123' },
  })),
}));

describe('useOrganizationData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with empty arrays', () => {
    const { result } = renderHook(() => useOrganizationData());
    
    expect(result.current.regions).toEqual([]);
    expect(result.current.centers).toEqual([]);
    expect(result.current.assignments).toEqual([]);
  });

  it('should initialize with loading true', () => {
    const { result } = renderHook(() => useOrganizationData());
    
    expect(result.current.loading).toBe(true);
  });

  it('should provide organization data', () => {
    const { result } = renderHook(() => useOrganizationData());
    
    expect(result.current).toHaveProperty('regions');
    expect(result.current).toHaveProperty('centers');
    expect(result.current).toHaveProperty('assignments');
    expect(result.current).toHaveProperty('loading');
  });
});

