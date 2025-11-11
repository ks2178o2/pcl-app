import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useIdleTimeout } from '../useIdleTimeout';

describe('useIdleTimeout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useIdleTimeout());
    expect(result.current).toBeDefined();
  });
});
