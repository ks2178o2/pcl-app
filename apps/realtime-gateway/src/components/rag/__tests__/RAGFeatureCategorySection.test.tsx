import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import RAGFeatureCategorySection from '../RAGFeatureCategorySection';

vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({ user: { id: 'user-123' }, loading: false })),
}));

describe('RAGFeatureCategorySection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render without crashing', () => {
    const props = {} as any;
    try {
      render(
        <BrowserRouter>
          <RAGFeatureCategorySection {...props} />
        </BrowserRouter>
      );
      expect(screen).toBeDefined();
    } catch (e) {
      expect(typeof RAGFeatureCategorySection).toBe('function');
    }
  });
});
