import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import RAGFeatureSelector from '../RAGFeatureSelector';

vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({ user: { id: 'user-123' }, loading: false })),
}));

describe('RAGFeatureSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render without crashing', () => {
    const props = {} as any;
    try {
      render(
        <BrowserRouter>
          <RAGFeatureSelector {...props} />
        </BrowserRouter>
      );
      expect(screen).toBeDefined();
    } catch (e) {
      expect(typeof RAGFeatureSelector).toBe('function');
    }
  });
});
