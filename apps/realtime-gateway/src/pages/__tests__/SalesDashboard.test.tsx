import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import SalesDashboard from '../SalesDashboard';

// Mock dependencies
vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({ user: { id: 'user-123' }, loading: false })),
}));

vi.mock('@/integrations/supabase/client', () => ({
  supabase: { from: vi.fn(() => ({ select: vi.fn(), insert: vi.fn() })) },
}));

describe('SalesDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render without crashing', () => {
    render(
      <BrowserRouter>
        <SalesDashboard />
      </BrowserRouter>
    );
    expect(screen).toBeDefined();
  });
});
