import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAppointments } from '../useAppointments';

// Mock dependencies
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          limit: vi.fn(() => ({
            order: vi.fn(() => ({
              then: vi.fn(),
            })),
          })),
          order: vi.fn(() => ({
            then: vi.fn(),
          })),
        })),
      })),
    })),
  },
}));

vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({
    user: { id: 'user-123', email: 'test@example.com' },
  })),
}));

vi.mock('@/hooks/useProfile', () => ({
  useProfile: vi.fn(() => ({
    profile: { timezone: 'America/Los_Angeles' },
  })),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: vi.fn(() => ({
    toast: vi.fn(),
  })),
}));

describe('useAppointments', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with empty appointments array', () => {
    const { result } = renderHook(() => useAppointments());
    
    expect(result.current.appointments).toEqual([]);
  });

  it('should initialize with loading false', () => {
    const { result } = renderHook(() => useAppointments());
    
    expect(result.current.loading).toBe(false);
  });

  it('should provide loadAppointments function', () => {
    const { result } = renderHook(() => useAppointments());
    
    expect(typeof result.current.loadAppointments).toBe('function');
  });

  it('should handle loadAppointments when user is not available', async () => {
    const { useAuth } = require('@/hooks/useAuth');
    useAuth.mockReturnValue({ user: null });

    const { result } = renderHook(() => useAppointments());
    
    // Should not throw error when user is null
    await expect(result.current.loadAppointments()).resolves.not.toThrow();
  });

  it('should provide createAppointment function', () => {
    const { result } = renderHook(() => useAppointments());
    
    expect(typeof result.current.createAppointment).toBe('function');
  });

  it('should provide updateAppointment function', () => {
    const { result } = renderHook(() => useAppointments());
    
    expect(typeof result.current.updateAppointment).toBe('function');
  });

  it('should provide deleteAppointment function', () => {
    const { result } = renderHook(() => useAppointments());
    
    expect(typeof result.current.deleteAppointment).toBe('function');
  });
});

