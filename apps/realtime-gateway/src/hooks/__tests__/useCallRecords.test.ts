import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useCallRecords } from '../useCallRecords';

// Mock dependencies
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
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
    })),
  },
}));

vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({
    user: { id: 'user-123', email: 'test@example.com' },
  })),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: vi.fn(() => ({
    toast: vi.fn(),
  })),
}));

vi.mock('@/services/transcriptionService', () => ({
  transcribeAudio: vi.fn(),
}));

vi.mock('@/services/audioConversionService', () => ({
  formatFileSize: vi.fn((size) => `${size} bytes`),
}));

describe('useCallRecords', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with empty calls array', () => {
    const { result } = renderHook(() => useCallRecords());
    
    expect(result.current.calls).toEqual([]);
  });

  it('should provide loadCalls function', () => {
    const { result } = renderHook(() => useCallRecords());
    
    expect(typeof result.current.loadCalls).toBe('function');
  });

  it('should handle loadCalls when user is not available', async () => {
    const { useAuth } = require('@/hooks/useAuth');
    useAuth.mockReturnValue({ user: null });

    const { result } = renderHook(() => useCallRecords());
    
    // Should not throw error when user is null
    await expect(result.current.loadCalls()).resolves.not.toThrow();
  });

  it('should provide addCall function', () => {
    const { result } = renderHook(() => useCallRecords());
    
    expect(typeof result.current.addCall).toBe('function');
  });

  it('should provide updateCall function', () => {
    const { result } = renderHook(() => useCallRecords());
    
    expect(typeof result.current.updateCall).toBe('function');
  });

  it('should provide deleteCall function', () => {
    const { result } = renderHook(() => useCallRecords());
    
    expect(typeof result.current.deleteCall).toBe('function');
  });
});

