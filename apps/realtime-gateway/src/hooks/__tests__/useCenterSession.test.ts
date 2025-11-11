import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useCenterSession } from '../useCenterSession';

vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({
    user: { id: 'user-123' },
  })),
}));

vi.mock('@/hooks/useProfile', () => ({
  useProfile: vi.fn(() => ({
    profile: { id: 'profile-123' },
  })),
}));

vi.mock('@/hooks/useOrganizationData', () => ({
  useOrganizationData: vi.fn(() => ({
    centers: [],
    assignments: [],
    loading: false,
  })),
}));

describe('useCenterSession', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useCenterSession());
    
    expect(result.current.activeCenter).toBeNull();
    expect(result.current.availableCenters).toEqual([]);
    expect(result.current.loading).toBe(true);
  });

  it('should provide center session state', () => {
    const { result } = renderHook(() => useCenterSession());
    
    expect(result.current).toHaveProperty('activeCenter');
    expect(result.current).toHaveProperty('availableCenters');
    expect(result.current).toHaveProperty('loading');
    expect(result.current).toHaveProperty('error');
  });
});

