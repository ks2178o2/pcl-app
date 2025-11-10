import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { use-toast } from '../use-toast';

describe('use-toast', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => use-toast());
    expect(result.current).toBeDefined();
  });
});
