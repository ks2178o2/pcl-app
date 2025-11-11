import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useFailedUploadCount } from '../useFailedUploadCount';

describe('useFailedUploadCount', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useFailedUploadCount());
    expect(result.current).toBeDefined();
  });
});
