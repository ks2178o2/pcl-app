import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSystemAdmin } from '../useSystemAdmin';

describe('useSystemAdmin', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useSystemAdmin());
    expect(result.current).toBeDefined();
  });
});
