import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useOrganizationSecurity } from '../useOrganizationSecurity';

describe('useOrganizationSecurity', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useOrganizationSecurity());
    expect(result.current).toBeDefined();
  });
});
