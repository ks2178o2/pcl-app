import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { use-mobile } from '../use-mobile';

describe('use-mobile', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => use-mobile());
    expect(result.current).toBeDefined();
  });
});
