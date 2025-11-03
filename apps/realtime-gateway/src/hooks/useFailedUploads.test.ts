import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useFailedUploads } from './useFailedUploads';
import { useAuth } from './useAuth';

// Mock dependencies - must define mocks inline to avoid hoisting issues
vi.mock('@/hooks/useAuth');
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          eq: vi.fn(() => ({
            or: vi.fn(() => ({
              order: vi.fn(() => ({
                limit: vi.fn(() => Promise.resolve({ data: [], error: null }))
              }))
            }))
          }))
        }))
      }))
    })),
    channel: vi.fn(() => ({
      on: vi.fn().mockReturnThis(),
      subscribe: vi.fn()
    })),
    removeChannel: vi.fn(),
    functions: {
      invoke: vi.fn()
    }
  }
}));

describe('useFailedUploads', () => {
  const mockUser = {
    id: 'user-123',
    email: 'test@example.com'
  };

  const mockFailedUploads = [
    {
      id: 'upload-1',
      customer_name: 'Customer A',
      start_time: new Date().toISOString(),
      duration_seconds: 120,
      created_at: new Date().toISOString()
    },
    {
      id: 'upload-2',
      customer_name: 'Customer B',
      start_time: new Date().toISOString(),
      duration_seconds: 180,
      created_at: new Date().toISOString()
    }
  ];

  beforeEach(async () => {
    vi.clearAllMocks();
    
    (useAuth as any).mockReturnValue({
      user: mockUser,
      loading: false
    });
  });

  it('loads failed uploads on mount', async () => {
    // Import supabase from mocked module
    const { supabase } = await import('@/integrations/supabase/client');
    
    // Create mock functions that chain properly - limit returns Promise directly
    const mockLimit = vi.fn().mockResolvedValue({
      data: mockFailedUploads,
      error: null
    });
    
    const mockOrder = vi.fn().mockReturnValue({
      limit: mockLimit
    });
    
    const mockOr = vi.fn().mockReturnValue({
      order: mockOrder
    });
    
    const mockEq2 = vi.fn().mockReturnValue({
      or: mockOr
    });
    
    const mockEq1 = vi.fn().mockReturnValue({
      eq: mockEq2
    });
    
    const mockSelect = vi.fn().mockReturnValue({
      eq: mockEq1
    });

    (supabase.from as any).mockImplementation(() => ({
      select: mockSelect
    }));

    const { result } = renderHook(() => useFailedUploads());

    await waitFor(() => {
      expect(result.current.failedUploads).toHaveLength(2);
    }, { timeout: 3000 });
  });

  it('returns empty array when no failed uploads', async () => {
    const { supabase } = await import('@/integrations/supabase/client');
    
    const mockLimit = vi.fn().mockResolvedValue({
      data: [],
      error: null
    });
    
    const mockOrder = vi.fn().mockReturnValue({
      limit: mockLimit
    });
    
    const mockOr = vi.fn().mockReturnValue({
      order: mockOrder
    });
    
    const mockEq2 = vi.fn().mockReturnValue({
      or: mockOr
    });
    
    const mockEq1 = vi.fn().mockReturnValue({
      eq: mockEq2
    });
    
    const mockSelect = vi.fn().mockReturnValue({
      eq: mockEq1
    });

    (supabase.from as any).mockImplementation(() => ({
      select: mockSelect
    }));

    const { result } = renderHook(() => useFailedUploads());

    await waitFor(() => {
      expect(result.current.failedUploads).toHaveLength(0);
    });
  });

  it('handles retry upload', async () => {
    const { supabase } = await import('@/integrations/supabase/client');
    const mockInvoke = vi.fn().mockResolvedValue({
      error: null
    });

    (supabase.functions as any).invoke = mockInvoke;
    
    // Setup initial query mock
    const mockSelect = vi.fn().mockReturnValue({
      eq: vi.fn().mockReturnValue({
        or: vi.fn().mockReturnValue({
          order: vi.fn().mockReturnValue({
            limit: vi.fn().mockResolvedValue({
              data: [],
              error: null
            })
          })
        })
      })
    });

    (supabase.from as any).mockImplementation(() => ({
      select: mockSelect,
      update: vi.fn().mockReturnValue({
        eq: vi.fn().mockResolvedValue({ data: {}, error: null })
      })
    }));

    const { result } = renderHook(() => useFailedUploads());

    await result.current.retryUpload('upload-1');

    expect(mockInvoke).toHaveBeenCalledWith('retry-recording-upload', {
      body: { callRecordId: 'upload-1' }
    });
  });

  it('handles delete failed upload', async () => {
    const { supabase } = await import('@/integrations/supabase/client');
    const mockUpdate = vi.fn().mockReturnValue({
      eq: vi.fn().mockResolvedValue({ data: {}, error: null })
    });

    const mockSelect = vi.fn().mockReturnValue({
      eq: vi.fn().mockReturnValue({
        or: vi.fn().mockReturnValue({
          order: vi.fn().mockReturnValue({
            limit: vi.fn().mockResolvedValue({
              data: mockFailedUploads,
              error: null
            })
          })
        })
      })
    });

    (supabase.from as any).mockImplementation((table: string) => {
      if (table === 'call_records') {
        return {
          update: mockUpdate,
          select: mockSelect
        };
      }
      return {
        select: mockSelect
      };
    });

    const { result } = renderHook(() => useFailedUploads());

    await result.current.deleteFailedUpload('upload-1');
  });

  it('handles errors gracefully', async () => {
    const { supabase } = await import('@/integrations/supabase/client');
    const mockSelect = vi.fn().mockReturnValue({
      eq: vi.fn().mockReturnThis(),
      or: vi.fn().mockReturnThis(),
      order: vi.fn().mockReturnThis(),
      limit: vi.fn().mockResolvedValue({
        data: null,
        error: new Error('Database error')
      })
    });

    (supabase.from as any).mockImplementation(() => ({
      select: mockSelect
    }));

    const { result } = renderHook(() => useFailedUploads());

    await waitFor(() => {
      expect(result.current.failedUploads).toHaveLength(0);
    });
  });

  it('subscribes to real-time updates', async () => {
    const { supabase } = await import('@/integrations/supabase/client');
    renderHook(() => useFailedUploads());

    expect(supabase.channel).toHaveBeenCalled();
  });

  it('returns loading state', () => {
    const { result } = renderHook(() => useFailedUploads());

    expect(result.current.loading).toBeDefined();
  });

  it('provides refresh function', () => {
    const { result } = renderHook(() => useFailedUploads());

    expect(typeof result.current.refresh).toBe('function');
  });
});


