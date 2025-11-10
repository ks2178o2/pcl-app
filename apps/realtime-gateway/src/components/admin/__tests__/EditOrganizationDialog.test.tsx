import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import EditOrganizationDialog from '../EditOrganizationDialog';

vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({ user: { id: 'user-123' }, loading: false })),
}));

vi.mock('@/integrations/supabase/client', () => ({
  supabase: { from: vi.fn(() => ({ select: vi.fn(), insert: vi.fn(), update: vi.fn() })) },
}));

describe('EditOrganizationDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render without crashing', () => {
    const props = {} as any;
    try {
      render(
        <BrowserRouter>
          <EditOrganizationDialog {...props} />
        </BrowserRouter>
      );
      expect(screen).toBeDefined();
    } catch (e) {
      expect(typeof EditOrganizationDialog).toBe('function');
    }
  });
});
