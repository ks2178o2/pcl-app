import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useRAGFeatures } from '../useRAGFeatures';

describe('useRAGFeatures', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useRAGFeatures());
    expect(result.current).toBeDefined();
  });
});
