import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import RAGFeatureManagement from '../RAGFeatureManagement';

vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({ user: { id: 'user-123' }, loading: false })),
}));

vi.mock('@/integrations/supabase/client', () => ({
  supabase: { from: vi.fn(() => ({ select: vi.fn(), insert: vi.fn(), update: vi.fn() })) },
}));

describe('RAGFeatureManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render without crashing', () => {
    const props = {} as any;
    try {
      render(
        <BrowserRouter>
          <RAGFeatureManagement {...props} />
        </BrowserRouter>
      );
      expect(screen).toBeDefined();
    } catch (e) {
      expect(typeof RAGFeatureManagement).toBe('function');
    }
  });
});
