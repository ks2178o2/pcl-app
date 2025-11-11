import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useOrganizations } from '../useOrganizations';

describe('useOrganizations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useOrganizations());
    expect(result.current).toBeDefined();
  });
});
