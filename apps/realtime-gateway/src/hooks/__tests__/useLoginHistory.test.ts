import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useLoginHistory } from '../useLoginHistory';

describe('useLoginHistory', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useLoginHistory());
    expect(result.current).toBeDefined();
  });
});
