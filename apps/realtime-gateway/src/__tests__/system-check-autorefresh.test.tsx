/**
 * System Check Auto-Refresh Test Suite
 * 
 * Tests for periodic health check refresh functionality
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup, fireEvent } from '@testing-library/react';
import React from 'react';
import SystemCheck from '@/pages/SystemCheck';
import { useAuth } from '@/hooks/useAuth';

vi.mock('@/hooks/useAuth');
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        limit: vi.fn(() => Promise.resolve({ data: [], error: null }))
      }))
    })),
    storage: {
      listBuckets: vi.fn(() => Promise.resolve({ 
        data: [{ name: 'call-recordings' }, { name: 'voice-samples' }],
        error: null 
      }))
    }
  }
}));

describe('SystemCheck Auto-Refresh', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    
    (useAuth as any).mockReturnValue({
      user: { id: 'user-123', email: 'admin@test.com' },
      session: { access_token: 'mock-token' }
    });
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
    cleanup();
  });

  it('should run checks immediately on mount', async () => {
    global.fetch = vi.fn().mockResolvedValue({ 
      ok: true, 
      json: async () => ({ version: '1.0.0' }) 
    });

    render(<SystemCheck />);

    await waitFor(() => {
      expect(screen.getByText(/Supabase Connection/i)).toBeInTheDocument();
    });
  });

  it('should auto-refresh every 60 seconds when enabled', async () => {
    global.fetch = vi.fn().mockResolvedValue({ 
      ok: true, 
      json: async () => ({ version: '1.0.0' }) 
    });

    render(<SystemCheck />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(3); // Initial checks
    });

    // Fast-forward 60 seconds
    vi.advanceTimersByTime(60000);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(6); // Refresh checks
    });
  });

  it('should not auto-refresh when disabled', async () => {
    global.fetch = vi.fn().mockResolvedValue({ 
      ok: true, 
      json: async () => ({ version: '1.0.0' }) 
    });

    render(<SystemCheck />);

    await waitFor(() => {
      const autoRefreshButton = screen.getByText(/Auto Refresh/i);
      fireEvent.click(autoRefreshButton);
    });

    const initialCallCount = global.fetch.mock.calls.length;

    // Fast-forward 60 seconds
    vi.advanceTimersByTime(60000);

    await waitFor(() => {
      expect(global.fetch.mock.calls.length).toBe(initialCallCount);
    });
  });

  it('should toggle auto-refresh on button click', async () => {
    global.fetch = vi.fn().mockResolvedValue({ 
      ok: true, 
      json: async () => ({ version: '1.0.0' }) 
    });

    const { container } = render(<SystemCheck />);

    await waitFor(() => {
      expect(screen.getByText(/Auto Refresh/i)).toBeInTheDocument();
    });

    const autoRefreshButton = screen.getByText(/Auto Refresh/i);
    
    // Auto-refresh should be enabled by default
    expect(autoRefreshButton).toHaveClass('bg-primary');
    
    // Click to disable
    fireEvent.click(autoRefreshButton);
    
    await waitFor(() => {
      expect(autoRefreshButton).toHaveClass('variant-outline');
    });

    // Click to enable again
    fireEvent.click(autoRefreshButton);
    
    await waitFor(() => {
      expect(autoRefreshButton).toHaveClass('bg-primary');
    });
  });

  it('should update last checked timestamp on refresh', async () => {
    global.fetch = vi.fn().mockResolvedValue({ 
      ok: true, 
      json: async () => ({ version: '1.0.0' }) 
    });

    render(<SystemCheck />);

    await waitFor(() => {
      expect(screen.getByText(/Last checked:/i)).toBeInTheDocument();
    });

    const initialTimestamp = screen.getByText(/Last checked:/i).textContent;

    // Click manual refresh
    const runCheckButton = screen.getByText(/Run Check Now/i);
    fireEvent.click(runCheckButton);

    await waitFor(() => {
      const newTimestamp = screen.getByText(/Last checked:/i).textContent;
      expect(newTimestamp).not.toBe(initialTimestamp);
    });
  });

  it('should display correct status for each health check', async () => {
    global.fetch = vi.fn().mockResolvedValue({ 
      ok: true, 
      json: async () => ({ version: '1.0.0' }) 
    });

    render(<SystemCheck />);

    await waitFor(() => {
      expect(screen.getByText(/Supabase Connection/i)).toBeInTheDocument();
    });

    // Check that status icons are displayed
    expect(screen.getAllByRole('img', { hidden: true })).toBeTruthy();
  });
});

