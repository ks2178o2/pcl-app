import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { use2FA } from '../use2FA';

describe('use2FA', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => use2FA());
    expect(result.current).toBeDefined();
  });
});
