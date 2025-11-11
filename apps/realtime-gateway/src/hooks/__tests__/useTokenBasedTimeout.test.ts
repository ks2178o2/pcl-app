import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useTokenBasedTimeout } from '../useTokenBasedTimeout';

describe('useTokenBasedTimeout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useTokenBasedTimeout());
    expect(result.current).toBeDefined();
  });
});
