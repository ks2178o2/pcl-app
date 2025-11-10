import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { CallAnalysisPage } from '../CallAnalysis';

vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({ user: { id: 'user-123' }, loading: false })),
}));

vi.mock('@/hooks/useCenterSession', () => ({
  useCenterSession: vi.fn(() => ({ availableCenters: [] })),
}));

vi.mock('@/integrations/supabase/client', () => ({
  supabase: { from: vi.fn(() => ({ select: vi.fn(), update: vi.fn() })) },
}));

describe('CallAnalysisPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render without crashing', () => {
    render(
      <BrowserRouter>
        <Routes>
          <Route path="/analysis/:callId" element={<CallAnalysisPage />} />
        </Routes>
      </BrowserRouter>
    );
    expect(screen).toBeDefined();
  });
});

