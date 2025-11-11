import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useInvitations } from '../useInvitations';

describe('useInvitations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    const { result } = renderHook(() => useInvitations());
    expect(result.current).toBeDefined();
  });
});
