import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Auth from '../Auth';

vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({ user: null, loading: false, signIn: vi.fn(), signUp: vi.fn() })),
}));

vi.mock('@/hooks/useOrganizations', () => ({
  useOrganizations: vi.fn(() => ({ organizations: [], loading: false })),
}));

describe('Auth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render without crashing', () => {
    render(
      <BrowserRouter>
        <Auth />
      </BrowserRouter>
    );
    expect(screen).toBeDefined();
  });
});

