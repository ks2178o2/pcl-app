import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useIdleTimeoutSettings } from '../useIdleTimeoutSettings';

describe('useIdleTimeoutSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useIdleTimeoutSettings());
    expect(result.current).toBeDefined();
  });
});
