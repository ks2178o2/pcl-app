import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useDashboardMetrics } from '../useDashboardMetrics';

vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          gte: vi.fn(() => ({
            lte: vi.fn(() => ({
              then: vi.fn(),
            })),
          })),
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

vi.mock('@/hooks/useProfile', () => ({
  useProfile: vi.fn(() => ({
    profile: { id: 'profile-123' },
  })),
}));

describe('useDashboardMetrics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default metrics', () => {
    const { result } = renderHook(() => useDashboardMetrics());
    
    expect(result.current.metrics.newLeadsThisWeek).toBe(0);
    expect(result.current.metrics.consultationsBooked).toBe(0);
    expect(result.current.metrics.dealsClosedThisMonth).toBe(0);
    expect(result.current.metrics.revenueGenerated).toBe(0);
  });

  it('should initialize with loading true', () => {
    const { result } = renderHook(() => useDashboardMetrics());
    
    expect(result.current.loading).toBe(true);
  });

  it('should provide metrics and loading state', () => {
    const { result } = renderHook(() => useDashboardMetrics());
    
    expect(result.current).toHaveProperty('metrics');
    expect(result.current).toHaveProperty('loading');
  });
});

